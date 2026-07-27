"""ICU OCW (ocw.info.icu.ac.jp) のページ解析。

Google Sites (新サイト)。全ページにサイト全体のナビが埋まる巨大 HTML
(約800KB) のため、role="main" 以降のみを対象にする。セクション:
- /majors (専攻科目)・/ge (一般教育)・/gs (大学院)・/for_high (オープン
  キャンパス講義)・/sl (公開講演等)・/ela・/wl・/japanese-languages-proguram
- 題名は <title>。本文に Course Description (英日併記が多い)、
  Instructor: / Lecture Date: / Major: / Course ID: / Category: のラベル行
- スラグに年度・学期 (BIO101_2017W / OC2017_kamito) が入ることが多い
- 動画は YouTube、資料は Google Drive リンク
- ライセンス: フッタは All Rights Reserved + CC への一般リンクのみで
  明示的な CC 指定なし → reuse: unspecified (OCW の理念文はあるが条件不明)
"""

from __future__ import annotations

import html as html_module
import re

# Major 欄 (英日併記) → about (部分一致・上から)
MAJOR_SUBJECT = [
    ("Computer", "ict"), ("Information Science", "ict"), ("情報", "ict"),
    ("Mathemat", "natural_sciences_math"), ("Physics", "natural_sciences_math"),
    ("Chemistry", "natural_sciences_math"), ("Biology", "natural_sciences_math"),
    ("Environmental", "natural_sciences_math"), ("数学", "natural_sciences_math"),
    ("物理", "natural_sciences_math"), ("化学", "natural_sciences_math"),
    ("生物", "natural_sciences_math"), ("環境", "natural_sciences_math"),
    ("Economics", "social_sciences"), ("経済", "social_sciences"),
    ("Business", "business_law"), ("経営", "business_law"),
    ("Law", "business_law"), ("法学", "business_law"), ("法律", "business_law"),
    ("Politic", "social_sciences"), ("政治", "social_sciences"),
    ("International Relations", "social_sciences"), ("国際関係", "social_sciences"),
    ("Sociology", "social_sciences"), ("社会", "social_sciences"),
    ("Anthropolog", "social_sciences"), ("人類学", "social_sciences"),
    ("Psycholog", "social_sciences"), ("心理", "social_sciences"),
    ("Media", "social_sciences"), ("メディア", "social_sciences"),
    ("Peace Studies", "social_sciences"), ("Development", "social_sciences"),
    ("Education", "education"), ("教育", "education"),
    ("Language", "arts_humanities"), ("Linguistic", "arts_humanities"),
    ("Literature", "arts_humanities"), ("Philosophy", "arts_humanities"),
    ("Religion", "arts_humanities"), ("Christian", "arts_humanities"),
    ("History", "arts_humanities"), ("Art", "arts_humanities"),
    ("Music", "arts_humanities"), ("文学", "arts_humanities"),
    ("哲学", "arts_humanities"), ("宗教", "arts_humanities"),
    ("歴史", "arts_humanities"), ("美術", "arts_humanities"),
    ("音楽", "arts_humanities"), ("語学", "arts_humanities"),
    ("キリスト教", "arts_humanities"),
]

SECTION_META = {
    # URL 1階層目 → (audience, educationalLevel, カテゴリ表示名)
    "majors": (["student"], "bachelor", "専攻科目"),
    "ge": (["student"], "bachelor", "一般教育科目"),
    "gs": (["student"], "master", "大学院科目"),
    "for_high": (["student"], "upper_secondary", "オープンキャンパス講義"),
    "sl": (["general_public"], None, "公開講演・特別講義"),
    "ela": (["student"], "bachelor", "英語教育プログラム"),
    "wl": (["student"], "bachelor", "世界の言語"),
    "japanese-languages-proguram": (["student"], "bachelor", "日本語教育プログラム"),
}


def slug_for(url: str):
    m = re.search(r"ocw\.info\.icu\.ac\.jp/((?:[a-z_-]+)/.+?)/?$", url)
    if not m:
        return None
    slug = re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "-", m.group(1).lower())).strip("-")
    return f"icu-{slug}"[:100] if slug else None


