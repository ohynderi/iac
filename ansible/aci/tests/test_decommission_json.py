from helpers import assert_matches


def test_decommission_renders_tdn_and_remove_from_controller(render_node):
    node = {"name": "leaf601", "leaf_id": 601, "pod_id": 1, "sn": "tep-1-601", "role": "leaf", "state": "absent"}
    body = render_node("decommission.json.j2", node=node)

    assert_matches(body, {
        "fabricRsDecommissionNode": {
            "attributes": {
                "tDn": "topology/pod-1/node-601",
                "status": "created,modified",
                "removeFromController": "true",
            },
        },
    })


def test_decommission_tdn_uses_pod_and_leaf_id(render_node):
    node = {"name": "leaf602", "leaf_id": 602, "pod_id": 3, "sn": "tep-3-602", "role": "leaf", "state": "absent"}
    body = render_node("decommission.json.j2", node=node)

    assert_matches(body, {
        "fabricRsDecommissionNode": {
            "attributes": {"tDn": "topology/pod-3/node-602"},
        },
    })
