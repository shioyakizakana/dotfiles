#!/usr/bin/env bash
set -euo pipefail

log() {
  printf "\n=== %s\n" "$*"
}

if ! command -v mise >/dev/null 2>&1; then
  read -rp "miseがインストールされていません。インストールしますか? [y/N]: " confirm

  if [[ "$confirm" =~ ^[Yy]$ ]]; then
    log "miseをインストールしています..."
    curl -fsSL https://mise.run/zsh | sh
  else
    log "miseのインストールをスキップしました。"
    exit 0
  fi
fi

log "デフォルトに定義したmiseツールのグローバルインストールを開始します。"

read -rp "インストールを開始しますか? [y/N]: " confirm
if [[ "$confirm" =~ ^[Yy]$ ]]; then

  log " Web Runtime ==="
  mise use -g node@24
  mise use -g npm
  mise use -g pnpm
  mise use -g bun
  mise use -g deno

  log " Typescript ==="
  mise use -g npm:typescript

  log " Prettier ==="
  mise use -g npm:@fsouza/prettierd
  mise use -g npm:prettier

  log " HTML/CSS/JSON/ESLint ==="
  mise use -g npm:vscode-langservers-extracted
  mise use -g npm:@olrtg/emmet-language-server
  mise use -g npm:@tailwindcss/language-server
  # mise use -g npm:unocss-language-server

  log " Bash ==="
  mise use -g npm:bash-language-server
  mise use -g shellcheck
  mise use -g shfmt

  log "Go ==="
  mise use -g go
  mise use -g gofumpt
  mise use -g golangci-lint
  mise use -g go:golang.org/x/tools/gopls@latest
  mise use -g go:github.com/nametake/golangci-lint-langserver@latest

  log " Python ==="
  mise use -g python@3.12
  mise use -g python@3.13
  mise use -g ruff
  mise use -g uv
  mise use -g pipx
  mise use -g npm:pyright
  mise use -g npm:basedpyright
  mise use -g pipx:ty

  log " Rust ==="
  mise use -g rust
  rustup component add rust-analyzer

  log " Ruby ==="
  mise use -g ruby

  log " YAML LSP ==="
  mise use -g npm:yaml-language-server

  log " TOML LSP ==="
  mise use -g taplo

  log " Markdown LSP ==="
  mise use -g marksman

  log " Git utils ==="
  mise use -g gh
  mise use -g delta
  mise use -g ghq
  mise use -g lazygit

  log " LazyDocker ==="
  mise use -g lazydocker

  log " SQL ==="
  mise use -g go:github.com/sqls-server/sqls
  mise use -g cargo:sleek # フォーマッター

  log " NeoVim / Lua ==="
  mise use -g neovim
  mise use -g lua@5.1 # NeoVim0.12に合わせる
  mise use -g lua-language-server 
  mise use -g stylua

  log " Nim ==="
  mise use -g nim

  log "インストールが完了しました。"
else
  log "インストールをスキップしました。"
  exit 0
fi

