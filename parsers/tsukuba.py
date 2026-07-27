"""筑波大学OCW (ocw.tsukuba.ac.jp) のページ解析。

2026-07 時点。WordPress 固定ページの階層構造で、目録単位は3系統:
- 講義動画: /course/<分野>/<slug>/ (下位の /p-N/ は各回ページ。目録単位にしない)
  <div class="page_ttl"> の h2 に「講義名 <span>所属 講師名</span>」、
  「講義の概要」「講師のプロフィール」「講義一覧」の h3 セクション、
  パンくず3番目が分野 (工学・体育学など)
- データサイエンス講義: /data-science/<slug>/ (YouTube 埋め込み。
  「講義概要」「プロフィール」「公開」(公開日) セクション)
- 筑波大の人々 (Discovery 特集): /discovery/<slug>/ (インタビュー・特集動画。
  「プロフィール」のみのページが多い)

ライセンスはサイト全体 CC BY-NC-SA 2.1 日本 (/guide/ に明記) →
schema は版・管轄付き CC 正規URLを受理するため URL 形式で返す。
"""

from __future__ import annotations

import hashlib
import html as html_module
import re

SITE_LICENSE = "https://creativecommons.org/licenses/by-nc-sa/2.1/jp/"

# パンくず分野 → about 語彙キー
CATEGORY_SUBJECT = {
    "体育学": "services",           # ISCED-F 1014 (スポーツ) はサービス分野
    "情報システム": "ict", "知識情報システム": "ict", "データサイエンス講義": "ict",
    "数学": "natural_sciences_math", "物理学": "natural_sciences_math",
    "生物学": "natural_sciences_math", "環境科学": "natural_sciences_math",
    "地球環境学": "natural_sciences_math",
    "心理学": "social_sciences", "社会学": "social_sciences",
    "国際関係学": "social_sciences",
    "工学": "engineering",
    "デザイン": "arts_humanities", "思想文化": "arts_humanities",
    "法学": "business_law",
    "医学": "health_welfare",
}


def slug_for(url: str):
    m = re.search(r"ocw\.tsukuba\.ac\.jp/(course/[^/]+|data-science|discovery)/([^/?#]+)/?$",
                  url)
    if not m:
        return None
    kind = m.group(1)
    prefix = ("tsukuba-ds" if kind == "data-science"
              else "tsukuba-discovery" if kind == "discovery" else "tsukuba")
    slug = re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "-", m.group(2).lower())).strip("-")
    if not slug:   # 日本語スラグは安定ハッシュで代替
        slug = hashlib.md5(m.group(2).encode()).hexdigest()[:10]
    return f"{prefix}-{slug}"[:100]


def _text(fragment: str) -> str:
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", fragment, flags=re.S | re.I)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_module.unescape(text).replace("　", " ")
    return re.sub(r"[ \t]+", " ", text).strip()


def _sections(main: str) -> dict:
    """h3 見出し → 直後の内容 (次の h3 まで)。"""
    parts = re.split(r"<h3[^>]*>(.*?)</h3>", main, flags=re.S)
    sections = {}
    for i in range(1, len(parts) - 1, 2):
        key = re.sub(r"\s+", "", _text(parts[i]))
        if key and key not in sections:
            # 節の本文は section 要素の終わりまで (越えると周辺要素が混入する)
            sections[key] = re.split(r"</section>", parts[i + 1])[0]
    return sections


