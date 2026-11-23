"""Nimの配布定義を、公式リリースの公開メタデータと照合する。"""

import unittest

from mise_config import load_mise_config


# 2026-11-14取得。ネットワークを使わず、URL・CPU・ダイジェストの組合せを検証する。
# https://api.github.com/repos/nim-lang/nightlies/releases/tags/
# 2026-11-13-version-2-4-b27dcb4f70883978e984e427cc24b64eeb7c875f
RELEASE = "2026-11-13-version-2-4-b27dcb4f70883978e984e427cc24b64eeb7c875f"
ASSETS = {
    "linux-arm64": ("linux_arm64.tar.xz", "58e86d84e679d003ec04320b2411cd10aefd942132f9eaf6c583012b22be3595"),
    "linux-x64": ("linux_x64.tar.xz", "0ee5b16e81852a956d4fddb4aa44b5958c645c992132fa43be45f489573ee325"),
    "macos-arm64": ("macosx_arm64.tar.xz", "0ba92eb537755ca3bdabd5add1a3b14ab114b382debdcdf647f5152675ef62a9"),
    "macos-x64": ("macosx_x64.tar.xz", "eb0486d36828027a84e36ad3747798adb1132fb42adec08cb759907c3e287d19"),
    "windows-x64": ("windows_x64.zip", "eb5345c78c989859c6642463069c1a389f83f6dc790a2283ba5931867e94daed"),
}


class NimConfigTests(unittest.TestCase):
    def setUp(self):
        self.nim = load_mise_config()["tools"]["nim"]

    def test_version_is_pinned_to_release_with_arm64_asset(self):
        self.assertEqual(self.nim["version"], "2.4.2")

    def test_each_platform_matches_published_asset_and_digest(self):
        platforms = self.nim["platforms"]
        self.assertEqual(set(platforms), {*ASSETS, "windows-arm64"})
        for platform, (suffix, digest) in ASSETS.items():
            with self.subTest(platform=platform):
                asset = platforms[platform]
                self.assertEqual(
                    asset["url"],
                    f"https://github.com/nim-lang/nightlies/releases/download/{RELEASE}/nim-2.4.2-{suffix}",
                )
                self.assertEqual(asset.get("checksum"), f"sha256:{digest}")

    def test_windows_arm64_keeps_x64_fallback_and_archive_layout(self):
        platforms = self.nim["platforms"]
        self.assertEqual(platforms["windows-arm64"], platforms["windows-x64"])
        self.assertEqual(str(self.nim["strip_components"]), "1")


if __name__ == "__main__":
    unittest.main()
