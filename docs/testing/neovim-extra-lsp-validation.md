# 追加LSPの用途と検証記録

2026-11-15、NV-03の残件として追加5サーバーを確認した。実行ホストはLinux aarch64、Neovimはv0.12.6。通常設定を起動せず、導入済みツール・nvim-lspconfig・管理ソースを隔離HOMEで読み込んだ。今回、LSP設定・導入定義・Mason構成は変更していない。

## 用途・導入担当・起動条件

| サーバー | 用途 | 導入担当 | 現在の起動設定 |
| --- | --- | --- | --- |
| emmet_language_server | HTML・CSS等のEmmet略記の補完 | mise `npm:@olrtg/emmet-language-server` | プロジェクト側のafter/lsp/emmet_language_server.luaは空の上書き。cmd・filetypes・Gitルート探索はnvim-lspconfigから継承 |
| tailwindcss | Tailwindのクラス補完・診断 | サーバーはmise `npm:@tailwindcss/language-server`。Tailwind本体・設定はプロジェクト側 | プロジェクト側のafter/lsp定義なし。nvim-lspconfigがTailwind・PostCSS設定、依存宣言、Git等を探索 |
| oxlint | JavaScript・TypeScript等のlint | mise `npm:oxlint`またはプロジェクト側 | プロジェクト側のafter/lsp定義なし。nvim-lspconfigがOxlint設定等を探索し、プロジェクト内実行ファイルを優先 |
| golangci_lint_ls | golangci-lintの診断をNeovimへ渡す | miseのlangserverとgolangci-lintの2つ | プロジェクト側の上書きは空。nvim-lspconfigのcmd・Goルート探索・linterの版判定を継承 |
| sqls | SQLの補完・DBスキーマ参照・クエリ操作 | mise `go:github.com/sqls-server/sqls`。接続情報は別途管理 | プロジェクト側の上書きは空。nvim-lspconfigのcmd・config.yml探索を継承。DB利用には接続設定が必要 |

登録は`home/dot_config/nvim/lua/plugins/lsp/server-register.lua`、導入定義は`home/dot_config/mise/config.toml`で管理する。空の上書きファイルを未実装とは扱わない。使用するnvim-lspconfigの版によって継承する設定が変わるため、公開プラグインの版固定はNV-05で扱う。

利用者が5件すべての継続使用を選択したため、有効登録を維持する。EmmetはHTML等の構文支援、Tailwindはクラス名、Oxlintはlintという担当で、vtslsの型解析とは役割が異なる。golangci-lintはgoplsの診断と重なるルールを持つ場合があるが、今回の確認だけでは不要とは判断しない。未使用のサーバーを除外する場合は、利用者が用途を確認してから決める。

## 隔離検証の結果

確認用プロジェクトは`/tmp/neovim-extra-lsp-check-_g4cxfb3`。一時領域なので永続保存は保証しない。ツールの実行パスはすべてmise管理下を選び、Masonは読み込んでいない。

| 対象・版 | 検証内容 | 結果・限界 |
| --- | --- | --- |
| Emmet 2.8.0 | HTMLでul>li.item*2の補完を要求 | 接続成功。ul内にliを2つ作るsnippetを取得 |
| Oxlint 1.93.0 | no-debuggerを有効にしたダミー設定で診断を確認し、debugger文を削除 | 接続・診断1件・修正後0件を確認。型情報を使うlintは対象外 |
| golangci-lint-langserver 0.0.12 / golangci-lint 2.15.0 | 標準ライブラリos.Chdirのエラー未処理をerrcheckで検出し、修正・保存 | 接続・診断1件・修正後0件を確認。実プロジェクトの全ルールを検証した結果ではない |
| Tailwind CSS language server 0.16.0 | Tailwind本体を追加せず、最小設定で初期化・flex補完・診断を要求 | 初期化とflex候補取得は成功。ただしログにtailwindcss/package.jsonの解決失敗があり、診断は0件。プロジェクト依存を使う機能確認は未完了 |
| sqls 0.2.48 | connectionsを空にした検証用config.ymlで起動 | 初期化成功。no database connectionの通知あり。DB接続・スキーマ補完・クエリ実行は未実施 |

検証ではroot_dirを確認用フォルダへ明示した。通常設定での自動root選択、補完UI、保存時の見え方は利用者による確認に残す。Tailwindで補完候補が得られたことを、プロジェクト依存の解決成功や診断成功とは扱わない。

GoはGOPROXY・GOSUMDBをoff、GOTOOLCHAINをlocal、GOENV・GOWORK・telemetryを無効にし、キャッシュを一時領域へ分離した。依存の取得を行わず標準ライブラリだけを解析した。OxlintとGoの修正後確認ではダミーファイルだけを保存し、終了後は手動確認用のエラー例へ戻した。sqlsは空の接続設定を明示し、実際の接続情報を読まず、DB操作も要求していない。

追加インストール、設定適用、実プロジェクト変更、commit・pushは行っていない。設定コードは変更していないため、前回のmake check成功結果（unittest 246件・Bats 18件、skipなし）を再利用し、今回は全体テストを再実行していない。

## 手動確認

確認用フォルダのREADME.mdとRESULTS.mdに手順と記入欄を用意した。各言語フォルダで、Masonを無効にして起動する。

```sh
nvim --cmd 'lua vim.g.dotfiles_use_mason = false' <確認用ファイル>
```

