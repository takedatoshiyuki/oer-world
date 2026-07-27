# OER World — 開発状況と引き継ぎ

- 更新: 2026-07-27 (京大1,078・東大579・北大584件を下書き生成。京大は description 生成済み)
- 位置づけ: **このプロジェクトの現在地・決定記録・再開手順の正本**。
  新しい作業セッションはまずこれを読む。システム設計は
  [oer-kit の設計書](https://github.com/takedatoshiyuki/oer-kit/blob/main/docs/design.md)、
  コマンドは [commands.md](https://github.com/takedatoshiyuki/oer-kit/blob/main/docs/commands.md) を参照。

## 1. 現在地

| 項目 | 状態 |
|------|------|
| リポジトリ | oer-world = このリポジトリ（`~/Projects/oer-world`。2026-07-26 に Dropbox 外へ移動。GitHub: takedatoshiyuki/oer-world・**private**）／ oer-kit = `~/Projects/oer-kit`（GitHub: takedatoshiyuki/oer-kit・**private**） |
| 公開サイト | **公開中**: https://takedatoshiyuki.github.io/oer-world/ （415件）。oer-world は public、**oer-kit は private のまま**（メンテ体制が整うまで公開タイミングを選ぶ判断・2026-07-27）。このため CI ではなく **`make deploy`（ローカルビルド → gh-pages ブランチ）** で配信する。CI 3本は手動起動のみに変更済み（oer-kit 公開後にトリガを復元） |
| 公開済みリソース | **414件**（名大413・東大series 1）。2026-07-27 に412件を昇格（機械検査全数+抜き取り読み10件+レビューシート提出のプロセスで実施）。自作教材1件は未完のため drafts へ差し戻し（07-27） |
| 下書き（`drafts/`・Git外） | **京大 1,078＋東大 579＋北大 584＋自作1件**（2026-07-27 生成。京大は description 生成済み 1,076/1,078・high 908/low 168。東大・北大は generate 待ち。年度不明は京大23・東大17・北大20件で、datePublished 無しの検証エラーとして残し人手調査に回す） |
| コーパス（`archive/`・Git外） | 名大の教材ファイル **2,305件・3.86GB**（sha256・権利・クレジット付き manifest）。取得失敗10件はサイト側のリンク切れ（manifest に記録）。京大の資料 PDF 2,839件は未取得（harvest 未実行） |
| バックアップ | git 管理分は GitHub。**`drafts/`・`archive/` は Git外でバックアップなし**（Dropbox から出たため）。archive は manifest から再取得可能だが、閉鎖サイト由来分は再取得不能なので、増えたら `archive_dir` を外部ディスクへ向けるか Time Machine 等で保全する |
| キャッシュ（`.cache/`・Git外） | 名大413・**京大1,209ページ**・**東大series 580ページ**（いずれも全量・失敗0）、ダイジェスト（`nagoya_u_digest.jsonl`・`kyoto_u_digest.jsonl`・`utokyo_channel_digest.jsonl`）、**`kyoto_taxonomy.json`**（検索一覧から逆引きしたカテゴリ・分野・年度。消すと make-drafts の再現性が落ちるので保持） |

配信の手順: `make deploy`（検証→ビルド→gh-pages へ push→Pages が配信）。oer-kit を公開したら CI トリガを復元して push 毎の自動配信に戻せる。

## 2. 主要な決定（日付つき）

詳細な根拠は oer-kit 設計書 §1 の決定表。プロジェクトとして効いている順に:

- **目的はオープンな知識の収集**（07-21）: カタログに加え、LLM のオープン学習データと
  LMS-NG（`~/Dropbox/Projects/LMS-NG`、`packages/oer-bridge` が接続）での素材利用
- **aggregator 運用**（07-21）: AI 生成メタデータは機械検査＋信頼度明示＋誤り報告窓口
  （Issues）で未レビュー公開可。根拠 = 名大413件のレビューで見つかった問題は
  **すべてシステム側の欠陥**（分類バグ135件・引用の省略記号97件・ラベル漏れ49件…）で、
  個別データの手直しは0件だった
- **二層ライセンス**（07-21）: メタデータ CC0／コンテンツは各リソース表示。引用原文
  （quotedDescription）は CC0 対象外・ページ表示のみ
- **CC 以外も目録化**（07-21）: 独自条件（名大型）・視聴のみ（東大型）・記載なし
  （個人ページ型）を区分して表示。コーパス取得は再利用可のもののみ
- **個人公開資料も対象**（07-24）: `sourceCollection.kind: personal`＋アーカイブ確保＋
  オプトアウト窓口。Wayback 保存とオプトアウトまでの公開維持が長期的立場（07-21記録）
- **モジュール分割**（07-24）と**命名 oer-world**（07-26）、**一旦 private**（07-26）

## 3. 収集対象の調査結果（2026-07-21 実測）

レジストリは [sites.yaml](../sites.yaml)（名大・東大は調査済み・パーサあり）。
JOCW 系11サイトの生存確認:

| 状態 | サイト |
|------|--------|
| 生存・構造良好 | **京大**（収集済み → §3.1）、**名大**（収集済み）、**北大**（収集済み → §3.3）、筑波（WP・/course 型）、上智（WP・小規模・説明文抽出0%）、九大（**http のみ**・2000年代の手組み静的） |
| 生存・移転 | 東大 → **ch.u-tokyo.ac.jp**（**収集済み → §3.2**。旧OCWのURLは series へ301。**規約が複製禁止**＝目録のみ）、ICU → ocw.info.icu.ac.jp |
| 閉鎖 | 東工大 OCW・早稲田 course-channel・放送大学 vod（3つとも Wayback にスナップショットあり。2023年キャッシュが手元にある） |

名大の実測ノート: SPA なので Playwright 必須／og:description はサイト定型文が混入
（頻度除外で対応済み）／「授業の目的」等のラベル辞書は `parsers/nagoya_u.py`。
説明文抽出の的中率（2023キャッシュ実測）: 旧東大100%・ICU84%・北大63%・上智0%
（ラベルも meta も無し → LLM の出番）。

### 3.1 京大OCW の実測（2026-07-27）

- WordPress 静的（requests で可）。sitemap のコース1,209行のうち**実コースは1,078件**
  （131行は部局別一覧ページ）。全ページ取得済み・パース失敗0
- **カテゴリ・分野・年度はコースページに出ない** → 検索UI（`/?s=&category=…` 等）の
  結果一覧を走査して逆引き（`.cache/kyoto_taxonomy.json`、判明率100%）。
  内訳: 通常講義337・**公開講義475**・最終講義81・国際会議95・その他90
- ライセンスは**ページごとの CC バッジ**（886件・BY-NC-SA 4.0 中心）が優先、
  無いページは guideline の独自条件（非営利・教育目的・クレジットで二次利用可）を
  usageTerms に。make_drafts はこのコース単位ライセンスに対応済み
- カテゴリで対象者を切替: 通常講義 → student（部局名から bachelor/master）、
  公開講義 → general_public + continuing_education、国際会議 → professional
- 検索UIの分野タグ34種 → about 語彙への対応表はパーサ内 `SUBJECT_MAP`
- 講義資料 PDF は `rel="archives"` リンクで2,839件（コーパス取得は未実施）

### 3.2 UTokyo Channel の実測（2026-07-27）

- 目録単位は**シリーズ**（sitemap `wp-sitemap-ut-ch-series-1.xml` に580件 =
  東大TV 403＋旧OCW 177。個別講義 ut-ch-content は約6,000件で目録単位にしない）。
  07-21 調査時のメモ「278件」は誤り（当時の数え方が不明。実際は580）
- 手作業の試作1件 (`utokyo-series-digital-humanities`) は公開済みのまま。
  make_drafts が公開済み externalUrl をスキップするため重複しない（579件生成）
- シリーズページのタグ（`?tag=…`）が有用: ジャンル（AI・情報〜食料・農業）→ about、
  中高生向け → student + upper_secondary、英語話者向け → inLanguage en (92件)、
  東京大学正規授業/Produced by → audience と learningResourceType の切替
- 「資料あり」はアイコン表記から検出できるが、**視聴のみ規約のため materials
  （ファイルURL）は載せない**。引用は著作権法32条の書式（make_drafts が
  license_status で切替）
- 年度不明17件は数理・情報系の正規授業群（ページに開講年表示なし）

### 3.3 北大OCW の実測（2026-07-27）

- WordPress だが講義は**カスタム投稿型で REST・sitemap に出ない** →
  `/lecture/page/N`（24頁）の一覧走査で **584講義** を発見
  （`.cache/urls_hokudai_lectures.tsv`）。トップページのみ locale クッキー要
- 講義情報は `cnt_left`/`cnt_right` のラベル・値ペア
  （タイトル/教員/概要/講義資料/タグ/キーワード/対象/単位等/備考）
- **ライセンスはページ単位のマーク**: 制限資料 444（閲覧のみ → reuse:
  not_allowed）/ CC BY-NC 2 / **無表記 138（→ reuse: unspecified**。映像内
  クレジット等での個別確認が必要）。make_drafts に `usage_reuse` 上書きを追加
- /licence は**教材**のマークを定めるものでページ本文の転載許諾ではない →
  引用の根拠は 32条の引用（sites.yaml `quote_basis: quotation` で強制。
  make_drafts 対応済み）
- 教員欄は書式ゆれが大きい（役割接頭辞・「名A・名B（共通所属）」・半角括弧・
  外部所属多数）→ 所属付き creators としてパース（make_drafts の creators 対応を追加）
- タグ: 種別（公開講座でさがす/学部でさがす/大学院でさがす）→ audience/level、
  ジャンル（理学／自然科学 等）→ about、japanese/english → inLanguage
- 対象者の内訳: 公開講座系 266 / 学部 140 / 大学院 53 / 種別不明 125（student扱い）
- 動画は旧 iTunesU リンク中心（129件）。資料 PDF 969件（コーパス取得は未実施）

## 4. 保留中の判断

1. **oer-kit の公開タイミング**（連合モデルの前提。メンテ体制と合わせて判断）
2. **w3id.org 名前空間取得**（本運用と判断した時点で。移管に耐える恒久ID）
3. 環境学研究科13件の主題分類（現在 engineering。学際組織なので要確認）
4. 収録方針（何を目録に入れるか）の文書化 — 個人資料が増えた段階で

## 5. 次の作業候補（優先順）

1. **京大＋東大＋北大の公開まで**: 京大は description 生成済み。東大579＋北大584
   ＋京大再試行2件を `python3 -m oer_kit.generate --model gpt-5.4-mini`
   （約1.2M tok。無料枠10M/日内）→ 横断検査 → レビュー → `approve --all` →
   `make deploy`。年度不明（京大23・東大17・北大20件）は昇格対象外のまま調査
2. **コーパスのテキスト抽出**: `archive/*/manifest.json` を起点に PDF→テキスト
   （`common_knowledge` の docling/OCR。`~/Applications/lib/python`）。
   LLM 学習データとオントロジー構築（LMS-NG 側の抽出器を使う）の前段。
   京大の資料 PDF 2,839件の harvest もここで
3. 閉鎖3サイトの目録化（2023キャッシュ＋Wayback。掲載ポリシーは §2 のとおり掲載推奨）

## 6. 再開の仕方（新セッション向け）

```sh
cd ~/Projects/oer-world     # プロジェクト（config.yaml がルートの目印）
make validate               # 動作確認（oer-kit は ~/Projects/oer-kit を既定参照）
```

- 全コマンド: `python3 -m oer_kit.<cmd>`（一覧は oer-kit の docs/commands.md）
- 実行環境: 通常は素の `python3`（pyenv 3.14.6）。**Playwright（JSレンダリング）は
  `~/Dropbox/Projects/genai_activities/.venv/bin/python3`**。Quarto は brew 導入済み
- description 生成: `python3 -m oer_kit.generate --model gpt-5.4-mini`
  （OpenAI 無料枠10M tok/日・実測1件約1,025 tok・全413件で0.41M。
  出力は機械検査され、不採用は TODO のまま残る）
- 取得層の正本は `common_knowledge.web`（`~/Applications/lib/python`）。
  一括取得は `fetch --batch`（render_pages でブラウザ使い回し）
