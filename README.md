# dotfiles

chezmoiとGitを使用して、Linux環境の設定ファイルを管理するためのdotfilesリポジトリ。
Proton Pass CLIと連携し、認証情報を必要とする設定ファイルも管理する。

## 1. 対応環境

現在、以下の実行環境を想定。

| 実行環境| `LINUX_ENV` | Key Provider |
| --- | --- | --- |
| Termux | `termux` | `env` |
| Proot版Ubuntu | `proot-ubuntu`| `env` |
| QEMU版Ubuntu | `qemu-ubuntu` | `keyring` / `env` |
| WSL版Ubuntu | `wsl-ubuntu` | `keyring` / `env` |
| ネイティブUbuntu | `native-ubuntu` | `keyring` / `env` |

`keyring`を利用する場合は、D-BusセッションおよびSecret Serviceが使用できる必要がある。

> [!Note]
> 実行環境の自動検出も実装しているが、Prootなどを正確に識別できない場合があるため、初期構築時には`LINUX_ENV`を明示することを推奨。

## 2. ディレクトリ構成

主要なファイル構成は以下の通り。

```tree
dotfiles/
├── .chezmoiroot
├── README.md
├── bootstrap/
│   └── setup-proton-pass.sh
└── home/
    ├── .chezmoi.toml.tmpl
    └── dot_local/
        └── bin/
            ├── executable-init-proton-pass.tmpl
            └── executable-proton-pass.tmpl

```

`.chezmoiroot`には`home`を指定。

## 3. セットアップ前の準備

### 3.1 必要なコマンド

初期構築には以下のコマンドが必要となる。

- `git`
- `chezmoi`
- `age` / `age-keygen`
- `pass-cli`（Proton Pass CLI）
- `openssl`
- `flock`
- その他、Bashおよび基本的なシステムコマンド

### 3.1.1 基礎ツールのインストール

```shell
# 先にaptをアップデート
apt update -y && apt upgrade -y
apt install -y age buiild-essential curl flock openssl wget vim
```

### 3.1.2 chezmoiとProton Pass CLIをインストール

`chezmoi`とProton Pass CLIは公式のインストールスクリプトを使ってインストール。

```shell
mkdir -p ~/.local/bin
# chezmoi
sh -c "$(curl -fsLS get.chezmoi.io)" -- -b ~/.local/bin
# Proton Pass CLI
curl -fsSL https://proton.me/download/pass-cli/install.sh | bash
```

### 3.2 Proton Pass PATの準備

Proton Pass CLIで使用するPersonal Access Token（PAT）を事前に発行しておく。

PATには必要なVaultまたはItemへのアクセス権限のみを付与し、有効期限を設定する。

> [!Note]
> PATはセットアップ時に対話入力する。READMEやシェルスクリプト、Gitリポジトリには記載しない。

## 4. chezmoiの初期化

### 4.1 dotfilesの取得

以下のコマンドでdotfilesをクローンする。

```shell
chezmoi init shioyakizakana
```

この段階では`--apply`を指定しない。

### 4.2 初期設定の入力

`.chezmoi.toml.tmpl`に定義されたプロンプトに従い、実行環境などを指定する。

| 設定| 内容 |
| --- | --- |
| `machineType` | `personal` / `work` |
| `linuxEnv` | Termux、Proot、WSLなどの実行環境 |
| `protonPassProvider` | `keyring` / `env` |

### 4.3 設定の確認

初期化後、chezmoiのテンプレートデータを確認。

```shell
chezmoi data
```

特に`protonPassProvider`が、使用するKey Providerと一致していることを確認する。

```shell
chezmoi execute-template '{{ .protonPassProvider }}'
```

設定内容を修正する場合は、chezmoiのローカル設定ファイルを編集する。(デフォルトは`~/.config/chezmoi/chezmoi.toml`)

## 5. Proton Pass CLIの初期構築

### 5.1 Bootstrapの実行

リポジトリ内のセットアップスクリプトを実行する。

```shell
# Proot版Ubuntuでの実行例
LINUX_ENV=proot-ubuntu \
  bash "$(chezmoi source-path)/bootstrap/setup-proton-pass.sh" env

# keyringを使用するネイティブUbuntuでの実行例
LINUX_ENV=native-ubuntu \
  bash "$(chezmoi source-path)/bootstrap/setup-proton-pass.sh" keyring```

