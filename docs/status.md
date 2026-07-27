# OER World — 開発状況と引き継ぎ

- 更新: 2026-07-27
- 位置づけ: **このプロジェクトの現在地・決定記録・再開手順の正本**。
  新しい作業セッションはまずこれを読む。システム設計は
  [oer-kit の設計書](https://github.com/takedatoshiyuki/oer-kit/blob/main/docs/design.md)、
  コマンドは [commands.md](https://github.com/takedatoshiyuki/oer-kit/blob/main/docs/commands.md) を参照。

## 1. 現在地

| 項目 | 状態 |
|------|------|
| リポジトリ | oer-world = このリポジトリ（`~/Projects/oer-world`。2026-07-26 に Dropbox 外へ移動。GitHub: takedatoshiyuki/oer-world・**private**）／ oer-kit = `~/Projects/oer-kit`（GitHub: takedatoshiyuki/oer-kit・**private**） |
| 公開サイト | **停止中**（2026-07-26 に一旦 private 化。Pages 設定も削除済み） |
| 公開済みリソース | **415件**（名大413・東大series 1・自作教材1）。2026-07-27 に412件を昇格（機械検査全数+抜き取り読み10件+レビューシート提出のプロセスで実施） |
| 下書き（`drafts/`・Git外） | 0件（全件昇格済み） |
| コーパス（`archive/`・Git外） | 名大の教材ファイル **2,305件・3.86GB**（sha256・権利・クレジット付き manifest）。取得失敗10件はサイト側のリンク切れ（manifest に記録） |
| バックアップ | git 管理分は GitHub。**`drafts/`・`archive/` は Git外でバックアップなし**（Dropbox から出たため）。archive は manifest から再取得可能だが、閉鎖サイト由来分は再取得不能なので、増えたら `archive_dir` を外部ディスクへ向けるか Time Machine 等で保全する |
| キャッシュ（`.cache/`・Git外） | 名大413コース＋京大・東大のサンプルページ、名大ダイジェスト（`nagoya_u_digest.jsonl`） |

再公開の手順: ①両リポを `gh repo edit --visibility public` ②`gh api
repos/takedatoshiyuki/oer-world/pages -X POST -f build_type=workflow` ③publish
ワークフロー再実行。※両方 private の間は oer-world の CI が oer-kit を
pip install できず**失敗する**（既知。ローカルは `make validate` で問題なし）。

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
| 生存・構造良好 | **京大**（?video_id= のサブページ型・242コース確認・CC 表記は要個別確認）、**名大**（収集済み）、北大、筑波、上智、九大 |
| 生存・移転 | 東大 → **ch.u-tokyo.ac.jp**（UTokyo Channel。旧OCWのURLは series へ301。**規約が複製禁止**＝目録のみ）、ICU → ocw.info.icu.ac.jp |
| 閉鎖 | 東工大 OCW・早稲田 course-channel・放送大学 vod（3つとも Wayback にスナップショットあり。2023年キャッシュが手元にある） |

名大の実測ノート: SPA なので Playwright 必須／og:description はサイト定型文が混入
（頻度除外で対応済み）／「授業の目的」等のラベル辞書は `parsers/nagoya_u.py`。
説明文抽出の的中率（2023キャッシュ実測）: 旧東大100%・ICU84%・北大63%・上智0%
（ラベルも meta も無し → LLM の出番）。

## 4. 保留中の判断

1. **リポジトリの public 復帰と Pages 再開**（カタログ415件は準備完了。これが最後の公開スイッチ）
2. **w3id.org 名前空間取得**（本運用と判断した時点で。移管に耐える恒久ID）
3. 環境学研究科13件の主題分類（現在 engineering。学際組織なので要確認）
4. 収録方針（何を目録に入れるか）の文書化 — 個人資料が増えた段階で

## 5. 次の作業候補（優先順）

1. **コーパスのテキスト抽出**: `archive/*/manifest.json` を起点に PDF→テキスト
   （`common_knowledge` の docling/OCR。`~/Applications/lib/python`）。
   LLM 学習データとオントロジー構築（LMS-NG 側の抽出器を使う）の前段
2. **次サイトの収集**: 京大から（構造調査済み）。discover → fetch --batch →
   パーサ作成 → make-drafts → generate → 横断検査
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
