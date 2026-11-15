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
  "nimls",
  "oxlint",
  "marksman",
  "basedpyright",
  "ruff",
  "rust_analyzer",
  -- "sourcekit",
  "sqls",
  "svelte",
  "tailwindcss",
  "taplo",
  "vtsls",
  "vue_ls",
  "yamlls",
}

if vim.g.dotfiles_use_mason ~= false then
  require("mason").setup({})
end

for _, server_name in pairs(lsp_list) do
  vim.lsp.enable(server_name)
end
