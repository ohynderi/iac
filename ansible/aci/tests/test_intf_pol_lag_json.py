from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render_fabric):
    pol = {"name": "lag1", "mode": "active", "state": "absent"}
    body = render_fabric("intf_pol_lag.json.j2", pol_name="lag1", pol=pol)

    assert_matches(body, {
        "lacpLagPol": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
                "mode": ABSENT,
                "minLinks": ABSENT,
                "maxLinks": ABSENT,
                "ctrl": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_state_present_renders_defaults(render_fabric):
    pol = {"name": "lag1", "mode": "active", "state": "present"}
    body = render_fabric("intf_pol_lag.json.j2", pol_name="lag1", pol=pol)

    assert_matches(body, {
        "lacpLagPol": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
                "mode": "active",
                "minLinks": "1",
                "maxLinks": "16",
                "ctrl": "fast-sel-hot-stdby,graceful-conv,susp-individual",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_does_not_crash(render_fabric):
    pol = {"name": "lag1", "mode": "active"}
    body = render_fabric("intf_pol_lag.json.j2", pol_name="lag1", pol=pol)

    assert_matches(body, {
        "lacpLagPol": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_still_renders_nested_tag_state(render_fabric):
    pol = {"name": "lag1", "mode": "active", "tags": [{"name": "t1", "value": "v1", "state": "absent"}]}
    body = render_fabric("intf_pol_lag.json.j2", pol_name="lag1", pol=pol)

    assert_matches(body, {
        "lacpLagPol": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "t1", "status": "deleted"}}},
            ],
        },
    })


def test_description_and_mode_overrides(render_fabric):
    pol = {"name": "lag1", "mode": "off", "description": "my lag policy"}
    body = render_fabric("intf_pol_lag.json.j2", pol_name="lag1", pol=pol)

    assert_matches(body, {
        "lacpLagPol": {
            "attributes": {
                "descr": "my lag policy",
                "mode": "off",
            },
        },
    })


def test_min_and_max_overrides(render_fabric):
    pol = {"name": "lag1", "mode": "active", "min": 2, "max": 8}
    body = render_fabric("intf_pol_lag.json.j2", pol_name="lag1", pol=pol)

    assert_matches(body, {
        "lacpLagPol": {
            "attributes": {
                "minLinks": "2",
                "maxLinks": "8",
            },
        },
    })


def test_ctrl_flags_all_enabled(render_fabric):
    pol = {
        "name": "lag1", "mode": "active",
        "fast_select_hot_standby_ports": True,
        "graceful_convergence": True,
        "suspend_individual_port": True,
        "symmetric_hashing": True,
    }
    body = render_fabric("intf_pol_lag.json.j2", pol_name="lag1", pol=pol)

    assert_matches(body, {
        "lacpLagPol": {
            "attributes": {
                "ctrl": "fast-sel-hot-stdby,graceful-conv,susp-individual,symmetric-hash",
            },
        },
    })


def test_ctrl_flags_all_disabled(render_fabric):
    pol = {
        "name": "lag1", "mode": "active",
        "fast_select_hot_standby_ports": False,
        "graceful_convergence": False,
        "suspend_individual_port": False,
        "symmetric_hashing": False,
    }
    body = render_fabric("intf_pol_lag.json.j2", pol_name="lag1", pol=pol)

    assert_matches(body, {
        "lacpLagPol": {
            "attributes": {
                "ctrl": "",
            },
        },
    })


def test_tags_render_with_state(render_fabric):
    pol = {
        "name": "lag1", "mode": "active",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render_fabric("intf_pol_lag.json.j2", pol_name="lag1", pol=pol)

    assert_matches(body, {
        "lacpLagPol": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1", "value": "value1", "status": "created,modified"}}},
                {"tagAnnotation": {"attributes": {"key": "tag2", "value": "value2", "status": "deleted"}}},
            ],
        },
    })
