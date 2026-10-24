#!/usr/bin/env python3
"""Fill a cauldron template with JSON data.

Usage:
  python scripts/fill_template.py <template.html> <data.json> <out.html>

Replaces the __DATA__ placeholder with the JSON from data.json. The JSON is
escaped so a stray "</script>" inside a skill name or note cannot break out
of the data block. Exits non-zero with a readable message on bad input.
"""
import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__.strip())
        return 2
    template, data_path, out = (Path(p) for p in sys.argv[1:])
    html = template.read_text(encoding="utf-8")
    if "__DATA__" not in html:
        print(f"error: {template} has no __DATA__ placeholder")
        return 1
    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"error: {data_path} is not valid JSON: {e}")
        return 1

    problems = check(data, template.name)
    for p in problems:
        print(f"warning: {p}")

    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    out.write_text(html.replace("__DATA__", payload), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    return 0


def check(data: dict, template_name: str) -> list[str]:
    """Light schema checks so a bad fill is caught before the user sees it."""
    problems = []
    if "cauldron" in template_name:
        rows = data.get("rows") or []
        if not rows:
            problems.append("no rows; the cauldron will be empty")
        names = []
        for r in rows:
            items = r.get("items") or []
            if not items:
                problems.append(f"row '{r.get('label')}' has no items")
            for it in items:
                if not it.get("name"):
                    problems.append(f"an item in row '{r.get('label')}' has no name")
                names.append(it.get("name"))
        dupes = {n for n in names if names.count(n) > 1}
        if dupes:
            problems.append(f"duplicate ingredient names (picks are keyed by name): {sorted(dupes)}")
        for n in data.get("preselected") or []:
            if n not in names:
                problems.append(f"preselected '{n}' is not an ingredient")
    elif "recipe" in template_name:
        if data.get("mode") == "dna":
            if not data.get("archetype"):
                problems.append("dna card has no archetype")
        else:
            if not data.get("ingredients"):
                problems.append("recipe card has no ingredients")
            if not (data.get("title") or data.get("name")):
                problems.append("recipe card has no title or name")
    return problems


if __name__ == "__main__":
    sys.exit(main())
