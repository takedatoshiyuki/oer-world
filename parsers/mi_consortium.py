"""数理・データサイエンス・AI教育強化拠点コンソーシアム (mi.u-tokyo.ac.jp/consortium)
の e ラーニング教材リスト解析。

リテラシーレベルと応用基礎レベルの2ページに、モデルカリキュラムの節ごとに
各大学提供の講義動画 (YouTube)・スライド (PDF) が並ぶ「1ページ複数エントリ」型
→ make_drafts の parse_many 契約で返す。

- ラベル書式: 「教材名 (動画・滋賀大学)」「教材名（スライド・東京大学）」。
  B節は「大阪大学 「…」（45動画）」形式のシリーズリンク
- 利用条件は提供大学ごと (滋賀大・阪大 = CC BY-NC-SA、九大・北海道医療大 = CC BY
  — いずれも版の明示なし → usageTerms に写す。東大・筑波・都市大・名大は個別条件)
- プレースホルダ行 (「第xx回 講義タイトル」・ダミー動画ID) と書籍・協力企業
  リンクは対象外
- 日付は PDF ファイル名の年のみ確実 → それ以外は年度不明として保留
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin

PLACEHOLDER_VIDEO = "V6dWPKv2ioY"
VIDEO_YEARS_PATH = Path(__file__).resolve().parent.parent / ".cache" / "mi_video_years.json"
PDF_YEARS_PATH = Path(__file__).resolve().parent.parent / ".cache" / "mi_pdf_years.json"
_video_years_cache = _pdf_years_cache = None


def _video_years() -> dict:
    global _video_years_cache
    if _video_years_cache is None:
        _video_years_cache = (json.loads(VIDEO_YEARS_PATH.read_text(encoding="utf-8"))
                              if VIDEO_YEARS_PATH.exists() else {})
    return _video_years_cache


def _pdf_years() -> dict:
    global _pdf_years_cache
    if _pdf_years_cache is None:
        _pdf_years_cache = (json.loads(PDF_YEARS_PATH.read_text(encoding="utf-8"))
                            if PDF_YEARS_PATH.exists() else {})
    return _pdf_years_cache

# 提供大学 → usageTerms (版の明示が無い CC は license 欄に入れない)
UNIV_TERMS = {
    "滋賀大学": ("クリエイティブ・コモンズ 表示-非営利-継承（CC BY-NC-SA。コンソーシアム"
                 "ページの表記で、版の明示なし）に従って利用可。", "allowed_with_conditions"),
    "大阪大学": ("クリエイティブ・コモンズ 表示-非営利-継承（CC BY-NC-SA。コンソーシアム"
                 "ページの表記で、版の明示なし）に従って利用可。", "allowed_with_conditions"),
    "九州大学": ("クリエイティブ・コモンズ 表示（CC BY。コンソーシアムページの表記で、"
                 "版の明示なし）に従って利用可。", "allowed_with_conditions"),
    "北海道医療大学": ("クリエイティブ・コモンズ 表示（CC BY。コンソーシアムページの"
                       "表記で、版の明示なし）に従って利用可。", "allowed_with_conditions"),
}
DEFAULT_TERMS = ("提供大学ごとに利用条件が定められている（コンソーシアムページの"
                 "「利用条件」の各大学のリンク先を参照）。", "unspecified")

SKIP_HOSTS = ("kspub.co.jp", "docs.microsoft.com", "learn.microsoft.com",
              "amazon", "gacco.org/about",
              # 旧東大OCWの各回講義リンク (UTokyo Channel へ301)。
              # UTokyo Channel はシリーズ単位で収録済みのため各回は目録単位にしない
              "ocw.u-tokyo.ac.jp")

KIND_LRT = {"動画": ["video"], "スライド": ["slide"], "zip": ["data"],
            "データ": ["data"], "ノートブック": ["worksheet"], "事例": ["case_study"],
            "資料": ["text"]}


class _LinkCollector(HTMLParser):
    """<a> と見出し (h3/h4) を文書順に集める。壊れ気味の HTML でも落ちない。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items = []          # (kind, text) kind = h3/h4/link
        self._link = None        # [href, buffer]
        self._heading = None     # [tag, buffer]

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            self._link = [href, []]
        elif tag in ("h3", "h4"):
            self._heading = [tag, []]

    def handle_endtag(self, tag):
        if tag == "a" and self._link:
            self.items.append(("link", self._link[0], " ".join(self._link[1]).strip()))
            self._link = None
        elif tag in ("h3", "h4") and self._heading and self._heading[0] == tag:
            self.items.append((tag, "", " ".join(self._heading[1]).strip()))
            self._heading = None

    def handle_data(self, data):
        text = re.sub(r"\s+", " ", data).strip()
        if not text:
            return
        if self._link:
            self._link[1].append(text)
        elif self._heading:
            self._heading[1].append(text)


