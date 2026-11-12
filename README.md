# dotfiles

chezmoiを中心に、Linux環境の設定ファイル、開発ツール、初期構築を管理するdotfilesリポジトリ。
開発ツールは主にmise、システム依存はAPT、補助ツールはHomebrewで管理する。Proton Pass CLIとageを使い、必要な設定へ秘密情報を渡す。

新規構築では1〜6節を順に確認する。通常の更新は7節、既存identityの移行は8節、問題が起きた場合は10節を参照する。
最初の`chezmoi init`では`--apply`を付けず、認証bootstrapとラッパーの限定展開を済ませてから全体を適用する。

## 1. 対応環境

以下はコード上の対象環境。実機での動作保証とは区別し、確認範囲は[環境別テストの説明](docs/testing/environment-matrix.md)を参照する。

| 実行環境| `LINUX_ENV` | Key Provider |
| --- | --- | --- |
| Termux | `termux` | `env` |
| Proot版Ubuntu | `proot-ubuntu`| `env` |
| QEMU版Ubuntu | `qemu-ubuntu` | `keyring` / `env` |
| WSL版Ubuntu | `wsl-ubuntu` | `keyring` / `env` |
| ネイティブUbuntu | `native-ubuntu` | `keyring` / `env` |

`keyring`を利用する場合は、D-Busセッション、`busctl`、Secret Serviceが必要になる。Termuxの基礎ツールはbootstrap-tools.shで導入できるが、pass-cliや追加ツールには手動準備が残る。Ubuntu向けの一括導入やmise設定はTermuxには適用しない。

> [!Note]
> 認証bootstrapはchezmoiに保存した環境フラグを使用する。`LINUX_ENV`を明示する場合も、保存した環境との一致を要求する。

## 2. ディレクトリ構成

主要なファイルを示す。作業規約は[AGENTS.md](AGENTS.md)、規約と手順の配置は[移動対応表](docs/agents/rule-mapping.md)を参照する。

```text
.
├── .agents/skills/
│   ├── chezmoi-template-validation/
│   ├── dotfiles-script-maintenance/
│   ├── dotfiles-test-runner/
│   └── secret-management-review/
├── .github/workflows/check.yml
├── .chezmoiroot
├── .chezmoi.toml.tmpl
├── AGENTS.md
├── README.md
├── Makefile
├── lefthook.yml
├── bootstrap/
│   ├── AGENTS.md
│   ├── bootstrap-tools.sh
│   └── setup-proton-pass.sh
├── docs/
│   ├── reviews/dotfiles-audit.md
│   ├── setup/proton-pass.md
│   └── testing/
│       ├── checks.md
│       ├── git-hooks.md
│       └── environment-matrix.md
├── home/
│   ├── AGENTS.md                  # 展開ソース用の局所規約（配布しない）
│   ├── .chezmoiignore
│   ├── .chezmoiexternal.toml.tmpl
│   ├── .chezmoiscripts/
│   ├── dot_agents/skills/
│   ├── dot_codex/symlink_AGENTS.md.tmpl
│   ├── dot_config/
│   │   └── shell/
│   │       ├── env.sh
│   │       └── aliases.sh
│   ├── dot_local/
│   │   ├── bin/
│   │   │   ├── executable_init-proton-pass.tmpl
│   │   │   ├── executable_proton-pass.tmpl
│   │   │   ├── private_executable_proton-pass-key-cache.py.tmpl
│   │   │   ├── executable_update_apps
│   │   │   ├── executable_update-agent-skills
│   │   │   └── executable_textlint-ja
│   │   └── share/textlint-ja/
│   ├── dot_zsh/
│   ├── scripts/desk/
│   ├── dot_Brewfile
│   └── dot_gitconfig.tmpl
└── tests/
```

