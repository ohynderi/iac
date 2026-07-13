from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render):
    l3out = {"name": "l3out1", "state": "absent", "vrf": "v", "domain": "d"}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
                "enforceRtctrl": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_state_present_minimal_renders_defaults(render):
    l3out = {"name": "l3out1", "state": "present", "vrf": "v", "domain": "d"}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
                "enforceRtctrl": "import",
            },
            "children": [
                {"l3extRsL3DomAtt": {"attributes": {"tDn": "uni/l3dom-d"}}},
                {"l3extRsEctx": {"attributes": {"tnFvCtxName": "v"}}},
            ],
        },
    })


def test_state_undefined_at_root_does_not_crash(render):
    # Regression test: this used to raise "'dict object' has no attribute
    # 'state'" once the task's `when:` was switched to has_nested_state,
    # which lets this task run without l3out.state ever being set.
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d"}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "attributes": {"status": "created,modified"},
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
            ],
        },
    })


def test_state_undefined_at_root_still_renders_nested_tag_state(render):
    l3out = {
        "name": "l3out1", "vrf": "v", "domain": "d",
        "tags": [{"name": "tag1", "value": "value1", "state": "absent"}],
    }
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"tagAnnotation": {"attributes": {"key": "tag1", "status": "deleted"}}},
            ],
        },
    })


def test_description_override(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "description": "my l3out"}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {"l3extOut": {"attributes": {"descr": "my l3out"}}})


def test_import_export_route_control_both_true(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d",
              "import_route_control": True, "export_route_control": True}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {"l3extOut": {"attributes": {"enforceRtctrl": "import,export"}}})


def test_import_export_route_control_export_only(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d",
              "import_route_control": False, "export_route_control": True}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {"l3extOut": {"attributes": {"enforceRtctrl": "export"}}})


def test_import_export_route_control_neither(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d",
              "import_route_control": False, "export_route_control": False}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {"l3extOut": {"attributes": {"enforceRtctrl": ""}}})


def test_tags_render_with_state(render):
    l3out = {
        "name": "l3out1", "vrf": "v", "domain": "d",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"tagAnnotation": {"attributes": {"key": "tag1", "status": "created,modified"}}},
                {"tagAnnotation": {"attributes": {"key": "tag2", "status": "deleted"}}},
            ],
        },
    })


def test_external_epg_renders_with_defaults(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "external_epgs": [{"name": "ext1"}]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {
                    "l3extInstP": {
                        "attributes": {
                            "name": "ext1",
                            "descr": "",
                            "status": "created,modified",
                        },
                        "children": [],
                    },
                },
            ],
        },
    })


def test_external_epg_description_override(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d",
              "external_epgs": [{"name": "ext1", "description": "my ext epg"}]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extInstP": {"attributes": {"descr": "my ext epg"}}},
            ],
        },
    })


def test_external_epg_preferred_group_member_default(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "external_epgs": [{"name": "ext1"}]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extInstP": {"attributes": {"prefGrMemb": "exclude"}}},
            ],
        },
    })


def test_external_epg_preferred_group_member_override(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d",
              "external_epgs": [{"name": "ext1", "preferred_group_member": "include"}]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extInstP": {"attributes": {"prefGrMemb": "include"}}},
            ],
        },
    })


def test_external_epg_contracts_consumer_and_provider_with_state(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "external_epgs": [
        {"name": "ext1", "contracts": [
            {"name": "c1", "type": "consumer"},
            {"name": "c2", "type": "provider", "state": "absent"},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extInstP": {"children": [
                    {"fvRsCons": {"attributes": {"tnVzBrCPName": "c1", "status": "created,modified"}}},
                    {"fvRsProv": {"attributes": {"tnVzBrCPName": "c2", "status": "deleted"}}},
                ]}},
            ],
        },
    })


def test_external_epg_subnets_and_contracts_together(render):
    # Regression test: the comma between the subnets loop and the contracts
    # loop is only emitted when both lists are non-empty.
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "external_epgs": [
        {
            "name": "ext1",
            "subnets": [{"ip": "0.0.0.0/0"}],
            "contracts": [{"name": "c1", "type": "provider"}],
        },
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extInstP": {"children": [
                    {"l3extSubnet": {"attributes": {"ip": "0.0.0.0/0"}}},
                    {"fvRsProv": {"attributes": {"tnVzBrCPName": "c1"}}},
                ]}},
            ],
        },
    })


def test_external_epg_contract_state_absent_does_not_affect_other_contracts(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "external_epgs": [
        {"name": "ext1", "contracts": [
            {"name": "c1", "type": "consumer", "state": "absent"},
            {"name": "c2", "type": "consumer"},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extInstP": {"children": [
                    {"fvRsCons": {"attributes": {"tnVzBrCPName": "c1", "status": "deleted"}}},
                    {"fvRsCons": {"attributes": {"tnVzBrCPName": "c2", "status": "created,modified"}}},
                ]}},
            ],
        },
    })