`LINUX_ENV`およびKey Providerは、chezmoi側の設定と一致させる。

セットアップスクリプトは以下の処理を実施する。

1. 実行環境とKey Providerの検証
2. age identityの生成または既存identityの検証
3. identityのパスフレーズによる暗号化
4. 公開鍵（recipient）の生成・整合性確認
5. Proton Pass PATの暗号化保存
6. `env`プロバイダーの場合、CLI用暗号化鍵の生成
7. PATによるProton Pass CLIへのログイン
8. chezmoi設定との整合性確認

> [!Note]
> Bootstrapは`chezmoi apply`を自動実行しない。


### 5.2 age identityのパスフレーズ設定

新規構築時には、`age identity`を生成し、パスフレーズによって暗号化する。
パスフレーズは安全な場所に保管しておく。

暗号化identityとパスフレーズの両方を失うと、保存されたPATなどを復号できなくなる可能性がある。
また、パスフレーズを忘れた場合の復旧手段として、identityのバックアップを別の安全な場所に保管することを推奨。

### 5.3 認証情報の保存先

標準設定では、以下のファイルを作成する。

```tree
~/.local/share/
├── age/
│   ├── id_proton_pat.age
│   └── proton-pass-recipient.txt
└── proton-pass/
    ├── token.age
    ├── encryption-key.age
    └── .setup-proton-pass.lock
```

| ファイル| 用途 |
| --- | --- |
| `id_proton_pat.age`| パスフレーズ付きage identity |
| `proton-pass-recipient.txt`| age公開鍵 |
| `token.age`| 暗号化されたProton Pass PAT |
| `encryption-key.age`| 暗号化されたCLI用暗号化鍵 |
| `.setup-proton-pass.lock`| Bootstrapの同時実行防止 |

`encryption-key.age`は`env`プロバイダーの場合に生成する。
これらの秘密情報はdotfilesリポジトリでは管理しない。

### 5.4 保存先の変更

必要に応じて、環境変数からidentityの保存先を変更できる。

```shell
export AGE_IDENTITY_DIR="$HOME/.local/state/secure-keys"
# ファイルを直接指定する場合
export AGE_IDENTITY_FILE="$HOME/.local/state/secure-keys/id_proton_pat.age"
```

変更した場合は、Bootstrapと通常操作の両方で同じ保存先を参照する必要がある。

## 6. chezmoiによる設定の適用

Proton Pass CLIの初期構築が完了したら、chezmoiの管理対象ファイルを適用する。

### 6.1 差分確認

`Makefile`より実行する場合は、以下のコマンドで適用対象のファイルを列挙した上で適用するかどうかを決める事ができる。

```shell
make -C ~/.local/share/chezmoi apply
```

`apply`ではまず適用されるファイルの一覧を表示し、実行前の確認にて`y`を選択した場合に`chezmoi apply`を実行する。

### 6.2 ツール類のインストール

`chezmoi apply`により管理ファイルの展開と`home/.chezmoiscripts`以下のセットアップスクリプトが実行される。

| スクリプト| 処理内容 |
| --- | --- |
| `run_after_install-apt.sh` | `apt`のアップデートおよびツール(OSの基本的な操作やシステム直接変更を加えるツール類)のインストール |
| `run_after_install-brew.sh` | `Homebrew`およびツール(主にユーティリティー系)のインストール |
| `run_after_install-mise.sh` | `mise`およびツール(主に開発、言語ランタイム等)のインストール |

また、`home/.chezmoiexternal.toml.tmpl`に定義した以下のツール、プラグインが指定のパスにインストールされる。

| ツール名 | ルートパス | 概要 |
| --------------- | --------------- | --------------- |
| `powerlevel10k` | `~/.zsh/plugin/plugins/` | `zsh`の外観をカスタマイズする。 |
| `fast-syntax-highlighting` | `~/.zsh/plugin/plugins/` | `zsh`上でシンタックスハイライトを適用するプラグイン |
| `zsh-autosuggesions` | `~/.zsh/plugin/plugins/` | `zsh`上で履歴から候補を表示するプラグイン |
| `zsh-completions` | `~/.zsh/plugin/plugins/` | `zsh`上で入力補完を行うプラグイン |
| `fzf` | `~/.zsh/plugin/plugins/` | コマンドの履歴やファイルをあいまい検索するツール |
| `zeno.zsh` | `~/.zsh/plugin/plugins/` | キーワードに対して定義したスニペットを展開するプラグイン(`fzf`と`deno`に依存) |
| `tpm` | `~/.config/tmux/plugins/` | `tmux`のプラグインマネージャー |

