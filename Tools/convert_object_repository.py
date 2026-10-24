"""
Convert the Katalon Object Repository (*.rs XML, one file per element) into compact YAML
(one file per page/section) for this framework.

    python Tools/convert_object_repository.py --katalon ../Commons_Automation --apps C3DC GC

What it does
  * Every Katalon folder becomes one YAML page file (Filters/Study -> filters/study.yaml).
  * Filter facets are recognised (a folder holding *Ddn / *Chkbx elements) and written as a
    `groups:` entry with dropdown / checkboxes / search box, instead of dozens of tiny files.
  * When most checkboxes in a group share one XPath that only differs by the value
    (…checkbox_dbGaP ACCESSION_phs000466…), they collapse into a single `checkbox_template`
    with a {value} placeholder. Irregular ones stay listed under `checkboxes:`.

Re-running is safe: files are regenerated from Katalon each time (edit the YAML by hand only
after you stop using this converter).
"""
import argparse
import collections
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

# Katalon Object Repository folder name (Commons_Automation still uses CDS for General Commons).
KATALON_APP = {"GC": "CDS", "ICDC": "Canine"}


def framework_element_name(app: str, katalon_name: str) -> str:
    """GC app uses GC_* locator keys; Katalon Object Repository still names them CDS_*."""
    if app != "GC":
        return katalon_name
    if katalon_name.startswith("CDSResults"):
        return "GCResults" + katalon_name[len("CDSResults") :]
    if katalon_name.startswith("CDS_"):
        return "GC_" + katalon_name[len("CDS_") :]
    return katalon_name


class FlowList(list):
    """A list dumped on one line: [a, b, c]."""


yaml.SafeDumper.add_representer(
    FlowList, lambda d, data: d.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True))

CHKBX_SUFFIX = re.compile(r"[-_]Chkbx$")
DDN_SUFFIX = re.compile(r"[-_]Ddn$")
SEARCH_SUFFIX = re.compile(r"_Search$")
SKIP_DIRS = {"Z-ObsoleteObjects"}
# CCDI Hub has no explore UI here — /explore opens C3DC. Do not import ExplorePage or Filters.
SKIP_REL_PREFIXES = {"CCDI": ("ExplorePage",)}
SKIP_ROOT_ELEMENTS = {"CCDI": {"Participants_ResultsTab"}}
TEMPLATE_MIN_COUNT = 3


def slug(part: str) -> str:
    """ResultTabs -> result_tabs, V_HomePage -> v_home_page, Data_page -> data_page"""
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", part)
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").lower()
    return s


def read_locator(rs_file: Path):
    """Return (name, xpath) for one Katalon .rs file, or (name, None) if unusable."""
    root = ET.parse(rs_file).getroot()
    name = root.findtext("name")
    method = root.findtext("selectorMethod")
    coll = {e.findtext("key"): (e.findtext("value") or "") for e in root.findall("selectorCollection/entry")}
    # Some objects keep their locator in a property that is not flagged "selected" and have an
    # empty selector collection (e.g. CDS Library Selection checkboxes). Use it as a fallback.
    props = {}
    for p in root.findall("webElementProperties"):
        if p.findtext("name") and p.findtext("value"):
            if p.findtext("isSelected") == "true" or p.findtext("name") not in props:
                props[p.findtext("name")] = p.findtext("value")

    def looks_like_xpath(x):
        return bool(x) and x.lstrip().startswith(("/", "(", "."))

    candidates = []
    if method in coll:
        candidates.append(coll[method])
    candidates += [coll.get("XPATH", ""), coll.get("BASIC", ""), props.get("xpath", "")]
    for c in candidates:
        if looks_like_xpath(c):
            return name, c.strip()
    if props.get("id"):
        return name, f'//*[@id="{props["id"]}"]'
    return name, None


def collapse_checkboxes(items: dict):
    """items: {token: xpath}. Returns (template or None, explicit_dict)."""
    counts = collections.Counter()
    per_token = {}
    for token, xp in items.items():
        if token and token in xp:
            tpl = xp.replace(token, "{value}")
            per_token[token] = tpl
            counts[tpl] += 1
    if not counts:
        return None, dict(items)
    tpl, n = counts.most_common(1)[0]
    if n < TEMPLATE_MIN_COUNT:
        return None, dict(items)
    explicit = {t: xp for t, xp in items.items() if per_token.get(t) != tpl}
    return tpl, explicit