def test_external_epg_state_absent_does_not_affect_other_epgs(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "external_epgs": [
        {"name": "ext1", "state": "absent"},
        {"name": "ext2"},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extInstP": {"attributes": {"name": "ext1", "status": "deleted"}}},
                {"l3extInstP": {"attributes": {"name": "ext2", "status": "created,modified"}}},
            ],
        },
    })


def test_external_epg_state_absent_omits_descr_and_pref_gr_memb(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "external_epgs": [
        {"name": "ext1", "state": "absent", "description": "should be omitted"},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extInstP": {"attributes": {
                    "status": "deleted",
                    "descr": ABSENT,
                    "prefGrMemb": ABSENT,
                }}},
            ],
        },
    })


def test_external_epg_state_absent_still_renders_children(render):
    # A deleted external EPG's own relations/subnets/tags still render
    # (deletion of the parent cascades on the APIC side), matching the
    # pattern used for route_map contexts.
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "external_epgs": [{
        "name": "ext1", "state": "absent",
        "tags": [{"name": "tag1", "value": "value1"}],
        "subnets": [{"ip": "0.0.0.0/0"}],
        "contracts": [{"name": "c1", "type": "consumer"}],
    }]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extInstP": {"children": [
                    {"tagAnnotation": {}},
                    {"l3extSubnet": {}},
                    {"fvRsCons": {}},
                ]}},
            ],
        },
    })


def test_external_epg_tags_render_with_state(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "external_epgs": [{
        "name": "ext1",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extInstP": {"children": [
                    {"tagAnnotation": {"attributes": {"key": "tag1", "status": "created,modified"}}},
                    {"tagAnnotation": {"attributes": {"key": "tag2", "status": "deleted"}}},
                ]}},
            ],
        },
    })


def test_external_epg_tags_subnets_and_contracts_together(render):
    # Regression test: with three independent optional loops (tags, subnets,
    # contracts) and no guaranteed-first child, every pairwise comma boundary
    # must fire only when both sides actually have content.
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "external_epgs": [{
        "name": "ext1",
        "tags": [{"name": "tag1", "value": "value1"}],
        "subnets": [{"ip": "0.0.0.0/0"}],
        "contracts": [{"name": "c1", "type": "provider"}],
    }]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extInstP": {"children": [
                    {"tagAnnotation": {"attributes": {"key": "tag1"}}},
                    {"l3extSubnet": {"attributes": {"ip": "0.0.0.0/0"}}},
                    {"fvRsProv": {"attributes": {"tnVzBrCPName": "c1"}}},
                ]}},
            ],
        },
    })


def test_external_epg_tags_and_contracts_without_subnets(render):
    # Comma boundary between tags and contracts must fire even when the
    # middle group (subnets) is empty.
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "external_epgs": [{
        "name": "ext1",
        "tags": [{"name": "tag1", "value": "value1"}],
        "contracts": [{"name": "c1", "type": "consumer"}],
    }]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extInstP": {"children": [
                    {"tagAnnotation": {}},
                    {"fvRsCons": {}},
                ]}},
            ],
        },
    })


def test_external_epg_subnet_description_default(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "external_epgs": [
        {"name": "ext1", "subnets": [{"ip": "0.0.0.0/0"}]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extInstP": {"children": [
                    {"l3extSubnet": {"attributes": {"descr": ""}}},
                ]}},
            ],
        },
    })


def test_external_epg_subnet_description_override(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "external_epgs": [
        {"name": "ext1", "subnets": [{"ip": "0.0.0.0/0", "description": "my subnet"}]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extInstP": {"children": [
                    {"l3extSubnet": {"attributes": {"descr": "my subnet"}}},
                ]}},
            ],
        },
    })


def test_external_epg_subnet_aggregate_and_scope_flags(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "external_epgs": [
        {"name": "ext1", "subnets": [{
            "ip": "0.0.0.0/0",
            "agg_export": True, "agg_inport": True, "agg_shared": True,
            "export_route_ctrl": True, "external_epg": True,
            "shared_route_ctrl": True, "shared_security_import": True,
        }]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extInstP": {"children": [
                    {"l3extSubnet": {"attributes": {
                        "ip": "0.0.0.0/0",
                        "aggregate": "export-rtctrl,inport-rtctrl,shared-rtctrl",
                        "scope": "export-rtctrl,import-security,shared-rtctrl,shared-security",
                        "status": "created,modified",
                    }}},
                ]}},
            ],
        },
    })


def test_external_epg_subnet_with_all_flags_off(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "external_epgs": [
        {"name": "ext1", "subnets": [{"ip": "0.0.0.0/0"}]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extInstP": {"children": [
                    {"l3extSubnet": {"attributes": {"aggregate": "", "scope": ""}}},
                ]}},
            ],
        },
    })


