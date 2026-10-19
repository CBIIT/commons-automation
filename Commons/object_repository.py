"""
Object repository: locators live in YAML files under ObjectRepository/<app>/.

Katalon equivalent: findTestObject('C3DC/ResultTabs/Studies-Tab')
Commons usage:      repo.xpath('ResultTabs/Studies-Tab')

The lookup key is the same as the Katalon path, minus the app name, so anything you knew in
Katalon is still findable. Filter facets are looked up as *groups*:

    repo.filter_group('Study/dbGaP_Accession').checkbox_xpath('phs000466')

Each filter group is YAML with `facet`, `dropdown`, and `checkboxes` (short key → xpath).
Optional: `search` (typeahead facets), `dropdowns` (two sub-lists), `other` (scroll helpers).
Legacy `checkbox_template` / `values` / `facet_key` are still loaded if present but prefer explicit checkboxes.
"""
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict, List, Optional

import yaml

from Commons.settings import OBJECT_REPO_ROOT


class LocatorNotFound(KeyError):
    pass


@dataclass
class FilterGroup:
    key: str
    facet: Optional[str] = None
    facet_key: Optional[str] = None  # element name on same YAML page (Katalon *Facet click)
    dropdown: Optional[str] = None
    dropdowns: List[str] = None
    values: List[str] = None
    search: Optional[str] = None
    checkbox_template: Optional[str] = None
    checkboxes: Dict[str, str] = None
    other: Dict[str, str] = None

    def dropdown_for(self, checkbox_xpath: str) -> Optional[str]:
        """The dropdown that opens the list holding this checkbox (some facets have two sub-lists,
        e.g. 'Library Source Material' and 'Library Source Molecule')."""
        for dd in self.dropdowns or []:
            m = re.search(r'@id\s*=\s*["\']([^"\']+)["\']', dd)
            if m and f"checkbox_{m.group(1)}_" in checkbox_xpath:
                return dd
        return self.dropdown

    def knows(self, value: str) -> bool:
        """True if Katalon had a locator for this value (used by the test generator)."""
        return value in (self.checkboxes or {}) or value in (self.values or [])

    def checkbox_xpath(self, value: str) -> str:
        """XPath of the checkbox for `value` (the token used in the Katalon object name)."""
        if self.checkboxes and value in self.checkboxes:
            return self.checkboxes[value]
        if self.checkbox_template:
            return self.checkbox_template.replace("{value}", value)
        known = ", ".join(sorted(self.checkboxes or {})) or "(none)"
        raise LocatorNotFound(
            f"No checkbox '{value}' in filter group '{self.key}'. Known values: {known}. "
            f"Add it under `checkboxes:` in the YAML file for this facet.")


class ObjectRepository:
    def __init__(self, app: str, root: Path = OBJECT_REPO_ROOT):
        self.app = app
        self._elements: Dict[str, str] = {}
        self._groups: Dict[str, FilterGroup] = {}
        self._load(Path(root) / app)

    def _load(self, folder: Path):
        if not folder.is_dir():
            raise FileNotFoundError(f"Object repository folder not found: {folder}")
        for f in sorted(folder.rglob("*.yaml")):
            doc = yaml.safe_load(f.read_text()) or {}
            page = doc.get("page", "")
            prefix = "" if page in ("", "(root)") else page + "/"
            page_elements: Dict[str, str] = {}
            for name, xp in (doc.get("elements") or {}).items():
                full = prefix + name
                self._elements[full] = xp
                page_elements[name] = xp
            for key, g in (doc.get("groups") or {}).items():
                facet = g.get("facet")
                facet_key = g.get("facet_key")
                if not facet and facet_key:
                    facet = page_elements.get(facet_key) or self._elements.get(prefix + facet_key)
                self._groups[key] = FilterGroup(
                    key=key,
                    facet=facet,
                    facet_key=facet_key,
                    dropdown=g.get("dropdown"),
                    dropdowns=g.get("dropdowns") or [],
                    values=g.get("values") or [],
                    search=g.get("search"),
                    checkbox_template=g.get("checkbox_template"),
                    checkboxes=g.get("checkboxes") or {},
                    other=g.get("other") or {},
                )

    def xpath(self, key: str) -> str:
        """Look up a single element, e.g. 'ResultTabs/Studies-Tab' (Katalon path minus the app)."""
        key = self._clean(key)
        try:
            return self._elements[key]
        except KeyError:
            close = [k for k in self._elements if k.lower().endswith(key.split("/")[-1].lower())][:5]
            hint = f" Did you mean: {close}?" if close else ""
            raise LocatorNotFound(f"Locator '{key}' not found for app {self.app}.{hint}") from None

    def has(self, key: str) -> bool:
        return self._clean(key) in self._elements

    def filter_group(self, key: str) -> FilterGroup:
        """Look up a filter group, e.g. 'Study/dbGaP_Accession'."""
        try:
            return self._groups[key]
        except KeyError:
            raise LocatorNotFound(
                f"Filter group '{key}' not found for app {self.app}. Known: {sorted(self._groups)}") from None

    def group_keys(self):
        return sorted(self._groups)

    def _clean(self, key: str) -> str:
        """Accept the full Katalon path too: 'Object Repository/C3DC/ResultTabs/X' or 'C3DC/ResultTabs/X'."""
        key = key.replace("Object Repository/", "")
        if key.startswith(self.app + "/"):
            key = key[len(self.app) + 1:]
        return key
