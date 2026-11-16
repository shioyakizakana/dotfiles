"""DAPの登録・Python選択・UIイベント・キー操作を隔離検証する。"""

from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
NVIM = ROOT / "home/dot_config/nvim"
LUA = shutil.which("lua")


class NeovimDapDependencyTests(unittest.TestCase):
    def test_debugpy_has_managed_tool_definition(self):
        tools = tomllib.loads((ROOT / "home/dot_config/mise/config.toml").read_text())["tools"]
        debugpy = tools["pipx:debugpy"]
        self.assertTrue(debugpy["version"])
        self.assertEqual(debugpy["uvx_args"], "--python 3.13")
        self.assertEqual(debugpy["pipx_args"], "--python python3.13")


@unittest.skipUnless(LUA, "Luaが必要です")
class NeovimDapTests(unittest.TestCase):
    def run_lua(self, script, *arguments):
        with tempfile.TemporaryDirectory(prefix="neovim dap ") as home:
            result = subprocess.run(
                [LUA, "-", str(NVIM), *arguments], input=script, text=True,
                capture_output=True, timeout=5,
                env={"HOME": home, "PATH": "", "LANG": "C"},
            )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_adapters_load_with_supported_dap_api(self):
        self.run_lua(ADAPTER_HARNESS + r'''
load_adapters()
assert(dap.configurations.lua and dap.configurations.python, "言語ごとの設定を登録する")
''')

    def test_lua_attach_configuration_matches_registered_adapter(self):
        self.run_lua(ADAPTER_HARNESS + r'''
load_adapters()
local config = dap.configurations.lua[1]
assert(config.type and dap.adapters[config.type], "Luaのtypeが登録済みアダプターを指す")
assert(config.request == "attach")
''')

    def test_lua_adapter_preserves_default_and_custom_endpoint(self):
        self.run_lua(ADAPTER_HARNESS + r'''
load_adapters()
local endpoint
dap.adapters.nlua(function(value) endpoint = value end, {})
assert(endpoint.type == "server" and endpoint.host == "127.0.0.1" and endpoint.port == 8086)
dap.adapters.nlua(function(value) endpoint = value end, {host="127.0.0.2",port=9000})
assert(endpoint.host == "127.0.0.2" and endpoint.port == 9000)
''')

    def test_python_launch_has_matching_adapter(self):
        self.run_lua(ADAPTER_HARNESS + r'''
load_adapters()
local config = dap.configurations.python[1]
assert(config.request == "launch" and config.program == "${file}")
assert(dap.adapters[config.type], "Pythonの起動先アダプターを登録する")
''')

    def test_python_interpreter_uses_supported_option(self):
        self.run_lua(ADAPTER_HARNESS + r'''
load_adapters()
assert(type(dap.configurations.python[1].pythonPath) == "function", "pythonPathで対象Pythonを選ぶ")
''')

    def test_debugpy_adapter_uses_its_own_path_with_spaces(self):
        self.run_lua(ADAPTER_HARNESS + r'''
vim.fn.exepath = function(name)
  assert(name == "debugpy-adapter")
  return "/managed debug tools/bin/debugpy-adapter"
end
load_adapters()
local adapter
dap.adapters.python(function(value) adapter = value end)
assert(adapter.type == "executable")
assert(adapter.command == "/managed debug tools/bin/debugpy-adapter")
''')

    def test_missing_debugpy_reports_error_without_starting_adapter(self):
        self.run_lua(ADAPTER_HARNESS + r'''
load_adapters()
local called = false
local ok, message = pcall(dap.adapters.python, function() called = true end)
assert(not ok and tostring(message):find("debugpy-adapter",1,true))
assert(not called)
''')

    def test_python_uses_project_dotvenv_with_spaces(self):
        self.run_lua(PYTHON_PATH_HARNESS, ".venv")

    def test_python_uses_project_venv_with_spaces(self):
        self.run_lua(PYTHON_PATH_HARNESS, "venv")

    def test_python_fallback_uses_executable_on_path(self):
        self.run_lua(PYTHON_PATH_HARNESS, "path")

    def test_python_preserves_venv_priority_when_both_exist(self):
        self.run_lua(ADAPTER_HARNESS + r'''
vim.fn.executable = function(path)
  return (path == "/project space/venv/bin/python" or path == "/project space/.venv/bin/python") and 1 or 0
end
load_adapters()
assert(dap.configurations.python[1].pythonPath() == "/project space/venv/bin/python")
''')

    def test_python_fallback_supports_python_command(self):
        self.run_lua(ADAPTER_HARNESS + r'''
vim.fn.exepath = function(name) return name == "python" and "/tools/python" or "" end
vim.fn.executable = function(path) return path == "/tools/python" and 1 or 0 end
load_adapters()
assert(dap.configurations.python[1].pythonPath() == "/tools/python")
''')

    def test_missing_target_python_reports_error(self):
        self.run_lua(ADAPTER_HARNESS + r'''
load_adapters()
local ok, message = pcall(dap.configurations.python[1].pythonPath)
assert(not ok and tostring(message):find("Python",1,true))
''')

    def test_ui_config_loads_with_supported_listener_tables(self):
        self.run_lua(UI_HARNESS, "strict")

    def test_ui_opens_after_python_initialization(self):
        self.run_lua(UI_HARNESS, "python")

    def test_ui_does_not_open_automatically_for_lua_attach(self):
        self.run_lua(UI_HARNESS, "lua")

    def test_ui_reconfiguration_does_not_duplicate_listener(self):
        self.run_lua(UI_HARNESS, "reload")

    def test_function_keys_invoke_debug_actions(self):
        self.run_lua(KEY_HARNESS + r'''
local expected = {
  {"<F5>", "continue"}, {"<F10>", "step_over"},
  {"<F11>", "step_into"}, {"<F12>", "step_out"},
}
local missing = {}
for _, binding in ipairs(expected) do
  if not keys[binding[1]] then missing[#missing+1] = binding[1] end
end
assert(#missing == 0, "関数キー未登録: " .. table.concat(missing, ", "))
for _, binding in ipairs(expected) do
  last_action = nil
  keys[binding[1]][2]()
  assert(last_action == binding[2], binding[1])
end
''')

    def test_key_bindings_do_not_shadow_other_actions(self):
        self.run_lua(KEY_HARNESS + r'''
local seen = {}
for _, spec in ipairs(specs) do
  local modes = type(spec.mode) == "table" and spec.mode or {spec.mode or "n"}
  for _, mode in ipairs(modes) do
    local id = mode .. ":" .. spec[1]
    assert(not seen[id], "同じモードのキー重複: " .. id)
    seen[id] = true
  end
end
''')

    def test_breakpoint_and_ui_toggle_remain_usable(self):
        self.run_lua(KEY_HARNESS + r'''
keys["<leader>b"][2]()
assert(last_action == "toggle_breakpoint")
keys["<F7>"][2]()
assert(last_action == "toggle_ui")
''')

    def test_logpoint_and_repl_use_distinct_working_keys(self):
        self.run_lua(KEY_HARNESS + r'''
vim = {fn = {input = function() return "value={value}" end}}
dap_mock.set_breakpoint = function(condition, hit, message)
  assert(condition == nil and hit == nil and message == "value={value}")
  last_action = "logpoint"
end
dap_mock.repl = {open = function() last_action = "repl" end}
keys["<leader>dL"][2]()
assert(last_action == "logpoint")
keys["<leader>dr"][2]()
assert(last_action == "repl")
''')