def test_external_epg_subnet_state_absent_does_not_affect_other_subnets(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "external_epgs": [
        {"name": "ext1", "subnets": [
            {"ip": "0.0.0.0/0", "state": "absent"},
            {"ip": "10.0.0.0/8"},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extInstP": {"children": [
                    {"l3extSubnet": {"attributes": {"ip": "0.0.0.0/0", "status": "deleted"}}},
                    {"l3extSubnet": {"attributes": {"ip": "10.0.0.0/8", "status": "created,modified"}}},
                ]}},
            ],
        },
    })


def test_tags_and_external_epgs_and_node_profiles_together(render):
    # Regression test for the l3out/l3out_ext_epg task merge: external_epgs
    # is now rendered by this same template, alongside tags and node
    # profiles, and each independent block's leading comma must still only
    # fire when that specific block is non-empty.
    l3out = {
        "name": "l3out1", "vrf": "v", "domain": "d",
        "tags": [{"name": "tag1", "value": "value1"}],
        "external_epgs": [{"name": "ext1"}],
        "node_profiles": [{"name": "np1"}],
    }
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"tagAnnotation": {}},
                {"l3extInstP": {}},
                {"l3extLNodeP": {}},
            ],
        },
    })


def test_ospf_renders_with_defaults(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d",
              "protocols": {"ospf": {"area_id": "0.0.0.1"}}}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {
                    "ospfExtP": {
                        "attributes": {
                            "areaId": "0.0.0.1",
                            "areaType": "regular",
                            "areaCost": "1",
                            "status": "created,modified",
                        },
                    },
                },
            ],
        },
    })


def test_ospf_area_id_accepts_backbone(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d",
              "protocols": {"ospf": {"area_id": "backbone"}}}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"ospfExtP": {"attributes": {"areaId": "backbone"}}},
            ],
        },
    })


def test_ospf_area_type_and_cost_overrides(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d",
              "protocols": {"ospf": {"area_id": "1", "area_type": "stub", "area_cost": 5}}}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"ospfExtP": {"attributes": {"areaType": "stub", "areaCost": "5"}}},
            ],
        },
    })


def test_ospf_state_absent(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d",
              "protocols": {"ospf": {"area_id": "1", "state": "absent"}}}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"ospfExtP": {"attributes": {"status": "deleted"}}},
            ],
        },
    })


def test_bgp_bare_key_enables_bgp_ext_p(render):
    # protocols.bgp can be a bare YAML key (parses to None) rather than {}.
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "protocols": {"bgp": None}}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"bgpExtP": {"attributes": {"status": "created,modified"}}},
            ],
        },
    })


def test_bgp_state_absent(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "protocols": {"bgp": {"state": "absent"}}}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"bgpExtP": {"attributes": {"status": "deleted"}}},
            ],
        },
    })


def test_ospf_and_bgp_together(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d",
              "protocols": {"ospf": {"area_id": "1"}, "bgp": {}}}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"ospfExtP": {}},
                {"bgpExtP": {}},
            ],
        },
    })


def test_pim_true_renders_pim_ext_p(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "PIM": True}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {
                    "pimExtP": {
                        "attributes": {
                            "annotation": "",
                            "enabledAf": "ipv4-mcast",
                            "name": "pim",
                            "status": "created,modified",
                        },
                    },
                },
            ],
        },
    })


def test_pim_false_renders_deleted(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "PIM": False}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"pimExtP": {"attributes": {"status": "deleted"}}},
            ],
        },
    })


def test_pim_toggle_true_to_false(render):
    # Confirms flipping the PIM flag from enabled to disabled converts
    # pimExtP's status from created,modified to deleted, so the APIC
    # actually removes the object instead of just seeing it omitted.
    l3out_enabled = {"name": "l3out1", "vrf": "v", "domain": "d", "PIM": True}
    body_enabled = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out_enabled, tenant={"name": "t1"})

    assert_matches(body_enabled, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"pimExtP": {"attributes": {"status": "created,modified"}}},
            ],
        },
    })

    l3out_disabled = {"name": "l3out1", "vrf": "v", "domain": "d", "PIM": False}
    body_disabled = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out_disabled, tenant={"name": "t1"})

    assert_matches(body_disabled, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"pimExtP": {"attributes": {"status": "deleted"}}},
            ],
        },
    })


def test_pim_omitted_when_not_defined(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d"}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
            ],
        },
    })


def test_router_renders_with_defaults(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "routers": [{"pod": 1, "leaf_id": 101, "router_id": "1.1.1.1"}]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {
                    "l3extLNodeP": {
                        "attributes": {"name": "np1", "status": "created,modified"},
                        "children": [
                            {
                                "l3extRsNodeL3OutAtt": {
                                    "attributes": {
                                        "tDn": "topology/pod-1/node-101",
                                        "rtrId": "1.1.1.1",
                                        "rtrIdLoopBack": "no",
                                        "status": "created,modified",
                                    },
                                },
                            },
                        ],
                    },
                },
            ],
        },
    })


