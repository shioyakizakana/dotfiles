---@type vim.lsp.Config
return {
  cmd = { "ruff", "server" },
  filetypes = { "python" },
  root_markers = { "pyproject.toml", "ruff.toml", ".ruff.toml", ".git" },
  settings = {},
  on_attach = function(client, bufnr)
    -- 型情報の表示はbasedpyrightへ任せる。
    client.server_capabilities.hoverProvider = false
    local function organize_imports()
      require("conform").format({
        bufnr = bufnr,
        formatters = { "ruff_organize_imports" },
        lsp_format = "never",
      })
    end
    for _, name in ipairs({ "LspRuffOrganizeImports", "LspPyrightOrganizeImports" }) do
      vim.api.nvim_buf_create_user_command(bufnr, name, organize_imports, {
        desc = "Ruffでimportを整理",
      })
    end
  end,
}
