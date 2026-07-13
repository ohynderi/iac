from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render_fabric):
    pol = {"name": "mcp1", "admin_state": "enabled", "state": "absent"}
    body = render_fabric("intf_pol_mcp.json.j2", pol_name="mcp1", pol=pol)

    assert_matches(body, {
        "mcpIfPol": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
                "adminSt": ABSENT,
                "mcpPduPerVlan": ABSENT,
                "maxPduPerVlanLimit": ABSENT,
                "mcpMode": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_state_present_renders_defaults(render_fabric):
    pol = {"name": "mcp1", "admin_state": "enabled", "state": "present"}
    body = render_fabric("intf_pol_mcp.json.j2", pol_name="mcp1", pol=pol)

    assert_matches(body, {
        "mcpIfPol": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
                "adminSt": "enabled",
                "mcpPduPerVlan": "on",
                "maxPduPerVlanLimit": "256",
                "mcpMode": "off",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_does_not_crash(render_fabric):
    pol = {"name": "mcp1", "admin_state": "enabled"}
    body = render_fabric("intf_pol_mcp.json.j2", pol_name="mcp1", pol=pol)

    assert_matches(body, {
        "mcpIfPol": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_still_renders_nested_tag_state(render_fabric):
    pol = {"name": "mcp1", "admin_state": "enabled", "tags": [{"name": "t1", "value": "v1", "state": "absent"}]}
    body = render_fabric("intf_pol_mcp.json.j2", pol_name="mcp1", pol=pol)

    assert_matches(body, {
        "mcpIfPol": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "t1", "status": "deleted"}}},
            ],
        },
    })


def test_description_override(render_fabric):
    pol = {"name": "mcp1", "admin_state": "enabled", "description": "my mcp policy"}
    body = render_fabric("intf_pol_mcp.json.j2", pol_name="mcp1", pol=pol)

    assert_matches(body, {
        "mcpIfPol": {
            "attributes": {
                "descr": "my mcp policy",
            },
        },
    })


def test_mcp_per_vlan_and_max_number_of_vlan_overrides(render_fabric):
    pol = {"name": "mcp1", "admin_state": "enabled", "MCP_per_VLAN": "off", "max_number_of_vlan": 512}
    body = render_fabric("intf_pol_mcp.json.j2", pol_name="mcp1", pol=pol)

    assert_matches(body, {
        "mcpIfPol": {
            "attributes": {
                "mcpPduPerVlan": "off",
                "maxPduPerVlanLimit": "512",
            },
        },
    })


def test_mcp_mode_strict_renders_on(render_fabric):
    pol = {"name": "mcp1", "admin_state": "enabled", "mcp_mode": "strict"}
    body = render_fabric("intf_pol_mcp.json.j2", pol_name="mcp1", pol=pol)

    assert_matches(body, {
        "mcpIfPol": {
            "attributes": {
                "mcpMode": "on",
            },
        },
    })


def test_mcp_mode_non_strict_renders_off(render_fabric):
    pol = {"name": "mcp1", "admin_state": "enabled", "mcp_mode": "non-strict"}
    body = render_fabric("intf_pol_mcp.json.j2", pol_name="mcp1", pol=pol)

    assert_matches(body, {
        "mcpIfPol": {
            "attributes": {
                "mcpMode": "off",
            },
        },
    })


def test_tags_render_with_state(render_fabric):
    pol = {
        "name": "mcp1", "admin_state": "enabled",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render_fabric("intf_pol_mcp.json.j2", pol_name="mcp1", pol=pol)

    assert_matches(body, {
        "mcpIfPol": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1", "value": "value1", "status": "created,modified"}}},
                {"tagAnnotation": {"attributes": {"key": "tag2", "value": "value2", "status": "deleted"}}},
            ],
        },
    })
