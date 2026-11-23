"""実設定を使わず、確認対象のchezmoiテンプレートを隔離して展開する。"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


def render_template(path, flags=None):
    chezmoi = shutil.which("chezmoi")
    if not chezmoi:
        raise unittest.SkipTest("chezmoiが必要です")
    with tempfile.TemporaryDirectory(prefix="chezmoi template ") as directory:
        base = Path(directory)
        (base / "source").mkdir()
        (base / "home").mkdir()
        config = base / "config.json"
        config.write_text(json.dumps({"data": flags or {}}))
        result = subprocess.run(
            [chezmoi, "--config", str(config), "--source", str(base / "source"),
             "--destination", str(base / "home"), "--cache", str(base / "cache"),
             "--persistent-state", str(base / "state.db"),
             "--refresh-externals=never", "--no-tty", "execute-template"],
            input=Path(path).read_text(), text=True, capture_output=True,
            check=True, timeout=10,
            env={"HOME": str(base / "home"), "PATH": os.defpath},
        )
    return result.stdout
