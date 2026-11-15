---@type vim.lsp.Config
local config = {
  cmd = { "vtsls", "--stdio" },
  filetypes = { "javascript", "javascriptreact", "typescript", "typescriptreact", "vue" },
  root_dir = function(bufnr, on_dir)
    local root = require("config.web-project").typescript_root(bufnr)
    if root then
      on_dir(root)
    end
  end,
}

-- mise・Masonの固定パスを避け、PATHで選ばれた実体を基準にVueの依存を探す。
local binary = vim.fn.exepath("vue-language-server")
local uv = vim.uv or vim.loop
local resolved = binary ~= "" and uv.fs_realpath(binary) or nil
local package_path
if resolved and resolved:match("/bin/vue%-language%-server%.js$") then
  package_path = vim.fs.dirname(vim.fs.dirname(resolved))
elseif resolved and resolved:match("/node_modules/%.bin/vue%-language%-server$") then
  -- aubeの.binはシェルランチャーなので、隣接するパッケージのリンクを解決する。
  local modules = vim.fs.dirname(vim.fs.dirname(resolved))
  package_path = uv.fs_realpath(vim.fs.joinpath(modules, "@vue", "language-server"))
end
local manifest = package_path and uv.fs_stat(vim.fs.joinpath(package_path, "package.json"))
local entry = package_path and uv.fs_stat(vim.fs.joinpath(package_path, "bin", "vue-language-server.js"))
if manifest and manifest.type == "file" and entry and entry.type == "file" then
  config.settings = {
    vtsls = {
      tsserver = {
        globalPlugins = {
          {
            name = "@vue/typescript-plugin",
            location = package_path,
            languages = { "vue" },
            configNamespace = "typescript",
          },
        },
      },
    },
  }
else
  vim.notify(
    "vue-language-serverのパッケージを確認できません。導入状態・PATH・@vue/language-serverの配置を確認してください。miseのshimだけが見える場合は実ツールのbinをPATHへ追加してください。VueのTypeScript支援は未設定です。",
    vim.log.levels.WARN
  )
end

return config
