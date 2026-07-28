"""北大 数理・データサイエンス教育研究センター 教育用データ提供システム
(data.mdsc.hokudai.ac.jp) のデータセット解析。

CKAN。メタデータは API ダンプ (.cache/mdsc_datasets.json、package_search で
事前生成) を正とし、キャッシュした HTML は引用照合用。ライセンスはデータセット
ごと (cc-by 15 / other-open 7 / cc-by-sa 2 / other-site 2 / gfdl 1) だが、
CC は版の明示が無いため license 欄には入れず usageTerms に写す (版を捏造しない)。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

CACHE = Path(__file__).resolve().parent.parent / ".cache"
_datasets_cache = None

# CKAN license_id → (usageTerms.summary, reuse)
LICENSE_TERMS = {
    "cc-by": ("クリエイティブ・コモンズ 表示（CC BY。CKAN 上の表記で、版の明示なし）に"
              "従って利用可。", "allowed_with_conditions"),
    "cc-by-sa": ("クリエイティブ・コモンズ 表示-継承（CC BY-SA。CKAN 上の表記で、版の"
                 "明示なし）に従って利用可。", "allowed_with_conditions"),
    "gfdl": ("GNU Free Documentation License に従って利用可。", "allowed_with_conditions"),
    "other-open": ("オープンライセンス（詳細はデータセットページの表示に従う）。",
                   "allowed_with_conditions"),
    "other-site": ("利用条件は配布元サイトを参照。", "unspecified"),
}

# 産業分類タグ → about (部分一致)。該当なしは generic (教育用データ全般)
TAG_SUBJECT = [
    ("情報通信", "ict"), ("医療", "health_welfare"), ("福祉", "health_welfare"),
    ("金融", "social_sciences"), ("保険", "social_sciences"),
    ("製造", "engineering"), ("建設", "engineering"), ("運輸", "engineering"),
    ("農業", "agriculture"), ("林業", "agriculture"), ("漁業", "agriculture"),
    ("教育", "education"),
]


def _datasets() -> dict:
    global _datasets_cache
    if _datasets_cache is None:
        path = CACHE / "mdsc_datasets.json"
        _datasets_cache = (json.loads(path.read_text(encoding="utf-8"))
                           if path.exists() else {})
    return _datasets_cache


def slug_for(url: str):
    m = re.search(r"/dataset/([a-z0-9_-]+)/?$", url)
    return f"mdsc-{m.group(1)}" if m else None


def parse_course(html: str, url: str):
    data = _datasets().get(url.rstrip("/"))
    if not data:
        return None

    notes = (data.get("notes") or "").strip()
    quoted, quoted_labels = "", []
    if len(re.sub(r"\s", "", notes)) >= 40:
        quoted, quoted_labels = notes, ["データセットの説明"]

    summary, reuse = LICENSE_TERMS.get(data.get("license_id") or "other-site",
                                       LICENSE_TERMS["other-site"])

    about = []
    for tag in data.get("tags", []):
        for keyword, subject in TAG_SUBJECT:
            if keyword in tag:
                about = [subject]
                break
        if about:
            break

    provider = (data.get("author") or "").strip() or data.get("org") or ""
    keywords = list(dict.fromkeys(
        [t.replace("ｰ", "・") for t in data.get("tags", [])]
        + (data.get("formats") or [])))[:8]

    return {
        "slug": slug_for(url),
        "externalUrl": url,
        "name_ja": data["title"],
        "faculty": None,
        "year": data.get("created") or None,
        "creator_organizations": [provider] if provider else [],
        "inLanguage": ["ja"],
        "quoted": quoted,
        "quoted_labels": quoted_labels,
        "materials": [],
        "learningResourceType": ["data"],
        "about": about or ["generic"],
        "educationalLevel": None,
        "audience": ["student", "teacher"],
        "license": None,
        "usage_terms": {"url": url, "summary": summary, "reuse": reuse},
        "provenance_note": "CKAN API のメタデータに基づく。datePublished は CKAN 登録日",
        "tags": keywords,
    }