### 6.3 Proton Pass CLIラッパーの確認

想定する配置先は以下の通り。

```tree
~/.local/bin/
├── init-proton-pass
└── proton-pass
```

`~/.local/bin`にPATHが通っていない場合は、`.bashrc`などのシェル設定を確認する。(`zsh`におけるPATHは`~/.zsh/path.zsh`にて管理)

### 6.4 認証状態の確認

以下のコマンドでProton Pass CLIの認証状態を確認。

```shell
proton-pass info
```

再ログインが必要な場合は、以下を実行。

```shell
init-proton-pass
```

`init-proton-pass`はPATを復号してログインを実行するためのエントリーポイント。
通常のProton Pass CLI操作には、`proton-pass`ラッパーを使用する。

## 7. Proton Pass CLIの通常運用

Proton Pass CLIに関わる各スクリプトの役割は次の通り。

| スクリプト| 役割 | 実行タイミング |
| --- | --- | --- |
| `setup-proton-pass.sh` | 認証環境の初期構築 | 新規環境構築時 |
| `init-proton-pass` | PATによるログイン| 再ログインが必要な場合 |
| `proton-pass` | 暗号化鍵を一時注入してCLIを実行| 通常操作時 |


> [!パスフレーズ入力について]
> 現在の構成では復号鍵のキャッシュを行わない。
> `env`プロバイダーの場合、通常操作でも暗号化鍵の復号時にパスフレーズ入力が必要となる。
> また、ログイン時はPATとCLI用暗号化鍵をそれぞれ復号するため、複数回入力を求められる場合がある。
> これは現在の設計上、正常な動作。

## 8. 既存環境からの移行

以前の構成で平文のage identityを使用していた場合、新規identityを生成する前に既存identityを暗号化する必要がある。

```
# 旧identityの例：
~/.local/share/age/proton-pass-identity.txt

# 新しい保存先
~/.local/share/age/id_proton_pat.age
```

既存の`token.age`および`encryption-key.age`は、対応する秘密鍵がなければ復号できない。
そのため、既存identityが存在する環境では、既存の鍵を維持したまま暗号化形式へ移行する必要がある。
移行作業前には、既存identityと暗号化認証情報を安全な場所にバックアップしておく。

新形式への移行完了後、旧平文identityを安全に廃止する。

## 9. セキュリティ上の注意点

- PAT、復号鍵、平文identityをGitにコミットしない。
- identityとパスフレーズは別々に安全に保管する。
- PATには必要最小限のアクセス権限と有効期限を設定する。
- 暗号化ファイルだけでなくidentityのバックアップも管理する。
- `env`プロバイダーでは、CLI実行時に秘密情報がプロセスの環境変数へ一時的に渡されることを理解しておく。
- パスフレーズ付きidentityによる暗号化は、実行中のプロセス侵害を防止する仕組みではない。

認証情報を変更した場合は、対応する暗号化ファイルの更新やPATの再発行を検討する。

## 10. トラブルシューティング

主なエラーログ別の対応方法を以下に記載する。

### 10.1 `chezmoi: map has no entry for key`

`chezmoi`の設定に必要なテンプレート変数が存在しない可能性がある。
`chezmoi data`で設定値を確認すること。

### 10.2 `IDENTITYとrecipientが一致しません`

暗号化identityと公開鍵が異なる鍵ペアに由来している可能性がある。

既存の認証情報を保持したまま、バックアップと設定ファイルを確認する。安易に新しい秘密鍵を生成しない。

### 10.3 `PATの復号に失敗しました`

パスフレーズ、identityの保存先、暗号化ファイルの組み合わせを確認する。
### 10.4 `Keyringの利用条件を満たしていません`

D-BusセッションおよびSecret Serviceが利用可能か確認する。
Keyringを使用できない環境では、`env`プロバイダーによる構築を検討する。

### 10.5 `Proton Passラッパーが見つかりません`

`chezmoi`による設定適用が完了しているか確認する。
`~/.local/bin/proton-pass`が存在し、実行権限が付与されていることも確認する。
