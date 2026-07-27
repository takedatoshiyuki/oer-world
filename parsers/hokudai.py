"""北海道大学OCW (ocw.hokudai.ac.jp) の講義ページ解析。

2026-07 時点。WordPress だが講義はカスタム投稿型で REST/サイトマップに出ない
(URL一覧は /lecture/page/N の一覧走査で作る。scratchpad の履歴参照)。構造:
- 講義情報タブ: <div class="cnt_left">ラベル</div><div class="cnt_right">値</div>
  (タイトル / 教員 / 概要 / 講義資料 / タグ / キーワード / 対象 / 単位等 / 備考)
- 年: <div class="info_box_year">NNNN 事業名…</div>
- ライセンス: /licence へのリンク文字列「制限資料」(閲覧のみ) または CC バッジ。
  無表記のページは映像内クレジット等での個別確認が必要 → reuse: unspecified
- タグ: 種別 (公開講座でさがす/学部でさがす/大学院でさがす)・ジャンル
  (理学／自然科学 等)・部局・言語 (japanese/english)・事業名が混在
- 資料: wp-content/uploads の PDF。動画は iTunesU リンク (旧) が中心
"""

from __future__ import annotations

import html as html_module
import re

# ジャンルタグ → about 語彙キー (部分一致・上から)
GENRE_SUBJECT = [
    ("理学／自然科学", "natural_sciences_math"),
    ("工学／情報", "engineering"),
    ("文学／思想／言語", "arts_humanities"), ("歴史／民俗", "arts_humanities"),
    ("音楽", "arts_humanities"), ("美術", "arts_humanities"),
    ("教育／学習", "education"),
    ("医学／保健学", "health_welfare"),
    ("ビジネス／経済", "social_sciences"), ("心理／社会学", "social_sciences"),
    ("法律／政治", "business_law"),
    ("農学", "agriculture"), ("水産学", "agriculture"), ("獣医学", "agriculture"),
    ("複合分野／学際", "generic"),
]

# 部局タグ → about (ジャンルタグが無い場合の予備。部分一致・上から)
FACULTY_SUBJECT = [
    ("情報科学", "ict"), ("情報基盤", "ict"),
    ("公共政策", "business_law"), ("法学", "business_law"),
    ("経済", "social_sciences"), ("スラブ", "social_sciences"),
    ("メディア", "social_sciences"), ("観光", "social_sciences"),
    ("文学", "arts_humanities"), ("大学文書館", "arts_humanities"),
    ("教育", "education"), ("外国語教育", "education"),
    ("工学", "engineering"), ("電子科学", "engineering"),
    ("医学", "health_welfare"), ("歯学", "health_welfare"), ("薬学", "health_welfare"),
    ("保健", "health_welfare"), ("人獣共通感染症", "health_welfare"),
    ("アイソトープ", "health_welfare"),
    ("農学", "agriculture"), ("水産", "agriculture"), ("獣医", "agriculture"),
    ("フィールド科学", "agriculture"),
    ("理学", "natural_sciences_math"), ("低温科学", "natural_sciences_math"),
    ("環境科学", "natural_sciences_math"), ("地球環境", "natural_sciences_math"),
    ("総合博物館", "natural_sciences_math"), ("サステ", "natural_sciences_math"),
]

# 公開講座系の事業タグ (audience: general_public の根拠)
PUBLIC_TAGS = ("公開講座", "市民セミナー", "サイエンス・カフェ", "時計台サロン",
               "人文学カフェ", "プロフェッサー・ビジット", "オープンキャンパス",
               "ひらめき☆ときめきサイエンス", "最終講義", "ノーベル賞")

LICENSE_BY_BADGE = {
    "by-nc-sa": "CC-BY-NC-SA-4.0", "by-nc-nd": "CC-BY-NC-ND-4.0",
    "by-nc": "CC-BY-NC-4.0", "by-sa": "CC-BY-SA-4.0", "by": "CC-BY-4.0",
}


