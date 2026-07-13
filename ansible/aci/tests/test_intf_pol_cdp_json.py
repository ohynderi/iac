from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render_fabric):
    pol = {"name": "cdp1", "admin_state": "enabled", "state": "absent"}
    body = render_fabric("intf_pol_cdp.json.j2", pol_name="cdp1", pol=pol)

    assert_matches(body, {
        "cdpIfPol": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
                "adminSt": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_state_present_renders_defaults(render_fabric):
    pol = {"name": "cdp1", "admin_state": "enabled", "state": "present"}
    body = render_fabric("intf_pol_cdp.json.j2", pol_name="cdp1", pol=pol)

    assert_matches(body, {
        "cdpIfPol": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
                "adminSt": "enabled",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_does_not_crash(render_fabric):
    # Regression test: this must keep working now that the task's `when:`
    # uses has_nested_state, which lets this task run without pol.state
    # ever being set (e.g. only a nested tag carries its own state).
    pol = {"name": "cdp1", "admin_state": "enabled"}
    body = render_fabric("intf_pol_cdp.json.j2", pol_name="cdp1", pol=pol)

    assert_matches(body, {
        "cdpIfPol": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
                "adminSt": "enabled",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_still_renders_nested_tag_state(render_fabric):
    pol = {"name": "cdp1", "admin_state": "enabled", "tags": [{"name": "t1", "value": "v1", "state": "absent"}]}
    body = render_fabric("intf_pol_cdp.json.j2", pol_name="cdp1", pol=pol)

    assert_matches(body, {
        "cdpIfPol": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "t1", "status": "deleted"}}},
            ],
        },
    })


def test_description_override(render_fabric):
    pol = {"name": "cdp1", "admin_state": "enabled", "description": "my cdp policy"}
    body = render_fabric("intf_pol_cdp.json.j2", pol_name="cdp1", pol=pol)

    assert_matches(body, {
        "cdpIfPol": {
            "attributes": {
                "descr": "my cdp policy",
            },
        },
    })


def test_admin_state_disabled(render_fabric):
    pol = {"name": "cdp1", "admin_state": "disabled"}
    body = render_fabric("intf_pol_cdp.json.j2", pol_name="cdp1", pol=pol)

    assert_matches(body, {
        "cdpIfPol": {
            "attributes": {
                "adminSt": "disabled",
            },
        },
    })


def test_tags_render_with_state(render_fabric):
    # Also a regression test for the double-comma bug: rendering must
    # produce valid JSON with exactly 2 tag children when there's more
    # than one tag.
    pol = {
        "name": "cdp1",
        "admin_state": "enabled",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render_fabric("intf_pol_cdp.json.j2", pol_name="cdp1", pol=pol)

    assert_matches(body, {
        "cdpIfPol": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1", "value": "value1", "status": "created,modified"}}},
                {"tagAnnotation": {"attributes": {"key": "tag2", "value": "value2", "status": "deleted"}}},
            ],
        },
    })
