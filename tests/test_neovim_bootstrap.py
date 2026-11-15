"""lazy.nvimの初期取得を、通信・実HOME・実プラグインなしで検証する。"""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
LUA = shutil.which("lua")
CONFIG = ROOT / "home/dot_config/nvim/lua/config/lazy.lua"


@unittest.skipUnless(LUA, "Luaが必要です")
class NeovimBootstrapTests(unittest.TestCase):
    def run_config(self, scenario):
        # 空のPATHと一時HOMEに加え、外部実行とファイル操作をLua側で置き換える。
        with tempfile.TemporaryDirectory(prefix="neovim bootstrap ") as directory:
            return subprocess.run(
                [LUA, "-", str(CONFIG), scenario],
                input=HARNESS, text=True, capture_output=True, timeout=5,
                env={"HOME": directory, "PATH": "", "LANG": "C"},
            )

    def test_existing_plugin_starts_without_clone_or_cleanup(self):
        result = self.run_config("existing")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("READY", result.stdout)
        self.assertNotIn("CLONE", result.stdout)
        self.assertNotIn("DELETE", result.stdout)

    def test_successful_clone_is_published_before_setup(self):
        result = self.run_config("success")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PUBLISH", result.stdout)
        self.assertIn("READY", result.stdout)
        self.assertLess(result.stdout.index("PUBLISH"), result.stdout.index("READY"))

    def test_clone_failure_reports_output_and_exits_without_prompt(self):
        result = self.run_config("clone-failure")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixture clone failed", result.stdout)
        self.assertNotIn("WAIT", result.stdout)
        self.assertNotIn("READY", result.stdout)
        self.assertNotIn("PUBLISH", result.stdout)

    def test_partial_clone_is_removed_without_deleting_destination(self):
        result = self.run_config("clone-failure")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DELETE staging", result.stdout)
        self.assertNotIn("DELETE destination", result.stdout)

    def test_retry_after_failure_uses_a_clean_destination(self):
        result = self.run_config("retry")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("CLONE"), 2)
        self.assertEqual(result.stdout.count("READY"), 1)
        self.assertIn("DELETE staging", result.stdout)

    def test_system_exception_removes_staging_and_reports_reason(self):
        result = self.run_config("system-error")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixture system failed", result.stdout)
        self.assertIn("DELETE staging", result.stdout)
        self.assertNotIn("READY", result.stdout)

    def test_staging_creation_failure_does_not_clone(self):
        result = self.run_config("staging-failure")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixture staging failed", result.stdout)
        self.assertNotIn("CLONE", result.stdout)
        self.assertNotIn("READY", result.stdout)

    def test_publish_failure_removes_staging_and_stops(self):
        result = self.run_config("rename-failure")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixture rename failed", result.stdout)
        self.assertIn("DELETE staging", result.stdout)
        self.assertNotIn("READY", result.stdout)

    def test_concurrent_destination_is_preserved(self):
        result = self.run_config("concurrent")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DELETE staging", result.stdout)
        self.assertNotIn("DELETE destination", result.stdout)
        self.assertNotIn("PUBLISH", result.stdout)

    def test_cleanup_failure_is_reported(self):
        result = self.run_config("cleanup-failure")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixture clone failed", result.stdout)
        self.assertIn("cleanup", result.stdout.lower())
        self.assertNotIn("READY", result.stdout)


HARNESS = r'''
local config, scenario = arg[1], arg[2]
local parent = "/fixture data/lazy"
local destination = parent .. "/lazy.nvim"
local staging = parent .. "/lazy.nvim-fixture"
local exists = scenario == "existing"
local staged = false
local clone_failed = scenario == "clone-failure" or scenario == "cleanup-failure" or scenario == "retry"
local function stat(path)
  if path == destination and exists then return {type = "directory"} end
  return nil
end
local uv = {
  fs_stat = stat,
  fs_mkdtemp = function(template)
    assert(template == parent .. "/lazy.nvim-XXXXXX")
    if scenario == "staging-failure" then return nil, "fixture staging failed" end
    staged = true
    return staging
  end,
  fs_rename = function(source, target)
    assert(source == staging and target == destination and staged)
    if scenario == "rename-failure" then return nil, "fixture rename failed" end
    assert(not exists)
    staged, exists = false, true
    print("PUBLISH")
    return true
  end,
}
vim = {
  loop = uv, uv = uv, v = {shell_error = 0},
  fn = {
    stdpath = function(kind) assert(kind == "data"); return "/fixture data" end,
    fnamemodify = function(path, modifier)
      assert(path == destination and modifier == ":h"); return parent
    end,
    mkdir = function(path, mode) assert(path == parent and mode == "p"); return 1 end,
    system = function(command)
      assert(command[1] == "git" and command[2] == "clone")
      assert(command[3] == "--filter=blob:none" and command[5] == "--branch=stable")
      assert(command[4] == "https://github.com/folke/lazy.nvim.git")
      assert(command[6] == staging or command[6] == destination)
      print("CLONE")
      if scenario == "system-error" then error("fixture system failed") end
      if scenario == "concurrent" then exists = true end
      vim.v.shell_error = clone_failed and 128 or 0
      return clone_failed and "fixture clone failed" or "fixture clone succeeded"
    end,
    delete = function(path, mode)
      assert(mode == "rf")
      if path == destination then print("DELETE destination"); error("destination is protected") end
      assert(path == staging and staged)
      print("DELETE staging")
      if scenario == "cleanup-failure" then return -1 end
      staged = false
      return 0
    end,
  },
  getchar = function() print("WAIT"); error("input must not be requested") end,
  api = {
    nvim_echo = function(chunks)
      for _, chunk in ipairs(chunks) do
        assert(type(chunk[1]) == "string", "echo message must be a string")
        io.write(chunk[1])
      end
      io.write("\n")
    end,
  },
  opt = {rtp = {prepend = function(_, path) assert(path == destination) end}},
}
package.preload.lazy = function()
  return {setup = function() print("READY") end}
end
if scenario == "retry" then
  os.exit = function(code) assert(code == 1); error("fixture exit") end
  local ok, failure = pcall(assert(loadfile(config)))
  assert(not ok and failure:match("fixture exit"))
  assert(not exists and not staged, "retry requires a clean destination")
  clone_failed = false
end
assert(loadfile(config))()
'''


if __name__ == "__main__":
    unittest.main()
