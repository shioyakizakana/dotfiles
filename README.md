# dotfiles

chezmoiにて運用管理するdotfiles

## Installation

### Ubuntu

#### 基礎のツールを手動インストール

```shell
# 先にaptをアップデート
apt update -y && apt upgrade -y
sudo apt install -y git build-essential curl wget vim
```

#### chezmoiとProton Pass CLIをインストール

```shell
mkdir -p ~/.local/bin
# Proton Pass CLI
curl -fsSL https://proton.me/download/pass-cli/install.sh | bash
# chezmoi
sh -c "$(curl -fsLS get.chezmoi.io)" -- -b ~/.local/bin
```

#### Proton Pass CLIのセットアップ

##### Proton Pass CLIへのログイン

```shell
# パスワードを入力
pass-cli login --interactive <ユーザー名>@proton.me
Enter password: password
```

keyringが使えない環境の場合はログイン前に以下の手順を実施

1. `PROTON_PASS_KEY_PROVIDER`を`env`に変更
1. 暗号化鍵を生成して`PROTON_PASS_ENCRYPTION_KEY`にセット

```shell
export PROTON_PASS_KEY_PROVIDER=env
export PROTON_PASS_ENCRYPTION_KEY=$(dd if=/dev/urandom bs=1 count=2048 2>/dev/null | sha256sum | awk '{print $1}')
```

##### PAT(Personal Access Token)を`viewer`権限で生成

> [!note]
> 既に生成/権限設定済みの場合はスキップ

```shell
# PATを新規作成(一度しか出力されないので必ず控える)
pass-cli pat create \
    --name "<トークン名>" \
    --expiration (1h,1d,1w,1m,3m,6m,1yのいずれか)
# dotfiles Vaultへのアクセス権限をviewerで付与
pass-cli pat access grant \
    --personal-access-token-name "<トークン名>" \
    --vault-name "dotfiles" \
    --role viewer
```


#### chezmoiでdotfilesをローカルに反映

```shell
~/local/bin/chezmoi init https://github.com/shioyakizakana/dotfiles.git
~/local/bin/chezmoi apply
```

