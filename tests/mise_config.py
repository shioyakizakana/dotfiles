"""実設定を使わず、管理ソースのmiseテンプレートを展開して解析する。"""

from pathlib import Path
import tomllib

from chezmoi_template import render_template


ROOT = Path(__file__).resolve().parents[1]


def load_mise_config(flags=None):
    return tomllib.loads(render_template(ROOT / "home/dot_config/mise/config.toml.tmpl", flags))
