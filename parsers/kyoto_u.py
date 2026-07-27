"""京都大学OCW (ocw.kyoto-u.ac.jp) のコースページ解析。

2026-07 時点の新サイト (WordPress・静的) 向け。構造:
- 題名: <h2 class="c-title__content">
- 概要: <div class="free-description__area"> (<strong>授業の特色</strong> 等の小見出し)
- 講義詳細: <h3>講義詳細</h3> に続く <dl><dt>ラベル</dt><dd>値</dd> の列
  (年度・期 / 年度 / 開催日 / 開講部局名 / 使用言語 / 教員／講師名 / 開催場所)
- ライセンス: コンテンツごとの CC バッジ (BY-NC-SA / BY-NC-ND)。無いページもある
  → 無ければ make_drafts がサイト共通の usageTerms (利用規約) を当てる
- 講義資料: <a href="…" rel="archives"><dl><dt>資料名</dt> の形 (絶対URL)
- 動画: YouTube 埋め込み + ?video_id=N の切り替えリンク

カテゴリ (通常講義/公開講義/最終講義/国際会議/その他) と分野タグは
ページに現れないため、検索一覧の走査結果 .cache/kyoto_taxonomy.json
(scratchpad/kyoto_taxonomy_sweep.py で生成) から course_id で引く。
"""

from __future__ import annotations

import html as html_module
import json
import re
from pathlib import Path

TAXONOMY_PATH = Path(__file__).resolve().parent.parent / ".cache" / "kyoto_taxonomy.json"
_taxonomy_cache = None

# 開講部局名 → ISCED-F 大分類 (上から順に部分一致。分野タグが無い場合の予備)
FACULTY_SUBJECT = [
    ("全学共通", "generic"), ("国際高等教育院", "generic"), ("総合人間", "generic"),
    ("高等教育研究開発", "education"), ("教育", "education"),
    ("情報学", "ict"), ("経営管理", "business_law"), ("公共政策", "business_law"),
    ("法", "business_law"), ("経済", "social_sciences"),
    ("アジア・アフリカ", "social_sciences"), ("総合生存", "social_sciences"),
    ("文学", "arts_humanities"), ("人文科学", "arts_humanities"),
    ("人間・環境", "social_sciences"),
    ("エネルギー", "engineering"), ("工学", "engineering"), ("防災", "engineering"),
    ("医学", "health_welfare"), ("薬学", "health_welfare"), ("ウイルス", "health_welfare"),
    ("病院", "health_welfare"),
    ("農学", "agriculture"), ("フィールド科学", "agriculture"),
    ("理学", "natural_sciences_math"), ("数理解析", "natural_sciences_math"),
    ("基礎物理学", "natural_sciences_math"), ("化学研究所", "natural_sciences_math"),
    ("生態学", "natural_sciences_math"), ("霊長類", "natural_sciences_math"),
    ("生命科学", "natural_sciences_math"), ("地球環境", "natural_sciences_math"),
    ("図書館", "generic"),
]

# 検索UIの分野キー → (about 語彙キー, 日本語ラベル)
SUBJECT_MAP = {
    "phi": ("arts_humanities", "哲学"), "eth": ("arts_humanities", "倫理学"),
    "art": ("arts_humanities", "芸術・文化"), "des": ("arts_humanities", "デザイン学"),
    "phil": ("social_sciences", "社会貢献"), "lit": ("arts_humanities", "文学"),
    "lan": ("arts_humanities", "語学"), "com": ("social_sciences", "コミュニケーション"),
    "his": ("arts_humanities", "歴史"), "law": ("business_law", "法学"),
    "eco": ("social_sciences", "経済学・金融"), "bus": ("business_law", "経営学"),
    "edu": ("education", "教育学"), "mat": ("natural_sciences_math", "数学"),
    "phy": ("natural_sciences_math", "物理学"),
    "ene": ("natural_sciences_math", "エネルギー・地球科学"),
    "eng": ("engineering", "工学"), "ele": ("engineering", "電子工学"),
    "arc": ("engineering", "建築"), "che": ("natural_sciences_math", "化学"),
    "agr": ("agriculture", "農学"), "bio": ("natural_sciences_math", "生物学・生命科学"),
    "foo": ("health_welfare", "食・栄養"), "hea": ("health_welfare", "安全・衛生"),
    "pha": ("health_welfare", "薬学"), "med": ("health_welfare", "医学"),
    "comp": ("ict", "コンピュータサイエンス"), "dat": ("ict", "データサイエンス"),
    "env": ("natural_sciences_math", "環境学"), "mus": ("arts_humanities", "音楽"),
    "sci": ("natural_sciences_math", "自然科学"), "hum": ("arts_humanities", "人文科学"),
    "soci": ("social_sciences", "社会科学"), "etc": (None, None),
}

CATEGORY_JA = {"course": "通常講義", "public-lecture": "公開講義",
               "final-lecture": "最終講義", "intl-conf": "国際会議", "others": "その他"}

LICENSE_BY_BADGE = {
    "by-nc-sa": "CC-BY-NC-SA-4.0",
    "by-nc-nd": "CC-BY-NC-ND-4.0",
    "by-nc": "CC-BY-NC-4.0",
    "by-sa": "CC-BY-SA-4.0",
    "by": "CC-BY-4.0",
}


def _taxonomy() -> dict:
    global _taxonomy_cache
    if _taxonomy_cache is None:
        if TAXONOMY_PATH.exists():
            _taxonomy_cache = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
        else:
            _taxonomy_cache = {"category": {}, "subject": {}}
    return _taxonomy_cache