def test_router_loopback_override(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "routers": [{"pod": 1, "leaf_id": 101, "router_id": "1.1.1.1", "loopback": True}]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extRsNodeL3OutAtt": {"attributes": {"rtrIdLoopBack": "yes"}}},
                ]}},
            ],
        },
    })


def test_router_state_absent_does_not_affect_other_routers(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "routers": [
            {"pod": 1, "leaf_id": 101, "router_id": "1.1.1.1", "state": "absent"},
            {"pod": 1, "leaf_id": 102, "router_id": "1.1.1.2"},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extRsNodeL3OutAtt": {"attributes": {"rtrId": "1.1.1.1", "status": "deleted"}}},
                    {"l3extRsNodeL3OutAtt": {"attributes": {"rtrId": "1.1.1.2", "status": "created,modified"}}},
                ]}},
            ],
        },
    })


def test_static_routes_are_broadcast_to_every_router(render):
    # Deliberate design choice (confirmed): static_routes live on the node
    # profile, not per-router, and are attached identically to every router
    # in that profile.
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {
            "name": "np1",
            "routers": [
                {"pod": 1, "leaf_id": 101, "router_id": "1.1.1.1"},
                {"pod": 1, "leaf_id": 102, "router_id": "1.1.1.2"},
            ],
            "static_routes": [{"prefix": "0.0.0.0/0", "nhop": "9.9.9.9"}],
        },
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extRsNodeL3OutAtt": {
                        "attributes": {"rtrId": "1.1.1.1"},
                        "children": [
                            {"ipRouteP": {"attributes": {"ip": "0.0.0.0/0"}, "children": [
                                {"ipNexthopP": {"attributes": {"nhAddr": "9.9.9.9"}}},
                            ]}},
                        ],
                    }},
                    {"l3extRsNodeL3OutAtt": {
                        "attributes": {"rtrId": "1.1.1.2"},
                        "children": [
                            {"ipRouteP": {"attributes": {"ip": "0.0.0.0/0"}}},
                        ],
                    }},
                ]}},
            ],
        },
    })


def test_multiple_static_routes_are_broadcast_identically_to_two_routers(render):
    # Both routers must end up with the exact same two routes, each with its
    # own correct prefix/nexthop pair (not just the same count of children).
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {
            "name": "np1",
            "routers": [
                {"pod": 1, "leaf_id": 101, "router_id": "1.1.1.1"},
                {"pod": 1, "leaf_id": 102, "router_id": "1.1.1.2"},
            ],
            "static_routes": [
                {"prefix": "0.0.0.0/0", "nhop": "10.0.0.254"},
                {"prefix": "10.10.0.0/16", "nhop": "10.0.0.253"},
            ],
        },
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    expected_routes = [
        {"ipRouteP": {
            "attributes": {"ip": "0.0.0.0/0", "status": "created,modified"},
            "children": [
                {"ipNexthopP": {"attributes": {"nhAddr": "10.0.0.254", "status": "created,modified"}}},
            ],
        }},
        {"ipRouteP": {
            "attributes": {"ip": "10.10.0.0/16", "status": "created,modified"},
            "children": [
                {"ipNexthopP": {"attributes": {"nhAddr": "10.0.0.253", "status": "created,modified"}}},
            ],
        }},
    ]

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extRsNodeL3OutAtt": {
                        "attributes": {"rtrId": "1.1.1.1"},
                        "children": expected_routes,
                    }},
                    {"l3extRsNodeL3OutAtt": {
                        "attributes": {"rtrId": "1.1.1.2"},
                        "children": expected_routes,
                    }},
                ]}},
            ],
        },
    })


def test_static_route_state_absent(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {
            "name": "np1",
            "routers": [{"pod": 1, "leaf_id": 101, "router_id": "1.1.1.1"}],
            "static_routes": [{"prefix": "0.0.0.0/0", "nhop": "9.9.9.9", "state": "absent"}],
        },
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extRsNodeL3OutAtt": {"children": [
                        {"ipRouteP": {
                            "attributes": {"status": "deleted"},
                            "children": [{"ipNexthopP": {"attributes": {"status": "deleted"}}}],
                        }},
                    ]}},
                ]}},
            ],
        },
    })


