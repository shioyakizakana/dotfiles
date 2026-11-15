---@type vim.lsp.Config
return {
  cmd = {
    "deno",
    "lsp",
  },
  filetypes = {
    "javascript",
    "javascriptreact",
    "typescript",
    "typescriptreact",
  },
  workspace_required = true,
  root_dir = function(bufnr, on_dir)
    local root = require("config.web-project").deno_root(bufnr)
    if root then
      on_dir(root)
    end
  end,
  ---@type lspconfig.settings.denols
  settings = {
    deno = {
      suggest = {
        imports = {
          hosts = {
            ["https://deno.land"] = true,
          },
        },
      },
    },
  },
}