def slug_for(url: str):
    found = re.search(r"/lecture/([^/?#]+)", url)
    if not found:
        return None
    slug = re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "-", found.group(1).lower())).strip("-")
    return f"hokudai-{slug}"[:100] if slug else None


def _text(fragment: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", fragment)
    text = re.sub(r"<[^>]+>", "", text)
    return html_module.unescape(text).replace(" ", " ").strip()


def _pairs(html: str) -> dict:
    """講義情報タブの cnt_left/cnt_right ペア (引用符は ' と " が混在)。"""
    pairs = {}
    for m in re.finditer(
            r"<div class=['\"]cnt_left['\"]>(.*?)</div>\s*"
            r"<div class=['\"]cnt_right['\"]>(.*?)</div>", html, re.S):
        key = re.sub(r"\s+", "", _text(m.group(1)))
        if key and key not in pairs:
            pairs[key] = m.group(2)
    return pairs


def _creators(raw: str):
    """教員欄 → [{name, affiliation}]。書式ゆれ対応:
    役割接頭辞 (担当者：/司会：…)、「名A・名B（共通所属）」、半角括弧、※注記。"""
    text = _text(raw)
    text = re.sub(r"(担当者|司会|監修|講師|登壇者|脚本／構成|ナビゲーター?)[：:]\s*", "", text)
    creators = []
    for chunk in re.split(r"[、,]|／(?![^（(]*[）)])|\n", text):
        chunk = chunk.strip()
        if not chunk:
            continue
        m = re.match(r"(.+?)[（(]([^）)]*)[）)]", chunk)
        names, affiliation = (m.group(1), m.group(2)) if m else (chunk, None)
        if affiliation:
            affiliation = re.sub(r"[※].*$|^旧[：:]?所属\s*", "", affiliation).strip() or None
        # 「姓 名・姓 名（共通所属）」は ・ で分割 (両側に空白を含む場合のみ。
        # 「シートン・フィリップ」のような単一名は分割しない)
        parts = [names]
        if "・" in names and all(" " in p or "　" in p
                                 for p in names.split("・") if p.strip()):
            parts = names.split("・")
        for person in parts:
            person = re.sub(r"[※].*$", "", person).strip(" 　")
            # 教員欄に組織名が入ることがある (附属図書館 等)。Person にしない
            # (講師が1人も残らなければ make_drafts が Organization 扱いにする)
            if re.search(r"(図書館|センター|機構|研究所|協会|株式会社|支援室)$", person):
                continue
            if person and len(person) <= 40 and person not in [c["name"] for c in creators]:
                creators.append({"name": person, "affiliation": affiliation})
    return creators[:8]


def _clean_quoted(raw: str) -> str:
    """概要から資料マーク行・事業説明の脚注 (＝＝＝以降) を落とす。"""
    body = re.split(r"＝＝＝", raw)[0]
    text = _text(body)
    text = re.sub(r"(限定公開資料|制限資料|CC\s*BY[A-Z\s-]*)\s*$", "", text.strip())
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def parse_course(html: str, url: str):
    pairs = _pairs(html)
    title_raw = pairs.get("タイトル", "")
    name = re.sub(r"\s+", " ", _text(title_raw))
    if not name:
        found = re.search(r'og:title" content="([^"]+)"', html)
        name = html_module.unescape(found.group(1)).strip() if found else ""
    if not name:
        return None

    tags = []
    if pairs.get("タグ"):
        tags = [t.strip() for t in re.findall(r">([^<]+)</a>", pairs["タグ"]) if t.strip()]

    year = None
    found = re.search(r'info_box_year"[^>]*>\s*(\d{4})', html)
    if found:
        year = found.group(1)
    if not year:
        found = re.search(r"((?:19|20)\d{2})年度", name) \
            or re.search(r"[（(]((?:19|20)\d{2})[）)]", name)
        if found:
            year = found.group(1)

    creators = _creators(pairs.get("教員", ""))

    quoted, quoted_labels = "", []
    if pairs.get("概要"):
        text = _clean_quoted(pairs["概要"])
        if len(re.sub(r"\s", "", text)) >= 40:
            quoted, quoted_labels = text, ["概要"]

    materials, seen = [], set()
    for m in re.finditer(r'<a[^>]+href="(https?://ocw\.hokudai\.ac\.jp/wp-content/'
                         r'uploads/[^"]+\.(?:pdf|pptx?|zip))"[^>]*>(.*?)</a>', html, re.S):
        file_url = html_module.unescape(m.group(1))
        if file_url in seen:
            continue
        seen.add(file_url)
        label = re.sub(r"\s+", " ", _text(m.group(2)))
        materials.append({"name": f"講義資料: {label or file_url.rsplit('/', 1)[-1]}"[:120],
                          "contentUrl": file_url})
    if not year and materials:
        file_years = [y for m in materials
                      for y in re.findall(r"(?:19[89]\d|20[012]\d)",
                                          m["contentUrl"].rsplit("/", 1)[-1])]
        if file_years:
            year = min(file_years)

    badge = re.search(r"creativecommons\.org/licenses/([a-z-]+)/", html)
    license_id = LICENSE_BY_BADGE.get(badge.group(1)) if badge else None
    # ページ単位のマーク: 制限資料 = 閲覧のみ / 無表記 = 個別確認が必要
    usage_reuse = None if license_id else \
        ("not_allowed" if "制限資料" in html else "unspecified")

    about = []
    for tag in tags:
        for keyword, subject in GENRE_SUBJECT:
            if keyword in tag:
                if subject not in about:
                    about.append(subject)
                break
    about = about[:3]
    if not about:
        for tag in tags:
            for keyword, subject in FACULTY_SUBJECT:
                if keyword in tag:
                    about = [subject]
                    break
            if about:
                break

    # 種別は明示タグで判定 (部局タグの「〜学部」は学部種別の根拠にしない)
    is_public = any(any(p in t for p in PUBLIC_TAGS) for t in tags)
    is_grad = any(t in ("大学院でさがす", "大学院共通授業科目") for t in tags)
    is_ugrad = any(t in ("学部でさがす", "全学教育科目", "General Education Courses")
                   for t in tags)
    if is_grad or is_ugrad:
        audience = ["student"]
        level = "master" if is_grad and not is_ugrad else "bachelor"
    elif is_public:
        audience = ["general_public"]
        level = "continuing_education" if any("公開講座" in t for t in tags) else None
    else:
        audience = ["student"]
        level = None

    languages = []
    if "japanese" in tags:
        languages.append("ja")
    if "english" in tags:
        languages.append("en")

    has_video = bool(re.search(r"youtube\.com/(embed|watch)|\.mp4|itunes|podcasts\.apple",
                               html, re.I))
    if audience == ["general_public"]:
        resource_types = ((["video"] if has_video else [])
                          + (["script"] if materials else [])) or ["web_page"]
    else:
        resource_types = (["course"] + (["video"] if has_video else [])
                          + (["script"] if materials else []))

    keywords = []
    if pairs.get("キーワード"):
        keywords = [k.strip() for k in re.split(r"[、,／/]", _text(pairs["キーワード"]))
                    if k.strip()][:6]
    genre_labels = [t for t in tags
                    if any(k in t for k, _s in GENRE_SUBJECT)][:3]
    keywords = list(dict.fromkeys(keywords + genre_labels))[:8]

    target = None
    if pairs.get("対象"):
        target = re.sub(r"\s+", " ", _text(pairs["対象"]))[:80] or None

    faculty = next((t for t in tags
                    if re.search(r"学部$|研究院|研究科|学院|センター|博物館|研究所", t)), "")

    return {
        "name_ja": name,
        "faculty": faculty,
        "year": year,
        "target": target,
        "creators": creators,
        "inLanguage": languages or ["ja"],
        "quoted": quoted,
        "quoted_labels": quoted_labels,
        "materials": materials,
        "learningResourceType": resource_types,
        "about": about or ["generic"],
        "educationalLevel": level,
        "audience": audience,
        "license": license_id,
        "usage_reuse": usage_reuse,
        "tags": keywords,
    }
