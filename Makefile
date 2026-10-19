# dotfiles/Makefile
# コマンドの前に@をつけると、実行時にコマンドそのものをechoしない
# $$でエスケープ

.DEFAULT_GOAL := help

# 初期設定・適用処理の並列実行を禁止
.NOTPARALLEL:

# Makefileのあるディレクトリを基準とする
REPO_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

BOOTSTRAP := $(REPO_ROOT)/bootstrap/setup-proton-pass.sh

CHEZMOI := chezmoi --source "$(REPO_ROOT)"

.PHONY: help doctor setup diff apply test status

help:
	@printf '%s\n' \
		'使用可能なターゲット:' \
		'  make setup/diff    : chezmoiの変更差分を表示' \
		'  make setup/apply   : chezmoiの設定を反映' \
		'  make setup/status  : chezmoi管理ファイルの状態確認' \
		'  make setup/doctor  : 実行環境の診断' \
		'  make pp/setup   : Proton Passとchezmoiの初期化'

setup/diff:
	@$(CHEZMOI) diff --no-pager 2> /dev/null | grep '^diff --git' | sed -E 's|^diff --git a/(.*) b/.*|\1|' || true

setup/apply:
	@$(CHEZMOI) apply

setup/status:
	@$(CHEZMOI) status

setup/doctor:
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

pp/setup:
	@bash "$(BOOTSTRAP)"