def test_multiple_static_routes_state_absent_does_not_affect_other_routes(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {
            "name": "np1",
            "routers": [{"pod": 1, "leaf_id": 101, "router_id": "1.1.1.1"}],
            "static_routes": [
                {"prefix": "0.0.0.0/0", "nhop": "10.0.0.254"},
                {"prefix": "10.10.0.0/16", "nhop": "10.0.0.253", "state": "absent"},
            ],
        },
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extRsNodeL3OutAtt": {"children": [
                        {"ipRouteP": {
                            "attributes": {"ip": "0.0.0.0/0", "status": "created,modified"},
                            "children": [
                                {"ipNexthopP": {"attributes": {"nhAddr": "10.0.0.254", "status": "created,modified"}}},
                            ],
                        }},
                        {"ipRouteP": {
                            "attributes": {"ip": "10.10.0.0/16", "status": "deleted"},
                            "children": [
                                {"ipNexthopP": {"attributes": {"nhAddr": "10.0.0.253", "status": "deleted"}}},
                            ],
                        }},
                    ]}},
                ]}},
            ],
        },
    })


def test_static_routes_without_any_routers_render_nothing(render):
    # Consequence of the broadcast-to-every-router design: with no routers to
    # broadcast to, the static routes have nowhere to attach.
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "static_routes": [{"prefix": "0.0.0.0/0", "nhop": "10.0.0.254"}]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": []}},
            ],
        },
    })


def test_node_profile_without_static_routes_renders_empty_router_children(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "routers": [{"pod": 1, "leaf_id": 101, "router_id": "1.1.1.1"}]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extRsNodeL3OutAtt": {"children": []}},
                ]}},
            ],
        },
    })


def test_interface_profile_l3_port(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "interface_profiles": [
            {"name": "ip1", "interfaces": {"l3-port": [
                {"pod": 1, "leaf_id": 101, "port": "Eth1/12", "addr": "10.19.0.1/30"},
            ]}},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extLIfP": {
                        "attributes": {"name": "ip1", "status": "created,modified"},
                        "children": [
                            {"l3extRsPathL3OutAtt": {
                                "attributes": {
                                    "addr": "10.19.0.1/30",
                                    "encap": ABSENT,
                                    "mode": ABSENT,
                                    "ifInstT": "l3-port",
                                    "mtu": "inherit",
                                    "tDn": "topology/pod-1/paths-101/pathep-[eth1/12]",
                                    "status": "created,modified",
                                },
                                "children": [],
                            }},
                        ],
                    }},
                ]}},
            ],
        },
    })


def test_interface_profile_sub_interface(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "interface_profiles": [
            {"name": "ip1", "interfaces": {"sub-interface": [
                {"pod": 1, "leaf_id": 101, "ipg": "po-ipg", "vlan": 1025, "addr": "10.2.0.1/30", "mtu": 1500},
            ]}},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extLIfP": {"children": [
                        {"l3extRsPathL3OutAtt": {
                            "attributes": {
                                "addr": "10.2.0.1/30",
                                "encap": "vlan-1025",
                                "mode": ABSENT,
                                "ifInstT": "sub-interface",
                                "mtu": "1500",
                                "tDn": "topology/pod-1/paths-101/pathep-[po-ipg]",
                            },
                        }},
                    ]}},
                ]}},
            ],
        },
    })


def test_interface_profile_svi_single_homed(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "interface_profiles": [
            {"name": "ip1", "interfaces": {"svi": [
                {"pod": 1, "leaf_id": 101, "ipg": "ipg1", "mode": "native", "vlan": 10, "addr": "10.0.0.1/30"},
            ]}},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extLIfP": {"children": [
                        {"l3extRsPathL3OutAtt": {
                            "attributes": {
                                "addr": "10.0.0.1/30",
                                "encap": "vlan-10",
                                "mode": "native",
                                "ifInstT": "ext-svi",
                                "tDn": "topology/pod-1/paths-101/pathep-[ipg1]",
                            },
                            "children": [],
                        }},
                    ]}},
                ]}},
            ],
        },
    })


def test_interface_profile_svi_vpc_members(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "interface_profiles": [
            {"name": "ip1", "interfaces": {"svi": [
                {
                    "pod": 1, "leaf_id": 101, "peer_leaf_id": 102, "ipg": "vpc-ipg",
                    "mode": "regular", "vlan": 20, "addr": "10.1.0.1/30", "peer_addr": "10.1.0.2/30",
                },
            ]}},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extLIfP": {"children": [
                        {"l3extRsPathL3OutAtt": {
                            "attributes": {
                                "addr": "0.0.0.0",
                                "tDn": "topology/pod-1/protpaths-101-102/pathep-[vpc-ipg]",
                            },
                            "children": [
                                {"l3extMember": {"attributes": {"addr": "10.1.0.1/30", "side": "A"}}},
                                {"l3extMember": {"attributes": {"addr": "10.1.0.2/30", "side": "B"}}},
                            ],
                        }},
                    ]}},
                ]}},
            ],
        },
    })


