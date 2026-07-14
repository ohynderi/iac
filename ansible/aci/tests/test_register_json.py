from helpers import assert_matches


def test_leaf_role_renders_as_is(render_node):
    node = {"name": "leaf601", "leaf_id": 601, "pod_id": 1, "sn": "tep-1-601", "role": "leaf"}
    body = render_node("register.json.j2", node=node)

    assert_matches(body, {
        "fabricNodeIdentP": {
            "attributes": {
                "serial": "tep-1-601",
                "nodeId": "601",
                "podId": "1",
                "name": "leaf601",
                "role": "leaf",
                "status": "created,modified",
            },
        },
    })


def test_spine_role_renders_as_is(render_node):
    node = {"name": "spine101", "leaf_id": 101, "pod_id": 1, "sn": "tep-1-101", "role": "spine"}
    body = render_node("register.json.j2", node=node)

    assert_matches(body, {
        "fabricNodeIdentP": {
            "attributes": {"role": "spine"},
        },
    })


def test_remote_leaf_wan_with_extended_pool_id(render_node):
    node = {
        "name": "rleaf701", "leaf_id": 701, "pod_id": 2, "sn": "tep-2-701",
        "role": "remote-leaf-wan", "extended_pool_id": 5,
    }
    body = render_node("register.json.j2", node=node)

    assert_matches(body, {
        "fabricNodeIdentP": {
            "attributes": {
                "role": "leaf",
                "nodeType": "remote-leaf-wan",
                "extPoolId": "5",
            },
        },
    })


def test_remote_leaf_wan_without_extended_pool_id_falls_back(render_node):
    # Documents current template behavior when the schema-level invariant
    # (extended_pool_id required when role == remote-leaf-wan) is bypassed:
    # it falls through to the plain else branch instead of setting nodeType.
    node = {"name": "rleaf701", "leaf_id": 701, "pod_id": 2, "sn": "tep-2-701", "role": "remote-leaf-wan"}
    body = render_node("register.json.j2", node=node)

    assert_matches(body, {"fabricNodeIdentP": {"attributes": {"role": "remote-leaf-wan"}}})
    assert "nodeType" not in body["fabricNodeIdentP"]["attributes"]
    assert "extPoolId" not in body["fabricNodeIdentP"]["attributes"]