ADAPTER_HARNESS = r'''
dap = {configurations = {}, adapters = {}}
package.preload.dap = function() return dap end
os.execute = function() error("外部コマンドを実行しない") end
io.popen = os.execute
local cwd = "/project space"
vim = {
  env = {},
  fn = {
    getcwd = function() return cwd end,
    executable = function() return 0 end,
    exepath = function() return "" end,
  },
  fs = {joinpath = function(...) return table.concat({...}, "/") end},
}
function load_adapters()
  assert(loadfile(arg[1] .. "/lua/plugins/dap/adapters.lua"))()
end
'''


PYTHON_PATH_HARNESS = ADAPTER_HARNESS + r'''
local project_python = "/project space/" .. arg[2] .. "/bin/python"
local path_python = "/managed tools/bin/python3"
vim.fn.executable = function(path)
  return (arg[2] ~= "path" and path == project_python or path == path_python) and 1 or 0
end
vim.fn.exepath = function(name)
  return name == "python3" and path_python or ""
end
load_adapters()
local config = dap.configurations.python[1]
local choose_python = config.pythonPath
assert(type(choose_python) == "function")
local actual = choose_python()
local expected = arg[2] == "path" and path_python or project_python
assert(actual == expected, "Python選択: " .. tostring(actual) .. " / 期待値: " .. expected)
'''


UI_HARNESS = r'''
local function listeners()
  return setmetatable({}, {__index = function(tbl, event)
    local callbacks = {}; rawset(tbl, event, callbacks); return callbacks
  end})
end
local dap = {listeners = {before = listeners(), after = listeners(), on_session = {}, on_config = {}}}
local configured = false
local opened = 0
vim = {g = {}}
package.preload.dap = function() return dap end
package.preload["dap-view"] = function() return {
  setup = function(opts) configured = type(opts.winbar.sections) == "table" end,
  open = function() opened = opened + 1 end,
} end
package.preload["plugins.dap.keymaps"] = function() return {} end
package.preload["plugins.dap.adapters"] = function() return {} end
local spec = assert(loadfile(arg[1] .. "/lua/plugins/dap/index.lua"))()
spec.config({},spec.opts)
assert(configured, "DAP UIを初期化する")
local registered = 0
for _, group in pairs(dap.listeners) do
  for _, value in pairs(group) do
    if type(value) == "function" then registered = registered + 1 end
    if type(value) == "table" then
      for _, callback in pairs(value) do
        if type(callback) == "function" then registered = registered + 1 end
      end
    end
  end
end
assert(registered > 0, "サポートされるリスナーへUI連携を登録する")
if arg[2] == "reload" then spec.config({},spec.opts) end
if arg[2] ~= "strict" then
  local kind = arg[2] == "lua" and "nlua" or "python"
  for _, callback in pairs(dap.listeners.after.event_initialized) do
    callback({config = {type = kind, name = "fixture"}})
  end
  assert(opened == (kind == "nlua" and 0 or 1), "初期化イベントでのUI表示回数")
end
'''


KEY_HARNESS = r'''
last_action = nil
local dap = {}
dap_mock = dap
for _, name in ipairs({"continue", "step_over", "step_into", "step_out", "toggle_breakpoint"}) do
  local action = name
  dap[name] = function() last_action = action end
end
package.preload.dap = function() return dap end
package.preload["dap-view"] = function() return {
  toggle = function() last_action = "toggle_ui" end,
} end
specs = assert(loadfile(arg[1] .. "/lua/plugins/dap/keymaps.lua"))()
keys = {}
for _, spec in ipairs(specs) do keys[spec[1]] = spec end
'''
