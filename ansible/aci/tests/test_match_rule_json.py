from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render):
    rule = {"name": "r1", "state": "absent"}
    body = render("match_rule.json.j2", rule=rule)

    assert_matches(body, {
        "rtctrlSubjP": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_state_present_minimal_renders_empty_children(render):
    rule = {"name": "r1", "state": "present"}
    body = render("match_rule.json.j2", rule=rule)

    assert_matches(body, {
        "rtctrlSubjP": {
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
    # which lets this task run without rule.state ever being set.
    rule = {"name": "r1"}
    body = render("match_rule.json.j2", rule=rule)

    assert_matches(body, {
        "rtctrlSubjP": {
            "attributes": {"status": "created,modified", "descr": ""},
            "children": [],
        },
    })


def test_state_undefined_at_root_still_renders_nested_tag_state(render):
    rule = {"name": "r1", "tags": [{"name": "tag1", "value": "value1", "state": "absent"}]}
    body = render("match_rule.json.j2", rule=rule)

    assert_matches(body, {
        "rtctrlSubjP": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1", "status": "deleted"}}},
            ],
        },
    })


def test_description_override(render):
    rule = {"name": "r1", "description": "my rule"}
    body = render("match_rule.json.j2", rule=rule)

    assert_matches(body, {"rtctrlSubjP": {"attributes": {"descr": "my rule"}}})


def test_tags_render_with_state(render):
    rule = {
        "name": "r1",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render("match_rule.json.j2", rule=rule)

    assert_matches(body, {
        "rtctrlSubjP": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1", "status": "created,modified"}}},
                {"tagAnnotation": {"attributes": {"key": "tag2", "status": "deleted"}}},
            ],
        },
    })


def test_prefix_renders_with_defaults(render):
    rule = {"name": "r1", "prefixes": [{"ip": "0.0.0.0/0"}]}
    body = render("match_rule.json.j2", rule=rule)

    assert_matches(body, {
        "rtctrlSubjP": {
            "children": [
                {
                    "rtctrlMatchRtDest": {
                        "attributes": {
                            "ip": "0.0.0.0/0",
                            "status": "created,modified",
                            "aggregate": ABSENT,
                            "descr": ABSENT,
                            "fromPfxLen": ABSENT,
                            "toPfxLen": ABSENT,
                        },
                    },
                },
            ],
        },
    })


def test_prefix_renders_with_all_optional_fields(render):
    rule = {"name": "r1", "prefixes": [{
        "ip": "10.0.0.0/8",
        "aggregate": True,
        "description": "my prefix",
        "greater_equal_mask": 16,
        "less_equal_mask": 24,
    }]}
    body = render("match_rule.json.j2", rule=rule)

    assert_matches(body, {
        "rtctrlSubjP": {
            "children": [
                {
                    "rtctrlMatchRtDest": {
                        "attributes": {
                            "ip": "10.0.0.0/8",
                            "status": "created,modified",
                            "aggregate": "yes",
                            "descr": "my prefix",
                            "fromPfxLen": "16",
                            "toPfxLen": "24",
                        },
                    },
                },
            ],
        },
    })


def test_prefix_aggregate_false_renders_no(render):
    rule = {"name": "r1", "prefixes": [{"ip": "0.0.0.0/0", "aggregate": False}]}
    body = render("match_rule.json.j2", rule=rule)

    assert_matches(body, {
        "rtctrlSubjP": {
            "children": [
                {"rtctrlMatchRtDest": {"attributes": {"aggregate": "no"}}},
            ],
        },
    })


def test_prefix_state_absent_omits_optional_attributes(render):
    rule = {"name": "r1", "prefixes": [{
        "ip": "0.0.0.0/0", "state": "absent", "aggregate": True, "description": "should be omitted",
    }]}
    body = render("match_rule.json.j2", rule=rule)

    assert_matches(body, {
        "rtctrlSubjP": {
            "children": [
                {
                    "rtctrlMatchRtDest": {
                        "attributes": {
                            "ip": "0.0.0.0/0",
                            "status": "deleted",
                            "aggregate": ABSENT,
                            "descr": ABSENT,
                        },
                    },
                },
            ],
        },
    })


def test_prefix_state_absent_does_not_affect_other_prefixes(render):
    rule = {"name": "r1", "prefixes": [
        {"ip": "0.0.0.0/0", "state": "absent"},
        {"ip": "10.0.0.0/8"},
    ]}
    body = render("match_rule.json.j2", rule=rule)

    assert_matches(body, {
        "rtctrlSubjP": {
            "children": [
                {"rtctrlMatchRtDest": {"attributes": {"ip": "0.0.0.0/0", "status": "deleted"}}},
                {"rtctrlMatchRtDest": {"attributes": {"ip": "10.0.0.0/8", "status": "created,modified"}}},
            ],
        },
    })


def test_tags_and_prefixes_together(render):
    # Regression test: the comma between the tags loop and the prefixes loop
    # is only emitted when both lists are non-empty.
    rule = {
        "name": "r1",
        "tags": [{"name": "tag1", "value": "value1"}],
        "prefixes": [{"ip": "0.0.0.0/0"}],
    }
    body = render("match_rule.json.j2", rule=rule)

    assert_matches(body, {
        "rtctrlSubjP": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1"}}},
                {"rtctrlMatchRtDest": {"attributes": {"ip": "0.0.0.0/0"}}},
            ],
        },
    })
