"""UTokyo Channel (ch.u-tokyo.ac.jp) のシリーズページ解析。

目録単位はシリーズ (旧 UTokyo OCW のコース / 東大TV の講演イベント)。2026-07 時点:
- 題名: <h2 class="p-series__fv__body__series-name">
- 開講年: p-series__fv__head__year「NNNN年 開講」
- 部局: p-series__fv__body__faculty-name (無いページも多い。東大TV系)
- 説明: p-series__series-info__text (無ければ最初のコンテンツ紹介文で代替)
- 講師: p-series__contents__item__professor「講師 | 氏名」(複数・重複あり)
- タグ: /search-result/?tag=… (data-ga-keyword-area="series_tag")。
  ジャンル (AI・情報 等)・対象 (中高生向け・英語話者向け・学内限定)・
  種別 (東京大学正規授業・学術イベント…) が混在
- Produced by: 東大TV (403件) / UTokyo OCW (177件)
- 資料: コンテンツ一覧の「資料あり」アイコン (PDF等は視聴のみ規約のため
  materials には載せない)

利用規約が複製・頒布等を禁止 (視聴のみ) のため、全件 usageTerms
(not_allowed) の referenced エントリになる。引用は著作権法32条による。
"""

from __future__ import annotations

import html as html_module
import re

# 部局名 → ISCED-F 大分類 (部分一致・上から)
FACULTY_SUBJECT = [
    ("教養", "generic"),
    ("教育", "education"),
    ("情報理工", "ict"), ("学際情報", "ict"), ("情報学環", "ict"),
    ("公共政策", "business_law"), ("法学", "business_law"),
    ("経済", "social_sciences"), ("社会科学", "social_sciences"),
    ("文学", "arts_humanities"), ("人文", "arts_humanities"),
    ("史料編纂", "arts_humanities"), ("東洋文化", "arts_humanities"),
    ("工学", "engineering"), ("生産技術", "engineering"), ("先端科学技術", "engineering"),
    ("医学", "health_welfare"), ("薬学", "health_welfare"),
    ("農学", "agriculture"),
    ("理学", "natural_sciences_math"), ("数理", "natural_sciences_math"),
    ("新領域", "natural_sciences_math"), ("地震", "natural_sciences_math"),
    ("宇宙", "natural_sciences_math"), ("カブリ", "natural_sciences_math"),
]

# ジャンルタグ → about 語彙キー (部分一致・上から)
GENRE_SUBJECT = [
    ("AI・情報", "ict"), ("情報技術", "ict"), ("AI", "ict"), ("データ", "ict"),
    ("ロボット・技術", "engineering"), ("災害・防災", "engineering"),
    ("エネルギー・資源", "engineering"), ("都市・建築", "engineering"),
    ("もの創り", "engineering"),
    ("言語・思想", "arts_humanities"), ("文化・芸術・文芸", "arts_humanities"),
    ("歴史", "arts_humanities"), ("人文", "arts_humanities"),
    ("政治・法律", "business_law"),
    ("国際関係", "social_sciences"), ("人口・社会問題", "social_sciences"),
    ("経済・金融", "social_sciences"), ("心理・認知", "social_sciences"),
    ("ジェンダー", "social_sciences"),
    ("宇宙・物理", "natural_sciences_math"), ("数理", "natural_sciences_math"),
    ("環境", "natural_sciences_math"), ("化学", "natural_sciences_math"),
    ("生物", "natural_sciences_math"),
    ("生命・医療", "health_welfare"), ("健康", "health_welfare"),
    ("食料・農業・水産業", "agriculture"),
    ("教育", "education"),
]

# 対象・種別を表すタグ (ジャンルではないので about に使わない)
AUDIENCE_TAGS = ("中高生向け", "英語話者向け", "学内限定", "学内向け研修・ガイダンス",
                 "東京大学正規授業", "学術イベント（公開講座・講演会・シンポジウム・セミナー）",
                 "オープンキャンパス・体験イベント", "東大TV", "UTokyo OCW")


def slug_for(url: str):
    found = re.search(r"[?&]id=([A-Za-z0-9]+)", url)
    return f"utokyo-series-{found.group(1).lower()}" if found else None


