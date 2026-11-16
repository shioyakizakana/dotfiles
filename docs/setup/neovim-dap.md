# NeovimのPython・Luaデバッグ

NV-04でDAPの登録・UIイベント・Python選択・キー操作を修正した。管理ソースはhome/dot_config/nvim/lua/plugins/dap/、導入定義はhome/dot_config/mise/config.tomlにある。Masonは使用しない。

## Pythonの導入担当と選択

Python用アダプターはdebugpy。ブレークポイント停止、ステップ実行、変数取得に使う。miseのpipx:debugpyで専用環境へ導入し、uvを使う場合もpipxを使う場合もアダプターのPythonは3.13を指定する。2026-11-15の実導入ではPython 3.13.18・debugpy 1.8.22を確認した。

debugpy-adapterをPATHから探して起動する。見つからなければ導入とPATHの確認を促すエラーを返し、起動時にパッケージを自動導入しない。対象プロジェクトの仮想環境へdebugpyを追加する必要はない。

デバッグ対象のPythonは、Neovimのカレントディレクトリを基準に次の順で選ぶ。既存のvenv優先順を維持した。

1. venv/bin/python
2. .venv/bin/python
3. PATHのpython3
4. PATHのpython

実行可能なPythonがなければエラーにする。空白を含むパスにも対応し、固定したmiseのインストール先やMasonのパスへ依存しない。basedpyright用のPythonパス変更コマンドと、DAPの対象Python選択は別の設定である。

debugpyの初期化警告までの猶予は20秒。今回の初回実接続でnvim-dap既定の4秒を超えたため、このアダプターに限って調整した。

## LuaとUI

Luaは既存のone-small-step-for-vimkind（OSV）へ接続する。既定の接続先は127.0.0.1:8086で、接続設定のhost・portで変更できる。

DAP UIはセッションのevent_initialized後に開く。Luaのnlua接続時には自動表示せず、必要ならF7で開く。同じ設定を再読み込みしてもリスナーを重複登録しない。セッション終了後のUI開閉は利用者が操作する。

| キー | 操作 | コマンドによる代替 |
| --- | --- | --- |
| F5 | 開始・続行 | :lua require("dap").continue() |
| F10 | ステップオーバー | :lua require("dap").step_over() |
| F11 | ステップイン | :lua require("dap").step_into() |
| F12 | ステップアウト | :lua require("dap").step_out() |
| leader + b | ブレークポイント切替 | :lua require("dap").toggle_breakpoint() |
| leader + B | 条件付きブレークポイント | キー操作で条件を入力 |
| leader + dL | ログポイント | キー操作でメッセージを入力 |
| leader + dr | REPL | :lua require("dap").repl.open() |
| F7 | DAP UI切替 | :lua require("dap-view").toggle() |

leaderは既存のNeovim設定に従う。Termux等で端末が関数キーを送れない場合は、右列のコマンドで同じDAP操作を確認する。

## 利用者による適用

対象を確認後、設定だけを適用する場合は次を使う。Codexはこの操作を行っていない。

```sh
chezmoi apply --exclude=scripts \
  "$HOME/.config/mise/config.toml" \
  "$HOME/.config/nvim/lua/plugins/dap/adapters.lua" \
  "$HOME/.config/nvim/lua/plugins/dap/index.lua" \
  "$HOME/.config/nvim/lua/plugins/dap/keymaps.lua"
```

今回の環境ではdebugpyを導入済み。他の対応環境で不足している場合は、既存Python 3.13とuvまたはpipxを準備してからmise install pipx:debugpyを実行する。Termux単体にはこのUbuntu用mise設定を展開しない既存方針を維持する。

Neovimを終了し、新しいシェルから起動する。アダプターが見つからない場合は次で確認し、実行パスが設定される起動方法を整える。対象のvenvへdebugpyを入れる方法で代用しない。

```vim
:lua print(vim.fn.exepath("debugpy-adapter"))
:lua print(vim.fn.exepath("python3"))
```

## Pythonの通常UI確認

確認用プロジェクトは/tmp/neovim-dap-check-w1w9oy58/python project。pipなしの.venvを作成済みで、debugpyはこの.venvへ入れていない。一時領域のため永続保存は保証しない。

