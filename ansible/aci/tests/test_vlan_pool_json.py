from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render_fabric):
    pool = {"name": "pool1", "state": "absent"}
    body = render_fabric("vlan_pool.json.j2", pool_name="pool1", pool=pool)

    assert_matches(body, {
        "fvnsVlanInstP": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
                "allocMode": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_state_present_minimal_renders_defaults(render_fabric):
    pool = {"name": "pool1", "state": "present"}
    body = render_fabric("vlan_pool.json.j2", pool_name="pool1", pool=pool)

    assert_matches(body, {
        "fvnsVlanInstP": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
                "allocMode": "dynamic",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_does_not_crash(render_fabric):
    # Regression test: this used to raise "'dict object' has no attribute
    # 'state'" once the task's `when:` was switched to has_nested_state,
    # which lets this task run without pool.state ever being set.
    pool = {"name": "pool1"}
    body = render_fabric("vlan_pool.json.j2", pool_name="pool1", pool=pool)

    assert_matches(body, {
        "fvnsVlanInstP": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
                "allocMode": "dynamic",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_still_renders_nested_range_state(render_fabric):
    pool = {"name": "pool1", "ranges": [{"from_": 100, "to_": 200, "state": "absent"}]}
    body = render_fabric("vlan_pool.json.j2", pool_name="pool1", pool=pool)

    assert_matches(body, {
        "fvnsVlanInstP": {
            "children": [
                {
                    "fvnsEncapBlk": {
                        "attributes": {
                            "from": "vlan-100",
                            "to": "vlan-200",
                            "status": "deleted",
                        },
                    },
                },
            ],
        },
    })


def test_description_and_allocation_mode_overrides(render_fabric):
    pool = {"name": "pool1", "description": "my pool", "allocation_mode": "static"}
    body = render_fabric("vlan_pool.json.j2", pool_name="pool1", pool=pool)

    assert_matches(body, {
        "fvnsVlanInstP": {
            "attributes": {
                "descr": "my pool",
                "allocMode": "static",
            },
        },
    })


def test_tags_render_with_state(render_fabric):
    pool = {
        "name": "pool1",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render_fabric("vlan_pool.json.j2", pool_name="pool1", pool=pool)

    assert_matches(body, {
        "fvnsVlanInstP": {
            "children": [
                {
                    "tagAnnotation": {
                        "attributes": {
                            "key": "tag1",
                            "value": "value1",
                            "status": "created,modified",
                        },
                    },
                },
                {
                    "tagAnnotation": {
                        "attributes": {
                            "key": "tag2",
                            "value": "value2",
                            "status": "deleted",
                        },
                    },
                },
            ],
        },
    })


def test_ranges_render_with_defaults(render_fabric):
    pool = {"name": "pool1", "ranges": [{"from_": 100, "to_": 200}]}
    body = render_fabric("vlan_pool.json.j2", pool_name="pool1", pool=pool)

    assert_matches(body, {
        "fvnsVlanInstP": {
            "children": [
                {
                    "fvnsEncapBlk": {
                        "attributes": {
                            "from": "vlan-100",
                            "to": "vlan-200",
                            "descr": "",
                            "role": "external",
                            "allocMode": "inherit",
                            "status": "created,modified",
                        },
                    },
                },
            ],
        },
    })


def test_ranges_description_role_and_allocation_mode_overrides(render_fabric):
    pool = {
        "name": "pool1",
        "ranges": [
            {"from_": 100, "to_": 200, "description": "my range", "role": "internal", "allocation_mode": "static"},
        ],
    }
    body = render_fabric("vlan_pool.json.j2", pool_name="pool1", pool=pool)

    assert_matches(body, {
        "fvnsVlanInstP": {
            "children": [
                {
                    "fvnsEncapBlk": {
                        "attributes": {
                            "descr": "my range",
                            "role": "internal",
                            "allocMode": "static",
                        },
                    },
                },
            ],
        },
    })


def test_ranges_render_with_state(render_fabric):
    # Also a regression test for the double-comma bug: rendering must
    # produce valid JSON with exactly 2 range children when there's more
    # than one range.
    pool = {
        "name": "pool1",
        "ranges": [
            {"from_": 100, "to_": 200},
            {"from_": 300, "to_": 400, "state": "absent"},
        ],
    }
    body = render_fabric("vlan_pool.json.j2", pool_name="pool1", pool=pool)

    assert_matches(body, {
        "fvnsVlanInstP": {
            "children": [
                {"fvnsEncapBlk": {"attributes": {"from": "vlan-100", "status": "created,modified"}}},
                {"fvnsEncapBlk": {"attributes": {"from": "vlan-300", "status": "deleted"}}},
            ],
        },
    })


def test_range_state_absent_does_not_affect_other_children(render_fabric):
    pool = {
        "name": "pool1",
        "tags": [{"name": "tag1", "value": "value1"}],
        "ranges": [
            {"from_": 100, "to_": 200},
            {"from_": 300, "to_": 400, "state": "absent"},
        ],
    }
    body = render_fabric("vlan_pool.json.j2", pool_name="pool1", pool=pool)

    assert_matches(body, {
        "fvnsVlanInstP": {
            "children": [
                {
                    "tagAnnotation": {
                        "attributes": {
                            "key": "tag1",
                            "status": "created,modified",
                        },
                    },
                },
                {
                    "fvnsEncapBlk": {
                        "attributes": {
                            "from": "vlan-100",
                            "status": "created,modified",
                        },
                    },
                },
                {
                    "fvnsEncapBlk": {
                        "attributes": {
                            "from": "vlan-300",
                            "status": "deleted",
                        },
                    },
                },
            ],
        },
    })


def test_only_ranges_no_tags_omits_leading_comma(render_fabric):
    # Regression test: with tags empty, the comma inserted between the
    # tags group and the ranges group must not appear (no leading comma
    # before the first range).
    pool = {"name": "pool1", "ranges": [{"from_": 100, "to_": 200}]}
    body = render_fabric("vlan_pool.json.j2", pool_name="pool1", pool=pool)

    assert_matches(body, {
        "fvnsVlanInstP": {
            "children": [
                {"fvnsEncapBlk": {"attributes": {"from": "vlan-100"}}},
            ],
        },
    })


def test_only_tags_no_ranges(render_fabric):
    pool = {"name": "pool1", "tags": [{"name": "tag1", "value": "value1"}]}
    body = render_fabric("vlan_pool.json.j2", pool_name="pool1", pool=pool)

    assert_matches(body, {
        "fvnsVlanInstP": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1"}}},
            ],
        },
    })
