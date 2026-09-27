# dotfiles

chezmoiにて運用管理するdotfiles

## Installation

### Ubuntu

基礎のツールを手動インストール

```shell
# 先にaptをアップデート
apt update -y && apt upgrade -y
sudo apt install -y git build-essential curl wget vim
```

chezmoiをインストール

```shell
mkdir -p ~/.local/bin
sh -c "$(curl -fsLS get.chezmoi.io)" -- -b ~/.local/bin
```
chezmoiでdotfilesをローカルに反映

```shell
~/local/bin/chezmoi init https://github.com/shioyakizakana/dotfiles.git
~/local/bin/chezmoi apply
```

