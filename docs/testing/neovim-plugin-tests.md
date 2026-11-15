# mini.testでNeovimプラグインをテストする

新規プラグインの開発にはmini.testを使う。Neovim内蔵Luaで実行し、外部Lua・LuaRocks・vustedはテスト実行に使わない。luacheckは静的解析用として通常導入に残す。

## dotfilesの設定と開発プロジェクトの依存

既存のhome/dot_config/nvim/lua/plugins/editor/mini-test.luaは、Luaファイルを開くとmini.testを読み込む。optsでsetupを有効にし、v0.18.0のコミット35c67cb7f2dc697ed0c7c06400fcf29a8a521d7dへ固定した。通常設定では読み込み後に:lua MiniTest.run()を使えるが、テスト対象のコードが現在の編集状態を変える可能性がある。

開発プロジェクトとCIでは、以下のように依存をプロジェクト内へ置き、個人の設定やlazy.nvimを読み込まずに実行する。mini.test全体の提供元は[公式リポジトリ](https://github.com/nvim-mini/mini.test)、テスト構成は[公式ガイド](https://nvim-mini.org/mini.nvim/TESTING.html)を参照する。

## 最小構成を準備する

以下は将来のプラグインリポジトリのルートで行う手順。このdotfilesの初期構築やmake checkからは、依存の取得を実行しない。deps/はそのプロジェクトの.gitignoreへ追加し、最小構成・テスト・固定コミットを記載した取得手順をGitで管理する。

最初に開発用依存を取得する。既存のdeps/mini.testがある場合は、状態とrevisionを確認し、このcloneを重ねて実行しない。

```shell
git clone --branch v0.18.0 --depth 1 https://github.com/nvim-mini/mini.test deps/mini.test
git -C deps/mini.test rev-parse HEAD
# 35c67cb7f2dc697ed0c7c06400fcf29a8a521d7dと一致することを確認する。
mkdir -p scripts tests
```

scripts/minimal_init.luaを作る。依存がない場合は異常終了し、テストを待ち続けないようにする。

```lua
vim.opt.rtp:prepend(vim.fn.getcwd())
vim.opt.rtp:append(vim.fn.getcwd() .. "/deps/mini.test")
local ok, mini_test = pcall(require, "mini.test")
if not ok then
  vim.api.nvim_err_writeln(tostring(mini_test))
  vim.cmd("cquit 1")
  return
end
mini_test.setup({ collect = { emulate_busted = false } })
```

tests/test_example.luaを作る。各テストで子Neovimを再起動し、バッファや設定の状態を分離する。実際のプラグインを検証するときは、子プロセスにも最小構成を指定し、対象モジュールを読み込む。

```lua
local child = MiniTest.new_child_neovim()
local T = MiniTest.new_set({
  hooks = {
    pre_case = function()
      child.restart({ "-u", "NONE", "--noplugin", "-i", "NONE" })
    end,
    post_once = child.stop,
  },
})
T["バッファへ書いた文字を取得できる"] = function()
  child.api.nvim_buf_set_lines(0, 0, -1, false, { "こんにちは" })
  MiniTest.expect.equality(child.api.nvim_buf_get_lines(0, 0, -1, false), { "こんにちは" })
end
T["新しい子プロセスではバッファが空である"] = function()
  MiniTest.expect.equality(child.api.nvim_buf_get_lines(0, 0, -1, false), { "" })
end
return T
```

## ローカルとCIで実行する

```shell
nvim --headless --noplugin -i NONE -u scripts/minimal_init.lua -c "lua MiniTest.run()"
```

同じコマンドを開発プロジェクトのMakefileから呼び出し、CIにも使用する。CIでは対象のNeovim版とmini.testのコミットを固定し、失敗時の非0終了を必須チェックへ伝える。取得と実行は分け、テスト実行中に依存を自動導入しない。dotfilesの既存Bats・unittestはそのまま維持する。

mini.testには組み込みのmock・spyと並列実行がない。まず子Neovimで状態を分け、必要な関数をテスト内で置き換える。Busted風構文は完全互換ではないため、新規テストではMiniTest.new_set()を使う。[公式の機能と制約](https://nvim-mini.org/mini.nvim/doc/mini-test.html)

Termuxは端末のNeovimと取得したmini.testでこの最小構成を確認する。LuaRocksのC拡張ビルドは不要だが、子プロセス起動や端末固有の制約まで確認済みとは扱わない。proot・WSL・ネイティブLinuxも環境別に結果を記録する。

## この変更で確認した結果

2026-11-14、公式タグv0.18.0を/tmpへ取得し、コミットの一致を確認した。実HOME外の一時HOMEとXDGディレクトリ、限定PATHを使い、通常のNeovim設定とlazy.nvimを読み込まずに上記の例を実行した。バッファ操作と子プロセス分離の2件は成功し、終了コードは0。意図的に失敗するテストを追加すると終了コード1になり、依存がない場合も終了コード1で停止した。

通常導入のモックは、LuaRocksにluacheckだけを要求し、後続のnimlspへ進むことと、導入済みの再適用でインストールしないことを確認した。mini.testの公開設定はopts・Luaでの読み込み・固定revisionを検証する。公開コードの取得は今回の手動検証のみで、unittestやCIから通信しない。Codexの隔離検証では、実HOMEの既存配置は確認したが、設定の適用・更新は行っていない。その後、利用者がchezmoi applyを実施し、:lua print(type(MiniTest))がtableになることを確認した。通常UIでのテスト実行とTermux端末での確認は残件。

make checkは静的確認、unittest全218件、Bats全18件が成功し、skipなし。対象LuaのStyLua、文書のtextlintとnatural-japanese、git diff --checkも成功した。監査台帳の過去の表現は今回の変更対象に含めていない。