def _text(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", "\n", fragment)
    text = html_module.unescape(text).replace("　", " ").replace(" ", " ")
    return text


def parse_course(html: str, url: str):
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    name = html_module.unescape(title.group(1)).strip() if title else ""
    name = re.sub(r"\s+", " ", name)
    if not name or name in ("Home", "Error"):
        return None

    main = re.search(r'role="main"(.*)', html, re.S)
    seg = main.group(1) if main else html
    end = seg.find("</main>")
    if end > 0:
        seg = seg[:end]
    seg = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", seg, flags=re.S | re.I)

    lines = [re.sub(r"[ \t]+", " ", l).strip() for l in _text(seg).splitlines()]
    lines = [l for l in lines if l]
    # フッタ以降を落とす
    for marker in ("ICU Official Web Site", "Copyright ©"):
        if marker in lines:
            lines = lines[:lines.index(marker)]

    def field(label):
        joined = "\n".join(lines)
        m = re.search(rf"{label}\s*:?\s*(.*)", joined)
        if not m:
            return ""
        value = m.group(1).strip()
        if not value:   # ラベル行の次行に値がある場合
            idx = next((i for i, l in enumerate(lines) if re.match(rf"{label}", l)), None)
            if idx is not None and idx + 1 < len(lines):
                value = lines[idx + 1]
        return value

    instructor_text = field("Instructor")
    lecturers = []
    STOPWORDS = {"年度", "学期", "講義", "大学", "教養", "科目", "専攻", "更新"}
    # 「KOSE, Hiroyuki 小瀬博之, MIZOGUCHI, Tsuyoshi 溝口剛」→ 日本語名優先
    for jp in re.findall(r"[一-龥]{1,6}\s?[一-龥]{1,6}", instructor_text):
        person = jp.strip()
        if (person and person not in lecturers and len(person) >= 2
                and not any(w in person for w in STOPWORDS)):
            lecturers.append(person)
    if not lecturers:
        for m in re.finditer(r"([A-Z][A-Za-z'-]+),\s*([A-Z][a-z'-]+)", instructor_text):
            person = f"{m.group(2)} {m.group(1)}"
            if person not in lecturers:
                lecturers.append(person)

    year = None
    m = re.search(r"((?:19|20)\d{2})", url.rsplit("/", 1)[-1])
    if m:
        year = m.group(1)
    date_text = field("Lecture Date")
    d = re.search(r"((?:19|20)\d{2})[./](\d{1,2})[./](\d{1,2})", date_text)
    if d:
        year = f"{d.group(1)}-{int(d.group(2)):02d}-{int(d.group(3)):02d}"
    elif not year:
        d = re.search(r"((?:19|20)\d{2})", date_text)
        if d:
            year = d.group(1)

    # Course Description 〜 次のラベルまでの散文行 → 引用
    quoted, quoted_labels = "", []
    start = next((i for i, l in enumerate(lines)
                  if re.match(r"Course Description|Description|講義概要", l)), None)
    if start is not None:
        prose = []
        for l in lines[start + 1:]:
            if re.match(r"(Basic Information|Syllabus|Instructor|Lecture Date|Major|"
                        r"Course ID|Category|Update|Schedule)", l):
                break
            prose.append(l)
        text = "\n".join(prose).strip()
        if len(re.sub(r"\s", "", text)) >= 40:
            quoted, quoted_labels = text, ["Course Description"]

    section_hint = url.replace("https://ocw.info.icu.ac.jp/", "").split("/")[0]
    major = field("Major")
    about = []
    haystack = f"{major} {name}"
    for keyword, subject in MAJOR_SUBJECT:
        if keyword.isascii():
            # 英語キーは単語境界で照合 ("Law" が "Liberal" 等に誤爆しないように)
            if re.search(rf"\b{re.escape(keyword)}\w{{0,4}}\b", haystack, re.I) \
                    and re.search(rf"\b{re.escape(keyword)}", haystack, re.I):
                about = [subject]
                break
        elif keyword in haystack:
            about = [subject]
            break
    if not about and section_hint in ("ela", "wl", "japanese-languages-proguram"):
        about = ["arts_humanities"]   # 語学教育プログラム

    audience, level, category = SECTION_META.get(section_hint, (["student"], None, ""))

    has_video = bool(re.search(r"youtube\.com/(embed|watch)|youtu\.be", html))
    materials, seen = [], set()
    for m in re.finditer(r'href="(https://drive\.google\.com/[^"]+)"', seg):
        file_url = html_module.unescape(m.group(1))
        if file_url not in seen:
            seen.add(file_url)
            materials.append({"name": "講義資料 (Google Drive)",
                              "contentUrl": file_url})
    materials = materials[:20]

    if section_hint in ("majors", "ge", "gs"):
        resource_types = (["course"] + (["video"] if has_video else [])
                          + (["script"] if materials else []))
    else:
        resource_types = ((["video"] if has_video else [])
                          + (["script"] if materials else [])) or ["web_page"]

    japanese = len(re.findall(r"[ぁ-んァ-ン一-龥]", quoted or name))
    latin = len(re.findall(r"[A-Za-z]", quoted or name))
    languages = ["ja"] if japanese and japanese >= latin / 4 else ["en"]
    if quoted and japanese > 20 and latin > 200:
        languages = ["en", "ja"]      # 英日併記

    course_id = field("Course ID")
    tags = [t for t in (category, major[:30] if major else None, course_id or None) if t]

    return {
        "name_ja": name,
        "faculty": None,
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
        "tags": tags[:8],
    }