def _text(fragment: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", fragment)
    text = re.sub(r"<[^>]+>", "", text)
    return html_module.unescape(text).strip()


def parse_course(html: str, url: str):
    title = re.search(r'series-name">\s*(.*?)\s*</h2>', html, re.S)
    if not title:
        return None
    name = re.sub(r"\s+", " ", _text(title.group(1)))
    if not name:
        return None

    year = None
    found = re.search(r'head__year">\s*(\d{4})年', html)
    if found:
        year = found.group(1)
    if not year:
        found = re.search(r"((?:19|20)\d{2})年", name)   # 題名中の年 (開催年であることが多い)
        if found:
            year = found.group(1)

    faculty = ""
    found = re.search(r'faculty-name">\s*<a[^>]*>\s*([^<]+?)\s*</a>', html, re.S)
    if found:
        faculty = found.group(1)

    produced = ""
    found = re.search(r'\?tag=([^"&]+)"[^>]*data-ga-keyword-area="produced_by"', html)
    if found:
        produced = html_module.unescape(found.group(1))

    tags = []
    for m in re.finditer(r'\?tag=([^"&]+)"[^>]*data-ga-keyword-area="series_tag"', html):
        value = html_module.unescape(m.group(1))
        if value not in tags:
            tags.append(value)

    # 説明: シリーズ紹介文 → 無ければ最初のコンテンツ紹介文
    quoted, quoted_labels = "", []
    found = re.search(r'series-info__text"[^>]*>(.*?)</div>', html, re.S)
    if found:
        text = re.sub(r"\n{2,}", "\n", _text(found.group(1)))
        if len(re.sub(r"\s", "", text)) >= 40:
            quoted, quoted_labels = text, ["シリーズ紹介文"]
    if not quoted:
        for m in re.finditer(r'contents__item__desc">\s*(.*?)\s*</p>', html, re.S):
            text = re.sub(r"\n{2,}", "\n", _text(m.group(1)))
            if len(re.sub(r"\s", "", text)) >= 40:
                quoted, quoted_labels = text, ["コンテンツ紹介文"]
                break

    lecturers = []
    for m in re.finditer(r'contents__item__professor">\s*(.*?)\s*</', html, re.S):
        for part in re.split(r"[、,／/]|\n", re.sub(r"^講師\s*\|\s*", "", _text(m.group(1)))):
            person = re.sub(r"（[^）]*）", "", part).strip()
            if person and len(person) <= 30 and person not in lecturers:
                lecturers.append(person)

    about = []
    genre_tags = [t for t in tags if t not in AUDIENCE_TAGS and t != faculty]
    for tag in genre_tags:
        for keyword, subject in GENRE_SUBJECT:
            if keyword in tag:
                if subject not in about:
                    about.append(subject)
                break
    about = about[:3]   # オムニバス講義はタグが多い。主要3分野まで
    if not about and faculty:
        for keyword, subject in FACULTY_SUBJECT:
            if keyword in faculty:
                about = [subject]
                break

    # 対象者・レベル: タグ → Produced by の順で判定
    level = None
    if "中高生向け" in tags:
        audience, level = ["student"], "upper_secondary"
    elif "東京大学正規授業" in tags or produced == "UTokyo OCW":
        audience = ["student", "general_public"]
    else:                       # 東大TV: 公開講座・講演会・シンポジウム
        audience = ["general_public"]

    languages = ["en"] if "英語話者向け" in tags else ["ja"]

    resource_types = ["video"]
    if "東京大学正規授業" in tags or produced == "UTokyo OCW":
        resource_types = ["course", "video"]
    if "資料あり" in html:
        resource_types.append("script")

    target = "・".join(t for t in ("中高生向け", "英語話者向け", "学内限定",
                                   "学内向け研修・ガイダンス") if t in tags) or None

    keywords = [t for t in genre_tags][:8]
    if produced:
        keywords.append(produced)

    return {
        "name_ja": name,
        "faculty": faculty,
        "year": year,
        "target": target,
        "lecturers": lecturers[:8],
        "inLanguage": languages,
        "quoted": quoted,
        "quoted_labels": quoted_labels,
        "materials": [],            # 視聴のみ規約のためファイルURLは載せない
        "learningResourceType": resource_types,
        "about": about or ["generic"],
        "educationalLevel": level,
        "audience": audience,
        "license": None,            # CC 表記なし → サイト共通の usageTerms
        "tags": keywords,
    }
