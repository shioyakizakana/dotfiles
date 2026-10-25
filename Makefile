# dotfiles/Makefile
# コマンドの前に@をつけると、実行時にコマンドそのものをechoしない
# $$でエスケープ

.DEFAULT_GOAL := help

# 初期設定・適用処理の並列実行を禁止
.NOTPARALLEL:

# Makefileのあるディレクトリを基準とする
REPO_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

# セットアップ用スクリプト
BOOTSTRAP := $(REPO_ROOT)/bootstrap/setup-proton-pass.sh

# 実行ファイルと引数
CHEZMOI_BIN := $(HOME)/.local/bin/chezmoi
CHEZMOI := "$(CHEZMOI_BIN)" --source "$(REPO_ROOT)"

# ラッパースクリプトの展開先
PROTON_PASS_WRAPPER := $(HOME)/.local/bin/proton-pass

.PHONY: help diff apply status require require-bootstrap wrapper bootstrap

# ========================================
# help
# ========================================
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
diff: require
	@$(CHEZMOI) diff --no-pager

apply: require
	@echo "以下のファイルが適用対象となります:"
	@$(CHEZMOI) diff --no-pager
	@printf "変更を適用しますか？ [y/N] "; \
	read -r confirm || exit 1; \
	case "$$confirm" in \
		[yY]) $(CHEZMOI) apply ;; \
		*) echo "キャンセルしました。" ;; \
	esac

status: require
	@$(CHEZMOI) status

# ========================================
# 実行環境確認
# ========================================
require:
	@missing=0; \
	for cmd in age age-keygen curl git pass-cli openssl wget; do \
		if command -v "$$cmd" >/dev/null 2>&1; then \
			printf '[OK] %s\n' "$$cmd"; \
		else \
			printf '[NG] %s\n' "$$cmd"; \
			missing=1; \
		fi; \
	done; \
	if test -x "$(CHEZMOI_BIN)"; then \
		printf '[OK] chezmoi\n'; \
	else \
		printf '[NG] chezmoi\n'; \
		missing=1; \
	fi; \
	exit "$$missing"

# ========================================
# Proton Pass
# ========================================
wrapper: require
	@echo "==> Proton Passラッパーを展開"
	@$(CHEZMOI) apply "$(PROTON_PASS_WRAPPER)"
	@test -x "$(PROTON_PASS_WRAPPER)" || { \
		echo "ERROR: ラッパーが実行可能ではありません" >&2; \
		exit 1; \
	}

# ========================================
# 初期セットアップ
# ========================================
bootstrap: wrapper
	@echo "==> Proton Pass初期セットアップ"
	@bash "$(BOOTSTRAP)"
