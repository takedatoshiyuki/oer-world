# OER World — 開発状況と引き継ぎ

- 更新: 2026-07-30 (oer-kit を public 化・CI トリガ復元。公開カタログ 3,685件)
- 位置づけ: **このプロジェクトの現在地・決定記録・再開手順の正本**。
  新しい作業セッションはまずこれを読む。システム設計は
  [oer-kit の設計書](https://github.com/takedatoshiyuki/oer-kit/blob/main/docs/design.md)、
  コマンドは [commands.md](https://github.com/takedatoshiyuki/oer-kit/blob/main/docs/commands.md) を参照。

## 1. 現在地

| 項目 | 状態 |
|------|------|
| リポジトリ | oer-world = このリポジトリ（`~/Projects/oer-world`・GitHub **public**）／ oer-kit = `~/Projects/oer-kit`（GitHub: takedatoshiyuki/oer-kit・**public 2026-07-30**。外部レビュー4指摘の修正と収集礼儀ゲート実装後に公開） |
| 公開サイト | **公開中**: https://takedatoshiyuki.github.io/oer-world/ （**3,685件**・10ソース）。配信は **`make deploy`（ローカルビルド → gh-pages ブランチ）**。CI は validate（push/PR）と linkcheck（週1）を復元済み（2026-07-30）、publish のみ手動のまま |
| 公開済みリソース | **3,685件**（名大413・京大1,055・東大563・北大564・筑波50・上智454・ICU411・九大28・MIコンソーシアム120・MDSC 27）。自作教材1件は未完のため drafts へ差し戻し中 |
| 下書き（`drafts/`・Git外） | **保留 176件＋自作1件**。保留の内訳 = 年度不明（京大23・東大17・北大20・筑波42・ICU5・九大58・MI 11）＋生成不採用4。人手調査で年度が判明したものから追加昇格できる |
| コーパス（`archive/`・Git外） | 名大の教材ファイル **2,305件・3.86GB**（sha256・権利・クレジット付き manifest）。取得失敗10件はサイト側のリンク切れ（manifest に記録）。京大の資料 PDF 2,839件は未取得（harvest 未実行） |
| バックアップ | git 管理分は GitHub。**`drafts/`・`archive/` は Git外でバックアップなし**（Dropbox から出たため）。archive は manifest から再取得可能だが、閉鎖サイト由来分は再取得不能なので、増えたら `archive_dir` を外部ディスクへ向けるか Time Machine 等で保全する |
| キャッシュ（`.cache/`・Git外） | 名大413・**京大1,209ページ**・**東大series 580ページ**（いずれも全量・失敗0）、ダイジェスト（`nagoya_u_digest.jsonl`・`kyoto_u_digest.jsonl`・`utokyo_channel_digest.jsonl`）、**`kyoto_taxonomy.json`**（検索一覧から逆引きしたカテゴリ・分野・年度。消すと make-drafts の再現性が落ちるので保持） |

配信の手順: `make deploy`（検証→ビルド→gh-pages へ push→Pages が配信）。**approve 実行後は `git add resources/ && git commit` までをワンセットで行う**（2026-07-30 に3,271件の昇格が未コミットのまま3日残る事故があった）。

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
| 生存・構造良好 | 生存7サイト**全て収集済み**: 名大・京大（§3.1）・東大（§3.2）・北大（§3.3）・筑波（§3.4）・上智（§3.5）・九大（§3.5）・ICU（§3.5） |
| 生存・移転 | 東大 → ch.u-tokyo.ac.jp（収集済み）、ICU → ocw.info.icu.ac.jp（収集済み・Google Sites）|
| 閉鎖 | 東工大 OCW・早稲田 course-channel・放送大学 vod — **目録化しないことを決定（2026-07-28）**。Wayback スナップショットと2023年キャッシュは存在するが対象外とする |

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

### 3.4 TSUKUBA OCW の実測（2026-07-27）

- 目録単位は3系統 **92件** = 講義動画 `/course/<分野>/<slug>/` 50・データサイエンス
  講義 `/data-science/<slug>/` 26・筑波大の人々 (Discovery特集) `/discovery/<slug>/` 16。
  コース下位の `/p-N/`（239頁）は各回ページで目録単位にしない
- **サイト全体が CC BY-NC-SA 2.1 日本**（/guide/ に明記）→ 全エントリに
  license を CC 正規URL（版・管轄付き）で付与。スキーマは変更不要だった
- レイアウトは page_ttl 型と movie 型が URL 系統と独立に混在（マークアップで判定）。
  講師は c_lect リンク＋プロフィール節から所属補完。年度表示はデータサイエンス
  講義の公開日のみ → 年度不明42件（題名・スラグ中の年で一部回復。残りは保留。
  Wayback 初出年での補完も選択肢）
- セクション本文が `</section>` を越えると隣接要素の CSS が引用に混入する事故が
  1件あった（機械照合 check-quotes が検出）→ パーサ側で境界を修正済み

### 3.5 上智・九大・ICU の実測（2026-07-28）

**上智 (ocw.cc.sophia.ac.jp・454講義)**
- WordPress の lecture 投稿型が **REST API 公開** → 発見・分類は REST ダンプ
  （`.cache/sophia_lectures.json`・`sophia_dep.json`）。**サイト全体 CC BY-NC-SA
  2.1 日本**（/about/ 明記）
- dep タクソノミで大分類: 講義60・最終講義10・**オープンキャンパス270**・
  高校生向け26・講演会等88。OC・高校生向けは student + upper_secondary
- 講義概要があるのは正規講義中心（108件）。OC・講演会は概要無し → LLM 生成頼み
  （2023調査の「上智0%」予測どおり）。年度は開催年度欄→REST公開日で**全件確保**
- 引用抽出の事故2種を check-quotes が検出（スクリプト内エスケープ断片への誤マッチ・
  `class="result_list"` での捕捉切れ）→ 本文領域限定と終端条件で修正

**九大 QOCW (ocw.kyushu-u.ac.jp・86講義)**
- **サイトが崩壊**（PHP 非実行で生ソース露出・ナビ喪失・2016年更新止まり）だが
  講義本文は静的 HTML で生存。URL は**旧 科研STOER 収集データ (2023) から復元**
- charset ヘッダ無し → requests の latin-1 仮定で二重符号化 → **fetch に
  apparent_encoding 対応を追加**（oer-kit 修正）
- ライセンス表記が確認できない（規約類は壊れた PHP 側と推定）→ 全件 reuse:
  unspecified・引用は32条
- **日付情報が皆無**。Wayback 初出は 2019-22 と遅すぎ（サイト更新停止 2016 と矛盾）、
  サーバ mtime は移行でリセット済み → **資料 PDF 内部の CreationDate** を作成年の
  証拠に採用（28コース判明・2004〜2016。`.cache/kyushu_pdf_years.json`、
  metadataProvenance に明記。make_drafts に provenance_note 追記対応を追加）。
  残り58件は年度不明のまま保留
- 部局欄（旧データ）は種別混在: 一般向け講演会20・最終講義18・基幹教育14・OC 3

**数理・データサイエンス・AI教育強化拠点コンソーシアム (mi.u-tokyo.ac.jp/consortium・131教材)**
- リテラシー/応用基礎の2ページにモデルカリキュラム節ごとの各大学教材が並ぶ
  **1ページ複数エントリ型** → make_drafts に parse_many 契約を新設
- 利用条件は**提供大学ごと**（滋賀大・阪大 CC BY-NC-SA / 九大・北海道医療大 CC BY —
  いずれも**版の明示なし**のため license 欄でなく usageTerms に写す。東大等は個別条件）
  → make_drafts に usage_terms（エントリ単位）と creator_organizations を新設
- 年度: 動画は **YouTube uploadDate**（72件走査・全件判明）、スライドはファイル名 →
  **PDF 内部 CreationDate**（26件・全件判明。九大方式の再利用）。残る年度不明11件
  （プレイリスト5・外部ページ6）は保留
- 旧東大OCWの各回講義リンク34件は除外（UTokyo Channel シリーズ単位で収録済み。
  各回は目録単位にしない方針）。筑波OCW等への既収録リンクはURL重複ガードで自動スキップ

**北大MDSC 教育用データ提供システム (data.mdsc.hokudai.ac.jp・27データセット)**
- **CKAN**。API (package_search) ダンプを正とし HTML は引用照合用。
  learningResourceType は **data**（カタログ初のデータセット収録）
- ライセンスはデータセットごと（CC BY 15 / other-open 7 / CC BY-SA 2 / 配布元参照 2 /
  GFDL 1。CC は版の明示なし → usageTerms）。提供元企業・組織を creator (Organization) に

**ICU (ocw.info.icu.ac.jp・442頁)**
- **Google Sites**。1ページ約800KB（全ページにサイト全体のナビ埋め込み）→
  `role="main"` 以降のみ解析。題名は title タグ。失敗0
- 内訳: for_high（OC講義）177・majors 112・ge 73・sl 63・その他17。
  スラグの年度・学期（BIO101_2017W）で年度不明は5件のみ
- Course Description は英日併記が多い → inLanguage を本文から推定
- **新サイトにライセンス表記が無い**（フッタ All Rights Reserved + CC への
  一般リンクのみ。理念文はあるが条件不明）→ 全件 reuse: unspecified・引用は32条

## 4. 保留中の判断

1. ~~oer-kit の公開タイミング~~ → **公開済み（2026-07-30）**。連合 (ingest) が他者からも利用可能に。CI トリガ復元済み（validate = push/PR、linkcheck = 週1。publish は手動のまま = 配信はローカル make deploy を継続）
2. **w3id.org 名前空間取得**（本運用と判断した時点で。移管に耐える恒久ID）
3. 環境学研究科13件の主題分類（現在 engineering。学際組織なので要確認）
4. 収録方針（何を目録に入れるか）の文書化 — 個人資料が増えた段階で
5. **サイトエンジンの Hugo 移行**（方針は決定済み・oer-kit design §8.4）:
   初期化時に Quarto/Hugo を選択制に。aggregator（oer-world）は Hugo が適合
   （3,537件で Quarto ビルド15分超・search.json 16MB の実測に基づく）。
   組織・個人サイトは Quarto の計算実行・引用が活きる。次の大量投入前が適期

## 5. 次の作業候補（優先順）

1. **7大学の公開まで**: 京大・東大・北大は description 生成済み（2,234件・不採用7）。
   筑波92＋上智454＋ICU442＋九大86 = 1,074件を
   `python -m oer_kit.generate --model gpt-5.4-mini`（約1.1M tok）で生成 →
   レビューシート → 承認リスト再作成（lms を除外）→ approve → `make deploy`。
   年度不明（京大23・東大17・北大20・筑波42・ICU5・九大58）は昇格対象外のまま調査
2. **コーパスのテキスト抽出**: `archive/*/manifest.json` を起点に PDF→テキスト
   （`common_knowledge` の docling/OCR。`~/Applications/lib/python`）。
   LLM 学習データとオントロジー構築（LMS-NG 側の抽出器を使う）の前段。
   京大の資料 PDF 2,839件の harvest もここで

## 6. 再開の仕方（新セッション向け）

```sh
cd ~/Projects/oer-world     # プロジェクト（config.yaml がルートの目印）
make validate               # 動作確認（oer-kit は ~/Projects/oer-kit を既定参照）
```

- 全コマンド: `python -m oer_kit.<cmd>`（一覧は oer-kit の docs/commands.md）
- 実行環境: 通常は素の `python`（pyenv 3.14.6）。**Playwright（JSレンダリング）は
  `~/Dropbox/Projects/genai_activities/.venv/bin/python`**。Quarto は brew 導入済み
- description 生成: `python -m oer_kit.generate --model gpt-5.4-mini`
  （OpenAI 無料枠10M tok/日・実測1件約1,025 tok・全413件で0.41M。
  出力は機械検査され、不採用は TODO のまま残る）
- 取得層の正本は `common_knowledge.web`（`~/Applications/lib/python`）。
  一括取得は `fetch --batch`（render_pages でブラウザ使い回し）
