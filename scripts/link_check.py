#!/usr/bin/env python3
"""
Simple link checker: scans markdown files for http/https links and reports status codes.
Exits with code 1 if any link returns a 4xx/5xx or times out.
"""
import re
import sys
from pathlib import Path
import requests

TIMEOUT = 10

link_re = re.compile(r"(?P<url>https?://[\w\-./?=#&%:]+)")

def find_markdown_files(root: Path):
    for p in root.rglob("*.md"):
        yield p


def check_url(url: str):
    try:
        r = requests.head(url, allow_redirects=True, timeout=TIMEOUT)
        code = r.status_code
        if code >= 400:
            return False, code
        return True, code
    except Exception as e:
        return False, str(e)


def main():
    repo = Path('.')
    failures = []
    for md in find_markdown_files(repo):
        text = md.read_text(encoding='utf-8')
        for m in link_re.finditer(text):
            url = m.group('url')
            ok, code = check_url(url)
            if not ok:
                failures.append((md.as_posix(), url, code))
                print(f"BROKEN: {md} -> {url} ({code})")
    if failures:
        print(f"Found {len(failures)} broken links")
        sys.exit(1)
    print("All checked links appear healthy")

if __name__ == '__main__':
    main()
