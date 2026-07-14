from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render_fabric):
    leaf_intf_prof = {"name": "lip1", "state": "absent"}
    body = render_fabric("leaf_intf_prof.json.j2", leaf_intf_prof_name="lip1", leaf_intf_prof=leaf_intf_prof)

    assert_matches(body, {
        "infraAccPortP": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_state_present_minimal_renders_empty_children(render_fabric):
    leaf_intf_prof = {"name": "lip1", "state": "present"}
    body = render_fabric("leaf_intf_prof.json.j2", leaf_intf_prof_name="lip1", leaf_intf_prof=leaf_intf_prof)

    assert_matches(body, {
        "infraAccPortP": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_does_not_crash(render_fabric):
    # Regression test: this used to raise "'dict object' has no attribute
    # 'state'" once the task's `when:` was switched to has_nested_state,
    # which lets this task run without leaf_intf_prof.state ever being set.
    leaf_intf_prof = {"name": "lip1"}
    body = render_fabric("leaf_intf_prof.json.j2", leaf_intf_prof_name="lip1", leaf_intf_prof=leaf_intf_prof)

    assert_matches(body, {
        "infraAccPortP": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
            },
            "children": [],
        },
    })


def test_description_override(render_fabric):
    leaf_intf_prof = {"name": "lip1", "description": "my leaf interface profile"}
    body = render_fabric("leaf_intf_prof.json.j2", leaf_intf_prof_name="lip1", leaf_intf_prof=leaf_intf_prof)

    assert_matches(body, {
        "infraAccPortP": {"attributes": {"descr": "my leaf interface profile"}},
    })


def test_tags_render_with_state(render_fabric):
    leaf_intf_prof = {
        "name": "lip1",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render_fabric("leaf_intf_prof.json.j2", leaf_intf_prof_name="lip1", leaf_intf_prof=leaf_intf_prof)

    assert_matches(body, {
        "infraAccPortP": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1", "value": "value1", "status": "created,modified"}}},
                {"tagAnnotation": {"attributes": {"key": "tag2", "value": "value2", "status": "deleted"}}},
            ],
        },
    })
