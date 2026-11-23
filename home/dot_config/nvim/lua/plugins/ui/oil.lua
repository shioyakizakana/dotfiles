return {
  "stevearc/oil.nvim",
  dependencies = { "nvim-tree/nvim-web-devicons" },
  cond = not vim.g.vscode,
  event = { "VeryLazy" },
  opts = {},
  config = function()
    require("oil").setup({
      view_options = {
          show_hidden = true,
      },
      keymaps = {
        ["<CR>"] = { "actions.select", desc = "[file]選択した項目を開く" },
        ["<C-CR>"] = { "actions.select", opts = { vertical = true }, desc = "[file]左右に分割して開く" },
        ["<C-s>"] = { "actions.select", opts = { horizontal = true }, desc = "[file]上下に分割して開く" },
        ["<C-t>"] = { "actions.select", opts = { tab = true }, desc = "[file]新しいタブで開く" },
        ["<C-p>"] = {
          "actions.preview",
          desc = "[ui]プレビューを開く"
        },
        ["<C-l>"] = {
          "actions.refresh",
          desc = "[ui]Oilをリフレッシュ"
        },
        ["q"] = {
          "actions.close",
          mode = "n",
          desc = "[ui]Oilを閉じる"
        },
        ["-"] = {
          "actions.parent",
          mode = "n",
          desc = "[ui]親ディレクトリに移動"
        },
        ["gh"] = { "actions.open_cwd", mode = "n", desc = "[directory]作業ディレクトリを開く" },
        ["g?"] = {
          "actions.show_help",
          mode = "n",
          desc = "[help]Oilのヘルプを開く"
        },
        ["gs"] = {
          "actions.change_sort",
          mode = "n",
          desc = "[ui]ソート順を変更"
        },
        ["gx"] = { "actions.open_external", desc = "[file]外部アプリで開く" },
        ["g."] = {
          "actions.toggle_hidden",
          mode = "n",
          desc = "[file]隠しファイルの表示を切り替える"
        },
        ["<Space>y"] = {
          callback = function()
            local oil = require("oil")
            local current_path = oil.get_current_dir()
            require("yazi").yazi(nil, current_path)
          end,
          desc = "[ui]Yaziをカレントディレクトリで開く",
        },
      },
    })

    -- oil fix relative path
    -- https://github.com/stevearc/oil.nvim/issues/234
    vim.api.nvim_create_augroup("OilRelPathFix", {})
    vim.api.nvim_create_autocmd("BufLeave", {
      group = "OilRelPathFix",
      pattern = "oil:///*",
      callback = function()
          vim.cmd("cd .")
      end,
    })
  end,
}
