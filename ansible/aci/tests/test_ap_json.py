from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render):
    body = render("ap.json.j2", ap_name="ap1", ap={"name": "ap1", "state": "absent"})

    assert_matches(body, {
        "fvAp": {
            "attributes": {
                "status": "deleted",
                "descr": "",
            },
            "children": ABSENT,
        },
    })


def test_state_present_with_description_and_tags(render):
    ap = {
        "name": "ap1",
        "state": "present",
        "description": "my ap",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render("ap.json.j2", ap_name="ap1", ap=ap)

    assert_matches(body, {
        "fvAp": {
            "attributes": {
                "status": "created,modified",
                "descr": "my ap",
            },
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
                    "tagAnnotation": {
                        "attributes": {
                            "key": "tag2",
                            "status": "deleted",
                        },
                    },
                },
            ],
        },
    })


def test_state_undefined_at_root_does_not_crash(render):
    # Regression test: this used to raise "'dict object' has no attribute
    # 'state'" once the task's `when:` was switched to has_nested_state,
    # which lets this task run without ap.state ever being set.
    body = render("ap.json.j2", ap_name="ap1", ap={"name": "ap1"})

    assert_matches(body, {
        "fvAp": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
            },
            "children": ABSENT,
        },
    })


def test_state_undefined_at_root_still_renders_nested_tag_state(render):
    ap = {
        "name": "ap1",
        "tags": [{"name": "tag1", "value": "value1", "state": "absent"}],
    }
    body = render("ap.json.j2", ap_name="ap1", ap=ap)

    assert_matches(body, {
        "fvAp": {
            "children": [
                {
                    "tagAnnotation": {
                        "attributes": {
                            "key": "tag1",
                            "status": "deleted",
                        },
                    },
                },
            ],
        },
    })


def test_empty_tags_list_omits_children(render):
    body = render("ap.json.j2", ap_name="ap1", ap={"name": "ap1", "state": "present", "tags": []})

    assert_matches(body, {
        "fvAp": {
            "children": ABSENT,
        },
    })
