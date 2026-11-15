"""Deno・Node・Biomeの接続と整形の分岐をダミー環境で検証する。"""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
NVIM = ROOT / "home/dot_config/nvim"
LUA = shutil.which("lua")


@unittest.skipUnless(LUA, "Luaが必要です")
class WebLspTests(unittest.TestCase):
    def run_lua(self, script, scenario):
        with tempfile.TemporaryDirectory(prefix="web lsp ") as home:
            result = subprocess.run(
                [LUA, "-", str(NVIM), scenario], input=script, text=True,
                capture_output=True, timeout=5,
                env={"HOME": home, "PATH": "", "LANG": "C"},
            )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_plain_git_project_uses_typescript_not_deno(self):
        self.run_lua(ROOT_HARNESS, "plain")

    def test_deno_config_wins_at_same_root(self):
        self.run_lua(ROOT_HARNESS, "deno")

    def test_deno_lock_only_project_excludes_typescript(self):
        self.run_lua(ROOT_HARNESS, "lock")

    def test_nested_node_lock_is_a_deno_boundary(self):
        self.run_lua(ROOT_HARNESS, "node-child")

    def test_nested_deno_project_excludes_typescript(self):
        self.run_lua(ROOT_HARNESS, "deno-child")

    def test_biome_binary_uses_project_path_with_spaces(self):
        self.run_lua(BIOME_HARNESS, "local")

    def test_biome_binary_falls_back_to_path(self):
        self.run_lua(BIOME_HARNESS, "global")

    def test_web_formatters_follow_buffer_not_current_directory(self):
        self.run_lua(FORMAT_HARNESS, "all")


ROOT_HARNESS = r'''
local mode = arg[2]
local scenarios = {
  plain = {git="/repo", expected="/repo"},
  deno = {deno="/repo", node="/repo"},
  lock = {deno="/repo", git="/repo"},
  ["node-child"] = {deno="/repo", node="/repo/node", expected="/repo/node"},
  ["deno-child"] = {deno="/repo/deno", node="/repo"},
}
local scenario = scenarios[mode]
vim = {
  fs = {root = function(bufnr, markers)
    assert(bufnr == 7)
    if markers[1] == "deno.json" then return scenario.deno end
    if type(markers[1]) == "table" then return scenario.node or scenario.git end
    return scenario.node
  end},
  fn = {
    getcwd = function() return "/unrelated" end,
    exepath = function() return "" end,
  },
  notify = function() end,
  log = {levels = {WARN = 2}},
}
package.path = arg[1] .. "/lua/?.lua;" .. package.path
local project = require("config.web-project")
local deno = project.deno_root(7)
local node = project.typescript_root(7)
if scenario.expected then
  assert(not deno); assert(node == scenario.expected, tostring(node))
else
  assert(deno == scenario.deno); assert(not node)
end
local called
local denols = assert(loadfile(arg[1] .. "/after/lsp/denols.lua"))()
denols.root_dir(7,function(root) called=root end)
assert(called == deno)
called = nil
local vtsls = assert(loadfile(arg[1] .. "/after/lsp/vtsls.lua"))()
vtsls.root_dir(7,function(root) called=root end)
assert(called == node)
'''

BIOME_HARNESS = r'''
local expected = arg[2] == "local" and "/project space/node_modules/.bin/biome" or "biome"
vim = {
  fs = {joinpath = function(...) return table.concat({...}, "/") end},
  fn = {executable = function(path)
    assert(path == "/project space/node_modules/.bin/biome")
    return arg[2] == "local" and 1 or 0
  end},
  lsp = {rpc = {start = function(cmd, dispatchers, opts)
    assert(cmd[1] == expected and cmd[2] == "lsp-proxy")
    assert(dispatchers.marker and opts.cwd == "/project space")
    return "started"
  end}},
}
package.preload["lspconfig.util"] = function() return {} end
local config = assert(loadfile(arg[1] .. "/after/lsp/biome.lua"))()
assert(type(config.cmd) == "function")
assert(config.cmd({marker=true},{root_dir="/project space"}) == "started")
'''

FORMAT_HARNESS = r'''
vim = {
  api = {nvim_create_user_command = function() end},
  fn = {getcwd = function() return "/unrelated" end},
  fs = {root = function(bufnr, markers)
    if markers[1] == "deno.json" then return bufnr == 1 and "/repo/deno" or nil end
    if markers[1] == "biome.json" then return bufnr == 2 and "/repo/biome" or nil end
    return nil
  end},
}
package.path = arg[1] .. "/lua/?.lua;" .. package.path
local opts = assert(loadfile(arg[1] .. "/lua/plugins/lsp/conform.lua"))().opts()
for _,ft in ipairs({"javascript","typescript","json","jsonc","html","css"}) do
  assert(#opts.formatters_by_ft[ft](1) == 0,"DenoはLSP整形")
  local biome = opts.formatters_by_ft[ft](2)
  assert(biome[1] == "biome-check" and biome[2] == "prettierd" and biome.stop_after_first)
  local plain = opts.formatters_by_ft[ft](3)
  assert(#plain == 1 and plain[1] == "prettierd")
end
'''
