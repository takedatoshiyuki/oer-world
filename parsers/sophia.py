"""上智大学OCW (ocw.cc.sophia.ac.jp) の講義ページ解析。

2026-07 時点。WordPress で lecture 投稿型が REST 公開されており、
発見と分類は REST ダンプ (.cache/sophia_lectures.json / sophia_dep.json、
kyoto_taxonomy と同じ事前生成方式) を併用する。ページ構造:
- <h2 class="result_title">題名</h2>
- 表: 学部／学科 / 教員／講師名 / 開催年度 / 開催日
- 「講義概要」(strong) の段落 → 引用。「使用テキスト」以降は除く
- 各回の表: 講義内容 / 講義映像 (YouTube) / 講義資料・配布資料 (PDF)
- dep タクソノミ: 大分類 (course-*=講義 / lastlecture-*=最終講義 / oc*=オープン
  キャンパス / veritas・highschool=高校生向け / renaissance・sophia 等=講演会 /
  研究機構) と学部・学科

ライセンスはサイト全体 CC BY-NC-SA 2.1 日本 (/about/ に明記。
「コンテンツの詳細ページに記載がある場合はそちらに従う」)。
"""

from __future__ import annotations

import html as html_module
import json
import re
from pathlib import Path

SITE_LICENSE = "https://creativecommons.org/licenses/by-nc-sa/2.1/jp/"
LECTURES_PATH = Path(__file__).resolve().parent.parent / ".cache" / "sophia_lectures.json"
_lookup_cache = None

# 学部・学科名 → about 語彙キー (部分一致・上から)
FACULTY_SUBJECT = [
    ("情報理工", "ict"),
    ("理工", "engineering"),
    ("神学", "arts_humanities"), ("哲学", "arts_humanities"), ("史学", "arts_humanities"),
    ("国文", "arts_humanities"), ("英文", "arts_humanities"), ("ドイツ文", "arts_humanities"),
    ("フランス文", "arts_humanities"), ("文学部", "arts_humanities"),
    ("外国語", "arts_humanities"), ("語学科", "arts_humanities"),
    ("言語", "arts_humanities"), ("アジア文化", "arts_humanities"),
    ("教育", "education"),
    ("心理", "social_sciences"), ("社会学", "social_sciences"),
    ("新聞", "social_sciences"), ("グローバル", "social_sciences"),
    ("国際関係", "social_sciences"), ("ヨーロッパ研究", "social_sciences"),
    ("比較文化", "social_sciences"),
    ("社会福祉", "health_welfare"), ("看護", "health_welfare"),
    ("法学", "business_law"), ("地球環境法", "business_law"),
    ("経済", "social_sciences"), ("経営", "business_law"),
    ("国際教養", "generic"), ("短期大学", "generic"),
]


def _lookup() -> dict:
    """REST ダンプを slug → {date, deps} に整形 (プロセス内キャッシュ)。"""
    global _lookup_cache
    if _lookup_cache is None:
        _lookup_cache = {}
        if LECTURES_PATH.exists():
            for x in json.loads(LECTURES_PATH.read_text(encoding="utf-8")):
                deps = [c.removeprefix("dep-") for c in x.get("class_list", [])]
                _lookup_cache[x["slug"]] = {"date": x.get("date", ""), "deps": deps}
    return _lookup_cache


def slug_for(url: str):
    found = re.search(r"/lecture/([^/?#]+)/?", url)
    if not found:
        return None
    slug = re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "-", found.group(1).lower())).strip("-")
    return f"sophia-{slug}"[:100] if slug else None