def test_interface_state_absent_does_not_affect_other_interfaces(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "interface_profiles": [
            {"name": "ip1", "interfaces": {"l3-port": [
                {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "addr": "10.0.0.1/30", "state": "absent"},
                {"pod": 1, "leaf_id": 101, "port": "Eth1/2", "addr": "10.0.0.5/30"},
            ]}},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extLIfP": {"children": [
                        {"l3extRsPathL3OutAtt": {"attributes": {"addr": "10.0.0.1/30", "status": "deleted"}}},
                        {"l3extRsPathL3OutAtt": {"attributes": {"addr": "10.0.0.5/30", "status": "created,modified"}}},
                    ]}},
                ]}},
            ],
        },
    })


def test_interface_profiles_with_all_three_buckets(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "interface_profiles": [
            {"name": "ip1", "interfaces": {
                "svi": [{"pod": 1, "leaf_id": 101, "ipg": "ipg1", "mode": "regular", "vlan": 1, "addr": "10.0.1.1/30"}],
                "sub-interface": [{"pod": 1, "leaf_id": 101, "ipg": "ipg2", "vlan": 2, "addr": "10.0.2.1/30"}],
                "l3-port": [{"pod": 1, "leaf_id": 101, "port": "Eth1/1", "addr": "10.0.3.1/30"}],
            }},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extLIfP": {"children": [
                        {"l3extRsPathL3OutAtt": {"attributes": {"ifInstT": "ext-svi"}}},
                        {"l3extRsPathL3OutAtt": {"attributes": {"ifInstT": "sub-interface"}}},
                        {"l3extRsPathL3OutAtt": {"attributes": {"ifInstT": "l3-port"}}},
                    ]}},
                ]}},
            ],
        },
    })


def test_connectivity_profile_renders_with_defaults(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "interface_profiles": [
            {"name": "ip1", "interfaces": {"l3-port": [
                {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "addr": "10.0.0.1/30",
                 "connectivity_profiles": [{"peer_address": "2.2.2.2", "remote_asn": 65001}]},
            ]}},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extLIfP": {"children": [
                        {"l3extRsPathL3OutAtt": {"children": [
                            {"bgpPeerP": {
                                "attributes": {
                                    "addr": "2.2.2.2",
                                    "ctrl": "",
                                    "descr": "",
                                    "peerCtrl": "",
                                    "ttl": "1",
                                    "weight": "0",
                                    "status": "created,modified",
                                },
                                "children": [
                                    {"bgpAsP": {"attributes": {"asn": "65001"}}},
                                ],
                            }},
                        ]}},
                    ]}},
                ]}},
            ],
        },
    })


def test_connectivity_profile_with_local_asn_and_route_maps(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "interface_profiles": [
            {"name": "ip1", "interfaces": {"l3-port": [
                {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "addr": "10.0.0.1/30",
                 "connectivity_profiles": [{
                     "peer_address": "2.2.2.2", "remote_asn": 65001, "local_asn": 65000,
                     "send_community": True, "send_extended_community": True, "bfd": True,
                     "route_maps": [{"name": "rm1", "direction": "import"}],
                 }]},
            ]}},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extLIfP": {"children": [
                        {"l3extRsPathL3OutAtt": {"children": [
                            {"bgpPeerP": {
                                "attributes": {"ctrl": "send-com,send-ext-com", "peerCtrl": "bfd"},
                                "children": [
                                    {"bgpAsP": {"attributes": {"asn": "65001"}}},
                                    {"bgpLocalAsnP": {"attributes": {"localAsn": "65000"}}},
                                    {"bgpRsPeerToProfile": {
                                        "attributes": {
                                            "tDn": "uni/tn-t1/prof-rm1",
                                            "direction": "import",
                                            "status": "created,modified",
                                        },
                                    }},
                                ],
                            }},
                        ]}},
                    ]}},
                ]}},
            ],
        },
    })


def test_connectivity_profile_description_override(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "interface_profiles": [
            {"name": "ip1", "interfaces": {"l3-port": [
                {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "addr": "10.0.0.1/30",
                 "connectivity_profiles": [{
                     "peer_address": "2.2.2.2", "remote_asn": 65001, "description": "my peer",
                 }]},
            ]}},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extLIfP": {"children": [
                        {"l3extRsPathL3OutAtt": {"children": [
                            {"bgpPeerP": {"attributes": {"descr": "my peer"}}},
                        ]}},
                    ]}},
                ]}},
            ],
        },
    })


def test_connectivity_profile_send_community_only(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "interface_profiles": [
            {"name": "ip1", "interfaces": {"l3-port": [
                {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "addr": "10.0.0.1/30",
                 "connectivity_profiles": [{
                     "peer_address": "2.2.2.2", "remote_asn": 65001, "send_community": True,
                 }]},
            ]}},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extLIfP": {"children": [
                        {"l3extRsPathL3OutAtt": {"children": [
                            {"bgpPeerP": {"attributes": {"ctrl": "send-com"}}},
                        ]}},
                    ]}},
                ]}},
            ],
        },
    })


