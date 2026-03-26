from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from update_quickstart_notebook import render_quickstart_template_dict


def test_readme_quickstart_uses_canonical_article_template():
    readme = (REPO_ROOT / "README.md").read_text()
    assert render_quickstart_template_dict() in readme