def convert_app(katalon_root: Path, app: str, out_root: Path) -> dict:
    katalon_app = KATALON_APP.get(app, app)
    src = katalon_root / "Object Repository" / katalon_app
    if not src.is_dir():
        raise SystemExit(f"Not found: {src}")

    # folder (relative posix path, '' for app root) -> {element name: xpath}
    folders = collections.defaultdict(dict)
    skipped = []
    for rs in sorted(src.rglob("*.rs")):
        rel_dir = rs.parent.relative_to(src).as_posix()
        rel_dir = "" if rel_dir == "." else rel_dir
        if any(p in SKIP_DIRS for p in rel_dir.split("/")):
            continue
        if any(rel_dir == p or rel_dir.startswith(p + "/") for p in SKIP_REL_PREFIXES.get(app, ())):
            continue
        if "Filters" in rel_dir.split("/"):
            continue
        name, xp = read_locator(rs)
        if not xp:
            skipped.append(str(rs.relative_to(src)))
            continue
        if not rel_dir and name in SKIP_ROOT_ELEMENTS.get(app, ()):
            continue
        folders[rel_dir][framework_element_name(app, name)] = xp

    def is_group_folder(d):
        return any(CHKBX_SUFFIX.search(n) or DDN_SUFFIX.search(n) for n in folders[d])

    pages = collections.OrderedDict()   # page_dir -> {"elements": {}, "groups": {}}
    for d in sorted(folders):
        if is_group_folder(d):
            page_dir = os.path.dirname(d)               # facet folder holds the yaml
            group_key = "/".join(d.split("/")[-2:])      # <Facet>/<Group>
            page = pages.setdefault(page_dir, {"elements": {}, "groups": {}})
            elems = folders[d]
            group = {}
            facet_candidates = [n for n in folders.get(page_dir, {}) if "facet" in n.lower()]
            if facet_candidates:
                group["facet"] = folders[page_dir][facet_candidates[0]]
            ddn = sorted(n for n in elems if DDN_SUFFIX.search(n))
            if ddn:
                group["dropdown"] = elems[ddn[0]]
            if len(ddn) > 1:      # e.g. Library Source Material / Library Source Molecule
                group["dropdowns"] = [elems[n] for n in ddn]
            search = [n for n in elems if SEARCH_SUFFIX.search(n)]
            if search:
                group["search"] = elems[search[0]]
            chk = {CHKBX_SUFFIX.sub("", n): xp for n, xp in elems.items() if CHKBX_SUFFIX.search(n)}
            tpl, explicit = collapse_checkboxes(chk)
            if tpl:
                group["checkbox_template"] = tpl
                # values that exist in Katalon (the template accepts any value at run time; the
                # generator uses this list to flag Katalon scripts that name a checkbox that never existed)
                group["values"] = FlowList(sorted(t for t in chk if t not in explicit))
            if explicit:
                group["checkboxes"] = explicit
            extras = {n: xp for n, xp in elems.items()
                      if not (CHKBX_SUFFIX.search(n) or DDN_SUFFIX.search(n) or SEARCH_SUFFIX.search(n))}
            if extras:
                group["other"] = extras
            page["groups"][group_key] = group
        else:
            page = pages.setdefault(d, {"elements": {}, "groups": {}})
            page["elements"].update(folders[d])

    written = 0
    n_elements = 0
    n_entries = 0
    for page_dir, page in pages.items():
        parts = [slug(p) for p in page_dir.split("/")] if page_dir else ["root"]
        out_file = out_root / app / Path(*parts[:-1]) / f"{parts[-1]}.yaml"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        doc = {"page": page_dir or "(root)"}
        if page["elements"]:
            doc["elements"] = dict(sorted(page["elements"].items()))
        if page["groups"]:
            doc["groups"] = dict(sorted(page["groups"].items()))
        with open(out_file, "w") as fh:
            fh.write(f"# Converted from Katalon Object Repository/{app}/{page_dir}\n")
            yaml.safe_dump(doc, fh, sort_keys=False, allow_unicode=True, width=10_000)
        written += 1
    for d in folders:
        n_elements += len(folders[d])
    for page in pages.values():
        n_entries += len(page["elements"])
        for g in page["groups"].values():
            n_entries += sum(1 for k in ("facet", "dropdown", "search", "checkbox_template") if k in g)
            n_entries += len(g.get("checkboxes", {})) + len(g.get("other", {}))
    return {"app": app, "katalon_elements": n_elements, "yaml_entries": n_entries,
            "yaml_files": written, "skipped": skipped}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--katalon", required=True, help="Path to the Katalon project (Commons_Automation)")
    ap.add_argument("--apps", nargs="+", default=["C3DC", "GC"])
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "ObjectRepository"))
    args = ap.parse_args()
    for app in args.apps:
        r = convert_app(Path(args.katalon), app, Path(args.out))
        print(f"{r['app']}: {r['katalon_elements']} Katalon files -> {r['yaml_files']} YAML files, "
              f"{r['yaml_entries']} entries" + (f"  (skipped {len(r['skipped'])} with no locator)" if r["skipped"] else ""))
        for s in r["skipped"]:
            print("   skipped:", s)


if __name__ == "__main__":
    main()
