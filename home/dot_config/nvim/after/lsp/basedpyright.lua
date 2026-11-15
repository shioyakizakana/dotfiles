local function set_python_path(command)
  local clients = vim.lsp.get_clients({
    bufnr = vim.api.nvim_get_current_buf(),
    name = "basedpyright",
  })
  for _, client in ipairs(clients) do
    local settings = client.settings or client.config.settings or {}
    settings.python = vim.tbl_deep_extend("force", settings.python or {}, { pythonPath = command.args })
    client.settings = settings
    client.config.settings = settings
    client:notify("workspace/didChangeConfiguration", { settings = settings })
  end
end

---@type vim.lsp.Config
return {
  cmd = { "basedpyright-langserver", "--stdio" },
  filetypes = { "python" },
  root_markers = {
    "pyrightconfig.json",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "Pipfile",
    ".git",
  },
  settings = {
    basedpyright = {
      disableOrganizeImports = true,
      analysis = {
        autoSearchPaths = true,
        diagnosticMode = "openFilesOnly",
        -- 移行時の既定値。pyproject.toml等のプロジェクト設定を優先する。
        typeCheckingMode = "standard",
      },
    },
  },
  on_attach = function(_, bufnr)
    -- 既存の操作を維持し、新しいサーバー名のコマンドも用意する。
    for _, name in ipairs({ "LspBasedpyrightSetPythonPath", "LspPyrightSetPythonPath" }) do
      vim.api.nvim_buf_create_user_command(bufnr, name, set_python_path, {
        desc = "basedpyrightのPython実行パスを変更",
        nargs = 1,
        complete = "file",
      })
    end
  end,
}