def slug_for(url: str):
    found = re.search(r"/course/(\d+)/?", url)
    return f"kyoto-u-course-{int(found.group(1)):04d}" if found else None


def _text(fragment: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", fragment)
    text = re.sub(r"<[^>]+>", "", text)
    return html_module.unescape(text).strip()


def _details(html: str) -> dict:
    """<h3>講義詳細</h3> に続く dt/dd を辞書に。"""
    section = re.search(r"講義詳細</h3>(.*?)(?:関連講義|PAGE TOP|</main>)", html, re.S)
    if not section:
        return {}
    pairs = re.findall(r"<dt>(.*?)</dt>\s*<dd>(.*?)</dd>", section.group(1), re.S)
    return {_text(k): re.sub(r"\s+\n", "\n", _text(v)).strip() for k, v in pairs}


def _quoted(html: str):
    """概要文。free-description__area、無ければ最初の動画紹介文。"""
    area = re.search(r'free-description__area">(.*?)</div>', html, re.S)
    if area:
        text = re.sub(r"\n{2,}", "\n", _text(area.group(1)))
        if len(re.sub(r"\s", "", text)) >= 40:
            labels = [l.strip() for l in re.findall(r"<strong>([^<]{2,20})</strong>",
                                                    area.group(1))]
            return text, (labels or ["講義概要"])
    # 動画一覧の紹介文 (dd = 講師名<br>紹介文)
    for found in re.finditer(r'video_id=\d+"[^>]*>.*?<dl>\s*<dt>.*?</dt>\s*<dd>(.*?)</dd>',
                             html, re.S):
        lines = [l.strip() for l in _text(found.group(1)).splitlines() if l.strip()]
        prose = "\n".join(lines[1:]) if len(lines) > 1 else ""
        if len(re.sub(r"\s", "", prose)) >= 40:
            return prose, ["動画紹介"]
    return "", []


def _materials(html: str):
    materials, seen = [], set()
    for found in re.finditer(
            r'<a(?=[^>]*rel="archives")[^>]*href="([^"]+)"[^>]*>\s*(?:<dl>\s*<dt>(.*?)</dt>)?',
            html, re.S):
        url = html_module.unescape(found.group(1))
        if url in seen or url.startswith("#"):
            continue
        seen.add(url)
        name = _text(found.group(2) or "") or url.rsplit("/", 1)[-1]
        materials.append({"name": f"講義資料: {name}"[:120], "contentUrl": url})
    return materials


def parse_course(html: str, url: str):
    title = re.search(r'c-title__content">(.*?)</h2>', html, re.S)
    if not title:
        return None
    name = _text(title.group(1))
    if not name:
        return None

    course_id = re.search(r"/course/(\d+)", url).group(1)
    taxonomy = _taxonomy()
    category = taxonomy["category"].get(course_id)          # course / public-lecture / …
    subject_keys = taxonomy["subject"].get(course_id, [])

    details = _details(html)
    faculty = details.get("開講部局名", "")
    lecturers = []
    for part in re.split(r"[、,／/]|\n", details.get("教員／講師名", "")):
        person = re.sub(r"（[^）]*）", "", part).strip()
        if person and len(person) <= 30:
            lecturers.append(person)

    year = term = None
    found = re.search(r"(\d{4})年度(?:・(\S+))?",
                      details.get("年度・期", details.get("年度", "")))
    if found:
        year, term = found.group(1), found.group(2)
    date = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", details.get("開催日", ""))
    if date:
        year = f"{date.group(1)}-{int(date.group(2)):02d}-{int(date.group(3)):02d}"

    language_text = details.get("使用言語", "")
    languages = []
    if "日本語" in language_text:
        languages.append("ja")
    if "英語" in language_text:
        languages.append("en")

    quoted, quoted_labels = _quoted(html)
    materials = _materials(html)
    has_video = "video_id=" in html or "youtube.com/embed" in html

    # 分野タグ → about (複数可)。タグが無いページは開講部局名から推定
    about = []
    for key in subject_keys:
        mapped = SUBJECT_MAP.get(key, (None, None))[0]
        if mapped and mapped not in about:
            about.append(mapped)
    if not about:
        for keyword, subject in FACULTY_SUBJECT:
            if keyword in faculty:
                about = [subject]
                break

    # カテゴリで対象者・レベル・種別を切り替える (未判明は通常講義扱い)
    if category in ("public-lecture", "final-lecture", "intl-conf", "others"):
        audience = ["professional"] if category == "intl-conf" else ["general_public"]
        level = "continuing_education" if category == "public-lecture" else None
        resource_types = (["video"] if has_video else []) \
            + (["script"] if materials else []) or ["web_page"]
    else:
        audience = ["student"]
        level = "master" if re.search(r"研究科|大学院|学館|法科", faculty) else "bachelor"
        resource_types = (["course"] + (["video"] if has_video else [])
                          + (["script"] if materials else []))

    badge = re.search(r"creativecommons\.org/licenses/([a-z-]+)/[0-9.]+", html)
    license_id = LICENSE_BY_BADGE.get(badge.group(1)) if badge else None

    tags = [label for key in subject_keys
            for label in [SUBJECT_MAP.get(key, (None, None))[1]] if label]
    if category and category != "course":
        tags.append(CATEGORY_JA[category])

    return {
        "name_ja": name,
        "faculty": faculty,
        "year": year,
        "term": term,
        "lecturers": lecturers[:8],
        "inLanguage": languages or ["ja"],
        "quoted": quoted,
        "quoted_labels": quoted_labels,
        "materials": materials,
        "learningResourceType": resource_types,
        "about": about or ["generic"],
        "educationalLevel": level,
        "audience": audience,
        "license": license_id,
        "tags": tags,
    }
