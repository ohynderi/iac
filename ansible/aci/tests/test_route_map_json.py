from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render):
    route_map = {"name": "rm1", "state": "absent"}
    body = render("route_map.json.j2", route_map=route_map)

    assert_matches(body, {
        "rtctrlProfile": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_state_present_minimal_renders_empty_children(render):
    route_map = {"name": "rm1", "state": "present"}
    body = render("route_map.json.j2", route_map=route_map)

    assert_matches(body, {
        "rtctrlProfile": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_does_not_crash(render):
    # Regression test: this used to raise "'dict object' has no attribute
    # 'state'" once the task's `when:` was switched to has_nested_state,
    # which lets this task run without route_map.state ever being set.
    route_map = {"name": "rm1"}
    body = render("route_map.json.j2", route_map=route_map)

    assert_matches(body, {
        "rtctrlProfile": {
            "attributes": {"status": "created,modified", "descr": ""},
            "children": [],
        },
    })


def test_state_undefined_at_root_still_renders_nested_tag_state(render):
    route_map = {"name": "rm1", "tags": [{"name": "tag1", "value": "value1", "state": "absent"}]}
    body = render("route_map.json.j2", route_map=route_map)

    assert_matches(body, {
        "rtctrlProfile": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1", "status": "deleted"}}},
            ],
        },
    })


def test_description_override(render):
    route_map = {"name": "rm1", "description": "my route map"}
    body = render("route_map.json.j2", route_map=route_map)

    assert_matches(body, {"rtctrlProfile": {"attributes": {"descr": "my route map"}}})


def test_tags_render_with_state(render):
    route_map = {
        "name": "rm1",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render("route_map.json.j2", route_map=route_map)

    assert_matches(body, {
        "rtctrlProfile": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1", "status": "created,modified"}}},
                {"tagAnnotation": {"attributes": {"key": "tag2", "status": "deleted"}}},
            ],
        },
    })


def test_context_without_match_rule_or_set_rule_renders_empty_children(render):
    # Regression test: this used to crash with "'dict object' has no
    # attribute 'match_rule'" since both relations were rendered
    # unconditionally with no guard.
    route_map = {"name": "rm1", "contexts": [{"name": "c1", "order": 1, "action": "permit"}]}
    body = render("route_map.json.j2", route_map=route_map)

    assert_matches(body, {
        "rtctrlProfile": {
            "children": [
                {
                    "rtctrlCtxP": {
                        "attributes": {
                            "name": "c1",
                            "order": "1",
                            "action": "permit",
                            "status": "created,modified",
                            "descr": "",
                        },
                        "children": [],
                    },
                },
            ],
        },
    })


def test_context_with_match_rule_only(render):
    route_map = {"name": "rm1", "contexts": [
        {"name": "c1", "order": 1, "action": "permit", "match_rule": "mr1"},
    ]}
    body = render("route_map.json.j2", route_map=route_map)

    assert_matches(body, {
        "rtctrlProfile": {
            "children": [
                {"rtctrlCtxP": {"children": [
                    {"rtctrlRsCtxPToSubjP": {"attributes": {"tnRtctrlSubjPName": "mr1"}}},
                ]}},
            ],
        },
    })


def test_context_with_set_rule_only(render):
    route_map = {"name": "rm1", "contexts": [
        {"name": "c1", "order": 1, "action": "permit", "set_rule": "sr1"},
    ]}
    body = render("route_map.json.j2", route_map=route_map)

    assert_matches(body, {
        "rtctrlProfile": {
            "children": [
                {"rtctrlCtxP": {"children": [
                    {
                        "rtctrlScope": {
                            "attributes": {"descr": "", "name": ""},
                            "children": [
                                {"rtctrlRsScopeToAttrP": {"attributes": {"tnRtctrlAttrPName": "sr1"}}},
                            ],
                        },
                    },
                ]}},
            ],
        },
    })


def test_context_with_both_match_rule_and_set_rule(render):
    route_map = {"name": "rm1", "contexts": [
        {"name": "c1", "order": 1, "action": "deny", "match_rule": "mr1", "set_rule": "sr1"},
    ]}
    body = render("route_map.json.j2", route_map=route_map)

    assert_matches(body, {
        "rtctrlProfile": {
            "children": [
                {"rtctrlCtxP": {
                    "attributes": {"action": "deny"},
                    "children": [
                        {"rtctrlRsCtxPToSubjP": {"attributes": {"tnRtctrlSubjPName": "mr1"}}},
                        {"rtctrlScope": {"children": [
                            {"rtctrlRsScopeToAttrP": {"attributes": {"tnRtctrlAttrPName": "sr1"}}},
                        ]}},
                    ],
                }},
            ],
        },
    })


def test_context_description_override(render):
    route_map = {"name": "rm1", "contexts": [
        {"name": "c1", "order": 1, "action": "permit", "description": "my context"},
    ]}
    body = render("route_map.json.j2", route_map=route_map)

    assert_matches(body, {
        "rtctrlProfile": {
            "children": [
                {"rtctrlCtxP": {"attributes": {"descr": "my context"}}},
            ],
        },
    })


def test_context_state_absent_omits_description_but_keeps_relations(render):
    route_map = {"name": "rm1", "contexts": [{
        "name": "c1", "order": 1, "action": "permit", "state": "absent",
        "match_rule": "mr1", "set_rule": "sr1", "description": "should be omitted",
    }]}
    body = render("route_map.json.j2", route_map=route_map)

    assert_matches(body, {
        "rtctrlProfile": {
            "children": [
                {"rtctrlCtxP": {
                    "attributes": {"status": "deleted", "descr": ABSENT},
                    "children": [
                        {"rtctrlRsCtxPToSubjP": {}},
                        {"rtctrlScope": {}},
                    ],
                }},
            ],
        },
    })


def test_context_state_absent_does_not_affect_other_contexts(render):
    route_map = {"name": "rm1", "contexts": [
        {"name": "c1", "order": 1, "action": "permit", "state": "absent"},
        {"name": "c2", "order": 2, "action": "deny"},
    ]}
    body = render("route_map.json.j2", route_map=route_map)

    assert_matches(body, {
        "rtctrlProfile": {
            "children": [
                {"rtctrlCtxP": {"attributes": {"name": "c1", "status": "deleted"}}},
                {"rtctrlCtxP": {"attributes": {"name": "c2", "status": "created,modified"}}},
            ],
        },
    })


def test_tags_and_contexts_together(render):
    # Regression test: the comma between the tags loop and the contexts loop
    # is only emitted when both lists are non-empty.
    route_map = {
        "name": "rm1",
        "tags": [{"name": "tag1", "value": "value1"}],
        "contexts": [{"name": "c1", "order": 1, "action": "permit"}],
    }
    body = render("route_map.json.j2", route_map=route_map)

    assert_matches(body, {
        "rtctrlProfile": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1"}}},
                {"rtctrlCtxP": {"attributes": {"name": "c1"}}},
            ],
        },
    })
