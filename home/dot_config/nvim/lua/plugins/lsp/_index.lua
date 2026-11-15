---@module "lazy"
---@type LazyPluginSpec[]
return {
  {
    "neovim/nvim-lspconfig",
    cond = not vim.g.vscode,
    event = {"FileType", "BufNewFile"},
    cmd = {"LspInfo"},
    dependencies = {
      {"b0o/schemastre.nvim"},
      {"saghen/blink.cmp"},
    },
    config = function ()
      require("plugins.lsp.diagnostic")
      require("plugins.lsp.format")
      require("plugins.lsp.attach")
      require("plugins.lsp.code-actions")
      require("plugins.lsp.server-register")
    end,
  },

  {import = "plugins.lsp.tiny-code-action"},
  {import = "plugins.lsp.conform"},
  {import = "plugins.lsp.none-ls"},
  {import = "plugins.lsp.lazydev"},
}
