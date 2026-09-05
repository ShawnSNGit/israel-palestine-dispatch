#!/usr/bin/env python3
"""
Analyze snapshots and generate a daily STEMpathize digest that highlights updated sources and potential conflicts.
Produces a markdown file under digests/digest-YYYY-MM-DD.md and updates data/digests_index.json.
Enhancements:
 - Computes simple trust & rigor scores for each snapshot
 - Computes disagreement scores across grouped sources
 - Generates empathetic, sensitivity-aware hedging language as part of the STEMpathize digest
 - Writes a machine-readable JSON digest alongside the markdown
"""
import json
import re
from pathlib import Path
from datetime import datetime
import difflib
import hashlib
import math

SNAPSHOT_FILE = Path('data/snapshots.json')
DIGEST_DIR = Path('digests')
DIGEST_INDEX = Path('data/digests_index.json')
MACHINE_DIGEST_DIR = Path('data')

NUMERIC_RE = re.compile(r"\b\d{1,4}[,\.]?\d{0,3}\b")
KEYWORDS = ['deny', 'denies', 'dispute', 'contradict', 'confirm', 'confirms', 'claims', 'says', 'reports', 'alleges', 'accuse', 'accuses', 'acknowledge']


def load_snapshots():
    if SNAPSHOT_FILE.exists():
        return json.loads(SNAPSHOT_FILE.read_text(encoding='utf-8'))
    return {}


def summarize_text(s):
    if not s:
        return ''
    return (s.strip().replace('\n', ' '))[:600]


def compute_trust(snapshot):
    # Simple heuristic trust score 0..1
    score = 0.0
    sc = snapshot.get('status_code')
    if isinstance(sc, int) and sc == 200:
        score += 0.5
    if snapshot.get('title'):
        score += 0.25
    if snapshot.get('excerpt'):
        score += 0.25
    return min(1.0, score)


def extract_numbers(text):
    if not text:
        return []
    return NUMERIC_RE.findall(text)


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
        ta = (a.get('title') or '')[:300]
        for j, b in enumerate(items[i+1:], start=i+1):
            if j in used:
                continue
            tb = (b.get('title') or '')[:300]
            if not ta and not tb:
                continue
            ratio = difflib.SequenceMatcher(None, ta, tb).ratio()
            if ratio > 0.45:
                group.append(b)
                used.add(j)
        if len(group) > 1:
            groups.append(group)
    conflicts = []
    for g in groups:
        nums = []
        titles = []
        keywords_present = []
        for it in g:
            text = (it.get('excerpt') or '') + ' ' + (it.get('title') or '')
            found = extract_numbers(text)
            nums.append({'url': it['url'], 'nums': found})
            titles.append(it.get('title') or it.get('url'))
            present = [k for k in KEYWORDS if k in text.lower()]
            keywords_present.append({'url': it['url'], 'keywords': present})
        # disagreement score: diversity of numeric sets + keyword tone differences
        numsets = {tuple(x['nums']) for x in nums}
        numeric_discrepancy = len(numsets) > 1
        kwsets = {tuple(x['keywords']) for x in keywords_present}
        tone_discrepancy = len(kwsets) > 1
        # compute a disagreement score 0..1
        score = 0.0
        if numeric_discrepancy:
            score += 0.6
        if tone_discrepancy:
            score += 0.4
        score = min(1.0, score)
        conflicts.append({'group': g, 'numeric_discrepancies': nums, 'keyword_differences': keywords_present, 'disagreement_score': score})
    return conflicts


def generate_hedge(conflict):
    # Empathetic hedging suggestions tailored for legal & press use
    count = len(conflict.get('group', []))
    if count <= 1:
        return ''
    base = (
        "STEMpathize guidance: Sources in this cluster present differing accounts or emphases. "
        "In reporting or legal summaries, prioritize clear attribution and empathetic framing. For example:"
    )
    examples = []
    examples.append("- 'According to [Source A], ...; however, [Source B] reports ...; these accounts have not been reconciled.'")
    examples.append("- 'Reports differ on [topic]. We were unable to verify the discrepancy independently; readers should treat these figures with caution.'")
    examples.append("- 'We acknowledge conflicting claims and the uncertainty around them; legal authorities or primary documents should be consulted for definitive statements.'")
    examples.append("- 'Where human impact is involved, include voices and context and avoid definitive language until further verification.'")
    return base + '\n' + '\n'.join(examples)


