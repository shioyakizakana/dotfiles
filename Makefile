# dotfiles/Makefile
# コマンドの前に@をつけると、実行時にコマンドそのものをechoしない
# $$でエスケープ

.DEFAULT_GOAL := help

# 初期設定・適用処理の並列実行を禁止
.NOTPARALLEL:

# Makefileのあるディレクトリを基準とする
REPO_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

BOOTSTRAP := $(REPO_ROOT)/bootstrap/setup-proton-pass.sh

CHEZMOI := ~/.local/bin/chezmoi --source "$(REPO_ROOT)"

# ラッパースクリプトの展開先
PROTON_PASS_WRAPPER := $(HOME)/.local/bin/proton-pass

.PHONY: help diff apply status require wrapper bootstrap

help:
	@printf '%s\n' \
		'使用可能なターゲット:' \
		'  diff    : chezmoiの変更差分を表示' \
		'  apply   : chezmoiの設定を反映' \
		'  status  : chezmoi管理ファイルの状態確認' \
		'  require  : セットアップ実行環境の診断' \
		'  wrapper  : Proton Passラッパーを展開' \
		'  bootstrap   : 初期セットアップを実行'

# ========================================
# chezmoi
# ========================================
diff:
	@$(CHEZMOI) diff --no-pager 2> /dev/null | grep '^diff --git' | sed -E 's|^diff --git a/(.*) b/.*|\1|' || true

apply:
	@echo "以下のファイルが適用対象となります。:"
	@$(MAKE) -s setup/diff | sed 's|^|  |'
	@printf "変更を適用しますか？ [y/N] "; read -r confirm; \
	if [[ ! "$$confirm" =~ ^[Yy]$$]]; then \
		echo "キャンセルしました。"; \
	else \
		@$(CHEZMOI) apply; \
	fi

status:
	@$(CHEZMOI) status

# ========================================
# bootstrap
# ========================================
require:
	@missing=0; \
	for cmd in bash age age-keygen pass-cli chezmoi openssl; do \
		if command -v "$$cmd" >/dev/null 2>&1; then \
			printf '[OK] %s\n' "$$cmd"; \
		else \
			printf '[NG] %s\n' "$$cmd"; \
			missing=1; \
		fi; \
	done; \
	exit "$$missing"

# Proton Passラッパースクリプトを先行展開
wrapper:
	@echo "==> Proton Passラッパーを展開"
	$(CHEZMOI) apply "$(PROTON_PASS_WRAPPER)"
	@test -x "$(PROTON_PASS_WRAPPER)" || { \
		echo "ERROR: ラッパーが実行可能ではありません" >&2; \
		exit 1; \
	}

bootstrap:
	@$(MAKE) wrapper
	@bash "$(BOOTSTRAP)"

