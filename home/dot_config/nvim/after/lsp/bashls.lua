---@type vim.lsp.Config
return {
  cmd = { "bash-language-server", "start" },
  ---@type lspconfig.settings.bashls
  settings = {
    bashIde = {
      globPattern = vim.env.GLOB_PATTERN or "*@(.sh|.inc|.bash|.command)",
    },
  },
  filetypes = { "sh", "bash", "zsh" },
}
