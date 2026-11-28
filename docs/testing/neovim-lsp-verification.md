# MasonなしのNeovim検証記録

2026-11-14、NV-03のMason削除を判断するため、当時のLinux aarch64環境で導入済みツールを確認した。主力7サーバーの隔離検証は成功したが、この時点では未確認言語の整理が残り、Masonの完全削除を保留していた。

過去の隔離検証時には環境の分類を記録していなかった。その後、利用者のNim・Rust手動確認はTermux + proot Ubuntu、Neovim v0.12.6で実施したと報告された。他の環境で同じ結果になるとは扱わない。設定一覧と作業項目は[Neovim依存一覧](../setup/neovim-dependencies.md)を参照する。

現在は管理ソースからMason依存を除去し、利用者による適用後の通常起動確認も完了した。以下の切替付き起動は過去の検証記録であり、現在の操作には切替を付けない。[最新の適用と確認手順](../setup/neovim-dependencies.md#利用者による適用と通常起動の確認)を参照する。

## Vueの確認結果

利用者から、Mason無効化モードで以下の成功報告があった。

- App.vueでprofileの補完とcreateGreetingからの定義ジャンプ。
- Diagnostics.vueで意図的な型エラー2件の検出と、修正後の解消。
- profile.tsで型定義と定義ジャンプ。
- vue_lsのon_initにnvim-lspconfigの定義を使用し、vtslsがmise管理下の実行パスを使用。
- aubeランチャー探索修正後、Vueパッケージの警告が解消。

その後のProfile.value診断は、作成した検証用プロジェクトにVue本体の依存がなかったことが原因だった。明示承認後、検証用プロジェクトだけにVue 3.5.45を追加した。Codexは実vtslsで修正済み2ファイルの診断0件と、保存しないバッファ内で意図的な型エラー2件の再検出を確認し、利用者も警告の解消を確認した。

LSP実行ファイルの導入と、プロジェクトが必要とするVue等の依存は別に準備する。今後の検証用プロジェクトでも、この区別を維持する。

## 今回の隔離検証

一時HOME・一時プロジェクトと限定PATHで、クリーンなNeovimから実サーバーを起動した。Masonは読み込まず、PATHにも追加していない。導入済みnvim-lspconfigの既定定義と、管理ソースのafter/lsp設定を使用した。root_dirは検証用フォルダへ明示しているため、自動ルート検出の成功までは含まない。

| 言語・役割 | サーバー | 初期化 | 期待した診断 | 検証用関数の補完・定義ジャンプ |
| --- | --- | --- | --- | --- |
| Lua | lua_ls 3.19.2 | 成功 | undefined-global | 両方成功 |
| Pythonの型・補完 | pyrightとして登録したbasedpyright 1.40.2 | 成功 | reportAssignmentType | 両方成功 |
| Pythonのlint | Ruff 0.17.5 | 成功 | F821 | lint担当のため対象外 |
| Go | gopls 0.24.0 | 成功 | IncompatibleAssign | 両方成功 |
| Bash | bash-language-server 5.8.1 | 成功 | SC2154 | 両方成功 |
| TypeScript | vtsls 0.3.0 | 成功 | TS2322 | 両方成功 |
| Svelte | svelte-language-server 0.18.6 | 成功 | TS2322 | 両方成功 |

通知だけでは診断を取得できなかったPython・Ruff・Svelteは、textDocument/diagnosticを明示的に要求して期待する診断を得た。vtslsではtypescript.tsserverRequestのsemanticDiagnosticsSyncを使用した。初期化や実行ファイルの存在だけで成功とは判断していない。

SvelteはLSPの整形要求でも編集を返した。他の整形は次の導入済みCLIへ標準入力を渡し、終了コード0・整形出力あり・入力からの変更ありを確認した。ファイルへは書き込んでいない。

| 設定と対応する用途 | 実行したCLI | 結果・範囲 |
| --- | --- | --- |
| Lua | stylua - | 成功 |
| Bash | shfmt | 成功。Zsh全構文の対応確認ではない |
| Go | goimports | 成功。標準ライブラリfmtだけを使う例 |
| Python | ruff format --isolated - | 成功 |
| Web整形の基礎確認 | prettier --parser typescript | 成功。Conformが呼ぶprettierd自体は未検証 |

GoはGOPROXY・GOSUMDBをoff、GOTOOLCHAINをlocalにし、telemetryとGOENV・GOWORKを無効化した。Goのキャッシュも一時領域へ分離した。TypeScriptの型定義自動取得とLuaの第三者ライブラリ確認を無効にし、パッケージの追加取得を前提にしない構成で検証した。

## 登録中23サーバーの実行パス

初回の確認では、通常のシェルから各コマンドの所在とrealpathを確認した。20件はMason外のツールを直接選び、rust-analyzerはmiseのshim、2件はコマンドがPATH上に見つからなかった。以下は初回時点の記録で、「未検証」は未導入とは異なる。現在のPython・Nimの結果は後段、Webと汎用LSPの結果は[継続確認記録](neovim-web-validation.md)を参照する。

| サーバー | PATHで選ばれた提供元・状態 | 実接続・機能の確認状況 |
| --- | --- | --- |
| bashls | miseのnpm:bash-language-server | 上記で確認 |
| biome | グローバルコマンドなし。設定はプロジェクト内node_modules/.bin/biomeを指定 | プロジェクト依存と起動ディレクトリは未検証 |
| cssls | miseのnpm:vscode-langservers-extracted | 未検証 |
| denols | miseのdeno | 未検証。vtslsとのルート分岐も未検証 |
| emmet_language_server | miseのnpm:@olrtg/emmet-language-server | 未検証 |
| golangci_lint_ls | miseのgo:github.com/nametake/golangci-lint-langserver | 未検証 |
| gopls | miseのgo:golang.org/x/tools/gopls | 上記で確認 |
| html | miseのnpm:vscode-langservers-extracted | 未検証 |
| jsonls | miseのnpm:vscode-langservers-extracted | 未検証 |
| lua_ls | miseのlua-language-server | 上記で確認 |
| nimls | 初回はPATH不足。その後、利用者が~/.nimble/binを追加し、Nimの導入成功を報告 | 利用者が接続・補完・定義ジャンプ成功、診断失敗を報告 |
| oxlint | miseのnpm:oxlint | 未検証 |
| marksman | miseのmarksman | 未検証 |
| pyright | pyright-langserverの実体がmiseのnpm:basedpyright管理下 | 上記で確認。npm:pyright 1.1.414も導入済みで選択は別途整理 |
| ruff | miseのruff | 上記で確認 |
| rust_analyzer | miseのshimが選ばれる。Rustupの導入済みcomponentと実バイナリを追加確認 | --versionは成功。その後、利用者が接続・補完・定義ジャンプ・診断成功を報告 |
| sqls | miseのgo:github.com/sqls-server/sqls | 未検証。DB接続を含む確認は別途範囲を決める |
| svelte | miseのnpm:svelte-language-server | 上記で確認 |
| tailwindcss | miseのnpm:@tailwindcss/language-server | 未検証 |
| taplo | miseのtaplo | 未検証 |
| vtsls | miseのnpm:@vtsls/language-server | 上記と利用者のVue確認 |
| vue_ls | miseのnpm:@vue/language-server | 利用者のVue確認 |
| yamlls | miseのnpm:yaml-language-server | 未検証 |

上表のPATH確認後、利用者が共通env.shへ~/.nimble/binを追加した。続くNim更新でLinux ARM64の配布URLが404になったため、公式配布物のある2.4.2へ取得定義を固定した。Nimだけの導入手順と更新方針は[バージョン方針](../setup/tool-version-policy.md)を参照する。利用者からchezmoi applyと導入スクリプトによるNim導入成功の報告があった。その後、利用者がnimlspの接続・補完・定義ジャンプを確認したが、診断は失敗し、Nimとのビルド時バージョン不一致が表示された。

Rustupの自動導入と更新確認を抑止してローカル一覧を確認し、active toolchainのrust-analyzer componentが導入済みであることを確認した。rustup whichで得た実バイナリの--versionも成功した（rust-analyzer 1.100.0 (0ef1bc3 2026-11-09)）。この時点では接続やRustプロジェクトの解析を確認していなかった。その後、下記の利用者報告で接続と各機能の成功を確認した。

Pythonは同じpyright-langserver名が複数ツールから提供される状態である。今回確認できた診断・補完はbasedpyrightによる結果で、upstreamのPyrightを検証済みとは扱わない。どちらを主に使うか決めてから設定名・導入一覧・PATHを整理する。

## NV-03の残件と推奨順序

Nim・Rustの接続と診断の確認は完了。NimはPATHを明示しない通常起動でハイライトと保存時の診断・解消まで利用者が確認した。残件は次の順で進める。

1. 未確認言語のうち実際に使用する対象を決め、プロジェクト依存を用意して確認する。未使用の設定を削除・無効化する場合も別途判断する。
2. 未確認言語のUIと整形、Biomeのルート分岐を確認する。prettierdの明示整形とDenoのLSPによる保存時整形は、下記の利用者報告で確認済み。
3. 対象環境ごとの未確認事項を記録した上で、Mason本体・連携プラグイン・setup・検証用切替の削除へ進む。既存のMasonインストール済みデータは自動削除しない。

Codexによる隔離検証では、chezmoi apply、ツールの導入・更新、Mason削除、実プロジェクトへの適用、Gitのcommit・pushは行っていない。利用者が実施した適用と導入の報告は下記に分けて記録する。現在の実機結果は単一ホストの記録として扱い、CIのmake checkとは分ける。

## 通常UIでの手動確認

自動検証と同じ最小ファイルを一時フォルダへ用意した。各言語フォルダをカレントディレクトリにし、新しいプロセスを`nvim --cmd 'lua vim.g.dotfiles_use_mason = false' <対象ファイル>`で起動する。これは利用者向け手順であり、Codexは通常設定を起動していない。

1. LspInfoで対象サーバーを確認し、exepathでMason配下を使っていないことを確認する。
2. greet（Bashではsay_hi）の呼び出し位置で補完・定義ジャンプを試す。Ruffはlint担当なのでこの操作の対象外とする。
3. 診断表の意図的なエラーが表示されることを確認し、型や未定義変数を修正して解消することを確認する。
4. 保存時にConformが対象の整形ツールを使うことを確認する。Lua・Python・Go・Bashに加え、Webはprettierd、DenoはLSP fallbackを分けて試す。確認用ファイルに対して行い、実プロジェクトには適用しない。
5. 環境名と使用したツール、成功・失敗・未確認を記録する。一時フォルダは再起動等で消えることがあるため、継続確認に使う場合は利用者が保管する。

今回の変更はこの記録と既存文書の更新のみ。関連unittestのtest_neovim_lsp.py全15件と相対リンク・差分の確認を行い、コード変更のないmake check全体の再実行は省略した。

## 利用者による実機確認の追記

次は利用者からの報告であり、Codexによる再実行結果ではない。

| 対象 | 利用者が確認した結果 | 残る確認 |
| --- | --- | --- |
| Nim | PATHを明示しない通常起動で接続・ハイライト、保存時の診断5件、フロート表示、修正・保存後の診断解消を確認 | 今回の対応は完了。他環境は別途確認 |
| Rust | 接続・補完・定義ジャンプ・型エラー検出・修正後の診断解消が成功 | 今回の報告にはshimの実行パスのみ記載。他環境での確認は別途行う |
| mini.test | chezmoi apply後、Luaファイルで:lua print(type(MiniTest))がtableになった | この報告は初期化の確認。通常UIでのプラグインテスト実行と他環境の確認は別途行う |
| 主力LSP | 確認対象のサーバーがMason配下を使っていないこと、補完と意図的な診断の解消を確認 | Pythonの提供元の統一、未確認言語 |
| Bash・Goの定義ジャンプ | :lua vim.lsp.buf.definition()で宣言位置へ移動。Goはamount := "wrong"への変更でST1023も解消 | 型定義ジャンプとは区別して記録 |
| prettierd | vtsls/main.tsのConformInfoで利用可能と表示。formatterをprettierd、lsp_formatをneverに指定した明示整形が成功 | 他のプロジェクト・環境の確認 |
| Deno | 別フォルダのdeno.jsonを認識してdenolsが接続。外部formatterを選ばず、保存時にLSPで整形 | 他のプロジェクト・環境の確認 |

Rustの手動確認は成功した。Nimの診断確認も成功した。未確認言語の整理が残るため、Masonの完全削除は保留する。確認用ファイルの準備は[Nim・Rustの手順](neovim-nim-rust.md)を参照する。

## Nim・Rustの手動確認結果（2026-11-14）

利用者が/tmp/neovim-nim-rust-check-sfy8nj62/RESULTS.mdへ記入した結果を転記した。環境はTermux + proot Ubuntu、Neovimはv0.12.6。Codexは今回LSPを再実行していない。

| 言語 | 報告された実行パス | 接続先のルート | 補完 | 定義ジャンプ | 型エラー検出 | 修正後の診断解消 |
| --- | --- | --- | --- | --- | --- | --- |
| Nim | /home/shioyaki/.nimble/bin/nimlsp | 確認用nim/ | 成功 | 成功 | 失敗 | 失敗 |
| Rust | /home/shioyaki/.local/share/mise/shims/rust-analyzer | 確認用rust/ | 成功 | 成功 | 成功 | 成功 |

Nimではファイルを開いた直後に、次の警告が表示された。

```text
LSP[nimls] Current Nim version does not match the one NimLSP is built against 2.4.2 != 2.2.12
```

利用者の報告では、nimsuggestは/home/shioyaki/.local/share/mise/installs/nim/2.4.2/bin/nimsuggestを使用していた。NimLSPのビルド時バージョンとの不一致はログで確認できる。ただし、診断が表示されない原因をこの警告だけで確定しない。現在の導入スクリプトはnimbleの一覧にnimlspがあれば導入を省略し、Nim更新後の再ビルドを判定していない。次はNim 2.4.2に対応するビルド方法を確認し、再ビルド後に同じファイルで診断を再検証する。実再導入は今回行っていない。

シンタックスハイライトも表示されなかったと報告された。管理対象のnvim-treesitterの導入言語一覧にはNimがない。実際のfiletype、syntax、パーサーの有無は今回確認していないため、ハイライト不適用の原因は未確定。LSP診断の失敗とは分けて調べる。

## NimLSP再ビルド後の確認

利用者の承認後、導入済みのNimLSP 0.4.7と依存の公開ソースを使い、Nim 2.4.2で一時ビルドした。版表示はbuilt for Nim version 2.4.2。既存バイナリを退避し、シンボリックリンクを保持して実体を切り替えた。切替前の候補と切替後の実バイナリで、隔離HOMEの型エラー2件、修正後の診断0件、greetings.nimへの定義ジャンプ、版不一致警告なしを確認した。既存の利用者確認用ファイルとRESULTS.mdは変更していない。

通常導入ではNimとのビルド時版の一致を確認するよう修正し、不一致を正常な導入済み状態として扱わない。再ビルドと切替は通常適用から自動実行しない。[再ビルドと復元の手順](../setup/nimlsp-recovery.md)を参照する。その後、利用者が通常UIで診断の検出と修正後の解消を確認した。Nimの通常起動時のPATH確認とハイライトは残件。

## Nimの通常UIでの診断確認

利用者から次の成功報告があった。PATHへ~/.nimble/binを明示して起動したNeovimでの結果として記録する。

- filetypeはnim。
- :wで診断内容と件数が表示された。
- vim.diagnostic.get(0)の件数は5。
- vim.diagnostic.open_float()でカーソル位置の診断が表示された。
- 型エラーを修正して保存すると診断が解消した。

NimLSPの診断は保存通知を契機とするため、ファイルを開いただけで0件でも診断失敗とは扱わない。再ビルド後の診断復旧は実機で確認済みとする。一方、PATHを明示しない起動ではnimlspの検索に失敗しており、その起動方法の修正・再確認は残る。シンタックスハイライトも未適用のまま。いずれも診断復旧とは分けて扱う。

## PATH補助探索・ハイライトのソース修正

nimls.luaへ既定のNimble配置とNIMBLE_DIRの補助探索を追加し、Tree-sitterの導入一覧へnimを追加した。PATHにNimbleがない隔離環境でも実LSPの起動と診断が成功した。nim_format_stringを含むパーサーも一時領域でビルドし、再起動後にハイライト24箇所を確認した。[適用と確認の手順](neovim-nim-rust.md#pathの補助探索とハイライトの適用)を参照する。実環境への適用と通常UIの確認は利用者が行う。

## 通常起動でのNimハイライト確認

利用者が共通env.shへNIMBLE_DIRとPATH設定を追加し、通常のNeovim起動でNimのシンタックスハイライトが適用されたことを確認した。変数名は実ファイルでNIMBLE_DIRと記述され、管理ソースと展開先のenv.shも一致していた。続く利用者報告で、PATHを明示しない通常起動でもNimLSP接続、保存時の診断5件、フロート表示、修正・保存後の診断解消が成功した。今回のNim対応は完了とする。

## basedpyrightとRuffへの統一

利用者が担当分離案を採用したため、登録をpyrightからbasedpyrightへ切り替え、正式な起動名・設定を使用するよう修正した。既存のbasedpyright 1.40.2とRuff 0.17.5で隔離検証し、型診断・補完・定義ジャンプ、lint、Conformによる修正・import整理・整形を確認した。バッファ内の型エラー等を直すと両者の診断が0件になった。プロジェクト側の設定がLSPのstandardを上書きすることも確認した。

自動回帰テスト6件を追加し、既存の3モードでの登録確認もbasedpyrightへ更新した。make checkはunittest 238件・Bats 18件が成功、skipなし。実環境への適用、実パッケージの導入・更新・削除は行っていない。[Python移行手順](../setup/python-lsp.md)に沿った通常UIでの確認は利用者が行う。過去のpyright名でのbasedpyright確認と区別して記録する。

## Python移行の通常UI確認（報告受領：2026-11-15）

利用者が/tmp/neovim-python-check-y_fbpsjc/RESULTS.mdに記入した結果を記録する。環境はTermux + proot Ubuntu、Neovim版は利用者の訂正によりv0.12.6。Codexによる再実行結果ではない。

| 確認項目 | 利用者の結果 |
| --- | --- |
| basedpyright・Ruffへの接続 | 成功 |
| 補完・定義ジャンプ | 成功 |
| 型エラー・Ruffのlintと修正後の解消 | 成功 |
| 保存時整形・import整理 | 成功 |

報告されたパスは、basedpyrightが/home/shioyaki/.local/share/mise/installs/npm-basedpyright/latest/node_modules/.bin/basedpyright、Ruffが/home/shioyaki/.local/share/mise/installs/ruff/latest/.mise-bins/ruff。前者はCLI名のため、実サーバーの起動コマンドbasedpyright-langserver --stdioとは区別して記録する。今回の結果にはサーバー用実行ファイルのパスそのものは記載されていない。

Pythonの担当分離と通常UIでの機能確認は完了。NV-03全体は未確認言語・Biome等の分岐・対象環境の整理を続けてからMason削除を判断する。既存のMasonデータは変更しない。

## Webと汎用LSPの継続確認（2026-11-15）

CSS・HTML・JSON・YAML・TOML・Markdownの6サーバーについて、隔離HOMEとダミープロジェクトで接続・機能を確認した。Deno・Nodeの選択とBiomeの起動設定を修正し、回帰テスト8件を追加した。[結果・確認範囲・残件](neovim-web-validation.md)を参照する。Masonの完全削除は未実施。

通常UIの追加報告では主要な操作の成功がある一方、Node配下での二重接続とBiomeの起動失敗が報告された。展開済み設定が修正前であることを確認したため、[適用状態と再確認手順](neovim-web-validation.md#通常uiの報告と適用状態の確認2026-11-15)に記録した。修正後の分岐とBiome接続の確認は継続する。

利用者が設定適用後、Node配下ではvtslsのみ接続し、Biome LSPもフォルダ内・別cwdの両方で接続することを確認した。ConformInfoの表示に加え、利用者がlist_formatters_to_run(0)の出力が`{ "biome-check" }`となることを確認した。stop_after_firstにより、実行予定はbiome-checkのみである。[再確認結果](neovim-web-validation.md#設定適用後の再確認結果2026-11-15)を参照する。NV-03全体とMason削除の判断は継続する。

## 追加5サーバーの継続確認（2026-11-15）

Emmet・Tailwind・Oxlint・golangci-lint・sqlsを隔離検証した。Emmetの補完、Oxlintとgolangci-lintの診断・修正後の解消が成功した。Tailwindは依存不足による部分確認、sqlsはDB接続なしの初期化だけである。[用途・結果・残件](neovim-extra-lsp-validation.md)を参照する。通常設定の自動root選択とUIは今回の検証対象ではない。

利用者の通常UI確認では、追加5サーバーすべての継続使用が選択された。Emmetの補完、Oxlintとgolangci-lintの診断・修正後解消、sqlsのDB接続なしの初期化が成功した。Tailwindは接続NGで、起動ログを含む追加確認が残る。[手動結果と次の確認](neovim-extra-lsp-validation.md#通常uiの手動確認結果2026-11-15)を参照する。

Tailwindについて、承認された検証用依存3.4.17の解決、自動接続・診断と解消・標準クラスと独自色の補完が隔離環境で成功した。[通常起動の再確認手順](neovim-tailwind-validation.md)を用意した。利用者が報告した接続NGは再現できておらず、通常UIの成功確認とは区別する。

Tailwindの通常UI再確認も成功した。利用者がMason無効化モードでmise管理のサーバーへの接続、期待するroot、標準クラスと独自色の補完、競合診断と修正・保存後の解消を確認した。[結果の詳細](neovim-tailwind-validation.md#通常uiの手動確認結果2026-11-15)を参照する。検証用v3構成の確認は完了し、Mason削除の範囲とsqlsのDB機能・未確認環境の扱いを整理する。

## Mason依存除去後の隔離検証（2026-11-15）

管理ソースの依存宣言・setup・切替参照と旧_index.luaのMason宣言を除去した。更新したLSP関連テスト23件、make checkのunittest 247件・Bats 18件が成功し、skipなし。実NeovimでもMasonを読み込まず23サーバーを有効化し、LspInfoを登録できた。外部サーバー起動を禁止した隔離スモーク確認で、通常起動の全機能確認ではない。適用後は切替指定を付けず、利用する言語の接続・補完・保存時整形を再確認する。既存MasonデータやSQLの接続情報は変更していない。

Mason除去後の通常起動確認として、利用者が各LSPと補完・診断・保存時整形の動作を報告したが、package.loaded["mason"]はtrueだった。展開済みのLSP設定3件にはMason宣言・初期化が残り、ソースと不一致だった。新しい設定の適用と新規プロセスでの確認を残し、NV-03は未完了とする。[展開状態と再確認](../setup/neovim-dependencies.md#通常起動の報告と展開状態2026-11-15)を参照する。

## Mason除去後の通常起動確認完了（2026-11-15）

利用者が各確認用プロジェクトで次の結果を報告した。

| 項目 | 利用者の結果 |
| --- | --- |
| LspInfoの接続 | 成功 |
| 実行パス・root | Mason除去前と同じ |
| 補完・診断・保存時整形 | Mason除去前と同様に機能 |
| package.loaded["mason"]の判定 | false |

読み取り比較でも、展開済みのLSP設定3件が管理ソースと一致した。Mason除去後の通常起動確認は完了とする。NV-03は確認済み環境・用途の範囲で完了し、sqlsのDB機能や未確認環境へ結果を一般化しない。今回の報告に伴うコード変更はなく、全体テストは既存の成功結果を再利用した。
