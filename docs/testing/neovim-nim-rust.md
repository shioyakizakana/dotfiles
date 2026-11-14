# Nim・RustのLSPをMasonなしで確認する

Nimの導入成功後、nimlsとrust_analyzerの接続・補完・定義ジャンプ・診断を確認する。以下は利用者向けの実機手順。確認用ファイルの作成だけでは、接続成功とは記録しない。

## 確認用プロジェクト

作成した一時ディレクトリのnim/とrust/を別々に開く。場所は作業完了時の案内に記載する。一時領域は再起動等で消える可能性があるため、継続使用する場合はフォルダ全体を利用者が保管する。

| 言語 | プロジェクトの目印 | 正常なコード | 意図的な型エラー |
| --- | --- | --- | --- |
| Nim | lsp_smoke.nimble | src/main.nimとsrc/greetings.nim | src/diagnostics.nim |
| Rust | Cargo.toml | src/main.rsとsrc/lib.rs | src/bin/diagnostics.rs |

どちらも外部パッケージを要求しない。Rustには空のworkspaceを宣言し、親のCargo workspaceから分離する。.cargo/config.tomlではオフラインを指定した。Nimの.nimbleとRustのCargo.tomlが、現在のLSP設定のルート検出条件に対応する。

診断用ファイルには、整数へ文字列を代入する誤りと、文字列引数の関数へ整数を渡す誤りを入れてある。Rustのプロジェクト全体の確認では、main.rsを開いていても別のbinのエラーが通知される可能性がある。正常なmain.rs自体の不具合とは区別する。

## 起動と実行パス

次の山括弧の部分を、案内された確認用ディレクトリのパスへ置き換える。ソースファイルを./main.rsなどの形でシェルから直接実行しない。

```shell
cd <確認用ディレクトリ>/nim
nvim --cmd 'lua vim.g.dotfiles_use_mason = false' src/main.nim
```

```shell
cd <確認用ディレクトリ>/rust
RUSTUP_AUTO_INSTALL=0 CARGO_NET_OFFLINE=true nvim --cmd 'lua vim.g.dotfiles_use_mason = false' src/main.rs
```

それぞれ新しいNeovimプロセスで開く。LspInfoでNimにはnimls、Rustにはrust_analyzerが接続し、root_dirがそれぞれの確認用プロジェクトを指すことを確認する。

Neovimで次を実行し、サーバーの起動設定と実行パスを記録する。

```vim
:lua for _, c in ipairs(vim.lsp.get_clients({bufnr = 0})) do print(c.name, vim.inspect(c.config.cmd), c.config.root_dir) end
:lua print(vim.fn.exepath("nimlsp"))
:lua print(vim.fn.exepath("nimsuggest"))
:lua print(vim.fn.exepath("rust-analyzer"))
```

rust-analyzerがshimの場合は、同じrust/フォルダのシェルでRUSTUP_AUTO_INSTALL=0 rustup which rust-analyzerを実行して実体も記録する。Mason配下を使っていないことを確認する。コマンドが見つからない場合と、起動したが解析できない場合を分けて報告する。

## 補完・定義ジャンプ・診断

1. main.nimまたはmain.rsのgreet呼び出しで補完を試す。確認後は元の正しいコードへ戻す。
2. 同じ呼び出しのgreet上で:lua vim.lsp.buf.definition()を実行する。Nimはgreetings.nim、Rustはlib.rsの宣言へ移動することを確認する。型定義ジャンプの操作とは分ける。
3. Nimは:e src/diagnostics.nim、Rustは:e src/bin/diagnostics.rsで診断用ファイルを開き、保存して意図的な型不一致が表示されるか確認する。
4. wrong_numberの値を42に、greetの引数をNimなら"Nim"、Rustなら"Rust"へ修正し、保存後に診断が解消することを確認する。Nimが先頭のエラーだけを表示する場合は、1件ずつ直して次の診断を確認する。同時に2件表示されることは条件にしない。
5. 確認用ディレクトリのRESULTS.mdへ環境名、実行パス、成功・失敗・未確認とログを記録する。実環境名はWSL・proot・Termux・ネイティブLinuxのどれかを利用者が記入する。

保存時の整形は今回の受け入れ条件に含めない。Mason削除の判断は、この結果と[既存の検証記録](neovim-lsp-verification.md)を合わせて行う。

## 手動確認後の状態

