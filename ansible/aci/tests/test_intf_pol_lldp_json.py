from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render_fabric):
    pol = {"name": "lldp1", "receive": "enabled", "transmit": "enabled", "state": "absent"}
    body = render_fabric("intf_pol_lldp.json.j2", pol_name="lldp1", pol=pol)

    assert_matches(body, {
        "lldpIfPol": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
                "adminRxSt": ABSENT,
                "adminTxSt": ABSENT,
                "portDCBXPVer": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_state_present_renders_defaults(render_fabric):
    pol = {"name": "lldp1", "receive": "enabled", "transmit": "enabled", "state": "present"}
    body = render_fabric("intf_pol_lldp.json.j2", pol_name="lldp1", pol=pol)

    assert_matches(body, {
        "lldpIfPol": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
                "adminRxSt": "enabled",
                "adminTxSt": "enabled",
                "portDCBXPVer": "CEE",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_does_not_crash(render_fabric):
    pol = {"name": "lldp1", "receive": "enabled", "transmit": "enabled"}
    body = render_fabric("intf_pol_lldp.json.j2", pol_name="lldp1", pol=pol)

    assert_matches(body, {
        "lldpIfPol": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_still_renders_nested_tag_state(render_fabric):
    pol = {
        "name": "lldp1", "receive": "enabled", "transmit": "enabled",
        "tags": [{"name": "t1", "value": "v1", "state": "absent"}],
    }
    body = render_fabric("intf_pol_lldp.json.j2", pol_name="lldp1", pol=pol)

    assert_matches(body, {
        "lldpIfPol": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "t1", "status": "deleted"}}},
            ],
        },
    })


def test_description_override(render_fabric):
    pol = {"name": "lldp1", "receive": "enabled", "transmit": "enabled", "description": "my lldp policy"}
    body = render_fabric("intf_pol_lldp.json.j2", pol_name="lldp1", pol=pol)

    assert_matches(body, {
        "lldpIfPol": {
            "attributes": {
                "descr": "my lldp policy",
            },
        },
    })


def test_receive_and_transmit_overrides(render_fabric):
    pol = {"name": "lldp1", "receive": "disabled", "transmit": "disabled"}
    body = render_fabric("intf_pol_lldp.json.j2", pol_name="lldp1", pol=pol)

    assert_matches(body, {
        "lldpIfPol": {
            "attributes": {
                "adminRxSt": "disabled",
                "adminTxSt": "disabled",
            },
        },
    })


def test_dcbxp_version_override(render_fabric):
    pol = {"name": "lldp1", "receive": "enabled", "transmit": "enabled", "DCBXP_version": "IEEE"}
    body = render_fabric("intf_pol_lldp.json.j2", pol_name="lldp1", pol=pol)

    assert_matches(body, {
        "lldpIfPol": {
            "attributes": {
                "portDCBXPVer": "IEEE",
            },
        },
    })


def test_tags_render_with_state(render_fabric):
    pol = {
        "name": "lldp1", "receive": "enabled", "transmit": "enabled",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render_fabric("intf_pol_lldp.json.j2", pol_name="lldp1", pol=pol)

    assert_matches(body, {
        "lldpIfPol": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1", "value": "value1", "status": "created,modified"}}},
                {"tagAnnotation": {"attributes": {"key": "tag2", "value": "value2", "status": "deleted"}}},
            ],
        },
    })
