#!/usr/bin/env python3
"""
Analyze snapshots and generate a daily digest that highlights updated sources and potential conflicts.
Produces a markdown file under digests/digest-YYYY-MM-DD.md and updates data/digests_index.json.
"""
import json
import re
from pathlib import Path
from datetime import datetime
import difflib
import hashlib

SNAPSHOT_FILE = Path('data/snapshots.json')
DIGEST_DIR = Path('digests')
DIGEST_INDEX = Path('data/digests_index.json')

NUMERIC_RE = re.compile(r"\b\d{3,}|\b\d{1,4}[\,\.]\d{1,3}|\b\d{1,4}\/\d{1,4}|\b\d{4}\b")


def load_snapshots():
    if SNAPSHOT_FILE.exists():
        return json.loads(SNAPSHOT_FILE.read_text(encoding='utf-8'))
    return {}


def find_conflicts(snapshots):
    # group by fuzzy title similarity
    items = list(snapshots.values())
    groups = []
    used = set()
    for i, a in enumerate(items):
        if i in used:
            continue
        group = [a]
        used.add(i)
        for j, b in enumerate(items[i+1:], start=i+1):
            if j in used:
                continue
            ta = (a.get('title') or '')[:300]
            tb = (b.get('title') or '')[:300]
            if not ta and not tb:
                continue
            ratio = difflib.SequenceMatcher(None, ta, tb).ratio()
            if ratio > 0.45:
                group.append(b)
                used.add(j)
        if len(group) > 1:
            groups.append(group)
    # for each group, look for numeric discrepancies
    conflicts = []
    for g in groups:
        nums = []
        for it in g:
            text = (it.get('excerpt') or '') + ' ' + (it.get('title') or '')
            found = NUMERIC_RE.findall(text)
            nums.append({'url': it['url'], 'nums': found, 'title': it.get('title')})
        # if numeric lists differ, flag as potential conflict
        numsets = {tuple(x['nums']) for x in nums}
        if len(numsets) > 1:
            conflicts.append({'group': g, 'numeric_discrepancies': nums})
        else:
            # also flag differences in wording like 'deny' vs 'confirm'
            keywords = ['deny', 'denies', 'dispute', 'contradict', 'confirm', 'confirms', 'claims', 'says', 'reports', 'alleges']
            ksets = []
            for it in g:
                txt = ((it.get('excerpt') or '') + ' ' + (it.get('title') or '')).lower()
                present = [k for k in keywords if k in txt]
                ksets.append((it['url'], present))
            if any(len(p) != len(ksets[0][1]) for _, p in ksets):
                conflicts.append({'group': g, 'keyword_differences': ksets})
    return conflicts


def generate_hedge(conflict):
    # Simple hedging suggestions
    count = len(conflict.get('group', []))
    if count == 0:
        return ''
    if count == 1:
        return ''
    return (
        "Note: sources in this cluster present different information or emphases. "
        "When reporting, use cautious language: e.g., 'reports differ on...', 'sources differ about...', 'claims are disputed', "
        "and include direct citations to the original reports. Consider indicating uncertainty (e.g., 'unverified', 'according to [source]')."
    )


def save_digest(md_text: str):
    DIGEST_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.utcnow().date().isoformat()
    fname = DIGEST_DIR / f'digest-{today}.md'
    fname.write_text(md_text, encoding='utf-8')
    # update index
    idx = []
    if DIGEST_INDEX.exists():
        try:
            idx = json.loads(DIGEST_INDEX.read_text(encoding='utf-8'))
        except Exception:
            idx = []
    idx.append({'date': today, 'path': str(fname)})
    DIGEST_INDEX.write_text(json.dumps(idx, indent=2), encoding='utf-8')
    return fname


def main():
    snapshots = load_snapshots()
    if not snapshots:
        print('No snapshots found, nothing to do')
        return
    conflicts = find_conflicts(snapshots)
    # build markdown
    lines = []
    lines.append(f"# Daily synthesis digest ({datetime.utcnow().isoformat()})\n")
    lines.append("## Summary\n")
    lines.append(f"Checked {len(snapshots)} sources. Found {len(conflicts)} clusters with potential conflicts.\n")

    if conflicts:
        lines.append('## Potential conflicts and suggested hedging\n')
        for i, c in enumerate(conflicts, start=1):
            lines.append(f"### Conflict cluster {i}\n")
            for it in c.get('group', []):
                lines.append(f"- [{it.get('title') or it.get('url')}]({it.get('url')}) (status: {it.get('status_code')})\n  > { (it.get('excerpt') or '')[:300] }\n")
            if 'numeric_discrepancies' in c:
                lines.append('\nNumeric discrepancies found across sources:')
                for n in c['numeric_discrepancies']:
                    lines.append(f"- {n['url']}: {', '.join(n['nums']) if n['nums'] else 'no numeric facts found'}\n")
            if 'keyword_differences' in c:
                lines.append('\nDifferences in reported tone/keywords:')
                for u, p in c['keyword_differences']:
                    lines.append(f"- {u}: keywords={p}\n")
            lines.append('\nSuggested hedging:')
            lines.append('\n' + generate_hedge(c) + '\n')
    else:
        lines.append('No potential conflicts detected today.\n')

    # list updated sources
    lines.append('## Updated / new sources\n')
    # naive: list all snapshots (could filter by last_fetched = today)
    for v in snapshots.values():
        lines.append(f"- [{v.get('title') or v.get('url')}]({v.get('url')}): status={v.get('status_code')}\n")

    md = '\n'.join(lines)
    fname = save_digest(md)
    print(f"Wrote digest to {fname}")

if __name__ == '__main__':
    main()
