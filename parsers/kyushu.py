"""九州大学OCW “QOCW” (ocw.kyushu-u.ac.jp) の講義ページ解析。

2000年代の手組み静的サイト (http のみ)。ヘッダ・ナビの PHP インクルードが
壊れておりサイト内導線は無いが、講義本文は静的 HTML で生きている。
URL 一覧は旧 科研STOER の収集データ (2023) から復元
(.cache/urls_kyushu.tsv / kyushu_legacy.json)。構造:
- <article class="course"><dl><h3>題名</h3>講師名<dt><h4>授業の概要</h4>本文…
- 資料: table.list 内の相対リンク PDF (講義スライド等)
- 部局は旧収集データの course_department から
- 日付情報がサイトにも旧データにも無い → Wayback 初出年
  (.cache/kyushu_wayback_years.json) を公開年の代理指標にする
- ライセンス表記はページに無い (規約類は壊れた PHP 側にあったと推定) →
  reuse: unspecified
"""

from __future__ import annotations

import html as html_module
import json
import re
from pathlib import Path
from urllib.parse import urljoin

CACHE = Path(__file__).resolve().parent.parent / ".cache"
_legacy_cache = _years_cache = None

# 部局名 → about (部分一致・上から)
FACULTY_SUBJECT = [
    ("情報基盤", "ict"), ("システム情報", "ict"), ("情報知能", "ict"),
    ("芸術工学", "arts_humanities"),
    ("工学", "engineering"),
    ("医学", "health_welfare"), ("歯学", "health_welfare"), ("薬学", "health_welfare"),
    ("病院", "health_welfare"),
    ("農学", "agriculture"),
    ("理学", "natural_sciences_math"), ("数理", "natural_sciences_math"),
    ("比較社会文化", "social_sciences"), ("人文", "arts_humanities"),
    ("言語文化", "arts_humanities"),
    ("経済", "social_sciences"), ("法学", "business_law"),
    ("教育", "education"),
]


def _load(name, cache_attr):
    path = CACHE / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _legacy():
    global _legacy_cache
    if _legacy_cache is None:
        _legacy_cache = _load("kyushu_legacy.json", "_legacy_cache")
    return _legacy_cache


def _years():
    global _years_cache
    if _years_cache is None:
        _years_cache = _load("kyushu_wayback_years.json", "_years_cache")
    return _years_cache


def slug_for(url: str):
    m = re.search(r"/menu/([a-z]+)/(.+?)\.html?$", url)
    if not m:
        return None
    tail = re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "-", m.group(2).lower())).strip("-")
    return f"kyushu-{m.group(1)}-{tail}"[:100]


def _text(fragment: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", fragment, flags=re.S | re.I)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_module.unescape(text).replace("　", " ").replace(" ", " ")
    return re.sub(r"[ \t]+", " ", text).strip()


def parse_course(html: str, url: str):
    article = re.search(r'<article class="course">(.*?)</article>', html, re.S)
    body = article.group(1) if article else html

    title = re.search(r"<h3>(.*?)</h3>", body, re.S)
    if not title:
        return None
    name = re.sub(r"\s+", " ", _text(title.group(1)))
    if not name:
        return None

    # 題名直後〜最初の <dt> までが講師行 (「青柳 睦 教授」「A教授、B准教授」)
    lecturers = []
    m = re.search(r"</h3>(.*?)<dt>", body, re.S)
    if m:
        for part in re.split(r"[、,／/]|\n", _text(m.group(1))):
            person = re.sub(r"(教授|准教授|助教授|講師|助教|名誉教授)$", "",
                            re.sub(r"（[^）]*）|\([^)]*\)", "", part).strip()).strip()
            person = re.sub(r"^(Prof\.|Asoc\. Prof\.|Assoc\. Prof\.|Dr\.)\s*", "", person)
            if person and len(person) <= 30 and person not in lecturers:
                lecturers.append(person)

    quoted, quoted_labels = "", []
    m = re.search(r"<h4>\s*([^<]{1,24})\s*</h4>(.*?)(?:</dt>|<h4>|<div class=\"table)",
                  body, re.S)
    if m:
        text = re.sub(r"\n{2,}", "\n", _text(m.group(2)))
        if len(re.sub(r"\s", "", text)) >= 40:
            quoted, quoted_labels = text, [m.group(1).strip()]

    materials, seen = [], set()
    for m in re.finditer(r'<a[^>]+href\s*=\s*"([^"]+\.(?:pdf|pptx?|zip))"[^>]*>(.*?)</a>',
                         html, re.S | re.I):
        file_url = urljoin(url, html_module.unescape(m.group(1)))
        if file_url in seen or "ocw.kyushu-u.ac.jp" not in file_url:
            continue
        seen.add(file_url)
        label = re.sub(r"\s+", " ", _text(m.group(2))) or file_url.rsplit("/", 1)[-1]
        materials.append({"name": f"講義資料: {label}"[:120], "contentUrl": file_url})

    legacy = _legacy().get(url, {})
    faculty = (legacy.get("department") or "").strip()

    year = _years().get(url)
    provenance_note = ("datePublished は Wayback Machine 初出年"
                       "（サイトに日付情報が無いため公開年の代理指標）" if year else None)

    about = []
    for keyword, subject in FACULTY_SUBJECT:
        if keyword in faculty:
            about = [subject]
            break

    # 旧データの部局欄は種別も混在 (一般向け講演会・最終講義・オープンキャンパス)。
    # 種別が分かればそれを優先し、無ければ URL 系統 (session=講習会/spclass=特別
    # 講義/faculty=学部・大学院講義) で判定する
    if faculty in ("一般向け講演会", "最終講義"):
        audience, level, category = ["general_public"], None, faculty
        faculty = ""
    elif faculty == "オープンキャンパス":
        audience, level, category = ["student"], "upper_secondary", "オープンキャンパス"
        faculty = ""
    elif faculty == "基幹教育・全学教育":
        audience, level, category = ["student"], "bachelor", "基幹教育・全学教育"
    else:
        kind = re.search(r"/menu/([a-z]+)/", url).group(1)
        if kind == "faculty":
            audience, level, category = ["student"], None, "学部・大学院講義"
        elif kind == "spclass":
            audience, level, category = ["student", "general_public"], None, "特別講義"
        else:
            audience, level, category = ["student", "professional"], None, "講習会"

    ascii_ratio = sum(c.isascii() for c in name) / max(len(name), 1)
    languages = ["en"] if ascii_ratio > 0.9 else ["ja"]

    has_video = bool(re.search(r"youtube|\.mp4|\.wmv|\.flv", html, re.I))
    resource_types = (["course"] + (["video"] if has_video else [])
                      + (["script"] if materials else []))

    return {
        "name_ja": name,
        "faculty": faculty or None,
        "year": year,
        "lecturers": lecturers[:8],
        "inLanguage": languages,
        "quoted": quoted,
        "quoted_labels": quoted_labels,
        "materials": materials,
        "learningResourceType": resource_types,
        "about": about or ["generic"],
        "educationalLevel": level,
        "audience": audience,
        "license": None,
        "usage_reuse": "unspecified",
        "provenance_note": provenance_note,
        "tags": [category],
    }
