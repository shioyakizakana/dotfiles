# Neovimの依存関係とmiseへの移行

Masonからmiseへの段階的な移行を進めるため、管理ソースにある依存と導入担当を整理した。調査日は2026-11-13。

Masonは移行完了まで維持する。有効なLSP23件を、miseの導入定義、補助処理、プロジェクト依存へ対応させた。環境別の実導入と実行パスの確認は残る。定義がないことから、実機でも未導入だとは判断しない。

1. 切替を指定しなければMasonの初期化と依存宣言を維持し、明示的に無効化できる切替を追加した。
2. TypeScript・Vue・Svelte・oxlintとGo整形のmise定義を追加した。実導入とMasonなしでの動作を確認してからMasonを削除する。
3. プラグイン取得・構文パーサー導入・ビルドが起こり得るため、通常設定の起動を自動テストとして扱わない。

## 起動と導入の担当

設定の起点は`home/dot_config/nvim/`。以下の短いパスは、このディレクトリを基準にしている。表中の`server-register.lua`は`lua/plugins/lsp/server-register.lua`の略。

| 処理・依存 | 現在の担当と根拠 | 移行時の扱い |
| --- | --- | --- |
| Neovim本体 | `home/dot_config/mise/config.toml:42`の`neovim = "latest"` | 起動・LSP・補完の組合せを確認してから固定候補を選ぶ |
| 起動順序 | `init.lua`→`lua/config/init.lua`→`lua/config/lazy.lua` | base・indent・ui・keymaps・filetypeもプラグインより先に読む |
| lazy.nvim | `lua/config/lazy.lua:1-41`で不足時にGit clone、`stable`ブランチ | 他プラグインの導入はlazy.nvim。miseへ移さない |
| プラグイン更新確認 | 同ファイル末尾の`checker = { enable = true }` | オフライン検証では実行しない |
| LSPの設定 | `lua/plugins/lsp/index.lua`と`after/lsp/*.lua`、nvim-lspconfig | 実行ファイルの導入とNeovimへの登録を区別する |
| LSPの有効化 | `lua/plugins/lsp/server-register.lua`の23件を`vim.lsp.enable` | リストの全件について提供元・実行パスを確認する |
| Mason | 同ファイルで`dotfiles_use_mason`がfalseでなければ`setup`。以前コメントアウトされていた自動導入指定は整理済み | 現在のファイルから全LSPの自動導入は確認できない。既存Masonの実データは未調査 |
| Mason関連の宣言 | `lua/plugins/lsp/index.lua`でMason有効時だけmason.nvim・mason-lspconfig.nvim・mason-null-ls.nvim・none-ls.nvimを宣言 | 移行後に参照を整理。LSP設定本体のnvim-lspconfigは別の役割 |
| Go・npm等のツール | miseのTOML、`home/.chezmoiscripts/run_after_install-mise.sh:100-139` | Ubuntu対象でmise installと不足分の補助導入を行う |

`lua/config/lazy.lua`は`plugins.lsp.index`を明示的にimportする。別ファイルの`lua/plugins/lsp/_index.lua`や、indexでimportがコメントアウトされた`none-ls.lua`を、現在の明示的なimportから読み込むとは扱わない。ただしnone-ls.nvim自体の依存宣言は残る。実際のlazy.nvimによる読み込み結果は未確認。

## LSPの23件を導入定義と対応させる

「mise定義あり」は管理ソース上の対応を示し、実バイナリの導入・互換性を保証しない。`cmd`を独自定義していないサーバーは、nvim-lspconfig側の定義が必要であり、以下の実行名候補は実機で確認する。

