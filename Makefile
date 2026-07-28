# oer-kit を使う OER プロジェクトのビルド。使い方: make site / make preview
# oer-kit の場所 (pip インストール済みなら OER_KIT= と空指定で上書き可)
OER_KIT ?= $(HOME)/Projects/oer-kit
PY = $(if $(OER_KIT),PYTHONPATH=$(OER_KIT) )python -m
QUARTO ?= quarto

.PHONY: validate prerender render catalog site preview clean

validate:            ## metadata.yaml の検証
	$(PY) oer_kit.validate

prerender:           ## metadata.yaml → site/r/ のページ生成 (+ _quarto.yml)
	$(PY) oer_kit.prerender

# 大規模カタログでは Quarto (dayjs) の日付処理がページ数に比例してスタックを食い、
# 約3,600頁で RangeError になる → V8 のスタックを広げて回避 (恒久対応は Hugo 移行)
render: prerender    ## Quarto で site/_site へレンダリング → _site/ へ同期
	QUARTO_DENO_V8_OPTIONS=--stack-size=8192 $(QUARTO) render site
	rsync -a --delete --exclude catalog.json --exclude jsonld --exclude .nojekyll \
	  site/_site/ _site/

catalog:             ## catalog.json + JSON-LD 全件 (+ sitemap は Quarto 優先)
	$(PY) oer_kit.build_catalog

site: validate render catalog  ## 検証 → レンダリング → カタログ (公開一式)

preview: prerender   ## ローカルプレビュー
	$(QUARTO) preview site

clean:
	rm -rf _site site/_site site/r site/_quarto.yml site/.quarto

deploy: site         ## 手元でビルドして gh-pages ブランチへ配信 (oer-kit 非公開の間の方式)
	touch _site/.nojekyll
	cd _site && rm -rf .git && git init -qb gh-pages && git add -A \
	  && git commit -qm "deploy: $$(date +%Y-%m-%dT%H:%M)" \
	  && git push -qf https://github.com/takedatoshiyuki/oer-world.git gh-pages \
	  && rm -rf .git
