# roles/fabric/templates/intf_selector.json.j2 and roles/node/templates/intf_selector.json.j2
# are intentional copies of each other (see the sync-note comment in both files), so this
# module runs every test against both templates via the render_intf_selector fixture.
import pytest
from helpers import ABSENT, assert_matches


@pytest.fixture(params=["render_fabric", "render_node"])
def render_intf_selector(request):
    return request.getfixturevalue(request.param)


def _render(render_intf_selector, intf, ipg_type="accportgrp", from_port=1, to_port=1):
    return render_intf_selector(
        "intf_selector.json.j2",
        intf_name="eth1_1",
        ipg_type=ipg_type,
        intf_from_port=from_port,
        intf_to_port=to_port,
        intf=intf,
    )


def test_state_absent_deletes_and_omits_children(render_intf_selector):
    intf = {"card": 1, "intf_pol_group": "server1", "state": "absent"}
    body = _render(render_intf_selector, intf)

    assert_matches(body, {
        "infraHPortS": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_state_present_minimal_renders_defaults(render_intf_selector):
    intf = {"card": 1, "intf_pol_group": "server1", "state": "present"}
    body = _render(render_intf_selector, intf)

    assert_matches(body, {
        "infraHPortS": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
            },
            "children": [
                {
                    "infraPortBlk": {
                        "attributes": {
                            "name": "block2",
                            "fromCard": "1",
                            "toCard": "1",
                            "fromPort": "1",
                            "toPort": "1",
                            "status": "created,modified",
                        },
                    },
                },
                {
                    "infraRsAccBaseGrp": {
                        "attributes": {
                            "tDn": "uni/infra/funcprof/accportgrp-server1",
                            "status": "created,modified",
                        },
                    },
                },
            ],
        },
    })


def test_state_undefined_at_root_does_not_crash(render_intf_selector):
    # Regression test: this must run without intf.state ever being set, since
    # the task's `when:` uses has_nested_state to allow nested-only state changes.
    intf = {"card": 1, "intf_pol_group": "server1"}
    body = _render(render_intf_selector, intf)

    assert_matches(body, {
        "infraHPortS": {
            "attributes": {"status": "created,modified"},
            "children": [
                {"infraPortBlk": {"attributes": {"status": "created,modified"}}},
                {"infraRsAccBaseGrp": {"attributes": {"status": "created,modified"}}},
            ],
        },
    })


def test_selector_description_override(render_intf_selector):
    intf = {"card": 1, "intf_pol_group": "server1", "selector_description": "my selector"}
    body = _render(render_intf_selector, intf)

    assert_matches(body, {"infraHPortS": {"attributes": {"descr": "my selector"}}})


def test_port_block_description_override(render_intf_selector):
    intf = {"card": 1, "intf_pol_group": "server1", "port_block_description": "my block"}
    body = _render(render_intf_selector, intf)
    port_blk = body["infraHPortS"]["children"][0]["infraPortBlk"]

    assert_matches(port_blk, {"attributes": {"descr": "my block"}})


def test_port_block_name_override(render_intf_selector):
    intf = {"card": 1, "intf_pol_group": "server1", "port_block_name": "my_block"}
    body = _render(render_intf_selector, intf)
    port_blk = body["infraHPortS"]["children"][0]["infraPortBlk"]

    assert_matches(port_blk, {"attributes": {"name": "my_block"}})


def test_port_range_renders_from_and_to_port(render_intf_selector):
    intf = {"card": 1, "intf_pol_group": "server1"}
    body = _render(render_intf_selector, intf, from_port=4, to_port=6)
    port_blk = body["infraHPortS"]["children"][0]["infraPortBlk"]

    assert_matches(port_blk, {"attributes": {"fromPort": "4", "toPort": "6"}})


def test_ipg_type_selects_functional_profile_kind(render_intf_selector):
    intf = {"card": 1, "intf_pol_group": "po1"}
    body = _render(render_intf_selector, intf, ipg_type="accbundle")
    rs_acc_base_grp = body["infraHPortS"]["children"][1]["infraRsAccBaseGrp"]

    assert_matches(rs_acc_base_grp, {"attributes": {"tDn": "uni/infra/funcprof/accbundle-po1"}})


def test_no_tags_renders_valid_json_with_exactly_two_children(render_intf_selector):
    # Regression test: the comma-boundary check before the tags loop used to
    # reference the nonexistent `intf.tag` instead of `intf.tags`, and a
    # hardcoded trailing comma after infraRsAccBaseGrp made this the *only*
    # broken case - i.e. it crashed whenever there were no tags at all.
    intf = {"card": 1, "intf_pol_group": "server1"}
    body = _render(render_intf_selector, intf)

    assert len(body["infraHPortS"]["children"]) == 2


def test_tags_render_with_state(render_intf_selector):
    intf = {
        "card": 1,
        "intf_pol_group": "server1",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = _render(render_intf_selector, intf)
    children = body["infraHPortS"]["children"]

    assert len(children) == 4  # infraPortBlk + infraRsAccBaseGrp + 2 tags
    assert_matches(children[-2:], [
        {"tagAnnotation": {"attributes": {"key": "tag1", "value": "value1", "status": "created,modified"}}},
        {"tagAnnotation": {"attributes": {"key": "tag2", "value": "value2", "status": "deleted"}}},
    ])
