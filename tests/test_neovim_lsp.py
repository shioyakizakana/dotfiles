"""LSP移行の依存定義・登録・Vue連携を実プラグインなしで検証する。"""

from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
NVIM = ROOT / "home/dot_config/nvim"
LUA = shutil.which("lua")


class NeovimDependencyTests(unittest.TestCase):
    def test_tools_provide_enabled_servers_and_go_formatter(self):
        tools = tomllib.loads((ROOT / "home/dot_config/mise/config.toml").read_text())["tools"]
        required = (
            "npm:@vtsls/language-server", "npm:@vue/language-server",
            "npm:svelte-language-server", "npm:oxlint",
            "go:golang.org/x/tools/cmd/goimports",
        )
        for name in required:
            with self.subTest(tool=name):
                self.assertIn(name, tools)
                self.assertTrue(tools[name])


@unittest.skipUnless(LUA, "Luaが必要です")
class NeovimLspTests(unittest.TestCase):
    def run_lua(self, script, *arguments):
        with tempfile.TemporaryDirectory(prefix="neovim lsp ") as home:
            result = subprocess.run(
                [LUA, "-", str(NVIM), *arguments], input=script, text=True,
                capture_output=True, timeout=5,
                env={"HOME": home, "PATH": "", "LANG": "C"},
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_enabled_servers_keep_typescript_vue_svelte_and_oxlint(self):
        self.run_lua(r'''
local enabled = {}
vim = {g = {}, lsp = {enable = function(name) enabled[name] = true end}}
package.preload.mason = function() return {setup = function() end} end
assert(loadfile(arg[1] .. "/lua/plugins/lsp/server-register.lua"))()
for _, name in ipairs({"vtsls", "vue_ls", "svelte", "oxlint"}) do assert(enabled[name], name) end
assert(not enabled.ts_ls, "TypeScriptサーバーを重複起動しない")
''')

    def test_default_mode_keeps_mason_and_all_servers(self):
        self.run_lua(PROVIDER_HARNESS, "default")

    def test_nim_uses_existing_path_command_first(self):
        self.run_lua(NIM_HARNESS, "path")

    def test_nim_finds_default_nimble_binary_without_path(self):
        self.run_lua(NIM_HARNESS, "default")

    def test_nim_finds_custom_nimble_directory_with_spaces(self):
        self.run_lua(NIM_HARNESS, "custom")

    def test_nim_empty_custom_directory_uses_default(self):
        self.run_lua(NIM_HARNESS, "empty")

    def test_nim_missing_binary_keeps_standard_missing_command(self):
        self.run_lua(NIM_HARNESS, "missing")

    def test_nim_custom_directory_does_not_select_another_installation(self):
        self.run_lua(NIM_HARNESS, "custom-missing")

    def test_treesitter_installs_nim_and_starts_highlighting(self):
        self.run_lua(r'''
local installed, autocmd, started
vim = {
  api = {
    nvim_create_augroup = function() return 1 end,
    nvim_create_autocmd = function(event, opts) assert(event == "FileType"); autocmd = opts end,
    nvim_buf_line_count = function() return 10 end,
    nvim_buf_get_lines = function() return {} end,
  },
  treesitter = {
    language = {get_filetypes = function(lang) return {lang} end},
    start = function() started = true end,
  },
  wo = {}, bo = {},
}
package.preload["nvim-treesitter"] = function() return {
  install = function(languages)
    installed = {}; for _, lang in ipairs(languages) do installed[lang] = true end
  end,
  get_available = function(tier) assert(tier == 2); return {"nim", "rust"} end,
} end
local specs = assert(loadfile(arg[1] .. "/lua/plugins/utils/nvim-treesitter.lua"))()
specs[1].config()
assert(installed.nim, "Nimを導入対象に含める")
assert(installed.rust and installed.python, "既存言語の導入を維持する")
local nim = false
for _, ft in ipairs(autocmd.pattern) do if ft == "nim" then nim = true end end
assert(nim, "NimのFileTypeでハイライトを開始する")
autocmd.callback({buf = 7})
assert(started)
''')

    def test_explicit_mason_mode_keeps_current_dependencies(self):
        self.run_lua(PROVIDER_HARNESS, "enabled")

    def test_external_tools_mode_registers_all_servers_without_mason(self):
        self.run_lua(PROVIDER_HARNESS, "disabled")

    def test_go_formatter_uses_goimports_and_keeps_lsp_fallback(self):
        self.run_lua(r'''
vim = {api = {nvim_create_user_command = function() end}, g = {}, b = {[1] = {}}}
local spec = assert(loadfile(arg[1] .. "/lua/plugins/lsp/conform.lua"))()
local opts = spec.opts()
assert(opts.formatters_by_ft.go[1] == "goimports")
assert(opts.format_on_save(1).lsp_format == "fallback")
''')

    def test_vue_plugin_resolves_real_binary_with_spaces(self):
        self.run_lua(VTSLS_HARNESS, "ready")

    def test_aube_launcher_resolves_package_without_executing_wrapper(self):
        self.run_lua(VTSLS_HARNESS, "aube-ready")

    def test_aube_package_without_manifest_warns(self):
        self.run_lua(VTSLS_HARNESS, "aube-no-manifest")

    def test_aube_package_without_server_entry_warns(self):
        self.run_lua(VTSLS_HARNESS, "aube-no-entry")

    def test_aube_broken_package_link_warns(self):
        self.run_lua(VTSLS_HARNESS, "aube-broken-link")

    def test_mise_shim_without_package_path_warns_and_keeps_typescript(self):
        self.run_lua(VTSLS_HARNESS, "shim")

    def test_missing_vue_server_warns_without_breaking_typescript(self):
        self.run_lua(VTSLS_HARNESS, "missing")

    def test_unresolvable_vue_binary_warns_without_installing(self):
        self.run_lua(VTSLS_HARNESS, "unresolved")

    def test_missing_package_manifest_warns_without_breaking_typescript(self):
        self.run_lua(VTSLS_HARNESS, "no-manifest")


NIM_HARNESS = r'''
local mode = arg[2]
local home_bin = "/fixture home/.nimble/bin/nimlsp"
local custom_bin = "/custom nimble/bin/nimlsp"
local custom = (mode == "custom" or mode == "custom-missing") and "/custom nimble" or nil
if mode == "empty" then custom = "" end
vim = {
  env = {NIMBLE_DIR = custom},
  fs = {joinpath = function(...) return table.concat({...}, "/") end},
  fn = {
    expand = function(value) assert(value == "~/.nimble"); return "/fixture home/.nimble" end,
    executable = function(path)
      if mode == "path" and path == "nimlsp" then return 1 end
      if mode == "custom" and path == custom_bin then return 1 end
      if (mode == "default" or mode == "empty" or mode == "custom-missing") and path == home_bin then return 1 end
      return 0
    end,
  },
}
local config = assert(loadfile(arg[1] .. "/after/lsp/nimls.lua"))()
local expected = "nimlsp"
if mode == "default" or mode == "empty" then expected = home_bin end
if mode == "custom" then expected = custom_bin end
assert(config.cmd[1] == expected, config.cmd[1] .. " != " .. expected)
assert(#config.cmd == 1 and config.filetypes[1] == "nim")
'''


PROVIDER_HARNESS = r'''
local root, mode = arg[1], arg[2]
local mason_enabled = mode ~= "disabled"
local setup_count = 0
local registered = {}
local globals = {}
if mode ~= "default" then globals.dotfiles_use_mason = mason_enabled end
vim = {g = globals, lsp = {enable = function(name) registered[name] = true end}}
package.preload.mason = function()
  assert(mason_enabled, "MasonなしモードではMasonを読み込まない")
  return {setup = function() setup_count = setup_count + 1 end}
end
for _, module in ipairs({"diagnostic", "attach", "code-actions"}) do
  package.preload["plugins.lsp." .. module] = function() return {} end
end
package.preload["plugins.lsp.server-register"] = function()
  return assert(loadfile(root .. "/lua/plugins/lsp/server-register.lua"))()
end
local specs = assert(loadfile(root .. "/lua/plugins/lsp/index.lua"))()
local lsp
for _, spec in ipairs(specs) do
  if spec[1] == "neovim/nvim-lspconfig" then lsp = spec end
end
assert(lsp, "LSP設定本体を維持する")
local dependencies = {}
local function collect(spec)
  if type(spec) == "string" then dependencies[spec] = true; return end
  if spec[1] then dependencies[spec[1]] = true end
  for _, dependency in ipairs(spec.dependencies or {}) do collect(dependency) end
end
for _, dependency in ipairs(lsp.dependencies) do collect(dependency) end
assert(dependencies["saghen/blink.cmp"], "補完連携を維持する")
for _, name in ipairs({"mason-org/mason.nvim", "mason-org/mason-lspconfig.nvim", "jay-babu/mason-null-ls.nvim"}) do
  assert((dependencies[name] == true) == mason_enabled, name)
end
local commands = {}
for _, command in ipairs(lsp.cmd) do commands[command] = true end
assert(commands.LspInfo)
assert((commands.LspInstall == true) == mason_enabled)
lsp.config()
assert(setup_count == (mason_enabled and 1 or 0))
local expected = {"bashls", "biome", "cssls", "denols", "emmet_language_server",
  "golangci_lint_ls", "gopls", "html", "jsonls", "lua_ls", "nimls", "oxlint",
  "marksman", "basedpyright", "ruff", "rust_analyzer", "sqls", "svelte", "tailwindcss",
  "taplo", "vtsls", "vue_ls", "yamlls"}
local count = 0
for name in pairs(registered) do count = count + 1 end
assert(count == #expected)
for _, name in ipairs(expected) do assert(registered[name], name) end
'''


VTSLS_HARNESS = r'''
local root, scenario = arg[1], arg[2]
local package_root = "/fixture tools/lib/node_modules/@vue/language-server"
local aube = scenario:match("^aube") ~= nil
if aube then package_root = "/fixture tools/node_modules/.mise/vue-with-peer/node_modules/@vue/language-server" end
local real_binary = package_root .. "/bin/vue-language-server.js"
local aube_launcher = "/fixture tools/node_modules/.bin/vue-language-server"
local aube_package = "/fixture tools/node_modules/@vue/language-server"
local warned = false
vim = {
  fn = {exepath = function(name)
    assert(name == "vue-language-server")
    return scenario == "missing" and "" or "/fixture tools/bin/vue-language-server"
  end},
  uv = {
    fs_realpath = function(path)
      if path == aube_package then
        if scenario == "aube-broken-link" then return nil end
        return package_root
      end
      assert(path == "/fixture tools/bin/vue-language-server")
      if scenario == "unresolved" then return nil end
      if aube then return aube_launcher end
      return scenario == "shim" and "/fixture tools/shims/vue-language-server" or real_binary
    end,
    fs_stat = function(path)
      if scenario == "shim" and path == "/fixture tools/package.json" then return {type = "file"} end
      if scenario ~= "no-manifest" and scenario ~= "aube-no-manifest" and path == package_root .. "/package.json" then
        return {type = "file"}
      end
      if scenario ~= "aube-no-entry" and path == real_binary then return {type = "file"} end
    end,
  },
  fs = {
    dirname = function(path) return path:match("^(.*)/[^/]+$") end,
    joinpath = function(...) return table.concat({...}, "/") end,
  },
  notify = function(message, level)
    assert(message:find("vue%-language%-server") and level == 2)
    warned = true
  end,
  log = {levels = {WARN = 2}},
}
local config = assert(loadfile(root .. "/after/lsp/vtsls.lua"))()
assert(config.cmd[1] == "vtsls" and config.cmd[2] == "--stdio")
local filetypes = {}
for _, ft in ipairs(config.filetypes) do filetypes[ft] = true end
for _, ft in ipairs({"typescript", "javascript", "typescriptreact", "javascriptreact", "vue"}) do
  assert(filetypes[ft], ft)
end
if scenario == "ready" or scenario == "aube-ready" then
  local plugins = config.settings.vtsls.tsserver.globalPlugins
  assert(#plugins == 1)
  assert(plugins[1].name == "@vue/typescript-plugin")
  assert(plugins[1].location == package_root)
  assert(plugins[1].languages[1] == "vue")
  assert(plugins[1].configNamespace == "typescript")
  assert(not warned)
else
  assert(warned, "利用者に不足とPATHの確認方法を示す")
  assert(not config.settings, "存在しない配置先を登録しない")
end
'''


if __name__ == "__main__":
    unittest.main()
