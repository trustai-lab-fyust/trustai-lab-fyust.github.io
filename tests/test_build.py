"""Build tests for the TrustAI Lab static site generator."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build  # noqa: E402

ZH_PAGES = ["index.html", "research.html", "people.html", "publications.html", "news.html", "join.html"]
EN_PAGES = ["en/index.html", "en/research.html", "en/people.html", "en/publications.html", "en/join.html"]
CJK = re.compile(r"[一-鿿]")


@pytest.fixture(scope="module")
def dist(tmp_path_factory):
    out = tmp_path_factory.mktemp("dist")
    build.build(ROOT, out)
    return out


def read(dist, rel):
    return (dist / rel).read_text(encoding="utf-8")


def test_all_pages_exist(dist):
    for rel in ZH_PAGES + EN_PAGES:
        assert (dist / rel).is_file(), rel


def test_home_has_lab_names(dist):
    zh = read(dist, "index.html")
    assert "安全可信智能联合实验室" in zh
    assert "TrustAI Lab" in zh
    en = read(dist, "en/index.html")
    assert "Joint Laboratory of Trustworthy and Secure Intelligence" in en
    assert "TrustAI Lab" in en


def test_page_skeleton(dist):
    for rel in ZH_PAGES + EN_PAGES:
        html = read(dist, rel)
        assert html.lstrip().startswith("<!DOCTYPE html>"), rel
        assert "<title>" in html, rel
        assert 'name="viewport"' in html, rel
        lang = "en" if rel.startswith("en/") else "zh-CN"
        assert f'<html lang="{lang}"' in html, rel
        assert "main.css" in html, rel


def test_internal_links_resolve(dist):
    broken = []
    for rel in ZH_PAGES + EN_PAGES:
        html = read(dist, rel)
        base = (dist / rel).parent
        for attr, target in re.findall(r'(href|src)="([^"]+)"', html):
            if target.startswith(("http://", "https://", "mailto:", "#", "data:")):
                continue
            path = target.split("#")[0]
            if not path:
                continue
            resolved = (dist / path.lstrip("/")) if path.startswith("/") else (base / path)
            if not resolved.exists():
                broken.append(f"{rel}: {target}")
    assert not broken, "\n".join(broken)


def test_faculty_on_people_pages(dist):
    zh = read(dist, "people.html")
    en = read(dist, "en/people.html")
    for name_zh, name_en in [("侯诚彬", "Chengbin Hou"), ("王春棉", "Chunmian Wang"), ("鲍光胜", "Guangsheng Bao")]:
        assert name_zh in zh, name_zh
        assert name_en in en, name_en


def test_people_tiers_valid():
    data = build.load_data(ROOT)
    allowed = {t["id"] for t in data["site"]["tiers"]}
    for person in data["people"]:
        assert person["tier"] in allowed, person


def test_people_page_lists_everyone_and_recruits_for_empty_tiers(dist):
    data = build.load_data(ROOT)
    zh = read(dist, "people.html")
    en = read(dist, "en/people.html")
    for person in data["people"]:
        assert person["name_zh"] in zh, person["name_zh"]
        assert person["name_en"] in en, person["name_en"]
    empty = [t for t in data["site"]["tiers"] if t["id"] != "alumni" and not any(p["tier"] == t["id"] for p in data["people"])]
    assert zh.count("招收中") == len(empty)


def test_faculty_order_by_surname_pinyin(dist):
    zh = read(dist, "people.html")
    assert zh.index("鲍光胜") < zh.index("侯诚彬") < zh.index("王春棉")


def test_school_logo_on_home(dist):
    assert (dist / "assets/img/fyust-logo.png").is_file()
    assert "assets/img/fyust-logo.png" in read(dist, "index.html")
    assert "assets/img/fyust-logo.png" in read(dist, "en/index.html")


def test_corresponding_author_legend(dist):
    data = build.load_data(ROOT)
    if any("*" in p["authors"] for p in data["publications"]):
        assert "* 通讯作者" in read(dist, "publications.html")
        assert "* Corresponding author" in read(dist, "en/publications.html")


def test_publications_sorted_desc(dist):
    for rel in ["publications.html", "en/publications.html"]:
        years = [int(y) for y in re.findall(r'data-year="(\d{4})"', read(dist, rel))]
        assert years, rel
        assert years == sorted(years, reverse=True), rel


def test_publication_ids_referenced_by_research_exist():
    data = build.load_data(ROOT)
    ids = {p["id"] for p in data["publications"]}
    for area in data["research"]:
        for pid in area.get("highlights", []):
            assert pid in ids, f"{area['id']} -> {pid}"


def test_english_pages_are_english(dist):
    for rel in EN_PAGES:
        html = read(dist, rel)
        html = re.sub(r'<a[^>]*class="lang-switch"[^>]*>.*?</a>', "", html, flags=re.S)
        cjk = CJK.findall(html)
        assert not cjk, f"{rel}: {''.join(cjk)[:40]}"


def test_news_sorted_desc(dist):
    dates = re.findall(r'data-date="([^"]+)"', read(dist, "news.html"))
    assert dates and dates == sorted(dates, reverse=True)


def test_assets_copied(dist):
    assert (dist / "assets/css/main.css").is_file()
    assert (dist / "assets/img/logo.svg").is_file()
    assert (dist / ".nojekyll").is_file()


def test_no_unparsed_yaml_structures(dist):
    """A colon inside an unquoted YAML string turns the item into a dict; catch it on every page."""
    for rel in ZH_PAGES + EN_PAGES:
        html = read(dist, rel)
        assert "{&#39;" not in html and "{'" not in html, rel


def test_student_initials_not_bolded(dist):
    html = read(dist, "publications.html")
    assert "<strong>X. Lin</strong>" not in html
    assert "<strong>C. Hou</strong>" in html


def test_research_images_exist(dist):
    data = build.load_data(ROOT)
    for area in data["research"]:
        assert (dist / "assets/img/research" / area["image"]).is_file(), area["id"]
    zh = read(dist, "index.html")
    assert "匿名网络" not in zh
