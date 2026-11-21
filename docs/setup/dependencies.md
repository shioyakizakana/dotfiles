# 設定が使うコマンドと追加プラグイン

この文書は、管理対象の設定と依存の準備方法を対応させる。以下の導入コマンドは利用者向けの手順であり、自動検証からは実行しない。実環境への導入・適用は内容を確認してから行う。

## 導入担当と環境の違い

| 対象 | 現在の準備方法 | 不足時の扱い |
| --- | --- | --- |
| 初期認証のPython 3.11以上、make、openssl、wget、flockなど | [READMEの初期準備](../../README.md#31-必要なコマンド)。認証前にOS側で準備する | miseの適用後処理では初期認証に間に合わない。`make require`だけですべての前提を確認したことにはならない |
| プロジェクト別PAT | グローバルの初期認証後に`setup-proton-pass-project NAME`を実行 | age・Python・pass-cliとdotfilesのチェックアウトが必要。既存identityを共有し、プロジェクト用PAT・CLI鍵を準備する。[利用手順](../../README.md#74-プロジェクト別patの登録と利用)を参照 |
| 基礎ツール | Ubuntu・Termux向け`bootstrap/bootstrap-tools.sh`。環境別のパッケージ一覧を同スクリプトで管理 | Ubuntuの基礎導入一覧にはPythonが含まれない。Zsh・LuaRocks・fzfは両環境で手動準備 |
| 開発CLI・ランタイム | Ubuntu系は`home/dot_config/mise/config.toml`とmiseの適用後処理。Termuxはbootstrapのpkg対象一覧 | 一覧の不足を導入する。個別の導入失敗は解決が必要 |
| lefthook | miseとCIは2.2.2へ固定。各作業コピーでGit hooksをインストール | bootstrap-tools.shの自動導入対象には含めない。Termux向けの準備は[Git hooksの手順](../testing/git-hooks.md)を参照 |
| Zsh本体・fzf実行ファイル | 利用環境のパッケージなどで手動準備 | Zsh設定のGit外部取得はfzf実行ファイルを導入しない |
| luacheck | mise処理の後半でLuaRocksを使う | LuaRocksがなければ処理は失敗する。Lua 5.1向けのLuaRocksとビルド環境を先に用意する |
| mini.test | 既存のlazy.nvim定義を使用。Luaファイルで読み込み、検証済みrevisionへ固定 | LuaRocksからは導入しない。開発プロジェクトでは[最小構成のテスト手順](../testing/neovim-plugin-tests.md)に従い、開発用依存を別に管理する |
| Rust補助ツール・nimlsp | 同じmise処理の後半でrustup・nimbleを使う | 各処理の失敗を終了状態で伝える。nimlspはNimとのビルド時版も確認し、不一致なら[復旧手順](nimlsp-recovery.md)を案内して停止する |
| chafa・resvg・フォントなど | Homebrew対象環境では`home/dot_Brewfile` | chafaは導入失敗のためmise一覧から除外済み。復活や他方式への自動移行は行わない |
| textlintのnpm依存 | 展開後に利用者が`npm ci`で準備 | ラッパーが不足と準備先を表示する。実行時の自動導入は行わない |

Ubuntu向けのAPT手順はnative Ubuntu・WSL Ubuntu・proot Ubuntuが対象。その他のLinuxではOSのパッケージ提供状況を確認する。bootstrap-tools.shはTermux本体も判定し、pkgを使う。chezmoi適用時の環境別制御では、引き続きTermux本体へのUbuntu用mise設定と3本の導入スクリプトの展開を除外する。

proot UbuntuではHomebrewを省くため、Brewfileの内容は準備されない。Termuxでも同様に、必要な機能だけをその環境で準備する。chafa・resvgがない場合は画像・SVGプレビューを保証しない。systemdやkeyringの導入を、これらの任意機能の前提にしない。

## Bash・Zsh

`bat`・`gomi`・`rg`・`tldr`・`fd`・`eza`がPATHにある場合だけ、対応する共通エイリアスを定義する。不足時は通常の`cat`・`rm`・`grep`・`man`・`find`・`ls`を利用できる。特に`gomi`未導入時の`rm`は通常の削除コマンドなので、ゴミ箱への移動を期待しない。

Zshの外部プラグインは、対応するファイルが読み取り可能な場合だけ読み込む。fzfのCtrl-Tには実行ファイルとGit取得された2本のシェル設定が必要。zenoにはそれらに加えてdenoとzenoのbootstrapが必要になる。欠落時はその連携を有効にしない。fzf本体とシェル設定のバージョン互換性は実端末で確認する。

導入状況は、使う環境で次のように確認する。値や認証情報は表示しない。

Ubuntu系とTermuxでは`bash bootstrap/bootstrap-tools.sh --check`も利用できる。手動準備する依存を含めて存在を表示し、ディレクトリの作成や導入処理は行わない。未導入でも確認コマンドは正常終了するため、表示された`[--]`を確認する。Termuxではpkg管理対象の導入状況も表示し、Homebrewは`[SKIP]`と表示する。pass-cliの起動や実認証は行わない。

```shell
command -v python3 zsh fzf luarocks deno
python3 --version
luarocks --lua-version=5.1 list --porcelain
```

LuaRocksの準備では、OS側のLuaとmiseのLua 5.1を混同しない。`--lua-version=5.1`で一覧を取得でき、同じLua向けにビルドできることを確認する。必要なヘッダー・ライブラリ・導入先は環境によるため、一律のインストール手順にはしていない。

依存を用意した後は、新しいシェルで確認する。ツールを削除した後の既存シェルには古いエイリアスが残り得るため、新しいシェルを使う。読み込み可能なプラグインの実装自体が正常であることまでは、存在確認で保証しない。

## Neovim

Pythonのデバッグにはmise管理のdebugpyを使い、アダプターと対象プロジェクトのPythonを分離する。[DAPの設定・導入と確認](neovim-dap.md)を参照する。

Pythonはbasedpyrightで型解析・補完・定義ジャンプ、Ruffでlint・import整理・整形を行う。[Pythonの移行と確認手順](python-lsp.md)を参照する。

LSP・整形・プラグインの導入担当、Masonからmiseへの移行条件、環境別の確認範囲は[Neovim依存一覧](neovim-dependencies.md)を参照する。管理ソースからMason依存を除去済みで、移行用の切替指定は不要。設定適用後の通常起動も利用者が確認済みで、既存のMasonデータは保持している。

## Yazi

提供元・使用箇所・固定候補・実機確認の記録は[Yazi依存一覧](yazi-dependencies.md)を参照する。管理ソースに取得定義がないことと、実端末で未導入であることは区別する。

`init.lua`の追加依存は`git`・`full-border`・`bunny-private`。読み込みに失敗した場合はプラグイン名だけをログへ通知して続行する。欠落と読み込み中の不具合は同じ通知になるため、導入済みなのに通知される場合は互換性を確認する。読み込み後の`setup`失敗は省略しない。

`keymap.toml`も`smart-enter`・`toggle-pane`・`bunny`・`chmod`を参照する。これらは自動導入しておらず、未導入のキー操作は利用できない。fzf・zoxideのキー操作にも対応する実行ファイルが必要になる。キー設定はDF-10でTOML 1.0互換の記法へ修正したが、追加プラグインの導入やキー操作の動作保証とは別である。

公開プラグイン6件とflavor 2件は`home/dot_config/yazi/package.toml`でrevisionを固定する。`ya`と`yazi`は26.9.1へそろえる。既存環境では、manifestの適用前に利用者が既存のpackage.tomlを退避し、個人用の依存との統合を確認する。既存manifestを無条件に上書きしたり、私的な取得元を共有ソースへ取り込んだりしない。[Yazi公式CLIドキュメント](https://yazi-rs.github.io/docs/cli/)

```shell
ya --version
yazi --version
# 共有manifestを確認・配置した後、公開依存を復元する。
ya pkg install
```

installは利用者が選択して実行する操作で、通信とプラグイン・flavorの配置を伴う。chezmoiの適用後スクリプトやテストから自動実行しない。manifestだけをchezmoiで管理し、本体ディレクトリは除外する。新しい依存やrevisionの変更は共有ソースのPRで行う。

`bunny-private`は利用者の任意設定。必要な場合だけbunny本体を準備し、`~/.config/yazi/plugins/bunny-private.yazi/main.lua`をローカルで用意する。既存の私的設定を調査・公開せず、Gitにも追加しない。不要なら未配置のままでよい。

## tmuxの補助コマンド

`tmux-session-manager`・`tmux-move-window`・`tmux-ghq`は、このリポジトリでは実装も導入元の指定もない。提供元を推測して導入しない。利用者が既存の提供元を確認し、必要なものだけPATHへ準備する。

各コマンドがテンプレート展開時のPATHにある場合だけ、順にprefix+m・prefix+M・prefix+wを定義する。コマンドは展開時には実行しない。後から導入した場合は再展開が必要で、実際の適用は別途行う。コマンドがない場合は、そのキーをこの設定で上書きしない。

既存サーバーで設定を再読込しても、以前のキーバインドは自動で消えない。任意コマンドを削除した場合の確認は、新しいサーバーで行うか、既存バインドを利用者が個別に見直す。

## textlint

Node.js・npmと設定ファイルの展開後に、利用者が次を実行する。依存は管理対象のlockfileに従う。

```shell
cd "$HOME/.local/share/textlint-ja"
npm ci
textlint-ja /path/to/document.md
```

## 残る実機確認

初期認証前のPython、LuaRocksのLua 5.1向けビルド、fzfとシェル設定の組み合わせ、Yazi追加プラグイン、tmux補助コマンド、画像プレビューは実機で確認する。隔離テストの成功を、パッケージの導入成功や実アプリの互換性保証として扱わない。

## Termuxでの導入と実機確認

APT/dpkg方式のTermuxを対象とする。Pacman方式、rootでのpkg操作、他のLinuxディストリビューションは導入対象にしない。Ubuntuゲストの判定を先に行うため、prootへTermuxのPREFIXが引き継がれていてもUbuntuの導入処理を使う。Termux側のPREFIXやパッケージ管理ツールが確認できない場合は停止する。

基礎パッケージに加え、Proton Pass CLIとpkg対応の開発ツールを導入する。対象一覧は`bootstrap/bootstrap-tools.sh`の`TERMUX_PACKAGES`で管理する。`make bootstrap-tools`も同じ処理を実行する。配置先はTermuxのパッケージに従う。公式の[chezmoi](https://github.com/termux/termux-packages/blob/master/packages/chezmoi/build.sh)・[age](https://github.com/termux/termux-packages/blob/master/packages/age/build.sh)・[mise](https://github.com/termux/termux-packages/blob/master/packages/mise/build.sh)のビルド定義と、[OpenSSLコマンドのサブパッケージ](https://github.com/termux/termux-packages/blob/master/packages/openssl/openssl-tool.subpackage.sh)を確認している。ただし、端末で選択しているミラーにすべての候補があるかは実機で確認する。

導入済みかどうかはローカルのdpkg情報で判断する。不足がある場合だけpkgで一覧を更新し、不足分を導入する。一覧更新はスクリプト内では1回にまとめ、pkg upgradeは実行しない。導入失敗や導入後のパッケージ確認失敗は異常終了とし、Linux向けバイナリの取得へは切り替えない。依存解決による既存パッケージの更新まで禁止するものではない。

利用者はTermux端末上で、次の順に確認する。以下は実機での操作手順であり、自動テストでは実行しない。

1. リポジトリ内で`bash bootstrap/bootstrap-tools.sh --check`を実行し、表示された環境と不足を確認する。Ubuntuゲストで実行する場合はTermux本体と混同しない。
2. 導入対象を確認し、通常ユーザーで`bash bootstrap/bootstrap-tools.sh --install`を実行する。ミラーやパッケージが原因で失敗した場合は、その問題を解決してから再実行する。Linux用インストーラーで置き換えない。
3. 次のコマンドで配置とバージョンを確認する。Pythonは3.11以上が必要。再度`--install`を実行し、導入済みパッケージが省かれることも確認する。

```shell
command -v chezmoi age age-keygen python3 make openssl wget flock mise pass-cli codex
pass-cli --version
codex --version
chezmoi --version
age --version
python3 --version
mise --version
```

### pkgへ移すツールとmiseの扱い

Ubuntu系のmise管理ツールのうち、Termux公式のパッケージ定義を確認できた51項目をpkgで導入する。名前が異なるものは次のとおり。その他は原則として同名のパッケージを使う。

| miseの指定 | Termuxのパッケージ |
| --- | --- |
| `biome` / `delta` | `biome2` / `git-delta` |
| `go` / `node` / `lua` | `golang` / `nodejs-lts` / `lua51` |
| `go:golang.org/x/tools/cmd/goimports` / `go:golang.org/x/tools/gopls` | `goimports` / `gopls` |
| `npm:@openai/codex` / `npm:oxlint` / `pipx:ty` | `codex` / `oxlint` / `ty` |
| Proton Pass CLI（mise管理外） | `proton-pass-cli`（コマンドは`pass-cli`） |

導入対象は[Termux公式のパッケージ定義](https://github.com/termux/termux-packages/tree/master/packages)で確認した。選択中のミラーやCPUでの候補は実機で確認する。候補がない場合は異常終了し、Linux向けインストーラーへは切り替えない。

TermuxにはUbuntu用mise設定と導入スクリプトを展開しないため、この処理が同じツールをmiseでも導入することはない。mise本体は今後の環境変数・タスク管理などに利用できる。利用者が別途作成したmise設定や既存のmiseインストールは変更・削除しない。移行済みの環境では`type -a node python3 codex pass-cli`などでPATHを確認し、pkg管理の実行ファイルを使っているか確かめる。導入済みパッケージは自動更新せず、更新はpkg側で行う。

pkg版のバージョンはリポジトリに従い、Ubuntuのmise固定版と同じとは限らない。Lua 5.1のコマンドはlua5.1、Pythonはpkgの提供版を使う。Python 3.13・3.12の併存、LuaRocks、debugpy、npm経由のLSP、lefthookなど、今回の一覧にないツールは自動導入しない。Zsh・fzfも引き続き別途準備する。NeovimのLSP・DAPやYaziプラグインの互換性は実機確認が必要。

Homebrewと認証の自動実行は対象外。利用者から、pkg install proton-pass-cli後のbootstrap、PATログイン、保管庫一覧表示、ssh-agent起動の成功報告を受けている。シバン修正後のchezmoi applyも正常終了したとの報告がある。今回追加した開発ツール一括導入の実機確認は未実施。

Makefileの既定のchezmoiは`~/.local/bin/chezmoi`であり、Termuxパッケージの配置先とは異なる。後続のMake操作では`CHEZMOI_BIN="$PREFIX/bin/chezmoi"`をコマンド引数に指定する。例えば`make CHEZMOI_BIN="$PREFIX/bin/chezmoi" require`で確認できるが、pass-cli未準備なら失敗する。適用・認証のターゲットは別途確認してから実行する。

### zenoのSQLite読み込みエラー

利用者はpkg導入後のZsh再起動で、zenoのソケットサーバーが起動せず、SQLite共有ライブラリの読み込みがlibm.so.6不足で失敗したと報告した。Deno用SQLiteライブラリが取得したLinux向け配布物をTermuxで読み込もうとしている。[該当する@db/sqlite 0.12.0の実装](https://github.com/denodrivers/sqlite3/blob/0.12.0/src/ffi.ts)は、DENO_SQLITE_PATHで共有ライブラリを指定できる。

TermuxのZsh設定では、DENO_SQLITE_PATHが空で、PREFIXが絶対パスかつlib/libsqlite3.soが読み取り可能なら、そのファイルを使う。明示済みの指定は変更しない。Ubuntu・prootにはこの設定を追加しない。この環境変数はZshの子プロセスへ引き継がれるため、zeno以外の同ライブラリを使うDeno処理にも適用される。

libsqliteは既存の[Termux版Pythonの依存](https://github.com/termux/termux-packages/blob/master/packages/python/build.sh)に含まれる。追加パッケージの導入や、Denoキャッシュ・zenoの履歴データの削除は行わない。ライブラリが存在しなければ自動指定せず、導入済みパッケージを確認する。

Termuxで一時的に試す場合は、次を実行する。新しいZshでzenoの起動を確認し、exitで元のシェルへ戻る。以下は利用者向けの実機手順であり、自動テストでは実行しない。

```shell
test -r "$PREFIX/lib/libsqlite3.so" && printf 'SQLite library: OK\n'
DENO_SQLITE_PATH="$PREFIX/lib/libsqlite3.so" zsh
```

恒久的な設定は、修正版を取得して.zshrcの差分を確認した後、次のように限定適用する。

```shell
chezmoi apply --include=files --refresh-externals=never "$HOME/.zshrc"
```

新しいZshを起動して確認する。隔離テストでは、子プロセスへのパス引き継ぎ、明示指定の保持、Ubuntu・prootへの影響、ライブラリ不在時の動作を確認する。Termux上での実SQLiteの読み込みとzeno起動の成功は未確認。