| 有効なLSP | 実行名・指定 | 導入担当・現状 | 設定の根拠 |
| --- | --- | --- | --- |
| bashls | `bash-language-server start` | mise `npm:bash-language-server` | `after/lsp/bashls.lua:3` |
| biome | `node_modules/.bin/biome lsp-proxy` | プロジェクト側。miseのグローバル定義なし。Biome設定がなければroot処理が戻る | `after/lsp/biome.lua:5-37` |
| cssls / html / jsonls | `vscode-css-language-server` / `vscode-html-language-server` / `vscode-json-language-server`、各`--stdio` | mise `npm:vscode-langservers-extracted` | 各`after/lsp/{cssls,html,jsonls}.lua:3` |
| denols | `deno lsp` | mise `deno` | `after/lsp/denols.lua:3-6` |
| emmet_language_server | 独自cmdなし | mise `npm:@olrtg/emmet-language-server` | `after/lsp/emmet_language_server.lua:1` |
| golangci_lint_ls | 独自cmdなし | mise `go:github.com/nametake/golangci-lint-langserver`と`golangci-lint` | `after/lsp/golangci_lint_ls.lua:1` |
| gopls | 独自cmdなし | mise `go:golang.org/x/tools/gopls` | `after/lsp/gopls.lua:1-9` |
| lua_ls | `lua-language-server` | mise `lua-language-server` | `after/lsp/lua_ls.lua:16` |
| nimls | `nimlsp` | miseのNimを前提に、補助処理の`nimble install -y nimlsp` | `after/lsp/nimls.lua:3`、導入スクリプト82-93行 |
| oxlint | nvim-lspconfigの`oxlint --lsp` | mise `npm:oxlint`を追加。実導入は未実施 | `server-register.lua:13` |
| marksman | `marksman server` | mise `marksman` | `after/lsp/marksman.lua:3` |
| pyright | `pyright-langserver --stdio` | mise `npm:pyright` | `after/lsp/pyright.lua:21` |
| ruff | `ruff server` | mise `ruff` | `after/lsp/ruff.lua:3` |
| rust_analyzer | `rust-analyzer` | miseのRustを前提に、補助処理のrustup component追加 | `after/lsp/rust_analyzer.lua:63`、導入スクリプト136行 |
| sqls | 独自cmdなし | mise `go:github.com/sqls-server/sqls` | `after/lsp/sqls.lua:1` |
| svelte | nvim-lspconfigの`svelteserver --stdio` | mise `npm:svelte-language-server`。0.18.6をnpm経由で実導入済み、隔離LSPの初期化・整形・正常終了を確認 | `server-register.lua:20` |
| tailwindcss | 独自cmd・同名の追加設定ファイルなし | mise `npm:@tailwindcss/language-server` | `server-register.lua:21` |
| taplo | `taplo lsp stdio` | mise `taplo` | `after/lsp/taplo.lua:3` |
| vtsls | `vtsls --stdio` | mise `npm:@vtsls/language-server`を追加。Vue用プラグインの配置を解決する設定も追加 | `server-register.lua:23`、`after/lsp/vtsls.lua` |
| vue_ls | nvim-lspconfigの`vue-language-server --stdio` | mise `npm:@vue/language-server`を追加。vtslsとの実接続は未確認 | `server-register.lua:24` |
| yamlls | `yaml-language-server --stdio` | mise `npm:yaml-language-server` | `after/lsp/yamlls.lua:3` |

`after/lsp/ts_ls.lua:4`は`typescript-language-server`を指定するが、有効化リストは`vtsls`で、`ts_ls`を含まない。NV-02ではvtslsを継続し、ts_lsを同時有効化しない。`eslint.lua`も有効化リストにない。miseの`npm:basedpyright`・`pipx:ty`・`npm:@astrojs/language-server`には、このリストでの同名LSP有効化がない。他用途の可能性があるため削除しない。

Rust設定は`rustc`と`cargo`も呼ぶ（`after/lsp/rust_analyzer.lua:22-23,84-94`）。rust-analyzerの存在だけでRustプロジェクト全体を検証済みとはしない。

## 整形・検索・デバッグにも別の依存がある

| 機能 | 外部依存と導入担当 | 根拠・未確認事項 |
| --- | --- | --- |
| Lua・Python・シェル整形 | miseのstylua・ruff・shfmt | `lua/plugins/lsp/conform.lua:33-43`。複数ruff処理とZsh整形の実動作は未確認 |
| Go整形 | mise `go:golang.org/x/tools/cmd/goimports`を追加 | 同ファイル35行。goplsやgofumptの定義と区別する |
| Web整形 | `biome-check`と`prettierd`。後者はmise `npm:@fsouza/prettierd` | 同ファイル19-33行。Conformの名前と実行ファイル名を混同しない。Biomeのプロジェクト内探索は実プラグインで未確認 |
| Deno整形 | ConformのWebリストを空にしてLSPへfallback | 同ファイル15-23,59行。判定はカレントディレクトリのdeno.json/jsonc |
| Git・GitHub・検索 | gitはbootstrap、gh・lazygit・ripgrep・fdはmiseに定義 | `lua/plugins/utils/snacks/index.lua`、`lua/plugins/ui/toggleterm.lua:21`。rg・fd等の正確な要件は採用したプラグイン版で確認する。gh機能の認証は今回対象外 |
| ファイラー | mise `yazi = "26.9.1"`、lazy.nvimのyazi.nvim | `lua/plugins/ui/yazi.lua`。Yazi側の公開依存は[別一覧](yazi-dependencies.md) |
| クリップボード | `unnamedplus`。OS別providerの明示定義なし | `lua/config/ui.lua:6`。Termux・WSL・SSH・デスクトップで別確認 |
| SKK | lazy.nvimのskkelua.nvimと`~/.skk/dic/SKK-JISYO.*` | `lua/plugins/completion/skkelua.lua:8-15`。辞書取得定義は今回の管理ソースでは見つからない。rank.jsonは利用時の保存データとして内容を読まない |
| 補完用辞書 | 管理ソースの`dict/user_dict.txt` | `lua/plugins/completion/sources.lua:49-50`。実機の個人辞書は読まない |
| Python DAP | Python実行環境とデバッグアダプター | `lua/plugins/dap/adapters.lua:19-37`。pythonアダプターの登録とdebugpyの導入定義は見つからない |
| Lua DAP | lazy.nvimのone-small-step-for-vimkindとnluaアダプター | 同ファイル3-17行。実接続・API互換性は未確認 |