def parse_course(html: str, url: str):
    main_match = re.search(r"<main[^>]*>(.*?)</main>", html, re.S)
    if not main_match:
        return None
    main = main_match.group(1)

    crumbs = [_text(c) for c in re.findall(r'property="name">(.*?)</span>', main, re.S)]
    crumbs = [c for c in crumbs if c and "Home" not in c]

    is_course = "/course/" in url
    is_ds = "/data-science/" in url

    # レイアウトは2系統: page_ttl 型 (コース一覧型) と movie 型 (動画1本型)。
    # /course/ でも動画型のページがあるため、URL でなくマークアップで判定する
    lecturer_from_h2 = ""
    h2 = re.search(r'page_ttl[^>]*>.*?<h2[^>]*>(.*?)</h2>', main, re.S)
    if h2:
        span = re.search(r"<span>(.*?)</span>", h2.group(1), re.S)
        lecturer_from_h2 = _text(span.group(1)) if span else ""
        name = _text(re.sub(r"<span>.*?</span>", "", h2.group(1), flags=re.S))
    else:
        h2 = re.search(r'movie_header.*?<h2[^>]*>(.*?)</h2>', main, re.S)
        if not h2:
            return None
        # 「シリーズ名<span>サブタイトル</span>」または「<span>タイトル</span>」
        span = re.search(r"<span>(.*?)</span>", h2.group(1), re.S)
        series = _text(re.sub(r"<span>.*?</span>", "", h2.group(1), flags=re.S))
        subtitle = _text(span.group(1)) if span else ""
        subtitle = re.sub(r"^(導入|基礎|発展|応用)[：:]\s*", "", subtitle)
        name = (f"{series} {subtitle}".strip() if series and subtitle
                else subtitle or series)
    if not name:
        return None

    sections = _sections(main)
    quoted, quoted_labels = "", []
    for label in ("講義の概要", "講義概要", "概要"):
        if label in sections:
            text = re.sub(r"\n{2,}", "\n", _text(sections[label]))
            if len(re.sub(r"\s", "", text)) >= 40:
                quoted, quoted_labels = text, [label]
            break
    # Discovery 特集はキャッチコピーが h3 見出しで、その本文が紹介文
    # (例: 「幾何学×折り紙で、あらゆる立体を具現化」)。既知ラベル以外の
    # 節を紹介文として採用する
    if not quoted:
        known = {"講義の概要", "講義概要", "概要", "プロフィール", "講師のプロフィール",
                 "講義一覧", "公開", "特集一覧", "関連講義"}
        for heading, body in sections.items():
            if heading in known:
                continue
            text = re.sub(r"\n{2,}", "\n", _text(body))
            if len(re.sub(r"\s", "", text)) >= 40:
                quoted, quoted_labels = text, [heading[:30]]
                break

    # 講師: 講師一覧ページへのリンク (c_lect) が最も確実。
    # <a class="c_lect" href="…/lecturer/…">氏名</a><span>所属</span>
    creators = []
    for m in re.finditer(r'<a class="c_lect"[^>]*>(.*?)</a>\s*(?:<span>(.*?)</span>)?',
                         main, re.S):
        person = _text(m.group(1))
        affiliation = _text(m.group(2) or "") or None
        if affiliation:
            affiliation = re.sub(r"（所属は公開時）|\(所属は公開時\)", "",
                                 affiliation).strip() or None
        if person and len(person) <= 40 and person not in [c["name"] for c in creators]:
            creators.append({"name": person, "affiliation": affiliation})
    creators = creators[:8]
    if not creators:
        profile = sections.get("講師のプロフィール") or sections.get("プロフィール")
        if profile:
            lines = [l.strip() for l in _text(profile).splitlines() if l.strip()]
            if lines:
                person, affiliation = lines[0], (lines[1] if len(lines) > 1 else None)
                # 「氏名 所属…」が1行に連結される場合は先頭の「姓 名」を切り出す
                if len(person) > 25 and "大学" in person:
                    tokens = person.split(" ")
                    if len(tokens) >= 3:
                        person, affiliation = " ".join(tokens[:2]), " ".join(tokens[2:])
                if len(person) <= 40 and not re.search(r"[。、]", person):
                    creators = [{"name": person, "affiliation": affiliation}]
    if not creators and lecturer_from_h2:
        # 「筑波大学 システム情報系…域 金久保 利之」→ 末尾の「姓 名」を講師とみなす
        m = re.match(r"(.*?)([^ ]+ [^ ]+)$", lecturer_from_h2.strip())
        if m:
            creators = [{"name": m.group(2), "affiliation": m.group(1).strip() or None}]
    # c_lect リンクに所属 span が無いページはプロフィール行「氏名 所属…」から補完
    profile = sections.get("講師のプロフィール") or sections.get("プロフィール")
    if profile:
        profile_text = _text(profile)
        for c in creators:
            if not c.get("affiliation") and c["name"] in profile_text:
                remainder = profile_text.split(c["name"], 1)[1]
                rest = (remainder.splitlines() or [""])[0].strip(" 　")
                if 2 <= len(rest) <= 60:
                    c["affiliation"] = rest

    year = None
    published = sections.get("公開")
    if published:
        d = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", _text(published))
        if d:
            year = f"{d.group(1)}-{int(d.group(2)):02d}-{int(d.group(3)):02d}"
    if not year:
        d = re.search(r"((?:19|20)\d{2})年度", name) \
            or re.search(r"((?:19|20)\d{2})(?:[/?#]|$)", url.rstrip("/").rsplit("/", 1)[-1])
        if d:
            year = d.group(1)

    category = ""
    if is_course and len(crumbs) >= 3:
        category = crumbs[-2]        # Home(除去済) 講義動画 <分野> 講義名
    elif is_ds:
        category = "データサイエンス講義"
    about = [CATEGORY_SUBJECT[category]] if category in CATEGORY_SUBJECT else []

    has_video = bool(re.search(r"youtube|youtu\.be|\.mp4", html, re.I))
    materials, seen = [], set()
    for m in re.finditer(r'<a[^>]+href="(https?://ocw\.tsukuba\.ac\.jp/[^"]+\.pdf)"'
                         r'[^>]*>(.*?)</a>', main, re.S):
        file_url = html_module.unescape(m.group(1))
        if file_url in seen:
            continue
        seen.add(file_url)
        label = _text(m.group(2)) or file_url.rsplit("/", 1)[-1]
        materials.append({"name": f"講義資料: {label}"[:120], "contentUrl": file_url})

    if is_course or is_ds:
        audience, level = ["student"], None
        resource_types = (["course"] + (["video"] if has_video else [])
                          + (["script"] if materials else []))
    else:
        audience, level = ["general_public"], None
        resource_types = ((["video"] if has_video else [])
                          + (["script"] if materials else [])) or ["web_page"]

    tags = [t for t in (category,) if t and t != "データサイエンス講義"]
    if is_ds:
        tags.append("データサイエンス")
    if not is_course and not is_ds:
        tags.append("筑波大の人々")

    return {
        "name_ja": name,
        "faculty": None,      # 分野はパンくず由来 (部局ではない) → about/keywords にのみ使う
        "year": year,
        "creators": creators,
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
