return {
  -- LSPや補完系プラグインと連携して補完候補にアイコンを表示する
  {
      "onsails/lspkind.nvim",
      -- nvim-cmp.lua
      event = "InsertEnter",
  },

  {
    "neovim/nvim-lspconfig",
    cond = not vim.g.vscode,
    event = { "FileType", "BufNewFile" },
    cmd = { "LspInfo", "LspInstall", "LspUnInstall" },
    dependencies = {
      {
        "mason-org/mason.nvim",

        dependencies = {
          {"mason-org/mason-lspconfig.nvim"},
          {"jay-babu/mason-null-ls.nvim"},
          {"nvimtools/none-ls.nvim"},
        },
        cmd = "Mason",
      },
      { "saghen/blink.cmp" },
    },
    config = function ()
      require("plugins.lsp.diagnostic")
      require("plugins.lsp.server-register")
    end,
  },
  { import = "plugins.lsp.lazydev" },
  { import = "plugins.lsp.none-ls" },
}

