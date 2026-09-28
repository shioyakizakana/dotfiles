
return {
  "folke/snacks.nvim",
  priority = 1000,
  lazy = false,
  cond = not vim.g.vscode,
  keys =  {
    -- Top Pickers & Explorer
    { "<leader><space>", function() Snacks.picker.smart() end, desc = "[file]ファイルをスマート検索" },
    { "<leader>,", function() Snacks.picker.buffers() end, desc = "[buffer]バッファ一覧表示" },
    { "<leader>/", function() Snacks.picker.grep() end, desc = "[search]Grep検索" },
    { "<leader>:", function() Snacks.picker.command_history() end, desc = "[command]コマンド履歴表示" },
    { "<leader>n", function() Snacks.picker.notifications() end, desc = "[notification]通知履歴表示" },
    { "<leader>e", function() Snacks.explorer() end, desc = "[file]ファイルエクスプローラー表示" },
    -- find
    { "<leader>fb", function() Snacks.picker.buffers() end, desc = "[buffer]バッファ一覧表示" },
    { "<leader>fc", function() Snacks.picker.files({ cwd = vim.fn.stdpath("config") }) end, desc = "[file]設定ファイル検索" },
    { "<leader>ff", function() Snacks.picker.files() end, desc = "[file]ファイル検索" },
    { "<leader>fg", function() Snacks.picker.git_files() end, desc = "[git]Gitファイル検索" },
    { "<leader>fp", function() Snacks.picker.projects() end, desc = "[project]プロジェクト一覧表示" },
    { "<leader>fr", function() Snacks.picker.recent() end, desc = "[file]最近使用したファイル表示" },
    -- git
    { "<leader>gb", function() Snacks.picker.git_branches() end, desc = "[git]ブランチ一覧表示" },
    { "<leader>gl", function() Snacks.picker.git_log() end, desc = "[git]Git履歴表示" },
    { "<leader>gL", function() Snacks.picker.git_log_line() end, desc = "[git]行のGit履歴表示" },
    { "<leader>gs", function() Snacks.picker.git_status() end, desc = "[git]Gitステータス表示" },
    { "<leader>gS", function() Snacks.picker.git_stash() end, desc = "[git]Stash一覧表示" },
    { "<leader>gd", function() Snacks.picker.git_diff() end, desc = "[git]差分表示" },
    { "<leader>gf", function() Snacks.picker.git_log_file() end, desc = "[git]ファイルのGit履歴表示" },
    -- gh
    { "<leader>gi", function() Snacks.picker.gh_issue() end, desc = "[github]未解決Issue一覧表示" },
    { "<leader>gI", function() Snacks.picker.gh_issue({ state = "all" }) end, desc = "[github]Issue一覧表示" },
    { "<leader>gp", function() Snacks.picker.gh_pr() end, desc = "[github]未解決Pull Request一覧表" },
    { "<leader>gP", function() Snacks.picker.gh_pr({ state = "all" }) end, desc = "[github]Pull Request一覧表" },
    -- Grep
    { "<leader>sb", function() Snacks.picker.lines() end, desc = "[buffer]バッファの行を検索" },
    { "<leader>sB", function() Snacks.picker.grep_buffers() end, desc = "[search]開いているバッファをGrep検索" },
    { "<leader>sg", function() Snacks.picker.grep() end, desc = "[search]Grep検索" },
    { "<leader>sw", function() Snacks.picker.grep_word() end, desc = "[search]選択範囲または単語を検索", mode = { "n", "x" } },
    -- search
    { '<leader>s"', function() Snacks.picker.registers() end, desc = "[register]レジスタ一覧表示" },
    { '<leader>s/', function() Snacks.picker.search_history() end, desc = "[search]検索履歴表示" },
    { "<leader>sa", function() Snacks.picker.autocmds() end, desc = "[autocmd]Autocmd一覧表示" },
    { "<leader>sb", function() Snacks.picker.lines() end, desc = "[buffer]バッファの行を検索" },
    { "<leader>sc", function() Snacks.picker.command_history() end, desc = "[command]コマンド履歴表示" },
    { "<leader>sC", function() Snacks.picker.commands() end, desc = "[command]コマンド一覧表示" },
    { "<leader>sd", function() Snacks.picker.diagnostics() end, desc = "[diagnostic]診断一覧表示" },
    { "<leader>sD", function() Snacks.picker.diagnostics_buffer() end, desc = "[diagnostic]バッファ診断表示" },
    { "<leader>sh", function() Snacks.picker.help() end, desc = "[help]ヘルプページ表示"},
    { "<leader>sH", function() Snacks.picker.highlights() end, desc = "[highlight]ハイライト一覧表示" },
    { "<leader>si", function() Snacks.picker.icons() end, desc = "[ui]アイコン一覧表示" },
    { "<leader>sj", function() Snacks.picker.jumps() end, desc = "[navigation]ジャンプリスト表示" },
    { "<leader>sk", function() Snacks.picker.keymaps() end, desc = "[keymap]キーマップ一覧表示" },
    { "<leader>sl", function() Snacks.picker.loclist() end, desc = "[diagnostic]ロケーションリスト表示" },
    { "<leader>sm", function() Snacks.picker.marks() end, desc = "[navigation]マーク一覧表示" },
    { "<leader>sM", function() Snacks.picker.man() end, desc = "[help]Manページ表示" },
    { "<leader>sp", function() Snacks.picker.lazy() end, desc = "[plugin]プラグイン仕様を検索" },
    { "<leader>sq", function() Snacks.picker.qflist() end, desc = "[diagnostic]Quickfixリスト表示" },
    { "<leader>sR", function() Snacks.picker.resume() end, desc = "[search]直前の検索を再開" },
    { "<leader>su", function() Snacks.picker.undo() end, desc = "[edit]Undo履歴表示" },
    { "<leader>uC", function() Snacks.picker.colorschemes() end, desc = "[ui]カラースキーム一覧表示" },
    -- LSP
    { "gd", function() Snacks.picker.lsp_definitions() end, desc = "[lsp]定義へ移動" },
    { "gD", function() Snacks.picker.lsp_declarations() end, desc = "[lsp]宣言へ移動" },
    { "gr", function() Snacks.picker.lsp_references() end, nowait = true, desc = "[lsp]参照一覧表示" },
    { "gI", function() Snacks.picker.lsp_implementations() end, desc = "[lsp]実装へ移動" },
    { "gy", function() Snacks.picker.lsp_type_definitions() end, desc = "[lsp]型定義へ移動" },
    { "gai", function() Snacks.picker.lsp_incoming_calls() end, desc = "[lsp]着信呼び出し表示" },
    { "gao", function() Snacks.picker.lsp_outgoing_calls() end, desc = "[lsp]発信呼び出し表示" },
    { "<leader>ss", function() Snacks.picker.lsp_symbols() end, desc = "[lsp]LSPシンボル一覧表示" },
    { "<leader>sS", function() Snacks.picker.lsp_workspace_symbols() end, desc = "[lsp]ワークスペースシンボル表示" },
    -- Other
    -- { "<leader>z",  function() Snacks.zen() end, desc = "Toggle Zen Mode" },
    -- { "<leader>Z",  function() Snacks.zen.zoom() end, desc = "[window]ズーム切替" },
    { "<leader>.",  function() Snacks.scratch() end, desc = "[buffer]スクラッチバッファ切替" },
    { "<leader>S",  function() Snacks.scratch.select() end, desc = "[buffer]スクラッチバッファ選択" },
    { "<leader>n",  function() Snacks.notifier.show_history() end, desc = "[notification]通知履歴表示" },
    { "<leader>bd", function() Snacks.bufdelete() end, desc = "[buffer]バッファ削除" },
    { "<leader>cR", function() Snacks.rename.rename_file() end, desc = "[file]ファイル名変更" },
    { "<leader>gB", function() Snacks.gitbrowse() end, desc = "[git]Gitリポジトリをブラウズ", mode = { "n", "v" } },
    { "<leader>gg", function() Snacks.lazygit() end, desc = "[git]Lazygit表示" },
    { "<leader>un", function() Snacks.notifier.hide() end, desc = "[notification]全通知を閉じる" },
    { "<c-/>",      function() Snacks.terminal() end, desc = "[terminal]ターミナル切替" },
    { "<c-_>",      function() Snacks.terminal() end, desc = "[keymap]which-keyから除外" },
    { "]]",         function() Snacks.words.jump(vim.v.count1) end, desc = "[lsp]次の参照へ移動", mode = { "n", "t" } },
    { "[[",         function() Snacks.words.jump(-vim.v.count1) end, desc = "[lsp]前の参照へ移動", mode = { "n", "t" } },
    {
      "<leader>N",
      desc = "[help]Neovimニュース表示",
      function()
        Snacks.win({
          file = vim.api.nvim_get_runtime_file("doc/news.txt", false)[1],
          width = 0.6,
          height = 0.6,
          wo = {
            spell = false,
            wrap = false,
            signcolumn = "yes",
            statuscolumn = " ",
            conceallevel = 3,
          },
        })
      end,
    },
    {
      "<C-j><space>f",
      mode = { "n", "i" },
      function ()
        local curdir = vim.bo.filetype == "oil" and require("oil").get_current_dir() or vim.expand("%:p:h")
        Snacks.picker.files( { dirs = { curdir } })
      end,
      silent = true,
      desc = "[file]Oilで選択したファイルをSnacksで開く"
    },
  },
  opts = function()
    return {
      picker = require("plugins.utils.snacks.picker").config,
    }
  end,
}