| フォルダ | 操作 | 期待結果 |
| --- | --- | --- |
| emmet_language_server | index.htmlの略記末尾で補完を開いて展開 | ul内にli.itemを2つ作る候補がある |
| oxlint | main.tsを開き、debugger文を削除して保存 | no-debuggerの診断が出て、削除後に解消 |
| golangci_lint_ls | main.goを開き、os.Chdirの戻り値を明示的に無視する形へ修正して保存 | errcheckの診断が出て、修正後に解消 |
| tailwindcss | 初期化確認のみ。機能確認は依存を備えたプロジェクトで実施 | 不足依存のある現在の例を、診断まで成功する例とは扱わない |
| sqls | 下記の専用コマンドでDB接続なしの初期化だけ確認 | no database connectionを許容。補完・クエリの確認は行わない |

Goの修正例は`_ = os.Chdir(".")`。この検証はLSPを通じた診断確認であり、各ソースファイルをシェルスクリプトとして実行する手順ではない。

sqlsだけは、確認用のsqlsフォルダで次のコマンドを使い、空の接続設定を明示する。通常の接続設定へ依存せず初期化を確認するための起動方法である。

```sh
nvim --cmd "lua vim.g.dotfiles_use_mason = false; vim.lsp.config('sqls', {cmd = {'sqls', '-config', vim.fn.getcwd() .. '/config.yml'}, settings = {sqls = {connections = {}}}})" main.sql
```

## NV-03の残件とMason削除の判断

1. 追加5サーバーの継続使用とEmmet・Oxlint・golangci-lintの通常UI確認は、下記の利用者報告で完了。sqlsもDB接続なしの初期化を確認済み。未確認言語の全機能を一律に必須とせず、採用する用途に合わせる。
2. Tailwindは承認された検証用依存3.4.17で隔離検証と通常UI確認が完了した。クラス生成・設定解決に使う本体はプロジェクト側の依存として維持する。v4や実プロジェクトの構成は今回の確認対象外。
3. sqlsのDB機能を確認する場合は、利用者が対象DBと認証方法を指定する。実接続の承認がない間は未検証として扱い、秘密情報を確認用ファイルへ記録しない。
4. 対象環境と残す機能が確定したら、Mason依存宣言・setup・インストール用コマンド・検証用切替を削除するタスクを実施する。既存のMasonデータは自動削除しない。

Linux aarch64で得た今回の結果をTermux単体・WSL・別のネイティブLinuxへ一般化しない。Mason削除後もmise、プロジェクト依存、PATHによる起動条件は引き続き必要になる。

## 通常UIの手動確認結果（2026-11-15）

利用者が記入した`/tmp/neovim-extra-lsp-check-_g4cxfb3/RESULTS.md`を確認した。依頼文の`/tmp/neovim-extra-lsp-check_g4cxfb3/RESULTS.md`は存在しなかった。環境はTermux + proot Ubuntu、Neovim v0.12.6。以下は利用者の報告であり、Codexの再実行結果ではない。

| 対象 | 継続使用 | 接続・機能の結果 | 実行パス・root |
| --- | --- | --- | --- |
| Emmet | 継続 | 接続・略記補完成功 | mise管理のemmet-language-server。rootは確認用emmet_language_serverフォルダ |
| Oxlint | 継続 | 接続・診断・修正後の解消が成功 | mise管理のoxlint。rootは確認用oxlintフォルダ |
| golangci-lint | 継続 | 接続・診断・修正後の解消が成功 | mise管理のgolangci-lint-langserver。rootは確認用golangci_lint_lsフォルダ |
| Tailwind | 継続 | 接続NG。プロジェクト依存を用意するまで部分確認 | 実行パスは空欄。rootは確認用tailwindcssフォルダ |
| sqls | 継続 | 接続成功。DB接続なしの初期化のみ | mise管理のsqls。rootは確認用sqlsフォルダ |

Emmet・Oxlint・golangci-lintの通常UI確認は完了とする。sqlsは初期化の確認までで、DBスキーマ補完やクエリ操作の成功とは扱わない。

Tailwindは、前回の隔離検証でtailwindcss/package.jsonの解決失敗を確認している。ただし今回の報告には起動エラーやログがなく、接続NGの直接原因は未確定。空欄の実行パスだけで、language-serverの未導入やPATH不良とは判断しない。

次はTailwindを優先し、プロジェクト依存と起動状態を確認する。必要な本体依存・採用版・検証用フォルダを決め、追加導入の承認後に確認用環境を整備する。既存のTailwind依存済みプロジェクトを使用できる場合は追加導入を省ける。起動ログとLspInfoで接続・実行パス・rootを確認し、その後にクラス補完と診断・修正後の解消を確認する。Mason削除とDB接続は今回行っていない。

## Tailwindの依存・起動の継続調査（2026-11-15）

元の確認用フォルダでも、隔離HOMEでの自動接続・診断・補完が成功し、通常UIの接続NGは再現できなかった。別の確認用フォルダに承認されたtailwindcss 3.4.17を導入し、実パッケージ解決、競合診断2件と修正後0件、標準クラスと独自色の補完を確認した。依存解決エラーも解消した。[検証内容と通常UIの再確認手順](neovim-tailwind-validation.md)を参照する。dotfilesの設定コードは変更せず、通常起動の確認を残す。

Tailwindの通常UI再確認も利用者が完了した。Termux + proot Ubuntu、Neovim v0.12.6で接続・期待するroot・mise管理の実行パス、標準クラスと独自色の補完、競合診断と修正・保存後の解消が成功した。[手動確認結果](neovim-tailwind-validation.md#通常uiの手動確認結果2026-11-15)を参照する。追加5サーバーでは、sqlsのDB機能だけが未検証であり、初期化成功とは区別する。