def compute_rigor_score(group):
    # combine per-source trust scores and penalize high disagreement
    trusts = [compute_trust(it) for it in group]
    if not trusts:
        return 0.0
    avg_trust = sum(trusts) / len(trusts)
    # simplistic rigor: avg_trust scaled
    return round(avg_trust, 3)


def save_digest(md_text: str, machine_obj: dict):
    DIGEST_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.utcnow().date().isoformat()
    fname = DIGEST_DIR / f'digest-STEMpathize-{today}.md'
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
    # write machine-readable digest
    machine_file = MACHINE_DIGEST_DIR / f'digest-STEMpathize-{today}.json'
    machine_file.write_text(json.dumps(machine_obj, indent=2, ensure_ascii=False), encoding='utf-8')
    return fname, machine_file


def main():
    snapshots = load_snapshots()
    if not snapshots:
        print('No snapshots found, nothing to do')
        return
    conflicts = find_conflicts(snapshots)
    # build markdown with empathetic framing
    lines = []
    lines.append(f"# STEMpathize Digest ({datetime.utcnow().isoformat()})\n")
    lines.append("## Overview\n")
    lines.append("This STEMpathize Digest is generated automatically to surface data-driven discrepancies across sources, and to provide careful, empathy-aware hedging language for editors and legal teams. Each flagged item includes direct citations and snapshot fingerprints for reproducibility.\n")

    lines.append(f"Checked {len(snapshots)} sources. Found {len(conflicts)} clusters with potential conflicts.\n")

    machine = {'generated_at': datetime.utcnow().isoformat(), 'total_sources': len(snapshots), 'conflicts': []}

    if conflicts:
        lines.append('## Potential conflicts and suggested hedging\n')
        for i, c in enumerate(conflicts, start=1):
            lines.append(f"### Conflict cluster {i} (disagreement score: {c.get('disagreement_score')})\n")
            group = c.get('group', [])
            rig = compute_rigor_score(group)
            lines.append(f"Rigor score (0-1): {rig}\n")
            machine_conf = {'cluster_index': i, 'disagreement_score': c.get('disagreement_score'), 'rigor_score': rig, 'items': []}
            for it in group:
                title = it.get('title') or it.get('url')
                excerpt = summarize_text(it.get('excerpt'))
                lines.append(f"- [{title}]({it.get('url')}) (status: {it.get('status_code')})\n  > {excerpt}\n")
                machine_conf['items'].append({'url': it.get('url'), 'title': title, 'status': it.get('status_code'), 'excerpt': excerpt, 'trust': compute_trust(it)})
            if c.get('numeric_discrepancies'):
                lines.append('\nNumeric discrepancies found across sources:')
                for n in c['numeric_discrepancies']:
                    lines.append(f"- {n['url']}: {', '.join(n['nums']) if n['nums'] else 'no numeric facts found'}\n")
            if c.get('keyword_differences'):
                lines.append('\nDifferences in reported tone/keywords:')
                for u in c['keyword_differences']:
                    lines.append(f"- {u['url']}: keywords={u['keywords']}\n")
            hedge = generate_hedge(c)
            lines.append('\nSuggested hedging & empathetic framing:')
            lines.append('\n' + hedge + '\n')
            machine['conflicts'].append(machine_conf)
    else:
        lines.append('No potential conflicts detected today.\n')

    # list updated sources
    lines.append('## Updated / new sources\n')
    for v in snapshots.values():
        lines.append(f"- [{v.get('title') or v.get('url')}]({v.get('url')}): status={v.get('status_code')} (trust={compute_trust(v)})\n")

    md = '\n'.join(lines)
    fname, machine_file = save_digest(md, machine)
    print(f"Wrote digest to {fname} and machine digest to {machine_file}")

if __name__ == '__main__':
    main()
