#!/usr/bin/env python3
"""Check a brewed skill folder and package it as <name>.skill.

Usage:
  python <skill-dir>/scripts/bottle.py <brewed-skill-folder> [--out DIR] [--check-only]

Checks:
  - SKILL.md has YAML frontmatter that parses, with name and description
  - name is kebab-case, at most 64 characters, and avoids reserved words
  - description is at most 1024 characters with no angle brackets
  - only name and description are in the frontmatter (claude.ai keeps no others)
  - the body is lean (warns past 120 non-empty lines, fails past 500)
  - RECIPE.md exists and its "## Ingredients" table has at least one row
  - every script in the folder is listed in RECIPE.md by its relative path

Packaging zips the folder (folder at the archive root) into <name>.skill,
which installs on claude.ai via the file card's Save skill button or
Settings > Skills upload, and in Claude Code by unzipping into
~/.claude/skills/.
"""
import argparse
import re
import sys
import zipfile
from pathlib import Path

RESERVED = ("claude", "anthropic")
SCRIPT_EXT = {".py", ".sh", ".bash", ".zsh", ".js", ".mjs", ".cjs", ".ts", ".rb", ".pl", ".ps1"}
BODY_WARN, BODY_MAX = 120, 500


def parse_frontmatter(text: str) -> tuple[dict | None, str, str | None]:
    """Return (meta, body, error). Uses PyYAML when present so folded
    descriptions parse and invalid YAML (an unquoted colon) is caught."""
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return None, text, "SKILL.md does not start with a --- frontmatter block"
    raw, body = m.group(1), m.group(2)
    try:
        import yaml  # type: ignore
    except ImportError:
        yaml = None
    if yaml is not None:
        try:
            meta = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            return None, body, f"frontmatter is not valid YAML ({str(e).splitlines()[0]}); quote values that contain ': '"
        if not isinstance(meta, dict):
            return None, body, "frontmatter is not a key: value mapping"
        return {k: ("" if v is None else str(v).strip()) for k, v in meta.items()}, body, None
    # Fallback without PyYAML: handle plain values and folded/literal blocks.
    meta, key, block = {}, None, []
    for line in raw.splitlines():
        if key and (line.startswith((" ", "\t")) or not line.strip()):
            block.append(line.strip())
            continue
        if key:
            meta[key] = " ".join(b for b in block if b)
            key, block = None, []
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip()
            if v in (">", ">-", "|", "|-", ">+", "|+"):
                key = k.strip()
                continue
            if ": " in v and not (v[:1] in "\"'" and v[-1:] == v[:1]):
                return None, body, f"value of '{k.strip()}' has an unquoted ': '; quote it"
            meta[k.strip()] = v.strip('"').strip("'")
    if key:
        meta[key] = " ".join(b for b in block if b)
    return meta, body, None


def ingredient_rows(recipe: str) -> list[str]:
    """Rows of the first table after the '## Ingredients' heading only."""
    m = re.search(r"^##\s+Ingredients\s*$(.*?)(?=^##\s|\Z)", recipe, re.S | re.M)
    if not m:
        return []
    rows, started = [], False
    for line in m.group(1).splitlines():
        if line.strip().startswith("|"):
            started = True
            if not re.match(r"^\s*\|[\s:|-]+\|\s*$", line):
                rows.append(line)
        elif started:
            break
    return rows[1:]  # drop the header row


def check(folder: Path) -> tuple[list[str], list[str], dict]:
    errors, warnings, info = [], [], {}
    skill_md = folder / "SKILL.md"
    if not skill_md.exists():
        return [f"{skill_md} is missing"], warnings, info
    meta, body, err = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    if err:
        return [err], warnings, info
    name, desc = meta.get("name", ""), meta.get("description", "")
    info["name"] = name

    if not name:
        errors.append("frontmatter has no name")
    else:
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
            errors.append(f"name '{name}' is not kebab-case")
        if len(name) > 64:
            errors.append("name is longer than 64 characters")
        if any(r in name for r in RESERVED):
            errors.append(f"name '{name}' contains a reserved word ({', '.join(RESERVED)})")
        if folder.name != name:
            warnings.append(f"folder '{folder.name}' differs from name '{name}'; packaging uses the name")

    if not desc:
        errors.append("frontmatter has no description")
    else:
        if len(desc) > 1024:
            errors.append(f"description is {len(desc)} characters (max 1024)")
        if "<" in desc or ">" in desc:
            errors.append("description contains angle brackets")
        if len(desc) > 400:
            warnings.append(f"description is {len(desc)} characters; aim for under 400, trigger conditions only")
    info["description_chars"] = len(desc)
    extra = sorted(set(meta) - {"name", "description"})
    if extra:
        warnings.append(f"extra frontmatter keys {extra} are dropped on claude.ai; keep them only for Claude Code")

    lines = [l for l in body.splitlines() if l.strip()]
    info["body_lines"] = len(lines)
    info["body_words"] = len(body.split())
    if len(lines) > BODY_MAX:
        errors.append(f"body has {len(lines)} non-empty lines (max {BODY_MAX})")
    elif len(lines) > BODY_WARN:
        warnings.append(f"body has {len(lines)} non-empty lines; a brew should usually stay under {BODY_WARN}")

    recipe = folder / "RECIPE.md"
    if not recipe.exists():
        errors.append("RECIPE.md is missing (provenance is part of the product)")
    else:
        rt = recipe.read_text(encoding="utf-8")
        rows = ingredient_rows(rt)
        info["ingredients"] = len(rows)
        if not rows:
            errors.append("RECIPE.md has no rows in a table under '## Ingredients'")
        elif len(rows) > 3:
            warnings.append(f"{len(rows)} ingredients; results tend to drop past three")
        scripts = [p for p in folder.rglob("*") if p.is_file() and p.suffix in SCRIPT_EXT]
        unlisted = [str(p.relative_to(folder)) for p in scripts if str(p.relative_to(folder)) not in rt]
        if unlisted:
            errors.append(f"scripts not listed in RECIPE.md by relative path: {unlisted}")
    return errors, warnings, info


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--out", default=None)
    ap.add_argument("--check-only", action="store_true")
    a = ap.parse_args()
    folder = Path(a.folder).resolve()

    errors, warnings, info = check(folder)
    for k, v in info.items():
        print(f"{k}: {v}")
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")
    if errors:
        print("not bottled: fix the errors above")
        return 1
    if a.check_only:
        print("check passed")
        return 0

    name = info["name"]
    out_dir = Path(a.out) if a.out else folder.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{name}.skill"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(folder.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and p.name != ".DS_Store":
                z.write(p, Path(name) / p.relative_to(folder))
    print(f"bottled: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