def _entry_slug(level: str, url: str) -> str:
    tail = url.rstrip("/").rsplit("/", 1)[-1]
    tail = re.sub(r"\.(pdf|html?)$", "", tail)
    clean = re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "-", tail.lower())).strip("-")
    if not clean or len(clean) < 3:
        clean = hashlib.md5(url.encode()).hexdigest()[:10]
    return f"mi-{level}-{clean}"[:100]


def parse_many(html: str, url: str):
    level = "ouyoukiso" if "ouyoukiso" in url else "literacy"
    level_ja = "応用基礎レベル" if level == "ouyoukiso" else "リテラシーレベル"

    collector = _LinkCollector()
    collector.feed(html)

    entries, seen = [], set()
    section = ""
    for kind, href, text in collector.items:
        if kind in ("h3", "h4"):
            section = text
            continue
        if not href or href.startswith(("#", "mailto:")):
            continue
        if any(host in href for host in SKIP_HOSTS) or PLACEHOLDER_VIDEO in href:
            continue
        if "第xx回" in text or not text:
            continue

        # 「教材名 (動画・大学)」型
        m = re.search(r"[（(]\s*(動画|スライド|zip|ノートブック|データ|事例|資料)"
                      r"[・･]\s*([^)）]+?)\s*[)）]", text)
        # B節の「大学 「タイトル」（N動画）」型
        m2 = re.match(r"(.+?(?:大学|大))\s*「(.+?)」\s*[（(](\d+)動画[)）]", text)
        if m:
            material_kind = m.group(1)
            univ = m.group(2).strip()
            # 「（動画・スライド・大阪大学）」のような複合ラベル: 末尾が大学名
            parts = [p.strip() for p in re.split(r"[・･]", univ) if p.strip()]
            extra_kinds = [p for p in parts[:-1] if p in KIND_LRT]
            if parts:
                univ = parts[-1]
            name = re.sub(r"[（(]\s*(?:動画|スライド|zip|ノートブック|データ|事例|資料)"
                          r"[・･][^)）]*[)）]", "", text).strip()
            # 同一ラベルに複数教材が並ぶ行は最初の教材名だけが該当リンクのもの
            name = name.split("  ")[0].strip() or text
            resource_types = KIND_LRT.get(material_kind, ["other"])
            for k in extra_kinds:
                resource_types += [t for t in KIND_LRT[k] if t not in resource_types]
        elif m2:
            univ = {"滋賀大": "滋賀大学"}.get(m2.group(1), m2.group(1))
            name = f"{m2.group(2)}（{m2.group(3)}動画）"
            resource_types = ["video", "course"]
        else:
            continue

        external = urljoin(url, href)
        if external in seen:
            continue
        seen.add(external)

        year = None
        found = re.search(r"((?:19|20)\d{2})", external.rsplit("/", 1)[-1])
        if found and external.lower().endswith(".pdf"):
            year = found.group(1)
        if not year:
            # YouTube の uploadDate / PDF 内部の CreationDate (いずれも事前走査)
            year = _video_years().get(external) or _pdf_years().get(external)

        summary, reuse = UNIV_TERMS.get(univ, DEFAULT_TERMS)
        entries.append({
            "slug": _entry_slug(level, external),
            "externalUrl": external,
            "name_ja": f"{name}（{univ}・数理DS-AI教育 {level_ja}）",
            "faculty": None,
            "year": year,
            "creator_organizations": [univ],
            "inLanguage": ["ja"],
            "quoted": "",
            "quoted_labels": [],
            "materials": [],
            "learningResourceType": resource_types,
            "about": ["ict"],
            "educationalLevel": "bachelor",
            "audience": ["student", "teacher"],
            "license": None,
            "usage_terms": {"url": url, "summary": summary, "reuse": reuse},
            "target": section[:60] or None,
            "provenance_note": ("数理・データサイエンス・AI教育強化拠点コンソーシアムの"
                                "モデルカリキュラム対応教材リストに基づく。datePublished は"
                                "動画は YouTube 公開年、スライドはファイル名または PDF 内部の作成年"),
            "tags": [t for t in ("データサイエンス", level_ja, section[:30] or None) if t],
        })
    return entries
