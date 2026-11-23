"""共通キーの衝突と、プラグインへ渡すキー・実行先を隔離検証する。"""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
NVIM = ROOT / "home/dot_config/nvim"
LUA = shutil.which("lua")


@unittest.skipUnless(LUA, "Luaが必要です")
class NeovimKeymapTests(unittest.TestCase):
    def run_lua(self, script):
        with tempfile.TemporaryDirectory(prefix="neovim keymaps ") as home:
            result = subprocess.run(
                [LUA, "-", str(NVIM)], input=HARNESS + script, text=True,
                capture_output=True, timeout=5, cwd=home,
                env={"HOME": home, "PATH": "", "LANG": "C"},
            )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_common_and_plugin_keys_have_distinct_actions(self):
        self.run_lua(r'''
load_spec("config/keymaps")
for _, name in ipairs({"utils/snacks/index", "editor/csvview", "utils/lazygit"}) do
  local spec = load_spec("plugins/" .. name)
  for _, key in ipairs(spec.keys) do
    record(key.mode or "n", key[1], key[2], key)
  end
end
local seen = {}
for _, map in ipairs(maps) do
  local lhs = normalize(map.lhs)
  local id = map.mode .. ":" .. lhs
  assert(not seen[id], "同じモードのキーが競合する: " .. id)
  seen[id] = true
end
''')

    def test_picker_bindings_keep_both_variants_accessible(self):
        self.run_lua(r'''
local spec = load_spec("plugins/utils/snacks/index")
local expected = {
  ["grr"]="lsp_references", ["<leader>lD"]="lsp_declarations",
  ["<leader>sn"]="notifications", ["<leader>sc"]="command_history",
  ["<leader>fr"]="recent",
}
for lhs, action in pairs(expected) do
  local key = find_key(spec, lhs)
  key[2]()
  assert(last_action == action, lhs)
  assert(not key.nowait, "LSPの長いキー列を妨げない")
end
find_key(spec, "<leader>n")[2]()
assert(last_action == "notification_history")
''')

    def test_oldfiles_and_csv_commands_have_separate_complete_bindings(self):
        self.run_lua(r'''
load_spec("config/keymaps")
local oldfiles
for _, map in ipairs(maps) do
  if normalize(map.lhs) == " fR" then oldfiles = map end
end
assert(oldfiles and oldfiles.mode == "n")
assert(oldfiles.rhs == "<cmd>oldfiles<CR>", "履歴一覧コマンドをそのまま実行する")
local csv = find_key(load_spec("plugins/editor/csvview"), "<leader>cv")
assert(csv[2] == "<Cmd>CsvViewToggle<CR>")
assert(type(csv.desc) == "string" and #csv.desc > 0)
''')

    def test_file_picker_uses_current_file_directory(self):
        self.run_lua(r'''
vim.bo.filetype = "lua"
find_key(load_spec("plugins/utils/snacks/index"), "<C-j><space>f")[2]()
assert(last_action == "files" and last_options.dirs[1] == "/project space/src")
''')

    def test_file_picker_preserves_oil_directory(self):
        self.run_lua(r'''
vim.bo.filetype = "oil"
vim.fn.expand = function() error("Oilのディレクトリを優先する") end
package.preload.oil = function()
  return {get_current_dir=function() return "/oil directory/" end}
end
find_key(load_spec("plugins/utils/snacks/index"), "<C-j><space>f")[2]()
assert(last_action == "files" and last_options.dirs[1] == "/oil directory/")
''')

    def test_quicker_setup_receives_working_buffer_key_commands(self):
        self.run_lua(r'''
local spec = load_spec("plugins/ui/quicker")
assert(type(spec.opts) == "table", "lazy.nvimのoptsでsetupへ渡す")
local actions = { [">"]="expand", ["<"]="collapse", gr="refresh" }
package.preload.quicker = function()
  local quicker = {}
  for _, action in pairs(actions) do
    local name = action
    quicker[name] = function() last_action = name end
  end
  return quicker
end
local count = 0
for _, key in ipairs(spec.opts.keys) do
  local command = assert(key[2]:match("^<cmd>lua (.-)<CR>$"))
  assert(loadstring(command))()
  assert(last_action == actions[key[1]], key[1])
  count = count + 1
end
assert(count == 3)
''')

    def test_lazygit_key_has_description_in_mapping_options(self):
        self.run_lua(r'''
local key = find_key(load_spec("plugins/utils/lazygit"), "<leader>lg")
assert(key[2] == "<cmd>LazyGit<CR>")
assert(type(key.desc) == "string" and #key.desc > 0, "キー定義のdescで説明を渡す")
''')


HARNESS = r'''
os.execute = function() error("外部コマンドを実行しない") end
io.popen = os.execute
maps = {}
function normalize(lhs)
  return lhs:gsub("<leader>", " "):gsub("<[Ss]pace>", " ")
end
function record(mode, lhs, rhs, opts)
  for _, m in ipairs(type(mode) == "table" and mode or {mode}) do
    maps[#maps+1] = {mode=m,lhs=lhs,rhs=rhs,opts=opts or {}}
  end
end
vim = {
  g={}, bo={}, keymap={set=record},
  fn={
    stdpath=function() return "/isolated config" end,
    expand=function(expr)
      assert(expr == "%:p:h")
      return "/project space/src"
    end,
  },
}
function load_spec(name)
  return assert(loadfile(arg[1] .. "/lua/" .. name .. ".lua"))()
end
function find_key(spec, lhs)
  for _, key in ipairs(spec.keys) do
    if normalize(key[1]) == normalize(lhs) then return key end
  end
  error("キーが見つからない: " .. lhs)
end
Snacks = {
  picker=setmetatable({}, {__index=function(_, name)
    return function(opts) last_action=name; last_options=opts end
  end}),
  notifier={show_history=function() last_action="notification_history" end},
}
'''


if __name__ == "__main__":
    unittest.main()
