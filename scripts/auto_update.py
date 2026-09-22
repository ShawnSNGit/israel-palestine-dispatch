#!/usr/bin/env python3
"""
Fetch sources listed in markdown dispatch frontmatter, snapshot their title and lead paragraph,
and write snapshots to data/snapshots.json. Returns a dict of {url: {title, excerpt, status_code, last_fetched}}.
Robustness improvements:
 - honors robots.txt where possible
 - uses a requests.Session with retries and backoff
 - rate-limits requests within a run
 - polite User-Agent identifying the STEMpathize crawler
"""
import json
import re
import sys
import time
from pathlib import Path
from datetime import datetime
import hashlib
import requests
from bs4 import BeautifulSoup
import yaml
import urllib.parse
import urllib.robotparser
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TIMEOUT = 10
ROOT = Path('.')
SNAPSHOT_FILE = Path('data/snapshots.json')

link_re = re.compile(r"https?://[\w\-./?=#&%:]+")

# polite defaults
USER_AGENT = 'STEMpathizeBot/1.0 (+https://github.com/ShawnSNGit/israel-palestine-dispatch)'
RATE_LIMIT_SECONDS = 0.5  # pause between requests to avoid hammering sites
MAX_RETRIES = 3


def find_markdown_files(root: Path):
    for p in root.rglob('*.md'):
        yield p


def extract_front_matter(text: str):
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            return parts[1]
    return None


def extract_urls_from_frontmatter(fm: str):
    try:
        obj = yaml.safe_load(fm)
    except Exception:
        return []
    urls = []
    if isinstance(obj, dict) and 'sources' in obj and isinstance(obj['sources'], list):
        for s in obj['sources']:
            if isinstance(s, dict) and 'url' in s:
                urls.append(s['url'])
            elif isinstance(s, str):
                urls.append(s)
    return urls


def is_allowed_by_robots(url: str, session: requests.Session):
    try:
        parsed = urllib.parse.urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        # fetch robots.txt with session
        resp = session.get(robots_url, timeout=5, headers={'User-Agent': USER_AGENT})
        if resp.status_code == 200:
            rp.parse(resp.text.splitlines())
            return rp.can_fetch(USER_AGENT, url)
        # if robots not present or inaccessible, default to allow
        return True
    except Exception:
        return True


def make_session():
    s = requests.Session()
    retries = Retry(total=MAX_RETRIES, backoff_factor=0.8, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET", "HEAD"])
    s.mount('https://', HTTPAdapter(max_retries=retries))
    s.mount('http://', HTTPAdapter(max_retries=retries))
    s.headers.update({'User-Agent': USER_AGENT})
    return s


def fetch_snapshot(session: requests.Session, url: str):
    try:
        # Respect robots.txt
        if not is_allowed_by_robots(url, session):
            return {'status_code': 'blocked_by_robots', 'title': '', 'excerpt': '', 'last_fetched': datetime.utcnow().isoformat()}
        r = session.get(url, timeout=TIMEOUT)
        status = r.status_code
        text = r.text if r.ok else ''
        title = ''
        excerpt = ''
        if text:
            soup = BeautifulSoup(text, 'lxml')
            t = soup.find('title')
            if t and t.string:
                title = t.string.strip()
            # find first meaningful paragraph (skip nav, scripts)
            for p in soup.find_all('p'):
                txt = p.get_text(strip=True)
                if txt and len(txt.split()) > 5:
                    excerpt = txt
                    break
        return {'status_code': status, 'title': title, 'excerpt': excerpt, 'last_fetched': datetime.utcnow().isoformat()}
    except Exception as e:
        return {'status_code': 'error', 'title': '', 'excerpt': str(e), 'last_fetched': datetime.utcnow().isoformat()}


def load_snapshots():
    if SNAPSHOT_FILE.exists():
        try:
            return json.loads(SNAPSHOT_FILE.read_text(encoding='utf-8'))
        except Exception:
            return {}
    return {}


def save_snapshots(d):
    SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_FILE.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding='utf-8')


def main():
    session = make_session()
    snapshots = load_snapshots()
    urls = set()
    for md in find_markdown_files(ROOT):
        text = md.read_text(encoding='utf-8')
        fm = extract_front_matter(text)
        if fm:
            for u in extract_urls_from_frontmatter(fm):
                urls.add(u)
        # also scan body for links as fallback
        for m in link_re.finditer(text):
            urls.add(m.group(0))
    changed = False
    count = 0
    for url in sorted(urls):
        count += 1
        key = hashlib.sha256(url.encode('utf-8')).hexdigest()
        existing = snapshots.get(key)
        new = fetch_snapshot(session, url)
        # compare simple fields
        if existing is None or existing.get('title') != new.get('title') or existing.get('excerpt') != new.get('excerpt') or existing.get('status_code') != new.get('status_code'):
            snapshots[key] = {'url': url, **new}
            changed = True
        # rate limit to be polite
        time.sleep(RATE_LIMIT_SECONDS)
    if changed:
        save_snapshots(snapshots)
    print(f"Checked {len(urls)} urls ({count} processed), changed={changed}")

if __name__ == '__main__':
    main()
