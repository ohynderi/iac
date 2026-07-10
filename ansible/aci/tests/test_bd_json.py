from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render):
    bd = {"name": "bd1", "vrf": "vrf1", "state": "absent"}
    body = render("bd.json.j2", bd_name="bd1", bd=bd)

    assert_matches(body, {
        "fvBD": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
                "epMoveDetectMode": ABSENT,
                "unicastRoute": ABSENT,
                "unkMacUcastAct": ABSENT,
                "unkMcastAct": ABSENT,
                "arpFlood": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_state_present_minimal_renders_fvrsctx_only_with_computed_defaults(render):
    bd = {"name": "bd1", "vrf": "vrf1", "state": "present"}
    body = render("bd.json.j2", bd_name="bd1", bd=bd)

    assert_matches(body, {
        "fvBD": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
                "epMoveDetectMode": "",
                "unicastRoute": "no",
                "unkMacUcastAct": "flood",
                "unkMcastAct": "flood",
                "arpFlood": "yes",
            },
            "children": [
                {
                    "fvRsCtx": {
                        "attributes": {
                            "tnFvCtxName": "vrf1",
                            "status": "created,modified",
                        },
                    },
                },
            ],
        },
    })


def test_state_undefined_at_root_does_not_crash(render):
    # Regression test: this used to raise "'dict object' has no attribute
    # 'state'" once the task's `when:` was switched to has_nested_state,
    # which lets this task run without bd.state ever being set.
    bd = {"name": "bd1", "vrf": "vrf1"}
    body = render("bd.json.j2", bd_name="bd1", bd=bd)

    assert_matches(body, {
        "fvBD": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
            },
            "children": [
                {"fvRsCtx": {"attributes": {"tnFvCtxName": "vrf1"}}},
            ],
        },
    })