```sh
cd '/tmp/neovim-dap-check-w1w9oy58/python project'
nvim main.py
```

1. :Lazy load nvim-dap-viewで、導入済みDAPプラグインと設定を読み込む。
2. greet呼び出し（初期ファイルでは5行目）へカーソルを置き、leader + bでブレークポイントを設定する。
3. F5で開始し、その行に停止することを確認する。F11でgreetへ入り、F10でmessageの代入を実行する。
4. UIのscopes等でmessageがHello, Codexであることを確認する。F12で呼び出し元へ戻り、F5で続行して正常終了することを確認する。
5. 必要ならF7でUIを閉じる。ルートのRESULTS.mdに結果を記録する。

## Luaの通常UI確認

2つのNeovimを、同じ/tmp/neovim-dap-check-w1w9oy58/lua project/main.luaで開く。一方をデバッグ対象、もう一方を操作側とする。

対象側でサーバーを起動する。

```vim
:lua require("osv").launch({host="127.0.0.1", port=8086, output=false})
```

1. 操作側で:Lazy load nvim-dap-viewを実行する。
2. 3行目のreturnへブレークポイントを設定し、F5でLuaの接続設定を選ぶ。
3. 対象側で:luafile %を実行する。操作側が3行目で停止することを確認する。
4. UIが自動表示されないことを確認し、F7で開いてmessageがHello, Luaであることを確認する。F10で進め、F5で続行する。
5. 操作側で切断し、対象側でOSVを停止する。

```vim
" 操作側
:lua require("dap").disconnect({terminateDebuggee=false})
" 対象側
:lua require("osv").stop()
```

8086が使用中なら他のプロセスを止めず、別ポートを決めて接続設定と起動側を合わせる。設定変更前に状況を記録する。

## 検証範囲と残件

隔離Neovimで実際のPython・Luaの停止、変数取得、ステップオーバー、続行を確認した。Pythonは対象終了コード0、Luaは処理完了と自動UI抑制も確認した。その後、利用者がTermux + proot Ubuntu・Neovim v0.12.6でF11・F12、UI表示、切断・終了、ログポイントとREPLを確認し、必要な範囲ですべて成功した。結果は[再現・回帰記録](../testing/neovim-dap-verification.md)を参照する。

プラグイン本体・認証・Masonデータ・既存の実プロジェクトの依存は変更していない。NV-04は確認済み環境・用途の範囲で完了とする。

提供コマンドは[debugpyの定義](https://github.com/microsoft/debugpy/blob/main/setup.py)、導入方式は[miseのPythonツール管理](https://mise.jdx.dev/dev-tools/backends/pypi.html)、Lua接続は[OSVの手順](https://github.com/jbyuki/one-small-step-for-vimkind#configuration)を参照した。

## Python管理の役割

利用者の方針は、既存ツールの互換性維持に必要なPythonをmiseへ残し、新規プロジェクトのPythonと依存はuvで管理するものである。今回の3.13指定はdebugpyアダプターの検証済み実行環境であり、新規プロジェクトのPython版を制限しない。uvの.venvをデバッグ対象として使える。

現行設定ではvenvと.venvが両方あればvenvを優先する。新しいuvプロジェクトでは.venvに統一し、古いvenvが併存しないよう確認する。今回の利用者方針の追記に伴うPython管理方式や依存定義の変更は行っていない。

uv管理Python 3.14.10の追加検証では、現在のPython 3.13/debugpyから停止・各ステップ・変数取得・対象終了コード0を確認した。proot上のonly-managed判定と、アダプター終了時の警告を残件として記録した。[uv Pythonの検証と手動確認](../testing/neovim-uv-python-dap.md)を参照する。今回の追加検証では設定コードを変更していない。

2026-11-16の利用者報告で、uv管理Python 3.14.10の通常UI確認も成功した。uv runの起動警告や不要な.venv再作成はなく、停止・各ステップ・変数表示・処理完了と、アダプター終了警告なしを確認した。[手動結果](../testing/neovim-uv-python-dap.md#通常uiの確認結果2026-11-16)を参照する。過去の隔離実行で観測した終了コード1の原因は未特定のまま保持する。