def test_connectivity_profile_send_extended_community_only(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "interface_profiles": [
            {"name": "ip1", "interfaces": {"l3-port": [
                {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "addr": "10.0.0.1/30",
                 "connectivity_profiles": [{
                     "peer_address": "2.2.2.2", "remote_asn": 65001, "send_extended_community": True,
                 }]},
            ]}},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extLIfP": {"children": [
                        {"l3extRsPathL3OutAtt": {"children": [
                            {"bgpPeerP": {"attributes": {"ctrl": "send-ext-com"}}},
                        ]}},
                    ]}},
                ]}},
            ],
        },
    })


def test_connectivity_profile_ttl_and_weight_overrides(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "interface_profiles": [
            {"name": "ip1", "interfaces": {"l3-port": [
                {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "addr": "10.0.0.1/30",
                 "connectivity_profiles": [{
                     "peer_address": "2.2.2.2", "remote_asn": 65001, "ttl": 16, "weight": 100,
                 }]},
            ]}},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extLIfP": {"children": [
                        {"l3extRsPathL3OutAtt": {"children": [
                            {"bgpPeerP": {"attributes": {"ttl": "16", "weight": "100"}}},
                        ]}},
                    ]}},
                ]}},
            ],
        },
    })


def test_connectivity_profile_state_absent(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "interface_profiles": [
            {"name": "ip1", "interfaces": {"l3-port": [
                {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "addr": "10.0.0.1/30",
                 "connectivity_profiles": [{
                     "peer_address": "2.2.2.2", "remote_asn": 65001, "state": "absent",
                 }]},
            ]}},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extLIfP": {"children": [
                        {"l3extRsPathL3OutAtt": {"children": [
                            {"bgpPeerP": {"attributes": {"status": "deleted"}}},
                        ]}},
                    ]}},
                ]}},
            ],
        },
    })


def test_multiple_connectivity_profiles_state_absent_does_not_affect_other_peers(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "interface_profiles": [
            {"name": "ip1", "interfaces": {"l3-port": [
                {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "addr": "10.0.0.1/30",
                 "connectivity_profiles": [
                     {"peer_address": "2.2.2.2", "remote_asn": 65001, "state": "absent"},
                     {"peer_address": "3.3.3.3", "remote_asn": 65002},
                 ]},
            ]}},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extLIfP": {"children": [
                        {"l3extRsPathL3OutAtt": {"children": [
                            {"bgpPeerP": {"attributes": {"addr": "2.2.2.2", "status": "deleted"}}},
                            {"bgpPeerP": {"attributes": {"addr": "3.3.3.3", "status": "created,modified"}}},
                        ]}},
                    ]}},
                ]}},
            ],
        },
    })


def test_connectivity_profile_route_maps_without_local_asn(render):
    # Regression test: the comma before the route_maps block must not depend
    # on local_asn also being set (bgpAsP is the guaranteed first child).
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "interface_profiles": [
            {"name": "ip1", "interfaces": {"l3-port": [
                {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "addr": "10.0.0.1/30",
                 "connectivity_profiles": [{
                     "peer_address": "2.2.2.2", "remote_asn": 65001,
                     "route_maps": [{"name": "rm1", "direction": "import"}],
                 }]},
            ]}},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extLIfP": {"children": [
                        {"l3extRsPathL3OutAtt": {"children": [
                            {"bgpPeerP": {"children": [
                                {"bgpAsP": {}},
                                {"bgpRsPeerToProfile": {"attributes": {"direction": "import"}}},
                            ]}},
                        ]}},
                    ]}},
                ]}},
            ],
        },
    })


def test_connectivity_profile_route_map_export_direction_and_state_absent(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "interface_profiles": [
            {"name": "ip1", "interfaces": {"l3-port": [
                {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "addr": "10.0.0.1/30",
                 "connectivity_profiles": [{
                     "peer_address": "2.2.2.2", "remote_asn": 65001,
                     "route_maps": [
                         {"name": "rm1", "direction": "export"},
                         {"name": "rm2", "direction": "import", "state": "absent"},
                     ],
                 }]},
            ]}},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extLIfP": {"children": [
                        {"l3extRsPathL3OutAtt": {"children": [
                            {"bgpPeerP": {"children": [
                                {"bgpAsP": {}},
                                {"bgpRsPeerToProfile": {
                                    "attributes": {
                                        "tDn": "uni/tn-t1/prof-rm1",
                                        "direction": "export",
                                        "status": "created,modified",
                                    },
                                }},
                                {"bgpRsPeerToProfile": {
                                    "attributes": {
                                        "tDn": "uni/tn-t1/prof-rm2",
                                        "direction": "import",
                                        "status": "deleted",
                                    },
                                }},
                            ]}},
                        ]}},
                    ]}},
                ]}},
            ],
        },
    })


