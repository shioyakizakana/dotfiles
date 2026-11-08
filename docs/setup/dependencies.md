# 設定が使うコマンドと追加プラグイン

この文書は、管理対象の設定と依存の準備方法を対応させる。以下の導入コマンドは利用者向けの手順であり、自動検証からは実行しない。実環境への導入・適用は内容を確認してから行う。

## 導入担当と環境の違い

| 対象 | 現在の準備方法 | 不足時の扱い |
| --- | --- | --- |
| 初期認証のPython 3.11以上、make、openssl、wget、flockなど | [READMEの初期準備](../../README.md#31-必要なコマンド)。認証前にOS側で準備する | miseの適用後処理では初期認証に間に合わない。`make require`だけですべての前提を確認したことにはならない |
| 基礎ツール | Ubuntu向け`bootstrap/bootstrap-tools.sh`。APTの一覧は同スクリプトで管理 | Python・Zsh・LuaRocks・fzfは、この基礎導入一覧に含まれない |
| 開発CLI・ランタイム | `home/dot_config/mise/config.toml`とmiseの適用後処理 | 一覧の不足を導入する。個別の導入失敗は解決が必要 |
| Zsh本体・fzf実行ファイル | 利用環境のパッケージなどで手動準備 | Zsh設定のGit外部取得はfzf実行ファイルを導入しない |
| luacheck・vuseted | mise処理の後半でLuaRocksを使う | LuaRocksがなければ処理は失敗する。Lua 5.1向けのLuaRocksとビルド環境を先に用意する |
| Rust補助ツール・nimlsp | 同じmise処理の後半でrustup・nimbleを使う | 各処理の失敗を終了状態で伝える |
| chafa・resvg・フォントなど | Homebrew対象環境では`home/dot_Brewfile` | chafaは導入失敗のためmise一覧から除外済み。復活や他方式への自動移行は行わない |
| textlintのnpm依存 | 展開後に利用者が`npm ci`で準備 | ラッパーが不足と準備先を表示する。実行時の自動導入は行わない |

Ubuntu向けのAPT手順はnative Ubuntu・WSL Ubuntu・proot Ubuntuが対象。その他のLinuxではOSのパッケージ提供状況を確認する。Termux本体ではUbuntu向けbootstrapを実行せず、Termux用のパッケージを使う。現在の環境別制御は、Termux本体へのmise設定と3本の導入スクリプトの展開を除外する。

proot UbuntuではHomebrewを省くため、Brewfileの内容は準備されない。Termuxでも同様に、必要な機能だけをその環境で準備する。chafa・resvgがない場合は画像・SVGプレビューを保証しない。systemdやkeyringの導入を、これらの任意機能の前提にしない。

## Bash・Zsh

`bat`・`gomi`・`rg`・`tldr`・`fd`・`eza`がPATHにある場合だけ、対応する共通エイリアスを定義する。不足時は通常の`cat`・`rm`・`grep`・`man`・`find`・`ls`を利用できる。特に`gomi`未導入時の`rm`は通常の削除コマンドなので、ゴミ箱への移動を期待しない。

Zshの外部プラグインは、対応するファイルが読み取り可能な場合だけ読み込む。fzfのCtrl-Tには実行ファイルとGit取得された2本のシェル設定が必要。zenoにはそれらに加えてdenoとzenoのbootstrapが必要になる。欠落時はその連携を有効にしない。fzf本体とシェル設定のバージョン互換性は実端末で確認する。

導入状況は、使う環境で次のように確認する。値や認証情報は表示しない。

```shell
command -v python3 zsh fzf luarocks deno
python3 --version
luarocks --lua-version=5.1 list --porcelain
```

LuaRocksの準備では、OS側のLuaとmiseのLua 5.1を混同しない。`--lua-version=5.1`で一覧を取得でき、同じLua向けにビルドできることを確認する。必要なヘッダー・ライブラリ・導入先は環境によるため、一律のインストール手順にはしていない。

依存を用意した後は、新しいシェルで確認する。ツールを削除した後の既存シェルには古いエイリアスが残り得るため、新しいシェルを使う。読み込み可能なプラグインの実装自体が正常であることまでは、存在確認で保証しない。

## Yazi

`init.lua`の追加依存は`git`・`full-border`・`bunny-private`。読み込みに失敗した場合はプラグイン名だけをログへ通知して続行する。欠落と読み込み中の不具合は同じ通知になるため、導入済みなのに通知される場合は互換性を確認する。読み込み後の`setup`失敗は省略しない。

`keymap.toml`も`smart-enter`・`toggle-pane`・`bunny`・`chmod`を参照する。これらは自動導入しておらず、未導入のキー操作は利用できない。fzf・zoxideのキー操作にも対応する実行ファイルが必要になる。キー設定のTOML互換性はDF-10で別途検証する。

公開プラグインは、提供元と利用中Yaziとの互換性を確認してから準備する。例えば公式のgitプラグインには次の導入方法がある。`ya`と`yazi`は同じバージョンを使う。[Yazi公式CLIドキュメント](https://yazi-rs.github.io/docs/cli/)

```shell
ya pkg add yazi-rs/plugins:git
```

この操作はネットワーク接続と展開先の変更を伴い、`package.toml`も生成・更新する。新たな管理ファイルをchezmoiへ取り込む場合は、私的設定を含まないことを確認し、取り込み操作を別途承認する。

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