`.chezmoiroot`は`home`をsource stateのルートに指定する。初期設定の`.chezmoi.toml.tmpl`はリポジトリ直下に置く。
管理対象はソース側を編集し、`dot_`、`executable_`、`private_`、`symlink_`、`.tmpl`などの属性に従ってホームへ展開する。
たとえば`home/dot_local/bin/executable_proton-pass.tmpl`は`~/.local/bin/proton-pass`になる。初期構築や文書用の`bootstrap/`、`docs/`、`tests/`はホームへ展開しない。

プロジェクト専用スキルはルートの`.agents/skills/`で直接管理する。このディレクトリもホームへの展開対象には含まれず、共通スキルは従来どおり`home/dot_agents/skills/`で管理する。
Codex CLIではこのリポジトリ内から`/skills`や`$スキル名`で選択できる。新しいスキルが表示されない場合はCodexを再起動して確認する。用途は[AGENTS.mdのスキル一覧](AGENTS.md#81-プロジェクト固有スキル)を参照する。

### 2.1 BashとZshの共通設定

`home/dot_config/shell/`を`~/.config/shell/`へ展開し、BashとZshの両方から読み込む。

| ファイル | 共通化する内容 |
| --- | --- |
| `env.sh` | TMPDIR、Go・pnpm・fzfのパス、EDITOR、LANG・LANGUAGE、既存ディレクトリのPATH追加 |
| `aliases.sh` | コマンド置換、eza、ホーム・chezmoiへの移動、LazyGit起動、upd |

BashもZshと同じ共通設定を使う。PATHは存在するディレクトリだけを末尾へ追加し、再読み込みで同じ項目を増やさない。
`upd`は管理対象の`~/.local/bin/update_apps`を呼ぶ。例えば`upd apt`のように更新対象を指定する。コマンド置換のエイリアスは、対応するツールがPATHにある場合だけ定義する。導入担当と手動準備は[設定の依存一覧](docs/setup/dependencies.md)を参照する。
reload、プロンプト、補完、キー操作、mise・zoxide・atuinなどのシェル別初期化は各シェルの設定に残す。SSH_AUTH_SOCKも既存どおりZsh側だけで設定する。

旧構成の`~/scripts/shell/funciton.sh`は、読み取り可能な場合だけ任意拡張として読み込む。既存端末の手動配置を引き続き利用できるが、その内容はリポジトリで管理・検証していない。
共通モジュール自体は必須の管理対象なので、適用時は新しい2ファイルと読み込み側のBash・Zsh設定をまとめて反映する。`.bashrc`や`.zshrc`だけを先に反映すると共通ファイルを読み込めない。

## 3. セットアップ前の準備

### 3.1 必要なコマンド

初期構築には以下のコマンドが必要となる。

- `curl`
- `wget`
- `git`
- `chezmoi`
- `age` / `age-keygen`
- `pass-cli`（Proton Pass CLI）
- `openssl`
- `make`、Bash、`flock`などの基本コマンド
- Python 3.11以上（env方式の鍵キャッシュに使用）

鍵キャッシュのシバンは`#!/usr/bin/env python3`なので、PATH上のPythonを使う。OS標準のPythonに固定されているわけではない。
`make require`の確認対象は主要コマンドと`~/.local/bin/chezmoi`。Pythonやflockなどは、このターゲットでは確認しない。基礎導入後も必要なコマンドとPythonのバージョンを確認する。

#### 3.1.1 基礎ツールのインストール

UbuntuとTermux（APT/dpkg方式）の基礎導入には`bootstrap/bootstrap-tools.sh`を使う。リポジトリを取得済みの場合は、リポジトリのルートで次を実行する。

```shell
bash bootstrap/bootstrap-tools.sh --check
# 導入内容を確認してから実行する。
bash bootstrap/bootstrap-tools.sh --install
```

`--check`はディレクトリを作成せずにコマンドの存在を表示する。Python・Zsh・fzf・LuaRocksなども確認するが、バージョンや動作の互換性は別途確認する。

| 実行環境 | `--install`の導入範囲 |
| --- | --- |
| Ubuntu系 | APTの基礎パッケージと、未導入のchezmoi・pass-cli・mise・Homebrew。Python・wget・opensslなどは別途準備 |
| proot Ubuntu | Ubuntuと同じ。ただしHomebrewの新規導入は省略 |
| Termux本体 | pkgによる基礎パッケージ・chezmoi・Python・make・OpenSSLコマンド・wget・util-linux・miseなど。Homebrewは対象外、pass-cliは手動準備 |

Termuxでは通常ユーザーで実行する。導入済みパッケージは省き、不足がある場合だけ一覧更新と導入を行う。APT・pkgとも、依存解決によって既存パッケージが更新される場合がある。一括upgradeは実行しない。詳細と実機での確認手順は[依存一覧](docs/setup/dependencies.md#termuxでの導入と実機確認)を参照する。
prootで自動判定が難しい場合は`BOOTSTRAP_PROOT=1`を付ける。prootのHomebrew新規導入は省く。

リポジトリを取得する前でも、GitHubからスクリプトを取得して起動できる。取得にBash・curlと有効なCA証明書が必要になる。次のコマンドは取得に成功した場合だけ確認処理を実行する。

```shell
bootstrap_script="$(curl -fsLS https://raw.githubusercontent.com/shioyakizakana/dotfiles/refs/heads/main/bootstrap/bootstrap-tools.sh)" &&
  bash -c "$bootstrap_script" bootstrap-tools.sh --check
```

取得と確認が成功し、内容と導入対象を確認したら、同じシェルで次を実行する。

```shell
bash -c "$bootstrap_script" bootstrap-tools.sh --install
```

実行する内容を固定したい場合は、取得URLの`refs/heads/main`を対象コミットのSHAへ置き換える。

基礎導入にはProton Passの認証、dotfilesの初期化・適用、mise管理ツール一式の導入は含まれない。Termuxのpass-cliは未導入なら`[MANUAL]`、存在しても`[UNVERIFIED]`と表示する。基礎導入の成功を認証準備の完了とは扱わない。

Termuxではchezmoiが`$PREFIX/bin/chezmoi`へ配置されるため、後続のMake操作に`CHEZMOI_BIN`を指定する。以下の確認はpass-cliが未準備なら失敗する。以降の手順でMakeを使う場合にも、同じ引数を付ける。

```shell
make CHEZMOI_BIN="$PREFIX/bin/chezmoi" require
```

#### 3.1.2 Ubuntuで個別に導入する場合

bootstrap-tools.shで導入済みのツールは、この手順を繰り返す必要はない。以下はUbuntu向けの手動準備例であり、Termux本体では実行しない。Termuxのpass-cliは[実機確認手順](docs/setup/dependencies.md#termuxでの導入と実機確認)を参照する。

sudoを利用できるUbuntuの通常ユーザーは、必要な基礎パッケージを次のように準備する。

```shell
sudo apt-get update
sudo apt-get install -y age build-essential ca-certificates curl git make openssl python3 wget
```

rootで基礎パッケージを準備する場合はsudoを外す。ただし、Proton Passの認証bootstrapはrootを拒否するため、認証は通常ユーザーで実行する。

chezmoiとProton Pass CLIを個別に導入する場合は、公式のインストールスクリプトを使う。

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
chezmoiを`~/.local/bin`へ導入した場合は、シェル設定の適用前にPATHを追加する。

```shell
export PATH="$HOME/.local/bin:$PATH"
chezmoi init shioyakizakana
```

この段階では`--apply`を指定しない。

### 4.2 初期設定の入力

`.chezmoi.toml.tmpl`に定義されたプロンプトに従い、実行環境などを指定する。

| 設定| 内容 |
| --- | --- |
| `machineType` | `personal` / `work` |
| 実行環境の入力 | `native-ubuntu` / `wsl-ubuntu` / `qemu-ubuntu` / `proot-ubuntu` / `termux` |
| `protonPassProvider` | Ubuntu系で`keyring` / `env`を選択。Termux・prootは`env` |

入力した環境名は`nativeUbuntu`、`wslUbuntu`、`qemuUbuntu`、`prootUbuntu`、`termux`のフラグへ変換する。保存される`linuxEnv`は環境名ではなく、Linux系環境かどうかを表す真偽値。再初期化では既存の環境フラグとproviderを引き継ぐ。

### 4.3 設定の確認

初期化後、秘密情報を含まないproviderだけを表示し、使用するKey Providerと一致していることを確認する。

```shell
~/.local/bin/chezmoi execute-template '{{ .protonPassProvider }}'
```

設定内容を修正する場合は、chezmoiのローカル設定ファイルを編集する。(デフォルトは`~/.config/chezmoi/chezmoi.toml`)

## 5. Proton Pass CLIの初期構築

### 5.1 Bootstrapの実行

初期化したリポジトリへ移動し、chezmoiに保存した実行環境とproviderでセットアップする。
以下は標準配置での例。別の場所にcloneした場合は、そのディレクトリを使う。

```shell
cd "$HOME/.local/share/chezmoi"
make bootstrap
# 初回の全体適用より前に、ラッパーと鍵キャッシュだけを展開する。
make wrapper
```

`LINUX_ENV`や`PROTON_PASS_KEY_PROVIDER`を指定した場合は、chezmoi側の設定との一致を要求する。
Termux・prootはenvを使用し、Ubuntu系は初期化時にenvまたはkeyringを選択する。
既存環境の確認、エラー時の対処、手動での適用手順は[Proton Passの構築・確認手順](docs/setup/proton-pass.md)を参照する。

セットアップスクリプトは以下の処理を実施する。

1. chezmoi設定と実行環境・Key Providerの整合性検証
2. age identityの生成または既存identityの検証
3. identityのパスフレーズによる暗号化
4. 公開鍵（recipient）の生成・整合性確認
5. Proton Pass PATの暗号化保存
6. `env`プロバイダーの場合、CLI用暗号化鍵の生成
7. PATによるProton Pass CLIへのログイン

> [!Note]
> Bootstrapは`chezmoi apply`を自動実行しない。


### 5.2 age identityのパスフレーズ設定

新規構築時には、age identityを生成し、パスフレーズによって暗号化する。
パスフレーズは安全な場所に保管しておく。

復号には暗号化identityとパスフレーズの両方が必要になる。どちらかを失うと、保存されたPATなどを復号できなくなる可能性がある。
暗号化identityは別の安全な場所にバックアップし、パスフレーズも保管する。同じ暗号化identityのコピーだけでは、忘れたパスフレーズを復旧できない。

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
認証関連ファイルはdotfilesリポジトリの外に保存する。recipientは公開鍵、`.setup-proton-pass.lock`は排他用ファイルであり、秘密情報そのものとは区別する。

### 5.4 保存先の変更

`XDG_DATA_HOME`を指定した場合、ageとproton-passの保存先はその配下になる。identityの保存先は次の変数で個別指定できる。

```shell
export AGE_IDENTITY_DIR="$HOME/.local/state/secure-keys"
# ファイルを直接指定する場合
export AGE_IDENTITY_FILE="$HOME/.local/state/secure-keys/id_proton_pat.age"
```

変更した場合は、Bootstrapと通常操作の両方で同じ保存先を参照する必要がある。

## 6. chezmoiによる設定の適用

Proton Pass CLIの初期構築が完了したら、chezmoiの管理対象ファイルを適用する。

### 6.1 差分確認

標準配置のリポジトリから、差分を確認して適用する。

```shell
make -C "$HOME/.local/share/chezmoi" diff
make -C "$HOME/.local/share/chezmoi" apply
```

`make apply`は`chezmoi diff`を表示し、`y`を入力した場合に全体を適用する。初期設定ではdiffからscriptsとexternalsを除外しているため、表示された差分が適用時の全処理を表すわけではない。
差分の生成にはProton Passへのアクセスや秘密情報の復号が伴う場合がある。出力は手元で確認し、共有ログへ貼り付けない。

### 6.2 ツール類のインストール

管理ファイルを展開した後、対象環境の`home/.chezmoiscripts/`を実行する。現在の3本はいずれも`run_after_`であり、適用ごとに導入状況を確認する。

| スクリプト| 処理内容 |
| --- | --- |
| `run_after_install-apt.sh` | 不足パッケージがある場合に確認し、一覧更新後に`--no-upgrade`で不足分を導入 |
| `run_after_install-brew.sh` | Homebrewの導入を確認し、`~/.Brewfile`の不足依存を`--no-upgrade`で導入 |
| `run_after_install-mise.sh` | `~/.config/mise/config.toml`に従い不足ツールを`mise install`で導入。Rust・LuaRocks・nimlspの補助依存も確認 |

| 環境 | APT | Homebrew | mise一括導入・管理設定 |
| --- | --- | --- | --- |
| ネイティブ・WSL・QEMUのUbuntu | 対象 | 対象 | 対象 |
| proot Ubuntu | 対象 | 既存Bundleも含めて対象外 | 対象 |
| Termux・未指定・未対応環境 | 対象外 | 対象外 | 対象外 |

不足導入を辞退した場合は次回の適用で再確認する。確認入力の取得失敗や導入失敗はエラーとして終了し、再適用で再試行できる。
通常適用では既存ツールの一括更新を行わない。更新は7.1節の`update_apps`で指定する。

`home/.chezmoiexternal.toml.tmpl`は、次のGitリポジトリの取得・更新も定義する。Zshプラグインとtpmの更新間隔は168時間。

| ツール名 | ルートパス | 概要 |
| --------------- | --------------- | --------------- |
| `powerlevel10k` | `~/.zsh/plugin/plugins/` | `zsh`の外観をカスタマイズする。 |
| `fast-syntax-highlighting` | `~/.zsh/plugin/plugins/` | `zsh`上でシンタックスハイライトを適用するプラグイン |
| `zsh-autosuggestions` | `~/.zsh/plugin/plugins/` | `zsh`上で履歴から候補を表示するプラグイン |
| `zsh-completions` | `~/.zsh/plugin/plugins/` | `zsh`上で入力補完を行うプラグイン |
| `fzf` | `~/.zsh/plugin/plugins/fzf/` | Gitソースの取得。実行ファイルの導入処理はこのexternals定義に含まれない |
| `zeno.zsh` | `~/.zsh/plugin/plugins/` | キーワードに対して定義したスニペットを展開するプラグイン(`fzf`と`deno`に依存) |
| `tpm` | `~/.config/tmux/plugins/` | `tmux`のプラグインマネージャー |
| `natural-japanese` | `~/.local/share/agent-skills/natural-japanese/` | 外部スキル。`~/.agents/skills/natural-japanese`から参照 |

外部スキルを専用コマンドで確認・更新する手順は7.3節を参照する。

### 6.3 Proton Pass CLIラッパーの確認

想定する配置先は以下の通り。

```tree
~/.local/bin/
├── init-proton-pass
├── proton-pass
└── proton-pass-key-cache.py
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

## 7. 日常の更新とProton Passの運用

Proton Pass CLIに関わる各スクリプトの役割は次の通り。

| スクリプト| 役割 | 実行タイミング |
| --- | --- | --- |
| `setup-proton-pass.sh` | identity・PAT・暗号化鍵の初期生成 | 新規環境構築時 |
| `init-proton-pass` | PATによる再ログイン | 再ログインが必要な場合 |
| `proton-pass` | 暗号化鍵を一時注入してProton Pass CLIを実行 | 通常操作時 |
| `proton-pass-key-cache.py` | CLI暗号化鍵のみを一時的にキャッシュして`pass-cli`へ注入 | `env`環境における通常操作時 |

### 7.1 ツールの更新

適用済みの`update_apps`で更新対象を明示する。引数なしでは何も更新せず、使用方法を表示して終了コード2で終了する。

```shell
update_apps apt
update_apps brew mise
update_apps all
```

APTは一覧更新・upgrade・autoremove・autoclean、Homebrewはupdate・upgrade・cleanup、miseはoutdatedの表示とupgradeを実行する。

miseの確認・更新はHOMEを対象にする。outdatedが非0で終了した場合はupgradeへ進まず、更新失敗として集計する。HOME配下の追加設定や環境変数の上書きはmiseの仕様に従う。
PATHに該当するパッケージマネージャーがなければ省略する。これはchezmoiの環境別除外とは独立した処理なので、`all`を指定する前に実行環境と対象を確認する。
miseのツール一覧は`home/dot_config/mise/config.toml`で管理し、多くは`latest`を指定している。全ツールのバージョンを厳密に固定した構成ではない。

現在の固定値、追加固定の候補、更新処理の制約は[バージョン管理方針](docs/setup/tool-version-policy.md)を参照する。Termuxでの確認は[実機チェックリスト](docs/testing/termux-checklist.md)に沿って段階ごとに記録する。

Yaziは26.9.1へ固定し、公開プラグイン・flavorを`home/dot_config/yazi/package.toml`で管理する。自動導入は行わない。既存manifestの統合確認と`ya pkg install`の手順は[Yazi依存一覧](docs/setup/yazi-dependencies.md)を参照する。

### 7.2 キャッシュスクリプトの仕様

env方式では、通常のCLI操作にも暗号化鍵を渡す必要がある。`proton-pass-key-cache.py`はCLI暗号化鍵だけを常駐プロセスのメモリに保持し、有効期限内は復号結果を再利用する。
PATとage identityはキャッシュしない。

キャッシュスクリプトの簡易的な仕様を示す。

| 項目   | 内容    |
|--------------- | --------------- |
| 使用言語   | Python 3。PATH上の`python3`を使用   |
| 保存対象  | Proton Pass CLIの暗号鍵のみ   |
| 標準有効期限   | 15分  |
| 設定可能な最大有効期限   | 60分  |
| 有効期限後   | プロセスを終了してキャッシュを破棄   |
| 手動ロック   | 対応   |
| 再起動後の状態   | ロック状態   |
| `pass-cli`の起動   | キャッシュスクリプト経由で実行   |

有効期限内はCLI暗号化鍵の復号を省略できる。再ログイン時のPAT復号では、別途ageのパスフレーズ入力が必要になる。
キャッシュの通信先は標準で`~/.cache/proton-pass-key-cache/agent.sock`。`PROTON_PASS_CACHE_DIR`でディレクトリを変更できる。平文の鍵をこのディレクトリに保存しない。

キャッシュを手動で破棄する場合は、以下を実行する。

```shell
proton-pass-key-cache.py lock
```

> [!Note]
> 有効期限は鍵を登録した時点から計算し、通常の参照では延長しない。`PROTON_PASS_CACHE_TTL`は秒単位で1〜3600を指定できる。
> 起動済みエージェントの有効期限を変更する場合は、一度ロックして再度解除する。

### 7.3 外部スキルと文章チェック

natural-japaneseの更新には専用コマンドを使う。`check`もGit fetchによる通信を行い、`update`は未コミット変更がある場合に停止する。

```shell
update-agent-skills list
update-agent-skills check natural-japanese
update-agent-skills update natural-japanese
```

`textlint-ja`は`~/.local/share/textlint-ja/node_modules/.bin/textlint`を使用する。設定とnpm依存定義は管理しているが、node_modulesの自動導入処理はない。Node.js・npmを用意し、初回は展開先の`~/.local/share/textlint-ja`で`npm ci`を実行する。

```shell
textlint-ja README.md
```

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

chezmoiの設定に必要なテンプレート変数がない可能性がある。ローカル設定の`[data]`と`.chezmoi.toml.tmpl`を比較する。
全データの出力を共有せず、必要な環境フラグとproviderだけを確認する。具体的なコマンドは[Proton Passの確認手順](docs/setup/proton-pass.md)を参照する。

### 10.2 `identityとrecipientが一致しません`

暗号化identityと公開鍵が異なる鍵ペアに由来している可能性がある。

既存の認証情報を保持したまま、バックアップと設定ファイルを確認する。安易に新しい秘密鍵を生成しない。

### 10.3 `PATの復号に失敗しました`

パスフレーズ、identityの保存先、暗号化ファイルの組み合わせを確認する。

### 10.4 `Keyringの利用条件を満たしていません`

D-BusセッションおよびSecret Serviceが利用可能か確認する。
初回構築ならenv方式も選べる。認証済みの環境では、providerを一時的に上書きして回避せず、認証方式の移行を別途計画する。

### 10.5 ラッパー・鍵キャッシュが見つからない

`make wrapper`が成功し、`~/.local/bin/proton-pass`と`proton-pass-key-cache.py`が実行可能であることを確認する。
ソースの`.tmpl`を直接実行しない。provider不一致や実行環境の不一致で停止した場合も、[手動手順の対処表](docs/setup/proton-pass.md#5-停止した場合の対処)を参照する。

## 11. 検証と改善状況

Python unittestは、隔離したHOME・ダミーコマンド・モックで認証周辺、環境分岐、導入失敗、再試行などを検証する。Batsは主にファイル配置を確認する。

```shell
make check       # 静的検査・単体テスト・配置テスト
make test        # 単体テストと配置テスト
make lint        # 静的検査のみ
```

検証ターゲットは必須ツールを事前確認し、予期しないskipや全件skipを失敗として扱う。Yazi実起動の1件だけは任意検証で、skipした理由を明示する。必要なツール、個別実行、対象を限定した静的検証の範囲は[検証手順](docs/testing/checks.md)を参照する。
実サービスへの認証、パッケージ導入、AndroidのBionicなどはモックの成功だけでは確認できない。環境ごとの手動確認範囲は[環境別テストの説明](docs/testing/environment-matrix.md)に記載している。

GitHub ActionsもUbuntu 24.04上で同じ`make check`を実行する。検証用依存の導入はCIジョブの準備段階だけで行い、ローカルの検証ターゲットからは実行しない。GitHub上での初回実行結果と、必須チェックへの登録は別途確認する。

Git hooksはルートの`lefthook.yml`で管理し、pre-commitでステージ済み差分の空白エラー、pre-pushで`make check`を実行する。lefthook 2.2.2を使い、既存hookとcore.hooksPathを確認した後、各作業コピーで`lefthook install pre-commit pre-push`を実行する。Termuxのシバン補正とPATH、個別確認の手順は[Git hooksの説明](docs/testing/git-hooks.md)を参照する。

変更は作業ブランチからPRを作成し、必須チェック`check`の成功を確認して`main`へ取り込む。GitHub CLIでのPR作成・自動マージ予約・ブランチ整理は[PRの運用手順](docs/testing/pull-requests.md)を参照する。

規約はルート・対象フォルダのAGENTS.mdと作業別スキルへ分けて管理する。make lintは配布元の規則を1本1000字・常時合計8000字以内か確認する。展開済み規約を含む確認と変更前後の比較は[字数管理](docs/agents/instruction-budget.md)を参照する。

未解決の依存関係、バージョン固定、CIの実行状況などは[監査記録](docs/reviews/dotfiles-audit.md)で管理する。コード上の対応状況と実機への適用状況を分けて確認する。
