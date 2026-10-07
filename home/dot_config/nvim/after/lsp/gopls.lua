---@type vim.lsp.Config
return {
  filetypes = { "go", "gomod", "gowork", "gotmpl" },
  settings = {
    gopls = {
      gofumpt = true,
    },
  },
}
