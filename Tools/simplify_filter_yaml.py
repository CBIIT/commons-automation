#!/usr/bin/env python3
"""Expand checkbox_template/values and facet_key into explicit facet + checkboxes."""
from __future__ import annotations

from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "ObjectRepository"


def simplify_group(g: dict, page_elements: dict) -> dict:
    if g.get("facet_key") and not g.get("facet"):
        fk = g["facet_key"]
        if fk in page_elements:
            g["facet"] = page_elements[fk]
        g.pop("facet_key", None)

    template = g.pop("checkbox_template", None)
    values = g.pop("values", None) or []
    boxes = dict(g.get("checkboxes") or {})
    if template:
        for v in values:
            if v not in boxes:
                boxes[v] = template.replace("{value}", v)
    if boxes:
        g["checkboxes"] = boxes
    return g


def simplify_file(path: Path) -> bool:
    doc = yaml.safe_load(path.read_text()) or {}
    if "groups" not in doc:
        return False
    page_elements = dict(doc.get("elements") or {})
    changed = False
    new_groups = {}
    for key, g in (doc.get("groups") or {}).items():
        before = yaml.dump(g, sort_keys=True)
        g = simplify_group(dict(g), page_elements)
        after = yaml.dump(g, sort_keys=True)
        if before != after:
            changed = True
        new_groups[key] = g
    doc["groups"] = new_groups

    # Drop elements section when nothing references facet_key anymore.
    if page_elements:
        still_need = any(g.get("facet_key") for g in new_groups.values())
        if not still_need:
            doc.pop("elements", None)
            changed = True

    if not changed:
        return False
    path.write_text(
        yaml.dump(
            doc,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
            width=4096,
        )
    )
    return True


def main() -> int:
    updated = []
    for path in sorted(REPO.rglob("*.yaml")):
        if simplify_file(path):
            updated.append(path.relative_to(ROOT))
    for p in updated:
        print(p)
    print(f"Updated {len(updated)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
