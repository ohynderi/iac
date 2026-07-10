from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render):
    set_rule = {"name": "sr1", "state": "absent"}
    body = render("set_rule.json.j2", set_rule=set_rule)

    assert_matches(body, {
        "rtctrlAttrP": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_state_present_minimal_renders_empty_children(render):
    # No as_path entries at all: this used to unconditionally render an
    # empty rtctrlSetASPath child regardless of whether as_path was set.
    set_rule = {"name": "sr1", "state": "present"}
    body = render("set_rule.json.j2", set_rule=set_rule)

    assert_matches(body, {
        "rtctrlAttrP": {
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
    # which lets this task run without set_rule.state ever being set.
    set_rule = {"name": "sr1"}
    body = render("set_rule.json.j2", set_rule=set_rule)

    assert_matches(body, {
        "rtctrlAttrP": {
            "attributes": {"status": "created,modified", "descr": ""},
            "children": [],
        },
    })


def test_state_undefined_at_root_still_renders_nested_tag_state(render):
    set_rule = {"name": "sr1", "tags": [{"name": "tag1", "value": "value1", "state": "absent"}]}
    body = render("set_rule.json.j2", set_rule=set_rule)

    assert_matches(body, {
        "rtctrlAttrP": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1", "status": "deleted"}}},
            ],
        },
    })


def test_description_override(render):
    set_rule = {"name": "sr1", "description": "my set rule"}
    body = render("set_rule.json.j2", set_rule=set_rule)

    assert_matches(body, {"rtctrlAttrP": {"attributes": {"descr": "my set rule"}}})


def test_tags_render_with_state(render):
    set_rule = {
        "name": "sr1",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render("set_rule.json.j2", set_rule=set_rule)

    assert_matches(body, {
        "rtctrlAttrP": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1", "status": "created,modified"}}},
                {"tagAnnotation": {"attributes": {"key": "tag2", "status": "deleted"}}},
            ],
        },
    })


def test_as_path_renders_hop_with_defaults(render):
    set_rule = {"name": "sr1", "as_path": [{"asn": 65000, "order": 1}]}
    body = render("set_rule.json.j2", set_rule=set_rule)

    assert_matches(body, {
        "rtctrlAttrP": {
            "children": [
                {
                    "rtctrlSetASPath": {
                        "attributes": {"criteria": "prepend", "type": "as-path"},
                        "children": [
                            {
                                "rtctrlSetASPathASN": {
                                    "attributes": {
                                        "asn": "65000",
                                        "order": "1",
                                        "status": "created,modified",
                                        "descr": "",
                                    },
                                },
                            },
                        ],
                    },
                },
            ],
        },
    })


def test_as_path_hop_description_override(render):
    set_rule = {"name": "sr1", "as_path": [{"asn": 65000, "order": 1, "description": "my hop"}]}
    body = render("set_rule.json.j2", set_rule=set_rule)

    assert_matches(body, {
        "rtctrlAttrP": {
            "children": [
                {"rtctrlSetASPath": {"children": [
                    {"rtctrlSetASPathASN": {"attributes": {"descr": "my hop"}}},
                ]}},
            ],
        },
    })


def test_as_path_hop_state_absent_omits_description(render):
    set_rule = {"name": "sr1", "as_path": [
        {"asn": 65000, "order": 1, "state": "absent", "description": "should be omitted"},
    ]}
    body = render("set_rule.json.j2", set_rule=set_rule)

    assert_matches(body, {
        "rtctrlAttrP": {
            "children": [
                {"rtctrlSetASPath": {"children": [
                    {
                        "rtctrlSetASPathASN": {
                            "attributes": {
                                "asn": "65000",
                                "order": "1",
                                "status": "deleted",
                                "descr": ABSENT,
                            },
                        },
                    },
                ]}},
            ],
        },
    })


def test_as_path_hop_state_absent_does_not_affect_other_hops(render):
    set_rule = {"name": "sr1", "as_path": [
        {"asn": 65000, "order": 1, "state": "absent"},
        {"asn": 65001, "order": 2},
    ]}
    body = render("set_rule.json.j2", set_rule=set_rule)

    assert_matches(body, {
        "rtctrlAttrP": {
            "children": [
                {"rtctrlSetASPath": {"children": [
                    {"rtctrlSetASPathASN": {"attributes": {"asn": "65000", "status": "deleted"}}},
                    {"rtctrlSetASPathASN": {"attributes": {"asn": "65001", "status": "created,modified"}}},
                ]}},
            ],
        },
    })


def test_tags_and_as_path_together(render):
    # Regression test: the comma between the tags loop and the as_path block
    # is only emitted when both are non-empty.
    set_rule = {
        "name": "sr1",
        "tags": [{"name": "tag1", "value": "value1"}],
        "as_path": [{"asn": 65000, "order": 1}],
    }
    body = render("set_rule.json.j2", set_rule=set_rule)

    assert_matches(body, {
        "rtctrlAttrP": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1"}}},
                {"rtctrlSetASPath": {}},
            ],
        },
    })
