"""mini.testのlazy.nvim公開設定を、実プラグインを使わず検証する。"""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
LUA = shutil.which("lua")


@unittest.skipUnless(LUA, "Luaが必要です")
class NeovimPluginTestConfigTests(unittest.TestCase):
    def test_mini_test_loads_for_lua_with_setup_options_and_pinned_revision(self):
        source = ROOT / "home/dot_config/nvim/lua/plugins/editor/mini-test.lua"
        with tempfile.TemporaryDirectory(prefix="mini-test-config-") as home:
            result = subprocess.run(
                [LUA, "-", str(source)],
                input='''
local spec = assert(loadfile(arg[1]))()
assert(spec[1] == "nvim-mini/mini.test")
assert(spec.ft == "lua")
assert(type(spec.opts) == "table", "lazy.nvimのoptsでsetupを有効にする")
assert(type(spec.commit) == "string" and #spec.commit == 40 and spec.commit:match("^%x+$"),
  "検証したrevisionに固定する")
''',
                text=True, capture_output=True, timeout=5,
                env={"HOME": home, "PATH": "", "LANG": "C"},
            )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