## プラグイン本体とビルドはlazy.nvimが担当する

以下は明示的なimportと依存宣言に沿った一覧。プラグイン内部の推移的依存は取得していないため含めない。省略した所有者名は、対応ファイルにあるGitHubリポジトリ名で確認できる。

| 設定ファイル（`lua/plugins/`以下） | 主なプラグイン・直接依存 | 導入時の注意 |
| --- | --- | --- |
| `completion/index.lua`・`luasnip.lua`・`skkelua.lua` | blink.cmp、blink.compat、blink-cmp-dictionary、blink-cmp-conventional-commits、LuaSnip、friendly-snippets、skkelua.nvim | blink.cmpはbuild関数を60000ms待つ。LuaSnipは`make install_jsregexp`を呼ぶ。採用版のビルド要件・Android対応は未確認 |
| `lsp/index.lua`・`conform.lua`・`lazydev.lua` | lspkind.nvim、nvim-lspconfig、Mason関連3件、none-ls.nvim、blink.cmp、conform.nvim、lazydev.nvim | サーバー実行ファイルとプラグイン本体を別管理にする |
| `utils/nvim-treesitter.lua`・`editor/treesj.lua` | nvim-treesitter、nvim-treesitter-context、treesj | mainブランチ、`:TSUpdate`、config内の14言語install呼び出しがある |
| `dap/index.lua` | nvim-dap-view、nvim-dap、one-small-step-for-vimkind、nvim-dap-virtual-text | プラグイン導入だけでPythonデバッグ環境は完成しない |
| `editor/`のその他のimport | csvview.nvim、in-and-out.nvim、lsp_signature.nvim、md-render.nvim、budoux.lua、mini.surround、mini.test、nvim-autopairs、tiny-cmdline.nvim | md-renderのweb-devicons・budouxは依存宣言でoptionalとコメントされている |
| `ui/`のimport | barbar.nvim、gitsigns.nvim、web-devicons、catppuccin/nvim、indent-blankline.nvim、lualine.nvim、no-neck-pain.nvim、nvim-scrollbar、oil.nvim、quicker.nvim、rainbow-delimiters.nvim、toggleterm.nvim、winresizer、yazi.nvim | アイコン用フォントとクリップボードはOS・端末側も確認する |
| `utils/`のその他のimport | lazygit.nvim、nvim-hlslens、snacks.nvim、which-key.nvim | lazygit.nvim・yazi.nvimの依存にplenary.nvimがある |
| `lua/config/lazy.lua`の直接宣言 | plenary.nvim、web-devicons、vim-operator-replace、vim-operator-user、vimdoc-ja | ロックと復元は別途設計する |

`plugins.skkeleton.index`はimportがコメントアウトされている。このimportが指定するdenops.vim・ddc.vim・pum.vim・skkeleton等を現行SKKの必須依存には含めない。`lsp/_index.lua`・`lsp/none-ls.lua`・`lsp/format.lua`にも別の宣言や処理が残るため、削除候補はrequireとimportを確認してから決める。

UbuntuのAPT定義にはbuild-essential・cmake・makeがあるが、全プラグインのビルド成功を保証しない。tree-sitter CLIはmise、RustコンパイラーはmiseのRustが担当する。パーサー・補完のネイティブモジュールについては、採用revisionの要件を確認して必要なC/C++コンパイラー等を確定する。

## 環境別に移行完了を判断する

| 環境 | 管理ソース上の状態 | 利用者が確認する範囲 |
| --- | --- | --- |
| ネイティブUbuntu・WSL Ubuntu | mise設定とAPT導入処理の対象 | PATH、LSP起動、保存整形、補完、クリップボード。WSLではWindows連携を別確認 |
| proot Ubuntu | Ubuntu用mise・APTの対象、Homebrewは除外 | ゲスト内の実行ファイルを選ぶこと、ビルド、clipboard、デバッグ接続。ホストのPREFIXとの混同を避ける |
| Termux本体 | Neovim設定は除外していないがUbuntu用mise設定と導入3スクリプトは除外 | AndroidネイティブのNeovim・Node・サーバー・ビルドツールを個別準備。Linux ARM64配布物の流用成功を前提にしない |
| その他のLinux | Neovim設定は除外していないがUbuntu用mise・APTは対象外 | OS側の導入担当を先に決める。systemd・keyringを本タスクの前提にしない |

根拠は`home/.chezmoiignore:17-30`とAPT・mise導入スクリプト。Termuxではmise本体の初期導入と、Ubuntu向けツール一覧の適用を区別する。

## 修正候補と推奨順序

