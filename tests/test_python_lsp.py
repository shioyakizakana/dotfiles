"""Pythonの型解析とRuffのlint・整形の分担を検証する。"""

from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
NVIM = ROOT / "home/dot_config/nvim"
LUA = shutil.which("lua")


class PythonToolTests(unittest.TestCase):
    def test_mise_defines_basedpyright_and_ruff_as_providers(self):
        tools = tomllib.loads((ROOT / "home/dot_config/mise/config.toml").read_text())["tools"]
        self.assertTrue(tools["npm:basedpyright"])
        self.assertTrue(tools["ruff"])
        self.assertNotIn("npm:pyright", tools, "PythonのLSP導入定義を一本化する")


@unittest.skipUnless(LUA, "Luaが必要です")
class PythonLspTests(unittest.TestCase):
    def run_lua(self, script, *args):
        with tempfile.TemporaryDirectory(prefix="python lsp ") as home:
            result = subprocess.run(
                [LUA, "-", str(NVIM), *args], input=script, text=True,
                capture_output=True, timeout=5,
                env={"HOME": home, "PATH": "", "LANG": "C"},
            )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_basedpyright_uses_explicit_command_and_preserves_type_services(self):
        self.run_lua(r'''
local config = assert(loadfile(arg[1] .. "/after/lsp/basedpyright.lua"))()
assert(config.cmd[1] == "basedpyright-langserver" and config.cmd[2] == "--stdio")
assert(config.filetypes[1] == "python")
assert(config.settings.basedpyright.analysis.typeCheckingMode == "standard")
assert(config.settings.basedpyright.analysis.diagnosticMode == "openFilesOnly")
assert(config.settings.basedpyright.disableOrganizeImports == true)
assert(not config.settings.basedpyright.disableLanguageServices)
local roots = {}; for _, marker in ipairs(config.root_markers) do roots[marker] = true end
assert(roots["pyproject.toml"] and roots["pyrightconfig.json"])
''')

    def test_python_path_command_updates_only_basedpyright_with_spaces(self):
        self.run_lua(PATH_HARNESS, "settings")

    def test_python_path_command_supports_config_settings_fallback(self):
        self.run_lua(PATH_HARNESS, "config")

    def test_ruff_owns_import_commands_and_defers_hover(self):
        self.run_lua(r'''
local commands, formatted = {}, nil
vim = {api = {nvim_buf_create_user_command = function(buf, name, callback)
  assert(buf == 17); commands[name] = callback
end}}
package.preload.conform = function() return {format = function(opts) formatted = opts end} end
local config = assert(loadfile(arg[1] .. "/after/lsp/ruff.lua"))()
assert(config.cmd[1] == "ruff" and config.cmd[2] == "server")
local client = {server_capabilities = {hoverProvider = true, codeActionProvider = true}}
config.on_attach(client,17)
assert(client.server_capabilities.hoverProvider == false)
assert(client.server_capabilities.codeActionProvider == true)
assert(commands.LspRuffOrganizeImports and commands.LspPyrightOrganizeImports)
for _, name in ipairs({"LspRuffOrganizeImports", "LspPyrightOrganizeImports"}) do
  commands[name]()
  assert(formatted.bufnr == 17 and formatted.lsp_format == "never")
  assert(#formatted.formatters == 1 and formatted.formatters[1] == "ruff_organize_imports")
end
''')

    def test_python_save_applies_fixes_and_imports_before_formatting(self):
        self.run_lua(r'''
vim = {api = {nvim_create_user_command = function() end}, g = {}, b = {[1] = {}}}
local config = assert(loadfile(arg[1] .. "/lua/plugins/lsp/conform.lua"))().opts()
local python = config.formatters_by_ft.python
assert(python[1] == "ruff_fix" and python[2] == "ruff_organize_imports" and python[3] == "ruff_format")
assert(#python == 3)
assert(config.format_on_save(1).lsp_format == "fallback")
''')


PATH_HARNESS = r'''
local commands, notified = {}, nil
local settings = {basedpyright = {analysis = {typeCheckingMode = "standard"}}, python = {other = true}}
local client = {config = {settings = settings}, notify = function(_, method, params)
  assert(method == "workspace/didChangeConfiguration"); notified = params
end}
if arg[2] == "settings" then client.settings = settings end
vim = {
  api = {
    nvim_get_current_buf = function() return 17 end,
    nvim_buf_create_user_command = function(buf, name, callback, opts)
      assert(buf == 17); commands[name] = callback
      assert(opts.nargs == 1 and opts.complete == "file")
    end,
  },
  lsp = {get_clients = function(filter)
    assert(filter.bufnr == 17 and filter.name == "basedpyright"); return {client}
  end},
  tbl_deep_extend = function(_, existing, update)
    local result = {}; for k,v in pairs(existing) do result[k] = v end
    for k,v in pairs(update) do result[k] = v end
    return result
  end,
}
local config = assert(loadfile(arg[1] .. "/after/lsp/basedpyright.lua"))()
config.on_attach(client,17)
assert(commands.LspBasedpyrightSetPythonPath and commands.LspPyrightSetPythonPath)
assert(not commands.LspPyrightOrganizeImports, "import整理はRuffが担当する")
for _, name in ipairs({"LspBasedpyrightSetPythonPath", "LspPyrightSetPythonPath"}) do
  commands[name]({args = "/fixture env/bin/python"})
  assert(client.settings.python.pythonPath == "/fixture env/bin/python")
  assert(client.settings.python.other == true)
  assert(client.settings.basedpyright.analysis.typeCheckingMode == "standard")
  assert(notified.settings.python.pythonPath == "/fixture env/bin/python")
end
'''


if __name__ == "__main__":
    unittest.main()
