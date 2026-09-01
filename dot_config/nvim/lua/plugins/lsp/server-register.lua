local lsp_list = {
    "lua_ls",
    "taplo",
    "rust_analyzer",
    "ts_ls",
    "pyright",
    "ruff",
    "bashls",
    "yamlls",
    "jsonls",
    "html",
    "cssls",
}

require("mason").setup({
  ui = {
      icons = {
      package_installed = "✓",
      package_pending = "➜",
      package_uninstalled = "✗"
    }
  }
})

require("mason-lspconfig").setup({
  ensure_installed = lsp_list
})

-- for _, lsp_server in ipairs(lsp_list) do
  -- vim.lsp.config(lsp_server, require("plugins.lsp.servers." .. lsp_server))
-- end
-- vim.lsp.enable(lsp_list)

for _, server_name in pairs(lsp_list) do
  vim.lsp.enable(server_name)
end
