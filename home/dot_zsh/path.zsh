. "$HOME/.config/shell/env.sh"

# 重複排除とパスの順序維持
typeset -U path PATH

# Proton PassのSSHエージェントソックファイル
export SSH_AUTH_SOCK="$HOME/.ssh/proton-pass-agent.sock"
