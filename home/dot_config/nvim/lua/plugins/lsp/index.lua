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
    cmd = { "LspInfo" },
    dependencies = { { "saghen/blink.cmp" } },
    config = function ()
      require("plugins.lsp.diagnostic")
      require("plugins.lsp.attach")
      require("plugins.lsp.code-actions")
      require("plugins.lsp.server-register")
    end,
  },
  -- { import = "plugins.lsp.none-ls" },
  { import = "plugins.lsp.conform" },
  { import = "plugins.lsp.lazydev" },
}

