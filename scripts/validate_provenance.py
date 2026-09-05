from pathlib import Path
import sys
import yaml

REQUIRED_FIELDS = ["title", "authors", "date_published", "sources", "confidence_level"]

def find_files(root: Path):
    for p in root.rglob("*.md"):
        yield p


def extract_front_matter(text: str):
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            return parts[1]
    return None


def validate_file(path: Path):
    text = path.read_text(encoding='utf-8')
    fm = extract_front_matter(text)
    if not fm:
        return False, 'missing frontmatter'
    try:
        obj = yaml.safe_load(fm)
    except Exception as e:
        return False, f'yaml parse error: {e}'
    for f in REQUIRED_FIELDS:
        if f not in obj:
            return False, f'missing field: {f}'
    return True, 'ok'


def main():
    repo = Path('.')
    failures = []
    for md in find_files(repo):
        ok, msg = validate_file(md)
        if not ok:
            failures.append((md.as_posix(), msg))
            print(f"INVALID: {md} -> {msg}")
    if failures:
        print(f"Found {len(failures)} invalid files")
        sys.exit(1)
    print('All markdown files passed provenance validation')

if __name__ == '__main__':
    main()
