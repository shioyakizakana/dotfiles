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
TEST_PYTHON ?= python3

# ラッパースクリプトの展開先
PROTON_PASS_WRAPPER := $(HOME)/.local/bin/proton-pass
PROTON_PASS_CACHE := $(HOME)/.local/bin/proton-pass-key-cache.py

.PHONY: help diff apply status require require-bootstrap wrapper bootstrap
.PHONY: check test test-unit test-smoke lint

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
		'  wrapper  : Proton Passラッパーと鍵キャッシュを限定展開' \
		'  bootstrap   : chezmoi設定に従って認証の初期セットアップを実行' \
		'  check       : 静的検査・単体テスト・配置テストを実行' \
		'  test        : 単体テストと配置テストを実行' \
		'  test-unit   : 必須依存とskipを確認してunittestを実行' \
		'  test-smoke  : Batsの配置テストを実行' \
		'  lint        : 対象を限定した構文・静的検査を実行'

# 設定適用・認証用のrequireには依存させない。
check: lint test

test: test-unit test-smoke

test-unit:
	@"$(TEST_PYTHON)" -B "$(REPO_ROOT)/tests/check.py" unit

test-smoke:
	@"$(TEST_PYTHON)" -B "$(REPO_ROOT)/tests/check.py" smoke

lint:
	@"$(TEST_PYTHON)" -B "$(REPO_ROOT)/tests/check.py" lint

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
	@$(CHEZMOI) apply --include=files --refresh-externals=never "$(PROTON_PASS_WRAPPER)" "$(PROTON_PASS_CACHE)"
	@test -x "$(PROTON_PASS_WRAPPER)" || { \
		echo "ERROR: ラッパーが実行可能ではありません" >&2; \
		exit 1; \
	}
	@test -x "$(PROTON_PASS_CACHE)" || { \
		echo "ERROR: 鍵キャッシュが実行可能ではありません" >&2; \
		exit 1; \
	}

# ========================================
# 初期セットアップ
# ========================================
bootstrap: require
	@echo "==> Proton Pass初期セットアップ"
	@CHEZMOI_SOURCE_DIR="$(REPO_ROOT)" CHEZMOI_BIN="$(CHEZMOI_BIN)" bash "$(BOOTSTRAP)"
