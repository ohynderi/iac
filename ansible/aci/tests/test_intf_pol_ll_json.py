from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render_fabric):
    pol = {"name": "1g_ll", "auto_negotiation": True, "speed": "1G", "state": "absent"}
    body = render_fabric("intf_pol_ll.json.j2", pol_name="1g_ll", pol=pol)

    assert_matches(body, {
        "fabricHIfPol": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
                "autoNeg": ABSENT,
                "speed": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_state_present_renders_defaults(render_fabric):
    pol = {"name": "1g_ll", "auto_negotiation": True, "speed": "1G", "state": "present"}
    body = render_fabric("intf_pol_ll.json.j2", pol_name="1g_ll", pol=pol)

    assert_matches(body, {
        "fabricHIfPol": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
                "autoNeg": "on",
                "speed": "1G",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_does_not_crash(render_fabric):
    pol = {"name": "1g_ll", "auto_negotiation": True, "speed": "1G"}
    body = render_fabric("intf_pol_ll.json.j2", pol_name="1g_ll", pol=pol)

    assert_matches(body, {
        "fabricHIfPol": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_still_renders_nested_tag_state(render_fabric):
    pol = {
        "name": "1g_ll", "auto_negotiation": True, "speed": "1G",
        "tags": [{"name": "t1", "value": "v1", "state": "absent"}],
    }
    body = render_fabric("intf_pol_ll.json.j2", pol_name="1g_ll", pol=pol)

    assert_matches(body, {
        "fabricHIfPol": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "t1", "status": "deleted"}}},
            ],
        },
    })


def test_description_override(render_fabric):
    pol = {"name": "1g_ll", "auto_negotiation": True, "speed": "1G", "description": "my link layer policy"}
    body = render_fabric("intf_pol_ll.json.j2", pol_name="1g_ll", pol=pol)

    assert_matches(body, {
        "fabricHIfPol": {
            "attributes": {
                "descr": "my link layer policy",
            },
        },
    })


def test_auto_negotiation_true_renders_on(render_fabric):
    pol = {"name": "1g_ll", "auto_negotiation": True, "speed": "1G"}
    body = render_fabric("intf_pol_ll.json.j2", pol_name="1g_ll", pol=pol)

    assert_matches(body, {
        "fabricHIfPol": {
            "attributes": {
                "autoNeg": "on",
            },
        },
    })


def test_auto_negotiation_false_renders_off(render_fabric):
    pol = {"name": "1g_ll", "auto_negotiation": False, "speed": "1G"}
    body = render_fabric("intf_pol_ll.json.j2", pol_name="1g_ll", pol=pol)

    assert_matches(body, {
        "fabricHIfPol": {
            "attributes": {
                "autoNeg": "off",
            },
        },
    })


def test_speed_override(render_fabric):
    pol = {"name": "40g_ll", "auto_negotiation": True, "speed": "40G"}
    body = render_fabric("intf_pol_ll.json.j2", pol_name="40g_ll", pol=pol)

    assert_matches(body, {
        "fabricHIfPol": {
            "attributes": {
                "speed": "40G",
            },
        },
    })


def test_tags_render_with_state(render_fabric):
    pol = {
        "name": "1g_ll", "auto_negotiation": True, "speed": "1G",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render_fabric("intf_pol_ll.json.j2", pol_name="1g_ll", pol=pol)

    assert_matches(body, {
        "fabricHIfPol": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1", "value": "value1", "status": "created,modified"}}},
                {"tagAnnotation": {"attributes": {"key": "tag2", "value": "value2", "status": "deleted"}}},
            ],
        },
    })