def test_state_undefined_at_root_still_renders_nested_tag_state(render):
    bd = {
        "name": "bd1",
        "vrf": "vrf1",
        "tags": [{"name": "tag1", "value": "value1", "state": "absent"}],
    }
    body = render("bd.json.j2", bd_name="bd1", bd=bd)

    assert_matches(body, {
        "fvBD": {
            "children": [
                {"fvRsCtx": {"attributes": {"tnFvCtxName": "vrf1"}}},
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


def test_description_and_endpoint_move_detection_overrides(render):
    bd = {
        "name": "bd1",
        "vrf": "vrf1",
        "description": "my bd",
        "endpoint_move_detection": "garp",
    }
    body = render("bd.json.j2", bd_name="bd1", bd=bd)

    assert_matches(body, {
        "fvBD": {
            "attributes": {
                "descr": "my bd",
                "epMoveDetectMode": "garp",
            },
        },
    })


def test_unicast_routing_enabled_changes_computed_defaults(render):
    bd = {"name": "bd1", "vrf": "vrf1", "unicast_routing": True}
    body = render("bd.json.j2", bd_name="bd1", bd=bd)

    assert_matches(body, {
        "fvBD": {
            "attributes": {
                "unicastRoute": "yes",
                "unkMacUcastAct": "proxy",
                "unkMcastAct": "opt-flood",
                "arpFlood": "no",
            },
        },
    })


def test_l2_l3_unknown_and_arp_flood_overrides(render):
    bd = {
        "name": "bd1",
        "vrf": "vrf1",
        "unicast_routing": True,
        "l2_unknown_unicast": "flood",
        "l3_unknown_multicast": "flood",
        "arp_flood": True,
    }
    body = render("bd.json.j2", bd_name="bd1", bd=bd)

    assert_matches(body, {
        "fvBD": {
            "attributes": {
                "unicastRoute": "yes",
                "unkMacUcastAct": "flood",
                "unkMcastAct": "flood",
                "arpFlood": "yes",
            },
        },
    })


def test_tags_render_with_state(render):
    bd = {
        "name": "bd1",
        "vrf": "vrf1",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render("bd.json.j2", bd_name="bd1", bd=bd)

    assert_matches(body, {
        "fvBD": {
            "children": [
                {"fvRsCtx": {"attributes": {"tnFvCtxName": "vrf1"}}},
                {
                    "tagAnnotation": {
                        "attributes": {
                            "key": "tag1",
                            "value": "value1",
                            "status": "created,modified",
                        },
                    },
                },
                {
                    "tagAnnotation": {
                        "attributes": {
                            "key": "tag2",
                            "value": "value2",
                            "status": "deleted",
                        },
                    },
                },
            ],
        },
    })


def test_subnets_render_with_preferred_scope_and_state(render):
    # Also a regression test for the double-comma bug: rendering must
    # produce valid JSON with exactly 2 subnet children when there's more
    # than one subnet.
    bd = {
        "name": "bd1",
        "vrf": "vrf1",
        "subnets": [
            {"ip": "10.0.0.1/24", "scope": "public"},
            {"ip": "10.10.0.1/24", "state": "absent"},
        ],
    }
    body = render("bd.json.j2", bd_name="bd1", bd=bd)

    assert_matches(body, {
        "fvBD": {
            "children": [
                {"fvRsCtx": {"attributes": {"tnFvCtxName": "vrf1"}}},
                {
                    "fvSubnet": {
                        "attributes": {
                            "ip": "10.0.0.1/24",
                            "preferred": "true",
                            "scope": "public",
                            "status": "created,modified",
                        },
                    },
                },
                {
                    "fvSubnet": {
                        "attributes": {
                            "ip": "10.10.0.1/24",
                            "preferred": "false",
                            "scope": ABSENT,
                            "status": "deleted",
                        },
                    },
                },
            ],
        },
    })


def test_l3outs_render_with_state(render):
    # Also a regression test for the double-comma bug with 2+ l3outs.
    bd = {
        "name": "bd1",
        "vrf": "vrf1",
        "l3outs": [
            {"name": "OSPF1"},
            {"name": "OSPF2", "state": "absent"},
        ],
    }
    body = render("bd.json.j2", bd_name="bd1", bd=bd)

    assert_matches(body, {
        "fvBD": {
            "children": [
                {"fvRsCtx": {"attributes": {"tnFvCtxName": "vrf1"}}},
                {
                    "fvRsBDToOut": {
                        "attributes": {
                            "tnL3extOutName": "OSPF1",
                            "status": "created,modified",
                        },
                    },
                },
                {
                    "fvRsBDToOut": {
                        "attributes": {
                            "tnL3extOutName": "OSPF2",
                            "status": "deleted",
                        },
                    },
                },
            ],
        },
    })


def test_subnet_state_absent_does_not_affect_other_children(render):
    bd = {
        "name": "bd1",
        "vrf": "vrf1",
        "tags": [
            {"name": "tag1", "value": "value1"},
        ],
        "subnets": [
            {"ip": "10.0.0.1/24"},
            {"ip": "10.10.0.1/24", "state": "absent"},
        ],
        "l3outs": [
            {"name": "OSPF1"},
        ],
    }
    body = render("bd.json.j2", bd_name="bd1", bd=bd)

    assert_matches(body, {
        "fvBD": {
            "children": [
                {"fvRsCtx": {"attributes": {"tnFvCtxName": "vrf1"}}},
                {
                    "tagAnnotation": {
                        "attributes": {
                            "key": "tag1",
                            "status": "created,modified",
                        },
                    },
                },
                {
                    "fvSubnet": {
                        "attributes": {
                            "ip": "10.0.0.1/24",
                            "status": "created,modified",
                        },
                    },
                },
                {
                    "fvSubnet": {
                        "attributes": {
                            "ip": "10.10.0.1/24",
                            "status": "deleted",
                        },
                    },
                },
                {
                    "fvRsBDToOut": {
                        "attributes": {
                            "tnL3extOutName": "OSPF1",
                            "status": "created,modified",
                        },
                    },
                },
            ],
        },
    })
