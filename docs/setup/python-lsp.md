# Pythonの型解析とRuffのlint・整形を分担する

型解析・補完・定義ジャンプ・hoverはbasedpyright、lint・import整理・整形はRuffが担当する。導入済みのbasedpyright 1.40.2とRuff 0.17.5で隔離検証した。今回の環境では追加インストールは不要で、実設定への適用やパッケージの更新・削除は行っていない。

## 起動と設定を一本化する

登録名はbasedpyright、起動はbasedpyright-langserver --stdioとする。miseのnpm:basedpyrightとruffを維持し、npm:pyrightの重複定義を除外した。既存のpyrightパッケージやMasonのデータを削除する操作は行わない。

設定はhome/dot_config/nvim/after/lsp/basedpyright.luaで管理する。analysisは正式なbasedpyright.analysisへ移し、openFilesOnlyを維持する。移行時の既定値はstandard。pyproject.tomlやpyrightconfig.jsonの設定があれば、プロジェクト側を優先する。useLibraryCodeForTypesは標準値を使うため、LSP側では明示しない。[公式LSP設定](https://docs.basedpyright.com/latest/configuration/language-server-settings/)

プロジェクトごとに診断方針を共有する場合は、次をそのプロジェクトのpyproject.tomlへ記述する。CLIとエディターの厳しさを揃えるためにも、プロジェクトでの明示を推奨する。実プロジェクトへは今回追加していない。[公式の設定優先順位](https://docs.basedpyright.com/latest/configuration/config-files/#overriding-language-server-settings)

```toml
[tool.basedpyright]
typeCheckingMode = "standard"
```

既存のtool.pyright設定も互換用として認識される。recommendedやstrictへの変更は、各プロジェクトの診断差分を確認してから判断する。

## Ruffと既存コマンドの担当

basedpyrightのOrganize Importsを無効にし、Ruffのhoverを無効にする。Ruffのlintとcode action、basedpyrightの型解析等は維持する。[basedpyrightの設定](https://docs.basedpyright.com/latest/configuration/language-server-settings/)、[RuffのNeovim連携](https://docs.astral.sh/ruff/editors/setup/#neovim)

保存時は既存のConformを使い、ruff_fix、ruff_organize_imports、ruff_formatの順で処理する。import整理や修正後のコードを最後に整形するため、従来の順序を変更した。追加の整形ツールは導入しない。

| コマンド | 担当・用途 |
| --- | --- |
| LspBasedpyrightSetPythonPath | 接続中のbasedpyrightへPythonの実行パスを通知する |
| LspPyrightSetPythonPath | 上記の互換名。既存の操作を維持する |
| LspRuffOrganizeImports | Conformのruff_organize_importsで現在のバッファを処理する |
| LspPyrightOrganizeImports | Ruffによるimport整理の互換名。Ruffが接続したバッファで使用する |

未定義名などは型解析とlintの両方で報告される場合がある。診断元を確認して判断し、重複を避けるために型診断全体を無効にはしない。

## 利用者が適用して確認する

導入先の設定を直接編集せず、次の管理対象だけを適用する。これは利用者向け手順で、Codexは今回実行していない。

```shell
chezmoi apply --exclude=scripts \
  "$HOME/.config/mise/config.toml" \
  "$HOME/.config/nvim/after/lsp/basedpyright.lua" \
  "$HOME/.config/nvim/after/lsp/ruff.lua" \
  "$HOME/.config/nvim/lua/plugins/lsp/server-register.lua" \
  "$HOME/.config/nvim/lua/plugins/lsp/conform.lua"
```

旧pyright.luaが展開先に残っていても、新しい登録リストはpyrightを有効化しない。既存ファイルを無断で削除せず、Neovimを再起動し、接続中のサーバーがbasedpyrightとRuffであることを確認する。

今回作成した一時確認用プロジェクトのproject/をカレントディレクトリにし、新しいNeovimでmain.pyを開く。場所は作業完了時の案内を参照する。一時領域は再起動等で消える場合がある。

```shell
nvim --cmd 'lua vim.g.dotfiles_use_mason = false' main.py
```

1. LspInfoでbasedpyrightとRuffの接続を確認し、exepathでbasedpyright-langserverとruffがMason外を指すことを確認する。
2. greetの補完・定義ジャンプでgreetings.pyへ移動できることを確認する。
3. messageの型不一致と未定義名の診断を確認する。message: strとし、missing_nameを文字列へ修正して保存し、診断の解消を確認する。
4. ConformInfoでRuffの3処理を確認し、保存時の整形と不要なimportの除去を確認する。LspRuffOrganizeImportsと既存の互換コマンドも必要に応じて試す。
5. 確認用ディレクトリのRESULTS.mdへ、環境・実行パス・成功・失敗・未確認を記録する。

## Codexで確認した範囲

一時HOME・限定PATH・専用プロジェクトを使い、通常設定・Mason・lazy.nvimを読み込まずに実サーバーを起動した。basedpyrightの型診断、greetの補完と定義ジャンプ、RuffのF401・F821を確認した。Conformを通じた修正・import整理・整形が成功し、バッファ内で型エラー等を直した後は両サーバーの診断が0件になった。確認用main.pyは元のエラーを含む状態で保存してある。

別の一時プロジェクトでは、LSP側のstandardよりプロジェクトのoff設定が優先されることを確認した。主機能の検証ではroot_dirを明示した。別途、導入済みnvim-lspconfigと変更したafter設定を使い、pyproject.tomlから両サーバーのルートを自動検出して起動できることも確認した。その後、利用者が通常UIで保存時整形とimport整理の成功を確認した。

自動回帰テストは実ツールを使わず、登録、起動コマンド、設定、空白を含むPythonパス変更、互換コマンド、Ruffのhover無効化、整形順序を検証する。Termux + proot Ubuntuの通常UIは利用者が確認済み。他環境は別途確認する。NV-03のMason完全削除はまだ実施しない。

make checkはunittest 238件・Bats 18件が成功し、skipなし。移行用の新規6件は修正前に失敗し、修正後に成功した。対象LuaのStyLua、TOML解析、git diff --checkも成功した。

## 利用者の通常UI確認

2026-11-15受領の結果では、Termux + proot Ubuntuで両サーバーの接続、補完・定義ジャンプ、型エラー・lintの修正後の解消、保存時整形・import整理がすべて成功した。Python移行の機能確認は完了。Neovim版は利用者の訂正によりv0.12.6。報告されたbasedpyrightのパスはCLI名であり、LSP用起動コマンドとは区別する。[実機確認記録](../testing/neovim-lsp-verification.md#python移行の通常ui確認報告受領2026-11-15)を参照する。