2026-11-14、利用者がTermux + proot Ubuntu、Neovim v0.12.6で確認した。Rustは接続・補完・定義ジャンプ・型エラー検出・修正後の診断解消が成功した。Nimは接続・補完・定義ジャンプが成功したが、診断は失敗。Nim 2.4.2とNimLSPのビルド時2.2.12の不一致が表示され、ハイライトも未適用だった。結果と次の切り分けは[検証記録](neovim-lsp-verification.md#nimrustの手動確認結果2026-11-14)を参照する。

## Nimの版不一致を解消する

承認後、NimLSPをNim 2.4.2で再ビルドし、既存バイナリを退避して切り替えた。隔離検証では版警告がなくなり、診断の検出・解消と定義ジャンプが成功した。Neovimを再起動して、この手順の診断確認を再実施する。手動結果は利用者がRESULTS.mdへ追記し、以前の失敗記録を残す。[再ビルド・退避先・復元手順](../setup/nimlsp-recovery.md)を参照する。

## 保存時の診断と最新の確認結果

再ビルド後、利用者がPATHへ~/.nimble/binを追加して起動したNeovimで、filetype=nim、保存時の診断5件、フロート表示、修正・保存後の診断解消を確認した。NimLSPは保存通知を受けて診断するため、接続後に:wを実行して確認する。PATHを明示しない起動方法と、未適用のシンタックスハイライトは別の残件。

## PATHの補助探索とハイライトの適用

ソースのnimls.luaは、PATH上のnimlspを優先する。見つからない場合はNIMBLE_DIR/bin/nimlsp、NIMBLE_DIRが未設定か空なら~/.nimble/bin/nimlspを確認し、実行可能な場合だけ絶対パスを指定する。どちらにもなければ標準のnimlspという指定を残し、Neovimが不足を通知する。NIMBLE_DIRを指定した場合、別の既定インストールへは切り替えない。シェルのPATH自体は変更しない。

ハイライトは、既存のTree-sitter導入一覧へnimを追加した。現在のプラグインの定義ではnim_format_stringも依存として導入される。[Tree-sitterの公式説明](https://github.com/nvim-treesitter/nvim-treesitter)と[使用するNim文法](https://github.com/alaviss/tree-sitter-nim)を参照する。

利用者は、次の2ファイルを適用してからNeovimを起動する。これは利用者向け手順で、Codexは今回実行していない。

```shell
chezmoi apply --exclude=scripts \
  "$HOME/.config/nvim/after/lsp/nimls.lua" \
  "$HOME/.config/nvim/lua/plugins/utils/nvim-treesitter.lua"
```

初回はパーサーと依存の取得・ビルド完了を待つ。messagesで失敗していないことを確認し、必要なら:TSInstall nimで再試行する。新規導入直後はパーサーを読み込めない場合があるため、完了後にNeovimを再起動する。以後は次のように、PATHを追加せず確認する。

```shell
cd <確認用ディレクトリ>/nim
nvim --cmd 'lua vim.g.dotfiles_use_mason = false' src/diagnostics.nim
```

LspInfoでcmdが既定配置の絶対パスを指すことを確認し、保存して診断を確認する。診断用ファイルを修正済みなら、再度意図的な型エラーを入れて試し、確認後は直す。ハイライトは:InspectTreeで構文木を開けること、キーワード等の上で:InspectにTree-sitterのcaptureが表示されることを確認する。色の違いだけで判断しない。

今回の隔離検証では、NimbleをPATHに入れず、修正ソースの既定配置探索から実NimLSPを起動して診断を取得した。Nimとnim_format_stringを一時領域だけへ取得・ビルドし、再起動後に構文エラーのない解析、ハイライト開始、capture 24件を確認した。実HOMEへのパーサー導入と設定の適用は未実施。適用後のTermux + proot Ubuntuでの通常起動と表示は利用者の確認待ち。

関連unittestは22件、make check全体はunittest 232件・Bats 18件が成功し、skipなし。PATH優先、既定配置、空白を含むNIMBLE_DIR、欠落時の動作、Nimの導入・ハイライト開始をモックで確認する。回帰テストとCIからパーサーを取得することはない。

その後、利用者が共通env.shへNIMBLE_DIRとPATHを設定し、通常起動でNimのハイライト適用を確認した。env.shの管理ソースと展開先は一致。その後、通常起動でのLSP接続、保存時の診断5件、フロート表示、修正後の診断解消も利用者が確認した。今回のNim対応は完了とする。
