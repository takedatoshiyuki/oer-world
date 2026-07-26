# OER コレクション

日本の大学 OCW・個人公開の授業資料などを収集し、カタログとコンテンツを公開する
プロジェクト。**オープンな知識の収集**が目的（LLM のオープンな学習データ・
LMS-NG での素材利用を含む）。

[oer-kit](../oer-kit/)（OER カタログ構築キット）の管理下で運用する。
スキーマ・ツール・設計文書はモジュール側にあり、ここには**このコレクション固有のもの**
だけを置く。

## 構成

```
config.yaml         サイト名・公開URL・運用モード (aggregator)・報告窓口
sites.yaml          収集対象サイトのレジストリ (名大の授業・UTokyo Channel …)
parsers/            サイト別パーサ (nagoya_u.py …)
resources/          公開中のリソース (metadata.yaml)
site/               サイトのページ (カタログ・使い方・about)
vocabularies/       統制語彙 (このプロジェクトで編集可)
drafts/             レビュー前の下書き (Git 管理外)
archive/            コーパス層: 収集した教材ファイル+権利manifest (Git 管理外)
.cache/             取得キャッシュ (Git 管理外)
```

## 日常の操作

```sh
make validate OER_KIT=../oer-kit     # 検証
make preview  OER_KIT=../oer-kit     # ローカルプレビュー
make site     OER_KIT=../oer-kit     # 公開一式を _site/ へ生成
```

oer-kit を `pip install -e ../oer-kit` してあれば `OER_KIT=` の指定は不要。
収集パイプライン等の全コマンドは [oer-kit の docs/commands.md](../oer-kit/docs/commands.md)、
手順の全体像は [docs/user-guide.md](../oer-kit/docs/user-guide.md) を参照。

## 運用方針の要点

- 運用モードは **aggregator**（[設計書 §9.1](../oer-kit/docs/design.md)）:
  AI 生成メタデータは機械検査＋信頼度明示＋誤り報告窓口を条件に公開し、
  誤りの訂正は利用者の指摘に委ねる
- メタデータは CC0 ／ 教材コンテンツは各リソースの表示に従う（[LICENSE.md](LICENSE.md)）
- 個人公開資料は出典種別 `personal` を付し、登録時に Web アーカイブを確保する