NV-01はソース修正済み。利用者から設定の実適用成功報告があり、初回取得・失敗復旧の実機確認は残る。NV-02は導入定義とVue連携を修正済み。利用者から4ツールの導入成功報告があり、Svelteは下記の復旧手順で実導入と隔離起動を確認した。Vueは利用者の通常操作と依存追加後の診断確認が成功した。NV-03は検証用切替と主力7サーバーの隔離検証まで対応済み。未確認言語とMasonの削除は残件。NV-04〜NV-06は未実装。ソース上の事実と、ダミーで再現した不具合、通常設定での実機確認を区別する。

| ID | 重要度・工数 | 区分・現状 | 次の作業と受け入れ条件 |
| --- | --- | --- | --- |
| NV-01 | Medium / Small | 信頼性・ソース修正済み。利用者から設定の適用成功報告あり。修正前の取得失敗時に未定義の`out`を表示してエラーになることをダミーで再現した | 同じ親ディレクトリの一時領域へ取得し、成功後に配置する。失敗時は自分の一時領域だけを削除して非0で終了する。回帰テスト10件が成功。実通信と実機確認は未実施 |
| NV-02 | Medium / Medium | DF-09後続・実機確認中。承認されたmise定義5件とVue/vtsls連携を追加 | 回帰テスト8件が成功。その後Svelteの実導入と隔離LSPを確認。各言語の実接続・Biomeの起動ディレクトリ検証は残件。Masonを削除する前に環境別の実行パスを確認する |
| NV-03 | Medium / Medium | 対応中。既定動作を維持するMason無効化の検証モードを追加 | 既定・有効・無効の各モードで23件の登録をダミー検証し、主力7サーバーも隔離確認済み。Rustの手動確認は成功。Pythonの提供元、未確認対象を整理してからMason本体・連携プラグイン・setup参照を削除する。既存のMasonデータは自動削除しない |
| NV-04 | Medium / Medium | 信頼性・潜在的リスク。DAPに`dap.configuration`・`tyoe`があり、Pythonのパス連結に区切り不足、fallbackが`usr/bin/python`。pythonアダプター定義もない（`lua/plugins/dap/adapters.lua:3-37`） | 採用するnvim-dap APIとPythonアダプターの担当を確定する。モックで設定登録を再現し、空白を含む仮想環境パス、未導入時の案内、Lua接続設定を検証する |
| NV-05 | Medium / Medium | DF-06後続・再現性。Neovimはlatest、lazy.nvimはstable、lazy-lock.jsonは除外 | 実機で動く組合せを記録し、Neovim本体と公開プラグインの固定・復元を設計する。既存lockfileを無断で上書きせず、個人依存の扱いを先に決める |
| NV-06 | Low / Small | 保守性・改善提案。現在importされない旧LSP・整形・SKK設定が残る | NV-03後に用途を確認し、維持・整理を選ぶ。現行importから未使用設定を呼ばないことを確認する |

NV-01の修正後は、NV-02→NV-03の順で移行する。NV-04は別PRで並行可能。NV-05の版選定は設定と主要機能を確認した後に行う。Mason併存そのものを不具合として扱わず、移行中の状態として維持する。

## Masonを削除するための確認手順

以下は次回以降の利用者向け手順であり、今回実行していない。通常設定の起動やcheckhealthには通信・取得・ビルドの可能性があるため、自動検証とは分ける。

1. 使用言語と対象環境を一覧表に追記する。各LSPを「mise・補助導入」「プロジェクト依存」「その環境の手動導入」「意図して無効化」のいずれかにする。登録だけが残るサーバーをなくす。
2. 下記の検証モードでMasonの依存宣言とsetupを無効化し、Masonを含まないPATHで新しく起動する。Codexのダミーテストは一時HOMEと空のPATHを使う。実機で隔離HOMEを使う場合も、必要な設定・公開プラグイン・ツールは別途準備する。実環境のMasonデータやプラグインを削除しない。
3. 必要な依存を用意した後、確認用の空プロジェクトを開く。`:lua print(vim.fn.exepath('pyright-langserver'))`等で各実行パスを確認し、`:lua print(vim.fn.exepath('node'))`も確認する。秘密情報や環境変数全体を出力しない。
4. 各言語の最小ファイルでLSPの接続・診断・補完・定義ジャンプを確認する。`:LspInfo`で使用サーバーを確認し、重複起動やMason配下からの起動がないかを確認する。プロジェクト依存を使う場合は、そのパスを正しい結果として記録する。
5. 保存整形を小さな検証用ファイルで試す。Go、Lua、Python、シェル、Web、Denoの分岐を分け、LSPのfallbackとgoimportsによる整形を区別する。
6. Termux・proot・WSL・ネイティブLinuxの結果を別々に記録する。未確認環境は未確認のまま残し、削除PRで対象範囲を示す。

## 自動検証と調査の限界

