import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1] / "plugins" / "agent-code-intelligence"


def test_vendored_plugin_package_is_valid() -> None:
    subprocess.run(
        [sys.executable, str(PLUGIN_ROOT / "tests" / "test_plugin.py")],
        cwd=PLUGIN_ROOT,
        check=True,
    )
