from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render):
    mcast_route_map = {"name": "mrm1", "state": "absent"}
    body = render("mcast_route_map.json.j2", mcast_route_map=mcast_route_map)

    assert_matches(body, {
        "pimRouteMapPol": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_state_present_minimal_renders_empty_children(render):
    mcast_route_map = {"name": "mrm1", "state": "present"}
    body = render("mcast_route_map.json.j2", mcast_route_map=mcast_route_map)

    assert_matches(body, {
        "pimRouteMapPol": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_does_not_crash(render):
    # Regression test pattern: this task is gated with has_nested_state, so
    # it can run without mcast_route_map.state ever being set at the root.
    mcast_route_map = {"name": "mrm1"}
    body = render("mcast_route_map.json.j2", mcast_route_map=mcast_route_map)

    assert_matches(body, {
        "pimRouteMapPol": {
            "attributes": {"status": "created,modified", "descr": ""},
            "children": [],
        },
    })


def test_state_undefined_at_root_still_renders_nested_tag_state(render):
    mcast_route_map = {"name": "mrm1", "tags": [{"name": "tag1", "value": "value1", "state": "absent"}]}
    body = render("mcast_route_map.json.j2", mcast_route_map=mcast_route_map)

    assert_matches(body, {
        "pimRouteMapPol": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1", "status": "deleted"}}},
            ],
        },
    })


def test_description_override(render):
    mcast_route_map = {"name": "mrm1", "description": "my mcast route map"}
    body = render("mcast_route_map.json.j2", mcast_route_map=mcast_route_map)

    assert_matches(body, {"pimRouteMapPol": {"attributes": {"descr": "my mcast route map"}}})


def test_tags_render_with_state(render):
    mcast_route_map = {
        "name": "mrm1",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render("mcast_route_map.json.j2", mcast_route_map=mcast_route_map)

    assert_matches(body, {
        "pimRouteMapPol": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1", "status": "created,modified"}}},
                {"tagAnnotation": {"attributes": {"key": "tag2", "status": "deleted"}}},
            ],
        },
    })


def test_entry_renders_with_all_fields(render):
    mcast_route_map = {"name": "mrm1", "entries": [{
        "group": "235.0.0.0/24", "rp": "10.65.110.2/32", "source": "0.0.0.0",
        "action": "permit", "order": 10,
    }]}
    body = render("mcast_route_map.json.j2", mcast_route_map=mcast_route_map)

    assert_matches(body, {
        "pimRouteMapPol": {
            "children": [
                {
                    "pimRouteMapEntry": {
                        "attributes": {
                            "order": "10",
                            "grp": "235.0.0.0/24",
                            "rp": "10.65.110.2/32",
                            "src": "0.0.0.0",
                            "action": "permit",
                            "status": "created,modified",
                        },
                    },
                },
            ],
        },
    })


def test_entry_source_defaults_when_omitted(render):
    mcast_route_map = {"name": "mrm1", "entries": [{
        "group": "235.0.0.0/24", "rp": "10.65.110.2/32", "action": "permit", "order": 10,
    }]}
    body = render("mcast_route_map.json.j2", mcast_route_map=mcast_route_map)

    assert_matches(body, {
        "pimRouteMapPol": {
            "children": [
                {"pimRouteMapEntry": {"attributes": {"src": "0.0.0.0"}}},
            ],
        },
    })


def test_entry_action_deny(render):
    mcast_route_map = {"name": "mrm1", "entries": [{
        "group": "235.0.0.0/24", "rp": "10.65.110.2/32", "source": "0.0.0.0",
        "action": "deny", "order": 10,
    }]}
    body = render("mcast_route_map.json.j2", mcast_route_map=mcast_route_map)

    assert_matches(body, {
        "pimRouteMapPol": {
            "children": [
                {"pimRouteMapEntry": {"attributes": {"action": "deny"}}},
            ],
        },
    })


def test_entry_state_absent_still_renders_action(render):
    # action is a mandatory, identity-relevant field (like order/group/rp),
    # so unlike descr-style optional fields it's not omitted on delete.
    mcast_route_map = {"name": "mrm1", "entries": [{
        "group": "235.0.0.0/24", "rp": "10.65.110.2/32", "source": "0.0.0.0",
        "order": 10, "state": "absent", "action": "deny",
    }]}
    body = render("mcast_route_map.json.j2", mcast_route_map=mcast_route_map)

    assert_matches(body, {
        "pimRouteMapPol": {
            "children": [
                {
                    "pimRouteMapEntry": {
                        "attributes": {
                            "order": "10",
                            "grp": "235.0.0.0/24",
                            "rp": "10.65.110.2/32",
                            "src": "0.0.0.0",
                            "action": "deny",
                            "status": "deleted",
                        },
                    },
                },
            ],
        },
    })


def test_entry_state_absent_does_not_affect_other_entries(render):
    mcast_route_map = {"name": "mrm1", "entries": [
        {"group": "235.0.0.0/24", "rp": "10.65.110.2/32", "action": "permit", "order": 10, "state": "absent"},
        {"group": "236.0.0.0/24", "rp": "10.65.110.3/32", "action": "permit", "order": 20},
    ]}
    body = render("mcast_route_map.json.j2", mcast_route_map=mcast_route_map)

    assert_matches(body, {
        "pimRouteMapPol": {
            "children": [
                {"pimRouteMapEntry": {"attributes": {"order": "10", "status": "deleted"}}},
                {"pimRouteMapEntry": {"attributes": {"order": "20", "status": "created,modified", "action": "permit"}}},
            ],
        },
    })


def test_tags_and_entries_together(render):
    # Regression test: the comma between the tags loop and the entries loop
    # is only emitted when both lists are non-empty.
    mcast_route_map = {
        "name": "mrm1",
        "tags": [{"name": "tag1", "value": "value1"}],
        "entries": [{"group": "235.0.0.0/24", "rp": "10.65.110.2/32", "action": "permit", "order": 10}],
    }
    body = render("mcast_route_map.json.j2", mcast_route_map=mcast_route_map)

    assert_matches(body, {
        "pimRouteMapPol": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1"}}},
                {"pimRouteMapEntry": {"attributes": {"grp": "235.0.0.0/24"}}},
            ],
        },
    })