def test_connectivity_profile_route_maps_both_directions_same_name(render):
    # Same route_map name attached twice to one peer, once per direction --
    # a common real-world pattern (one map used for both import and export).
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "interface_profiles": [
            {"name": "ip1", "interfaces": {"l3-port": [
                {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "addr": "10.0.0.1/30",
                 "connectivity_profiles": [{
                     "peer_address": "2.2.2.2", "remote_asn": 65001,
                     "route_maps": [
                         {"name": "rm-to-isp", "direction": "import"},
                         {"name": "rm-to-isp", "direction": "export"},
                     ],
                 }]},
            ]}},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extLIfP": {"children": [
                        {"l3extRsPathL3OutAtt": {"children": [
                            {"bgpPeerP": {"children": [
                                {"bgpAsP": {}},
                                {"bgpRsPeerToProfile": {
                                    "attributes": {
                                        "tDn": "uni/tn-t1/prof-rm-to-isp",
                                        "direction": "import",
                                        "status": "created,modified",
                                    },
                                }},
                                {"bgpRsPeerToProfile": {
                                    "attributes": {
                                        "tDn": "uni/tn-t1/prof-rm-to-isp",
                                        "direction": "export",
                                        "status": "created,modified",
                                    },
                                }},
                            ]}},
                        ]}},
                    ]}},
                ]}},
            ],
        },
    })


def test_connectivity_profile_route_maps_different_names_per_peer(render):
    # Sibling isolation across two different peers on the same interface,
    # each with its own independent route_maps list.
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "interface_profiles": [
            {"name": "ip1", "interfaces": {"l3-port": [
                {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "addr": "10.0.0.1/30",
                 "connectivity_profiles": [
                     {
                         "peer_address": "2.2.2.2", "remote_asn": 65001,
                         "route_maps": [{"name": "rm-peer-a", "direction": "import"}],
                     },
                     {
                         "peer_address": "3.3.3.3", "remote_asn": 65002,
                         "route_maps": [{"name": "rm-peer-b", "direction": "export"}],
                     },
                 ]},
            ]}},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extLIfP": {"children": [
                        {"l3extRsPathL3OutAtt": {"children": [
                            {"bgpPeerP": {
                                "attributes": {"addr": "2.2.2.2"},
                                "children": [
                                    {"bgpAsP": {}},
                                    {"bgpRsPeerToProfile": {
                                        "attributes": {"tDn": "uni/tn-t1/prof-rm-peer-a", "direction": "import"},
                                    }},
                                ],
                            }},
                            {"bgpPeerP": {
                                "attributes": {"addr": "3.3.3.3"},
                                "children": [
                                    {"bgpAsP": {}},
                                    {"bgpRsPeerToProfile": {
                                        "attributes": {"tDn": "uni/tn-t1/prof-rm-peer-b", "direction": "export"},
                                    }},
                                ],
                            }},
                        ]}},
                    ]}},
                ]}},
            ],
        },
    })


def test_connectivity_profile_route_maps_empty_list_omits_bgp_rs_peer_to_profile(render):
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {"name": "np1", "interface_profiles": [
            {"name": "ip1", "interfaces": {"l3-port": [
                {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "addr": "10.0.0.1/30",
                 "connectivity_profiles": [{
                     "peer_address": "2.2.2.2", "remote_asn": 65001, "route_maps": [],
                 }]},
            ]}},
        ]},
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extLIfP": {"children": [
                        {"l3extRsPathL3OutAtt": {"children": [
                            {"bgpPeerP": {"children": [
                                {"bgpAsP": {}},
                            ]}},
                        ]}},
                    ]}},
                ]}},
            ],
        },
    })


def test_routers_and_interface_profiles_together(render):
    # Regression test: the comma between the routers loop and the interface
    # profiles loop is only emitted when both lists are non-empty.
    l3out = {"name": "l3out1", "vrf": "v", "domain": "d", "node_profiles": [
        {
            "name": "np1",
            "routers": [{"pod": 1, "leaf_id": 101, "router_id": "1.1.1.1"}],
            "interface_profiles": [
                {"name": "ip1", "interfaces": {"l3-port": [
                    {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "addr": "10.0.0.1/30"},
                ]}},
            ],
        },
    ]}
    body = render("l3out.json.j2", l3out_name="l3out1", l3out=l3out, tenant={"name": "t1"})

    assert_matches(body, {
        "l3extOut": {
            "children": [
                {"l3extRsL3DomAtt": {}},
                {"l3extRsEctx": {}},
                {"l3extLNodeP": {"children": [
                    {"l3extRsNodeL3OutAtt": {}},
                    {"l3extLIfP": {}},
                ]}},
            ],
        },
    })
