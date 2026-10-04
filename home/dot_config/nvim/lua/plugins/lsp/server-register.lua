local lsp_list = {
  "bashls",
  "biome",
  "cssls",
  "denols",
  "emmet_language_server",
  "golangci_lint_ls",
  "gopls",
  "html",
  "jsonls",
  "lua_ls",
  "oxlint",
  "marksman",
  "pyright",
  "ruff",
  "rust_analyzer",
  "sourcekit",
  "sqls",
  "svelte",
  "tailwindcss",
  "taplo",
  "vtsls",
  "vue_ls",
  "yamlls",
}

require("mason").setup({
  -- ui = {
  --     icons = {
  --     package_installed = "✓",
  --     package_pending = "➜",
  --     package_uninstalled = "✗"
  --   }
  -- }
})

-- require("mason-lspconfig").setup({
--  ensure_installed = lsp_list
-- })

for _, server_name in pairs(lsp_list) do
  vim.lsp.enable(server_name)
end
