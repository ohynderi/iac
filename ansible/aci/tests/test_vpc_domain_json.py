from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render_fabric):
    vpc_grp = {"name": "grp1", "group_id": 102, "pod_id": 1, "leaf_id": 1103, "peer_leaf_id": 1104, "state": "absent"}
    body = render_fabric("vpc_domain.json.j2", vpc_grp_name="grp1", vpc_grp=vpc_grp)

    assert_matches(body, {
        "fabricExplicitGEp": {
            "attributes": {"status": "deleted"},
            "children": ABSENT,
        },
    })


def test_state_present_renders_name_and_id(render_fabric):
    vpc_grp = {"name": "grp1", "group_id": 102, "pod_id": 1, "leaf_id": 1103, "peer_leaf_id": 1104, "state": "present"}
    body = render_fabric("vpc_domain.json.j2", vpc_grp_name="grp1", vpc_grp=vpc_grp)

    assert_matches(body, {
        "fabricExplicitGEp": {
            "attributes": {
                "name": "grp1",
                "id": "102",
                "status": "created,modified",
            },
        },
    })


def test_state_undefined_at_root_does_not_crash(render_fabric):
    # Regression test: this must run without vpc_grp.state ever being set,
    # since the task's `when:` uses has_nested_state to allow nested-only
    # state changes (e.g. a tag) without a state on the group itself.
    vpc_grp = {"name": "grp1", "group_id": 102, "pod_id": 1, "leaf_id": 1103, "peer_leaf_id": 1104}
    body = render_fabric("vpc_domain.json.j2", vpc_grp_name="grp1", vpc_grp=vpc_grp)

    assert_matches(body, {
        "fabricExplicitGEp": {
            "attributes": {"status": "created,modified"},
        },
    })


def test_node_peps_render_leaf_and_peer_leaf_with_pod(render_fabric):
    vpc_grp = {"name": "grp1", "group_id": 102, "pod_id": 1, "leaf_id": 1103, "peer_leaf_id": 1104}
    body = render_fabric("vpc_domain.json.j2", vpc_grp_name="grp1", vpc_grp=vpc_grp)

    assert_matches(body, {
        "fabricExplicitGEp": {
            "children": [
                {"fabricNodePEp": {"attributes": {"id": "1103", "podId": "1"}}},
                {"fabricNodePEp": {"attributes": {"id": "1104", "podId": "1"}}},
            ],
        },
    })


def test_no_tags_renders_exactly_two_node_peps(render_fabric):
    vpc_grp = {"name": "grp1", "group_id": 102, "pod_id": 1, "leaf_id": 1103, "peer_leaf_id": 1104}
    body = render_fabric("vpc_domain.json.j2", vpc_grp_name="grp1", vpc_grp=vpc_grp)

    assert len(body["fabricExplicitGEp"]["children"]) == 2


def test_tags_render_with_state(render_fabric):
    vpc_grp = {
        "name": "grp1", "group_id": 102, "pod_id": 1, "leaf_id": 1103, "peer_leaf_id": 1104,
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render_fabric("vpc_domain.json.j2", vpc_grp_name="grp1", vpc_grp=vpc_grp)
    children = body["fabricExplicitGEp"]["children"]

    assert len(children) == 4  # 2 fabricNodePEp + 2 tags
    assert_matches(children[-2:], [
        {"tagAnnotation": {"attributes": {"key": "tag1", "value": "value1", "status": "created,modified"}}},
        {"tagAnnotation": {"attributes": {"key": "tag2", "value": "value2", "status": "deleted"}}},
    ])
