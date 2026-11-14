-- 実機での移行確認中も、指定がなければ既存のMason構成を維持する。
local use_mason = vim.g.dotfiles_use_mason ~= false
local dependencies = { { "saghen/blink.cmp" } }
if use_mason then
  table.insert(dependencies, 1, {
    "mason-org/mason.nvim",
    dependencies = {
      { "mason-org/mason-lspconfig.nvim" },
      { "jay-babu/mason-null-ls.nvim" },
      { "nvimtools/none-ls.nvim" },
    },
  })
end

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
    cmd = use_mason and { "LspInfo", "LspInstall", "LspUnInstall" } or { "LspInfo" },
    dependencies = dependencies,
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

