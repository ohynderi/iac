import json
from pathlib import Path

import jinja2
import pytest
import yaml

ROLE_DIR = Path(__file__).resolve().parents[1] / "roles" / "tenant"
TEMPLATES_DIR = ROLE_DIR / "templates"
ROLE_VARS = yaml.safe_load((ROLE_DIR / "vars" / "main.yml").read_text())


@pytest.fixture
def render():
    """Render a role template exactly like Ansible would and parse it as JSON.

    Uses StrictUndefined so an unset variable raises the same
    'has no attribute' error Ansible raises, instead of silently
    rendering as an empty string. Role vars (e.g. the *_default_*
    values in vars/main.yml) are loaded automatically as a base
    context, matching how Ansible would supply them; pass a kwarg
    of the same name to override one for a specific test.
    """
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        undefined=jinja2.StrictUndefined,
    )

    def _render(template_name, **context):
        text = env.get_template(template_name).render(**{**ROLE_VARS, **context})
        return json.loads(text)

    return _render
