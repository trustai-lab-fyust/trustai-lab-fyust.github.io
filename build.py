#!/usr/bin/env python3
"""Generate the TrustAI Lab static site.

Reads data/*.yaml and templates/*.html, writes plain HTML into dist/.
Usage: python3 build.py [--out DIR]
"""
import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

DATA_FILES = ["site", "research", "people", "publications", "news", "join"]
LANGS = {
    "zh": {"code": "zh-CN", "prefix": "", "pages": ["index", "research", "people", "publications", "news", "join"]},
    "en": {"code": "en", "prefix": "en/", "pages": ["index", "research", "people", "publications", "join"]},
}
TIER_COLORS = {"faculty": "#1f4e79", "graduate": "#2d6a4f", "intern": "#b5651d", "undergrad": "#7b4f9d", "alumni": "#6b7a8d"}


CJK_GAP = re.compile(r"(?<=[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef])\s+(?=[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef])")


def tidy_zh(value):
    """Remove the spaces YAML folding inserts between Chinese characters."""
    if isinstance(value, str):
        return CJK_GAP.sub("", value)
    if isinstance(value, list):
        return [tidy_zh(v) for v in value]
    if isinstance(value, dict):
        return {k: (tidy_zh(v) if (k.endswith("_zh") or k == "zh") else _walk(v)) for k, v in value.items()}
    return value


def _walk(value):
    if isinstance(value, dict):
        return tidy_zh(value)
    if isinstance(value, list):
        return [_walk(v) for v in value]
    return value


def load_data(root):
    root = Path(root)
    data = {}
    for name in DATA_FILES:
        with open(root / "data" / f"{name}.yaml", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or ([] if name != "site" and name != "join" else {})
        data[name] = _walk(raw)
    return data


def person_aliases(person):
    """Name forms used to bold lab members inside author strings.

    The abbreviated form (e.g. "C. Hou") is only used for faculty; for students it is
    too ambiguous (an "X. Lin" in an author list may be someone else).
    """
    full = person["name_en"].strip()
    parts = full.split()
    aliases = [full]
    if len(parts) >= 2 and person.get("tier") == "faculty":
        aliases.append(f"{parts[0][0]}. {parts[-1]}")
    return aliases


def bold_members(authors, aliases):
    text = str(escape(authors))
    for alias in sorted(aliases, key=len, reverse=True):
        text = re.sub(rf"(?<![\w.]){re.escape(alias)}(?![\w])", f"<strong>{alias}</strong>", text)
    return Markup(text)


def avatar_svg(initials, color):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" width="160" height="160">'
        f'<rect width="160" height="160" rx="12" fill="{color}"/>'
        '<text x="80" y="80" text-anchor="middle" dominant-baseline="central" '
        'font-family="-apple-system, Segoe UI, Helvetica, Arial, sans-serif" font-size="56" '
        f'font-weight="600" fill="#ffffff">{escape(initials)}</text></svg>\n'
    )


def build(root, out):
    root, out = Path(root), Path(out)
    data = load_data(root)
    site = data["site"]

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copytree(root / "assets", out / "assets")
    (out / ".nojekyll").write_text("", encoding="utf-8")

    people = data["people"]
    people_by_id = {p["id"]: p for p in people}
    aliases = [a for p in people for a in person_aliases(p)]
    tiers = site["tiers"]
    people_by_tier = {t["id"]: [p for p in people if p["tier"] == t["id"]] for t in tiers}

    # Placeholder avatars for members without a photo.
    avatar_dir = out / "assets" / "img" / "people"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    for p in people:
        if p.get("photo"):
            p["_img"] = f"assets/img/people/{p['photo']}"
        elif p["tier"] != "faculty":
            p["_img"] = None  # students are listed by name only
        else:
            parts = p["name_en"].split()
            initials = (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else parts[0][:2].upper()
            (avatar_dir / f"{p['id']}.svg").write_text(avatar_svg(initials, TIER_COLORS.get(p["tier"], "#6b7a8d")), encoding="utf-8")
            p["_img"] = f"assets/img/people/{p['id']}.svg"

    pubs = sorted(data["publications"], key=lambda p: (-int(p["year"]), p.get("order", 0)))
    pubs_by_id = {p["id"]: p for p in pubs}
    for p in pubs:
        p["_authors_html"] = bold_members(p["authors"], aliases)
    has_corresponding = any("*" in p["authors"] for p in pubs)
    news = sorted(data["news"], key=lambda n: str(n["date"]), reverse=True)
    research = data["research"]
    for area in research:
        area["_lead"] = people_by_id[area["lead"]]
        area["_pubs"] = [pubs_by_id[i] for i in area.get("highlights", []) if i in pubs_by_id]

    # Selected publications for the home page: two per area, newest first.
    selected = []
    for area in research:
        selected.extend(area["_pubs"][:2])
    selected = sorted({p["id"]: p for p in selected}.values(), key=lambda p: -int(p["year"]))

    env = Environment(
        loader=FileSystemLoader(str(root / "templates")),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    for lang, spec in LANGS.items():
        rel = "../" if spec["prefix"] else ""
        ui = site["ui"][lang]
        nav = [n for n in site["nav"] if n.get(lang)]

        def t(obj, key, _lang=lang):
            return obj.get(f"{key}_{_lang}") or obj.get(key) or ""

        env.globals["t"] = t
        for page in spec["pages"]:
            other = "en" if lang == "zh" else "zh"
            if page in LANGS[other]["pages"]:
                switch_href = (f"en/{page}.html" if lang == "zh" else f"../{page}.html")
            else:
                switch_href = ui["lang_switch_file"]
            template = env.get_template(f"{page}.html")
            html = template.render(
                lang=lang,
                lang_code=spec["code"],
                rel=rel,
                page=page,
                site=site,
                ui=ui,
                nav=nav,
                switch_href=switch_href,
                research=research,
                people=people,
                people_by_id=people_by_id,
                tiers=tiers,
                people_by_tier=people_by_tier,
                pubs=pubs,
                selected_pubs=selected,
                has_corresponding=has_corresponding,
                news=news,
                recent_news=news[:5],
                join=data["join"],
                year=date.today().year,
            )
            target = out / spec["prefix"] / f"{page}.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(html, encoding="utf-8")
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="dist", help="output directory (default: dist)")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parent
    out = build(root, root / args.out if not Path(args.out).is_absolute() else Path(args.out))
    pages = sorted(str(p.relative_to(out)) for p in out.rglob("*.html"))
    print(f"built {len(pages)} pages into {out}:")
    for p in pages:
        print("  " + p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