今回の調査は追跡対象のLua・TOML・シェル・ignore・既存テストを読む静的解析。プラグイン本体、実機のlockfile、Masonのインストール済み一覧、個人プロジェクト・辞書・環境変数は読んでいない。初回の静的調査では外部配布元への通信、認証、導入、更新、Neovim通常起動は行っていない。NV-02では承認に基づき下記の公式資料だけを閲覧した。API互換性や正確なバックエンド要件は、今後採用する版の公式資料と隔離検証で確認する。

`tests/test_neovim_bootstrap.py`で初回取得を検証する。実プラグインを含む起動・LSP登録のテストはまだない。Yazi向けLua検証や全体のmake check成功を、Neovimの動作確認には代用しない。新しいテストでは標準ライブラリのunittestから既存Luaを呼び、vim・require・外部コマンドをダミーへ置き換える方式を優先する。Luaはcompileだけなら構文を確認できるが、nvim-dapやLSP APIの正しさまでは確認できない。既存のシェルテストにあるnvimのダミーは、エイリアス呼び出しの確認用。

通信を伴う公開依存の実起動は、別途範囲を決めて実施する。プラグインやツールを自動導入するCIの追加は今回の対象外とする。

依存一覧作成時の確認結果：LSP23件の掲載、miseの対応定義16件、関連文書の相対リンク22件、Lua設定82ファイルの構文確認が成功した。Luaはloadfileでコンパイルするだけで、設定の実行はしていない。字数上限の配布元確認とgit diff --checkも成功した。依存一覧作成時は文書のみの変更のためmake checkを再実行していない。NV-01の検証結果は下記に追記する。

## NV-01の修正と回帰検証（2026-11-13）

修正前は取得結果を変数に保持せず、失敗時に未定義のoutを表示しようとしていた。初回のダミーテスト9件中8件が失敗し、取得失敗の理由が表示されないことと、途中のディレクトリへの対策不足を確認した。重複した再試行テストを同じ状態からの再試行へ置き換え、Git起動例外も追加した最終10件は成功した。

取得先は展開先と同じ親の一時ディレクトリとし、clone成功後にrenameする。Gitの失敗・起動例外・配置失敗では一時ディレクトリだけを後始末し、入力待ちをせず終了コード1を返す。後始末失敗時は一時パスを表示する。既存のlazy.nvimは変更せず、取得中に展開先が作られた場合も配置を中止する。

以前の処理で不完全なlazy.nvimがすでに残っている場合は、その内容を自動削除しない。利用者が退避と復旧を判断する必要がある。同時起動に対する確認はrename直前の存在確認であり、ロックによる排他制御ではない。

テストはLuaのvim・外部実行・ファイル操作・lazy.nvimをダミーにし、一時HOMEと空のPATHで実行する。実プラグインの取得・インストール・設定適用は行っていない。NV-02の新規依存定義はその後の明示承認に基づいて追加した。Mason関連設定は維持している。

NV-01修正後のmake checkは静的確認・unittest全198件・Bats全18件が成功し、skipはなかった。通信・実導入・Neovimの通常起動は引き続き未実施。

## NV-02の定義追加とVue連携（2026-11-13）

利用者の明示承認に基づき、次の5件をmiseのTOMLへ追加した。既存の同種ツールに合わせlatestを指定したが、実機で動く組合せの固定はNV-05に残す。定義の追加は実インストールの成功を意味しない。

