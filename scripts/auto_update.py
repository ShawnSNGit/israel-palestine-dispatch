#!/usr/bin/env python3
"""
Fetch sources listed in markdown dispatch frontmatter, snapshot their title and lead paragraph,
and write snapshots to data/snapshots.json. Returns a dict of {url: {title, excerpt, status_code, last_fetched}}.
"""
import json
import re
import sys
from pathlib import Path
from datetime import datetime
import hashlib
import requests
from bs4 import BeautifulSoup
import yaml

TIMEOUT = 10
ROOT = Path('.')
SNAPSHOT_FILE = Path('data/snapshots.json')

link_re = re.compile(r"https?://[\w\-./?=#&%:]+")


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


def fetch_snapshot(url: str):
    try:
        r = requests.get(url, timeout=TIMEOUT, headers={'User-Agent': 'Mozilla/5.0 (compatible)'} )
        status = r.status_code
        text = r.text if r.ok else ''
        title = ''
        excerpt = ''
        if text:
            soup = BeautifulSoup(text, 'lxml')
            t = soup.find('title')
            if t and t.string:
                title = t.string.strip()
            # find first meaningful paragraph
            p = soup.find('p')
            if p and p.get_text(strip=True):
                excerpt = p.get_text(strip=True)
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
    for url in sorted(urls):
        key = hashlib.sha256(url.encode('utf-8')).hexdigest()
        existing = snapshots.get(key)
        new = fetch_snapshot(url)
        # compare simple fields
        if existing is None or existing.get('title') != new.get('title') or existing.get('excerpt') != new.get('excerpt') or existing.get('status_code') != new.get('status_code'):
            snapshots[key] = {'url': url, **new}
            changed = True
    if changed:
        save_snapshots(snapshots)
    print(f"Checked {len(urls)} urls, changed={changed}")

if __name__ == '__main__':
    main()