def _text(fragment: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", fragment, flags=re.S | re.I)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_module.unescape(text).replace("　", " ").replace(" ", " ")
    return re.sub(r"[ \t]+", " ", text).strip()


def parse_course(html: str, url: str):
    title = re.search(r'result_title">(.*?)</h2>', html, re.S)
    if not title:
        return None
    name = re.sub(r"\s+", " ", _text(title.group(1)))
    if not name:
        return None

    pairs = {}
    for m in re.finditer(r"<th>(.*?)</th>\s*<td[^>]*>(.*?)</td>", html, re.S):
        key = re.sub(r"\s+", "", _text(m.group(1)))
        if key and key not in pairs:
            pairs[key] = m.group(2)

    faculty = re.sub(r"\s+", " ", _text(pairs.get("学部／学科", ""))).strip()
    if not faculty:
        # OC・講演会ページは表に学部が無い → パンくず (/dep/... リンク) から補完
        skip = {"講義", "最終講義", "オープンキャンパス", "研究機構", "講演会",
                "高校生向け", "HOME", "講演会・イベント"}
        for m in re.finditer(r'<a href="/dep/[^"]+">([^<]+)</a>', html):
            crumb = m.group(1).strip()
            if crumb not in skip:
                faculty = crumb
                break

    lecturers = []
    for part in re.split(r"[、,／/・]|\n", _text(pairs.get("教員／講師名", ""))):
        person = re.sub(r"（[^）]*）", "", part).strip()
        if person and len(person) <= 30 and person not in lecturers:
            lecturers.append(person)

    slug = re.search(r"/lecture/([^/?#]+)", url).group(1)
    info = _lookup().get(slug, {})
    deps = info.get("deps", [])

    year = term = None
    found = re.search(r"(\d{4})年度?", _text(pairs.get("開催年度", "")))
    if found:
        year = found.group(1)
    day_text = _text(pairs.get("開催日", ""))
    date = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", day_text)
    if date:
        year = f"{date.group(1)}-{int(date.group(2)):02d}-{int(date.group(3)):02d}"
    elif day_text:
        term = day_text[:20]
    if not year and info.get("date"):
        # REST の投稿日 (サイトへの公開日) を最後の拠り所にする
        year = info["date"][:4]

    # 講義概要 → 引用 (「使用テキスト」等の後続ラベルの手前まで)
    quoted, quoted_labels = "", []
    # 本文領域 (result_title 以降) に限定し、script/style を先に除去してから探す
    # (ナビ・スクリプト内のエスケープ断片への誤マッチ防止)
    content = html[html.find("result_title"):]
    content = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", content, flags=re.S | re.I)
    for label in ("講義概要", "テーマ"):
        m = re.search(rf"<strong>\s*{label}\s*</strong>(.*?)"
                      rf"(?:<strong>|</table>|<div class=\"(?:result_list|img_box)|"
                      rf"<footer|Copyright ©|$)",
                      content, re.S)
        if m:
            body = re.sub(r"<[^>]*$", "", m.group(1))   # 終端で切れた不完全タグを除去
            text = _text(body)
            text = re.sub(r"\n[ 　]*(?=\n)", "", text)
            text = re.sub(r"\n{2,}", "\n", text).strip()
            if len(re.sub(r"\s", "", text)) >= 40:
                quoted, quoted_labels = text, [label]
                break

    materials, seen = [], set()
    for m in re.finditer(r'<a[^>]+href="(https?://ocw\.cc\.sophia\.ac\.jp/wp-content/'
                         r'uploads/[^"]+\.(?:pdf|pptx?|zip|docx?))"', html):
        file_url = html_module.unescape(m.group(1))
        if file_url not in seen:
            seen.add(file_url)
            materials.append({"name": f"講義資料: {file_url.rsplit('/', 1)[-1]}"[:120],
                              "contentUrl": file_url})

    has_video = "youtube" in html.lower()

    # dep 大分類 → 対象者・レベル・種別
    dep_all = " ".join(deps)
    is_course = any(d.startswith("course-") or d == "course" for d in deps)
    is_oc = any(d == "oc" or d.startswith("oc-") for d in deps)
    is_high = any(d in ("veritas", "highschool", "oslecture") for d in deps)
    is_last = any(d.startswith("lastlecture") for d in deps)
    if is_course:
        audience, level, category = ["student"], "bachelor", "講義"
    elif is_oc or is_high:
        # オープンキャンパス模擬講義・高校生講座 → 高校生対象
        audience, level = ["student"], "upper_secondary"
        category = "オープンキャンパス" if is_oc else "高校生向け"
    elif is_last:
        audience, level, category = ["general_public"], None, "最終講義"
    else:
        audience, level, category = ["general_public"], None, "講演会・イベント"

    if is_course:
        resource_types = (["course"] + (["video"] if has_video else [])
                          + (["script"] if materials else []))
    else:
        resource_types = ((["video"] if has_video else [])
                          + (["script"] if materials else [])) or ["web_page"]

    about = []
    for keyword, subject in FACULTY_SUBJECT:
        if keyword in faculty:
            about = [subject]
            break

    tags = [t for t in (category,) if t]

    return {
        "name_ja": name,
        "faculty": faculty or None,
        "year": year,
        "term": term,
        "lecturers": lecturers[:8],
        "inLanguage": ["ja"],
        "quoted": quoted,
        "quoted_labels": quoted_labels,
        "materials": materials,
        "learningResourceType": resource_types,
        "about": about or ["generic"],
        "educationalLevel": level,
        "audience": audience,
        "license": SITE_LICENSE,
        "tags": tags,
    }
