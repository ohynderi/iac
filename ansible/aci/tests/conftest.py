import json
from pathlib import Path

import jinja2
import pytest
import yaml

ROLES_DIR = Path(__file__).resolve().parents[1] / "roles"

ROLE_DIR = ROLES_DIR / "tenant"
TEMPLATES_DIR = ROLE_DIR / "templates"
ROLE_VARS = yaml.safe_load((ROLE_DIR / "vars" / "main.yml").read_text())

FABRIC_ROLE_DIR = ROLES_DIR / "fabric"
FABRIC_TEMPLATES_DIR = FABRIC_ROLE_DIR / "templates"
FABRIC_ROLE_VARS = yaml.safe_load((FABRIC_ROLE_DIR / "vars" / "main.yml").read_text())


def _make_render(templates_dir, role_vars):
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(templates_dir)),
        undefined=jinja2.StrictUndefined,
    )

    def _render(template_name, **context):
        text = env.get_template(template_name).render(**{**role_vars, **context})
        return json.loads(text)

    return _render


@pytest.fixture
def render():
    """Render a tenant role template exactly like Ansible would and parse it as JSON.

    Uses StrictUndefined so an unset variable raises the same
    'has no attribute' error Ansible raises, instead of silently
    rendering as an empty string. Role vars (e.g. the *_default_*
    values in vars/main.yml) are loaded automatically as a base
    context, matching how Ansible would supply them; pass a kwarg
    of the same name to override one for a specific test.
    """
    return _make_render(TEMPLATES_DIR, ROLE_VARS)


@pytest.fixture
def render_fabric():
    """Same as `render`, but for the fabric role's templates/vars."""
    return _make_render(FABRIC_TEMPLATES_DIR, FABRIC_ROLE_VARS)