| mise定義 | 提供元・実行名を確認した公式資料 |
| --- | --- |
| `npm:@vtsls/language-server` | [yioneko/vtslsのpackage.json](https://github.com/yioneko/vtsls/blob/main/packages/server/package.json)に`vtsls`のbin定義がある |
| `npm:@vue/language-server` | [Vue Language Toolsのpackage.json](https://github.com/vuejs/language-tools/blob/master/packages/language-server/package.json)に`vue-language-server`と`@vue/typescript-plugin`への依存定義がある |
| `npm:svelte-language-server` | [Svelte Language Toolsのpackage.json](https://github.com/sveltejs/language-tools/blob/master/packages/language-server/package.json)に`svelteserver`のbin定義がある |
| `npm:oxlint` | [Oxlint公式CLI](https://oxc.rs/docs/guide/usage/linter/cli)に`--lsp`があり、[nvim-lspconfigの設定](https://github.com/neovim/nvim-lspconfig/blob/master/lsp/oxlint.lua)がnpmのoxlintを案内する |
| `go:golang.org/x/tools/cmd/goimports` | [Go公式パッケージ資料](https://pkg.go.dev/golang.org/x/tools/cmd/goimports)で導入パスと整形・import更新の役割を確認した |

[Vue公式のNeovim案内](https://github.com/vuejs/language-tools/wiki/Neovim)と[nvim-lspconfigのvtsls設定例](https://github.com/neovim/nvim-lspconfig/blob/master/lsp/vtsls.lua)に従い、vtslsの対象filetypesへvueを追加し、globalPluginsへ`@vue/typescript-plugin`を登録した。Vueの依存に含まれるプラグインを使うため、別の直接依存は追加しない。vue_lsの要求転送はnvim-lspconfig側へ任せ、独自のon_initを重ねない。実機にあるnvim-lspconfigの版がこの連携に対応するかは別途確認する。

`after/lsp/vtsls.lua`はPATH上のvue-language-serverをrealpathで解決する。JavaScript本体へのリンクなら親パッケージを使い、aubeのnode_modules/.binランチャーなら隣接する@vue/language-serverのリンクを解決する。miseやMasonのインストール先を固定しない。package.jsonとサーバー本体を確認できなければ警告し、通常のTypeScript設定を返す。ランチャーや外部コマンドは実行せず、パッケージの自動導入も呼ばない。

miseのshimは実体へのシンボリックリンクとは限らないため、shimしか見えない場合はVue支援を設定できない。利用者はmiseでツールを準備し、実ツールのbinがPATHにあるシェルからNeovimを起動する。GUIや別の起動方法でも同じPATHを確認する。Masonが先にPATHへ追加されるとMason側を選ぶ可能性があるため、NV-03ではMasonなしの環境で再確認する。

SvelteとOxlintの独自cmdは追加せず、nvim-lspconfigの既存定義を使う。[Svelte設定](https://github.com/neovim/nvim-lspconfig/blob/master/lsp/svelte.lua)のプロジェクト内サーバー優先も維持する。JS/TSファイルからSvelteへの参照・リネーム等の追加連携や、Oxlintの型情報を使う診断に必要な依存は今回追加していない。プロジェクト別に必要性を判断する。

NodeとTypeScriptは既存のmise定義を維持した。閲覧したSvelteとVueのpackage.jsonにはTypeScriptのpeerDependenciesがあるため、実導入時は採用版との整合も確認する。TermuxにはこのUbuntu用mise設定を展開しない方針を維持する。特にOxlintのネイティブ配布物や各バックエンドのAndroid対応は未確認で、自動導入に対応済みとはしない。

`tests/test_neovim_lsp.py`はTOMLの導入定義、対象LSPの登録、Go整形の選択、Vueの実体解決をダミーで検証する。空白を含むパス、shim、実行ファイルの欠落、realpathの失敗、package.jsonの欠落を含む8件が成功した。通常設定の実起動やサーバーとの接続は行っていない。

NV-02修正後のmake checkはunittest全206件・Bats全18件が成功し、skipなし。新規LuaのStyLua確認と差分確認も成功した。採用版の固定、実インストール、実際のLSP接続はこの結果に含まない。

### 利用者が行う実機確認

設定と5件のツールを別途準備した後、新しいシェルで次を実行し、すべての名前にパスが表示されることを確認する。Termux本体はUbuntu用mise一覧の対象外なので、その環境の導入方法を先に決める。

```shell
command -v vtsls vue-language-server svelteserver oxlint goimports
```

Neovimでも`:lua print(vim.fn.exepath('vue-language-server'))`と`:lua print(vim.fn.exepath('vtsls'))`を実行する。MasonがPATHへ追加された後の結果が、シェルの結果と異なる場合がある。Vueの配置場所に関する警告が出た場合は、実行ファイルの実体がPATHで選ばれる起動方法を確認する。

小さなVue・TypeScript・Svelteファイルを、それぞれ依存を用意した検証用プロジェクトで開く。LspInfoで接続を確認し、Vueではvue_lsとvtslsの両方が働き、TypeScript部分の診断・補完・定義ジャンプが使えることを確認する。Oxlintは設定を置いたプロジェクトで診断を、Goは検証用ファイルの保存でgoimportsの整形を確認する。Masonを使わない状態でも同じ結果になることを確認してからNV-03の完全削除へ進む。

## NV-03の検証モード（2026-11-13）

Masonを削除する前の比較用に`vim.g.dotfiles_use_mason`を追加した。未指定とtrueでは従来のMason関連依存とsetupを維持し、falseでは両方を使わない。LSPの有効化リストとnvim-lspconfig・補完連携は維持する。無効化時のlazy.nvim起動コマンドはLspInfoだけにし、LspInstall・LspUnInstallの起動トリガーを除く。

この切替は外部ツールをインストールせず、既存のMasonデータも削除しない。起動後の値変更や設定の再読み込みで切り替える用途には使わず、毎回新しいNeovimプロセスで比較する。すでにPATHへ入ったMasonのbinを取り除く処理は含まない。

`tests/test_neovim_lsp.py`に3モードの検証を追加した。修正前はMason無効化の1件が失敗し、修正後は関連11件が成功した。無効化時にMasonのrequireを試みると失敗するダミーを使い、Masonが存在しなくても同じ23件が登録されることを確認している。実プラグインの依存解決やサーバー起動の成功を示す結果ではない。

### 利用者が行う比較と復帰

通常設定の起動はプラグイン・パーサーの取得やビルドを伴う場合がある。以下は必要なツールと設定を別途準備した利用者向けの手順であり、Codexでは実行していない。

1. NV-01・NV-02・今回の切替を含む設定を内容確認の上で展開し、対象環境の方法で各ツールを準備する。今回の作業ではchezmoi適用・実インストールを行っていない。TermuxにUbuntu用mise一覧は展開しない。
2. 新しいシェルから起動する。Neovim内のターミナルからの起動では、元プロセスのMason入りPATHを継承する可能性がある。NV-02のcommand -vと各LSPの依存一覧を使い、実行パスがMason配下ではないことを確認する。
3. 検証用プロジェクトで次のコマンドを使う。

```shell
nvim --cmd 'lua vim.g.dotfiles_use_mason = false'
```

4. Neovim内で`:lua print(vim.g.dotfiles_use_mason)`がfalseであることを確認する。`:lua print(vim.fn.exepath('node'))`と各サーバーのexepathを確認し、Mason配下が選ばれていないことを記録する。Vueの配置場所に関する警告が出た場合はPATHを確認する。
5. 言語ごとにLspInfoで接続を確認し、診断・補完・定義ジャンプを試す。保存整形も検証用ファイルで確認する。Termux・proot・WSL・ネイティブLinuxを一括で成功扱いにせず、環境とツールの版、成功・失敗・未確認を記録する。実行ファイルの存在確認だけでは移行完了にしない。
6. 問題があればNeovimを終了し、上記の--cmdを付けずに新しく起動すると既定のMason構成へ戻る。無効化時にはMasonのデータを消さないため、復帰のための再インストールはこの切替からは要求しない。既存データ自体に問題がある場合の修復は別途判断する。

実機結果がそろうまではNV-03を対応中とし、Masonの完全削除、旧設定整理、版固定は続くタスクに残す。

NV-03の切替追加後のmake checkはunittest全209件・Bats全18件が成功し、skipなし。通常起動・実導入・実接続・設定適用は未実施。

## Svelteのaube依存解決失敗と復旧（2026-11-13）

利用者のmise 2026.10.25・Linux ARM64のログでは、vtsls・Vue・Oxlint・goimportsは導入に成功し、Svelte Language Server 0.18.6だけが`aube install failed: failed to resolve dependencies`で失敗した。chezmoiのmise導入スクリプトが終了コード1で停止したことは、部分失敗を成功扱いしない既存の動作である。goimportsの最初の3秒タイムアウトは、その後の導入成功と分けて記録する。

利用者の明示承認後、Codexは次のコマンドでSvelteだけを再試行し、導入に成功した。miseによる管理とソースのlatest指定は維持し、再試行だけをログと同じ0.18.6へ限定した。他のツールの再インストール、mise本体の更新、chezmoi applyは実行していない。

```shell
MISE_NPM_PACKAGE_MANAGER=npm \
  mise --cd "$HOME" install npm:svelte-language-server@0.18.6
```

この環境変数は当該コマンドだけに適用する。[mise v2026.10.25の設定定義](https://github.com/jdx/mise/blob/v2026.10.25/settings.toml#L2372-L2389)でnpmの選択と環境変数名を確認した。既存の全npmツールに影響する`npm.package_manager`の恒久設定は追加していない。今後の新規環境でも同じ失敗が発生した場合は、対象版を記録してこの単体再試行を使う。npmで導入できた理由がaubeの不具合によるものかは、詳細ログがないため未確定。

npmの出力には、svelte-language-serverがSvelte 4を依存に持つ一方、別名のprettier-plugin-svelte4がSvelte 5をpeer dependencyとして要求する警告が出た。npmは警告を表示して55パッケージの導入を完了した。元のaubeエラーには依存名の詳細がないため、この不整合がその失敗原因だったかは未確定。強制フラグ、peer dependencyを無視する設定、信頼ポリシーの例外は追加していない。

実導入後は一時HOME・一時プロジェクトと限定した環境変数でsvelteserverを起動し、LSPのinitialize、検証用App.svelteの整形応答（編集1件）、shutdown・exit（終了コード0）を確認した。実際の個人プロジェクト、秘密情報、Mason、Neovimの通常設定は使っていない。Vue・TypeScript連携、Svelte全機能、各環境の動作を確認した結果ではない。

この導入結果を確認してもNV-03のMason完全削除は未実施のままとする。利用者は引き続きMason無効化モードで各言語の実行パスと接続を確認する。

導入後の`mise --cd "$HOME" ls --missing --no-header npm:svelte-language-server`は終了コード0・出力なしで、通常設定でも未導入扱いにならないことを確認した。関連するLSP回帰テスト11件とgit diff --checkも成功した。今回の追加変更は文書のみで、make check全体は直前の209件・Bats18件成功の結果を参照し、再実行していない。

## Vueのaubeランチャー探索修正（2026-11-14）

利用者からMason無効化モードでもVueの警告が出る報告があった。読み取り確認ではPATHがmiseのVueパッケージを選んでいたが、node_modules/.bin/vue-language-serverはシンボリックリンクではなく、aubeが生成したシェルランチャーだった。従来の探索はrealpathがbin/vue-language-server.jsで終わることを要求しており、この正常な導入形式を見つけられなかった。以前のMasonやPATHを原因とする説明は、この形式を確認する前の推測だった。

node_modules/.bin形式では、隣接するnode_modules/@vue/language-serverのリンクを解決してパッケージを探すよう修正した。JavaScript本体へのリンク形式も維持し、package.jsonとbin/vue-language-server.jsがファイルとして存在することを確認する。シェルランチャーの内容は解析・実行しない。miseの汎用shimはパッケージの配置が異なるため、aubeの.bin形式と区別する。

`tests/test_neovim_lsp.py`へaube形式、manifest欠落、サーバー本体欠落、パッケージのリンク切れを追加した。修正前は関連15件中aube形式の1件だけが失敗し、修正後は15件すべて成功した。空白を含むパスとpeer dependencyによる格納ディレクトリの違いもダミーで確認する。

実導入済みVue Language Server 3.3.14についても、一時HOME・限定PATHのNeovimを-u NONE・--noplugin・-i NONEで起動し、ソースの探索処理だけを評価した。警告なしで@vue/language-serverのパッケージを特定できた。通常のNeovim設定、Mason、Vueサーバー本体は実行しておらず、この時点ではVueファイルの補完・診断・定義ジャンプは未確認だった。その後の利用者による確認と、Vue依存追加後の再検証は[実機確認記録](../testing/neovim-lsp-verification.md)へ記録した。

利用者は修正したafter/lsp/vtsls.luaのソースを確認して別途展開し、新しいNeovimプロセスをMason無効化モードで起動する。この不具合に対するPATH変更や再インストールは不要。Mason削除の判断は、警告の消失だけでなく各言語の接続・操作結果から行う。

探索修正後のmake checkは静的確認・unittest全213件・Bats全18件が成功し、skipなし。新規LuaのStyLua確認とgit diff --checkも成功した。実環境へのchezmoi適用・再インストール・コミットは行っていない。

## 継続する実機確認

Vueの利用者確認と、2026-11-14の7サーバー・5整形CLIの隔離検証、登録中23サーバーのPATH確認は[専用記録](../testing/neovim-lsp-verification.md)を参照する。Masonの完全削除には、Pythonの提供元と残る言語・通常UIの確認が必要。Rustの接続・補完・定義ジャンプ・診断は利用者が確認した。Nimは利用者のPATH追加後に配布URLの404が判明し、公式2.4.2のURL・SHA256へ固定した。[更新方針と導入手順](tool-version-policy.md)を参照する。利用者の共通env.shの未コミット変更は保持し、今回書き換えていない。

## Luaプラグインの開発用テスト

通常導入のvusetedはvustedの誤記だった。将来の開発用途はmini.testへ切り替え、LuaRocksの必須導入から外した。既存のeditor/mini-test.luaのotsをoptsへ修正し、v0.18.0のrevisionへ固定した。開発プロジェクトでは依存を個別に管理し、[最小構成の手順と検証結果](../testing/neovim-plugin-tests.md)を使う。luacheckのLuaRocks導入と既存のdotfilesテストは維持する。

利用者による最新の実機報告では、Nimの導入とmini.testの初期化が成功した。Rustの接続・補完・定義ジャンプ・診断は成功した。Nimは接続・補完・定義ジャンプが成功したが、ビルド時バージョン不一致が表示され、診断は失敗した。[実機確認記録](../testing/neovim-lsp-verification.md#利用者による実機確認の追記)と[次の確認手順](../testing/neovim-nim-rust.md)を参照する。

NimLSPは承認後にNim 2.4.2で再ビルドし、退避して実体を切り替えた。隔離検証で診断の検出・解消と定義ジャンプが成功し、版警告は出なかった。利用者がPATH明示の起動で保存時の診断5件、フロート表示、修正・保存後の診断解消を確認した。通常起動時のPATH確認とハイライトは残件。[復旧手順](nimlsp-recovery.md)を参照する。

Nimの起動とハイライトはソース修正済み。PATH上のnimlspを優先し、NIMBLE_DIRまたは既定のNimble配置を補助探索する。Tree-sitterはnimと、その必須依存nim_format_stringを既存の導入方式で準備する。隔離検証は成功し、[実環境への適用と通常UIの確認](../testing/neovim-nim-rust.md#pathの補助探索とハイライトの適用)は利用者が行う。

Nimのハイライトは利用者が通常起動で適用を確認した。NIMBLE_DIRとPATH設定は共通env.shのソースにも反映済み。その後、利用者がPATHを明示しない通常起動でNimLSP接続・保存時の診断5件・フロート表示・修正後の診断解消も確認した。Nim対応は完了。次はPythonの提供元と未確認言語の整理へ進む。
