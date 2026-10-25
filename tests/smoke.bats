#!/usr/bin/env bats

REPO_ROOT="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"
ZDIR="$REPO_ROOT/home/dot_zsh"
# -----------------------------------------------------------
# chezmoiroot
# -----------------------------------------------------------

@test ".chezmoiroot exists" {
  [ -f "$REPO_ROOT/.chezmoiroot" ]
}

@test ".chezmoiroot points to 'home'" {
  run cat "$REPO_ROOT/.chezmoiroot"
  [ "$status" -eq 0 ]
  [ "$output" = "home" ]
}

@test ".chezmoi.toml.tmpl is at repo root, not inside home/" {
  [ -f "$REPO_ROOT/.chezmoi.toml.tmpl" ]
  [ ! -f "$REPO_ROOT/home/.chezmoi.toml.tmpl" ]
}

# -----------------------------------------------------------
# key dofiles
# -----------------------------------------------------------
@test "home/dot_bashrc exists" {
  [ -f "$REPO_ROOT/home/dot_bashrc" ]
}

@test "home/dot_zshrc.tmpl exists" {
  [ -f "$REPO_ROOT/home/dot_zshrc.tmpl" ]
}

@test "home/dot_gitconfig.tmpl exists" {
  [ -f "$REPO_ROOT/home/dot_gitconfig.tmpl" ]
}

@test "home/dot_Brewfile.tmpl exists" {
  [ -f "$REPO_ROOT/home/dot_Brewfile.tmpl" ]
}

@test "home/dot_tmux.conf exists" {
  [ -f "$REPO_ROOT/home/dot_tmux.conf" ]
}

# -----------------------------------------------------------
# zsh modules
# -----------------------------------------------------------

@test "home/dot_zsh exists" {
  [ -d "$ZDIR" ]
}

@test "home/dot_zsh/path.zsh exists" {
  [ -f "$ZDIR/path.zsh" ]
}

@test "home/dot_zsh/operation.zsh exists" {
  [ -f "$ZDIR/operation.zsh" ]
}

@test "home/dot_zsh/complesion.zsh exists" {
  [ -f "$ZDIR/completion.zsh" ]
}

@test "home/dot_zsh/plugin.zsh exists" {
  [ -f "$ZDIR/plugin.zsh" ]
}

@test "home/dot_zsh/alias.zsh exists" {
  [ -f "$ZDIR/alias.zsh" ]
}

# -----------------------------------------------------------
# setup scripts
# -----------------------------------------------------------

CHEZMOI_SCRIPTS_DIR="$REPO_ROOT/home/.chezmoiscripts"

@test "home/.chezmoiscriots dir is exists" {
  [ -d "$CHEZMOI_SCRIPTS_DIR" ]
}

@test "home/.chezmoiscripts/run_after_install-apt.sh exists" {
  [ -f "$CHEZMOI_SCRIPTS_DIR/run_after_install-apt.sh" ]
}

@test "home/.chezmoiscripts/run_after_install-brew.sh exists" {
  [ -f "$CHEZMOI_SCRIPTS_DIR/run_after_install-brew.sh" ]
}

@test "home/.chezmoiscripts/run_after_install-mise.sh exists" {
  [ -f "$CHEZMOI_SCRIPTS_DIR/run_after_install-mise.sh" ]
}
