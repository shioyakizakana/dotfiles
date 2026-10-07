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
    local root = vim.fs.root(bufnr, {
      "deno.json",
      "deno.jsonc",
      "deno.lock",
      ".git",
    })
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
