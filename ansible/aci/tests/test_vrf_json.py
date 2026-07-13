from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render):
    vrf = {"name": "vrf1", "state": "absent"}
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
                "pcEnfPref": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_state_present_minimal_renders_vzany_only_with_defaults(render):
    vrf = {"name": "vrf1", "state": "present"}
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
                "pcEnfPref": "enforced",
            },
            "children": [
                {
                    "vzAny": {
                        "attributes": {
                            "prefGrMemb": "disabled",
                        },
                        "children": [],
                    },
                },
            ],
        },
    })


def test_state_undefined_at_root_does_not_crash(render):
    # Regression test: this used to raise "'dict object' has no attribute
    # 'state'" once the task's `when:` was switched to has_nested_state,
    # which lets this task run without vrf.state ever being set.
    vrf = {"name": "vrf1"}
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
            },
            "children": [
                {"vzAny": {"attributes": {"prefGrMemb": "disabled"}}},
            ],
        },
    })


def test_state_undefined_at_root_still_renders_nested_tag_state(render):
    vrf = {
        "name": "vrf1",
        "tags": [{"name": "tag1", "value": "value1", "state": "absent"}],
    }
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
            "children": [
                {
                    "tagAnnotation": {
                        "attributes": {
                            "key": "tag1",
                            "status": "deleted",
                        },
                    },
                },
                {"vzAny": {"attributes": {"prefGrMemb": "disabled"}}},
            ],
        },
    })


def test_description_and_enforcement_overrides(render):
    vrf = {
        "name": "vrf1",
        "description": "my vrf",
        "enforcement": "unenforced",
    }
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
            "attributes": {
                "descr": "my vrf",
                "pcEnfPref": "unenforced",
            },
        },
    })


def test_preferred_group_override(render):
    vrf = {"name": "vrf1", "preferred_group": "enabled"}
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
            "children": [
                {"vzAny": {"attributes": {"prefGrMemb": "enabled"}}},
            ],
        },
    })


def test_tags_render_with_state(render):
    vrf = {
        "name": "vrf1",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
            "children": [
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
                {"vzAny": {}},
            ],
        },
    })


def test_contracts_consumer_and_provider_with_state(render):
    vrf = {
        "name": "vrf1",
        "contracts": [
            {"name": "c1", "type": "consumer"},
            {"name": "c2", "type": "provider", "state": "absent"},
        ],
    }
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
            "children": [
                {
                    "vzAny": {
                        "children": [
                            {
                                "vzRsAnyToCons": {
                                    "attributes": {
                                        "tnVzBrCPName": "c1",
                                        "status": "created,modified",
                                    },
                                },
                            },
                            {
                                "vzRsAnyToProv": {
                                    "attributes": {
                                        "tnVzBrCPName": "c2",
                                        "status": "deleted",
                                    },
                                },
                            },
                        ],
                    },
                },
            ],
        },
    })


def test_ipv4_route_targets_only(render):
    vrf = {
        "name": "vrf1",
        "ipv4_route_targets": [
            {"name": "65000:1", "type": "export"},
            {"name": "65000:2", "type": "import", "state": "absent"},
        ],
    }
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
            "children": [
                {"vzAny": {}},
                {
                    "bgpRtTargetP": {
                        "attributes": {
                            "af": "ipv4-ucast",
                        },
                        "children": [
                            {
                                "bgpRtTarget": {
                                    "attributes": {
                                        "rt": "65000:1",
                                        "type": "export",
                                        "status": "created,modified",
                                    },
                                },
                            },
                            {
                                "bgpRtTarget": {
                                    "attributes": {
                                        "rt": "65000:2",
                                        "type": "import",
                                        "status": "deleted",
                                    },
                                },
                            },
                        ],
                    },
                },
            ],
        },
    })


def test_ipv6_route_targets_only(render):
    # Regression test: with the pre-fix template this combination raised a
    # JSON parse error (missing comma before the ipv6 block when ipv4 isn't
    # also set).
    vrf = {
        "name": "vrf1",
        "ipv6_route_targets": [
            {"name": "65000:3", "type": "export"},
        ],
    }
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
            "children": [
                {"vzAny": {}},
                {
                    "bgpRtTargetP": {
                        "attributes": {
                            "af": "ipv6-ucast",
                        },
                        "children": [
                            {
                                "bgpRtTarget": {
                                    "attributes": {
                                        "rt": "65000:3",
                                        "type": "export",
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


def test_empty_route_target_lists_are_omitted(render):
    vrf = {"name": "vrf1", "ipv4_route_targets": [], "ipv6_route_targets": []}
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
            "children": [
                {"vzAny": {}},
            ],
        },
    })


def test_tags_contracts_and_both_route_targets_together(render):
    # Regression test: with the pre-fix template this combination raised a
    # JSON parse error (trailing comma before the closing `]` whenever
    # ipv6_route_targets was set).
    vrf = {
        "name": "vrf1",
        "tags": [{"name": "tag1", "value": "value1"}],
        "contracts": [{"name": "c1", "type": "consumer"}],
        "ipv4_route_targets": [{"name": "65000:1", "type": "export"}],
        "ipv6_route_targets": [{"name": "65000:2", "type": "export"}],
    }
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1"}}},
                {
                    "vzAny": {
                        "children": [
                            {"vzRsAnyToCons": {"attributes": {"tnVzBrCPName": "c1"}}},
                        ],
                    },
                },
                {"bgpRtTargetP": {"attributes": {"af": "ipv4-ucast"}}},
                {"bgpRtTargetP": {"attributes": {"af": "ipv6-ucast"}}},
            ],
        },
    })


def test_pim_omitted_when_not_defined(render):
    vrf = {"name": "vrf1"}
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
            "children": [
                {"vzAny": {}},
            ],
        },
    })


def test_pim_renders_with_defaults_when_empty(render):
    vrf = {"name": "vrf1", "PIM": {}}
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
            "children": [
                {"vzAny": {}},
                {
                    "pimCtxP": {
                        "attributes": {
                            "mtu": "1500",
                            "ctrl": "",
                            "status": "created,modified",
                        },
                    },
                },
            ],
        },
    })


def test_pim_mtu_and_ctrl_flags_overrides(render):
    vrf = {
        "name": "vrf1",
        "PIM": {
            "mtu": 9000,
            "fast-convergenace": True,
            "strict-RFC-compilant": True,
        },
    }
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
            "children": [
                {"vzAny": {}},
                {
                    "pimCtxP": {
                        "attributes": {
                            "mtu": "9000",
                            "ctrl": "fast-conv,strict-rfc-compliant",
                            "status": "created,modified",
                        },
                    },
                },
            ],
        },
    })


def test_pim_single_ctrl_flag(render):
    vrf = {"name": "vrf1", "PIM": {"fast-convergenace": True}}
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
            "children": [
                {"vzAny": {}},
                {"pimCtxP": {"attributes": {"ctrl": "fast-conv"}}},
            ],
        },
    })


def test_pim_state_absent(render):
    vrf = {"name": "vrf1", "PIM": {"state": "absent"}}
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
            "children": [
                {"vzAny": {}},
                {"pimCtxP": {"attributes": {"status": "deleted"}}},
            ],
        },
    })


def test_pim_toggle_present_to_absent(render):
    # Confirms flipping PIM.state from present to absent converts pimCtxP's
    # own status to deleted (the APIC cascades that delete down to its
    # static_rp/route_map descendants regardless of their own status).
    tenant = {"name": "tenant1"}
    pim_config = {
        "mtu": 1600,
        "static_rp": [{"ip": "5.5.5.5", "route_map": "rm1"}],
    }

    vrf_present = {"name": "vrf1", "PIM": {**pim_config, "state": "present"}}
    body_present = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf_present, tenant=tenant)

    assert_matches(body_present, {
        "fvCtx": {
            "children": [
                {"vzAny": {}},
                {
                    "pimCtxP": {
                        "attributes": {"status": "created,modified"},
                        "children": [
                            {
                                "pimStaticRPPol": {
                                    "children": [
                                        {
                                            "pimStaticRPEntryPol": {
                                                "attributes": {"rpIp": "5.5.5.5", "status": "created,modified"},
                                                "children": [
                                                    {
                                                        "pimRPGrpRangePol": {
                                                            "children": [
                                                                {
                                                                    "rtdmcRsFilterToRtMapPol": {
                                                                        "attributes": {
                                                                            "status": "created,modified",
                                                                        },
                                                                    },
                                                                },
                                                            ],
                                                        },
                                                    },
                                                ],
                                            },
                                        },
                                    ],
                                },
                            },
                        ],
                    },
                },
            ],
        },
    })

    vrf_absent = {"name": "vrf1", "PIM": {**pim_config, "state": "absent"}}
    body_absent = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf_absent, tenant=tenant)

    assert_matches(body_absent, {
        "fvCtx": {
            "children": [
                {"vzAny": {}},
                {
                    "pimCtxP": {
                        "attributes": {"status": "deleted"},
                        "children": [
                            {
                                "pimStaticRPPol": {
                                    "children": [
                                        {
                                            "pimStaticRPEntryPol": {
                                                "attributes": {"rpIp": "5.5.5.5", "status": "created,modified"},
                                                "children": [
                                                    {
                                                        "pimRPGrpRangePol": {
                                                            "children": [
                                                                {
                                                                    "rtdmcRsFilterToRtMapPol": {
                                                                        "attributes": {
                                                                            "status": "created,modified",
                                                                        },
                                                                    },
                                                                },
                                                            ],
                                                        },
                                                    },
                                                ],
                                            },
                                        },
                                    ],
                                },
                            },
                        ],
                    },
                },
            ],
        },
    })


def test_pim_static_rp_omitted_when_not_defined(render):
    vrf = {"name": "vrf1", "PIM": {}}
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
            "children": [
                {"vzAny": {}},
                {"pimCtxP": {"children": ABSENT}},
            ],
        },
    })


def test_pim_static_rp_with_route_map_as_string(render):
    # A bare string route_map is assumed to live in the same tenant as the vrf.
    vrf = {
        "name": "vrf1",
        "PIM": {
            "static_rp": [
                {"ip": "5.5.5.5", "route_map": "rm1"},
            ],
        },
    }
    tenant = {"name": "tenant1"}
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf, tenant=tenant)

    assert_matches(body, {
        "fvCtx": {
            "children": [
                {"vzAny": {}},
                {
                    "pimCtxP": {
                        "children": [
                            {
                                "pimStaticRPPol": {
                                    "children": [
                                        {
                                            "pimStaticRPEntryPol": {
                                                "attributes": {
                                                    "rpIp": "5.5.5.5",
                                                    "status": "created,modified",
                                                },
                                                "children": [
                                                    {
                                                        "pimRPGrpRangePol": {
                                                            "children": [
                                                                {
                                                                    "rtdmcRsFilterToRtMapPol": {
                                                                        "attributes": {
                                                                            "tDn": "uni/tn-tenant1/rtmap-rm1",
                                                                            "status": "created,modified",
                                                                        },
                                                                    },
                                                                },
                                                            ],
                                                        },
                                                    },
                                                ],
                                            },
                                        },
                                    ],
                                },
                            },
                        ],
                    },
                },
            ],
        },
    })


def test_pim_static_rp_with_route_map_as_dict_in_other_tenant(render):
    # A {name, tenant} mapping lets the route_map live in a different tenant.
    vrf = {
        "name": "vrf1",
        "PIM": {
            "static_rp": [
                {"ip": "5.5.5.5", "route_map": {"name": "rm1", "tenant": "tenant2"}},
            ],
        },
    }
    tenant = {"name": "tenant1"}
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf, tenant=tenant)

    assert_matches(body, {
        "fvCtx": {
            "children": [
                {"vzAny": {}},
                {
                    "pimCtxP": {
                        "children": [
                            {
                                "pimStaticRPPol": {
                                    "children": [
                                        {
                                            "pimStaticRPEntryPol": {
                                                "children": [
                                                    {
                                                        "pimRPGrpRangePol": {
                                                            "children": [
                                                                {
                                                                    "rtdmcRsFilterToRtMapPol": {
                                                                        "attributes": {
                                                                            "tDn": "uni/tn-tenant2/rtmap-rm1",
                                                                        },
                                                                    },
                                                                },
                                                            ],
                                                        },
                                                    },
                                                ],
                                            },
                                        },
                                    ],
                                },
                            },
                        ],
                    },
                },
            ],
        },
    })


def test_pim_static_rp_without_route_map(render):
    vrf = {"name": "vrf1", "PIM": {"static_rp": [{"ip": "5.5.5.5"}]}}
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
            "children": [
                {"vzAny": {}},
                {
                    "pimCtxP": {
                        "children": [
                            {
                                "pimStaticRPPol": {
                                    "children": [
                                        {
                                            "pimStaticRPEntryPol": {
                                                "attributes": {"rpIp": "5.5.5.5"},
                                                "children": ABSENT,
                                            },
                                        },
                                    ],
                                },
                            },
                        ],
                    },
                },
            ],
        },
    })


def test_pim_static_rp_state_absent_deletes_route_map_relation_too(render):
    vrf = {
        "name": "vrf1",
        "PIM": {
            "static_rp": [
                {"ip": "5.5.5.5", "route_map": "rm1", "state": "absent"},
            ],
        },
    }
    tenant = {"name": "tenant1"}
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf, tenant=tenant)

    assert_matches(body, {
        "fvCtx": {
            "children": [
                {"vzAny": {}},
                {
                    "pimCtxP": {
                        "children": [
                            {
                                "pimStaticRPPol": {
                                    "children": [
                                        {
                                            "pimStaticRPEntryPol": {
                                                "attributes": {"rpIp": "5.5.5.5", "status": "deleted"},
                                                "children": [
                                                    {
                                                        "pimRPGrpRangePol": {
                                                            "children": [
                                                                {
                                                                    "rtdmcRsFilterToRtMapPol": {
                                                                        "attributes": {
                                                                            "tDn": "uni/tn-tenant1/rtmap-rm1",
                                                                            "status": "deleted",
                                                                        },
                                                                    },
                                                                },
                                                            ],
                                                        },
                                                    },
                                                ],
                                            },
                                        },
                                    ],
                                },
                            },
                        ],
                    },
                },
            ],
        },
    })


def test_pim_static_rp_multiple_entries_share_same_route_map(render):
    vrf = {
        "name": "vrf1",
        "PIM": {
            "static_rp": [
                {"ip": "5.5.5.5", "route_map": "rm1"},
                {"ip": "5.5.5.6", "route_map": "rm1"},
            ],
        },
    }
    tenant = {"name": "tenant1"}
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf, tenant=tenant)

    assert_matches(body, {
        "fvCtx": {
            "children": [
                {"vzAny": {}},
                {
                    "pimCtxP": {
                        "children": [
                            {
                                "pimStaticRPPol": {
                                    "children": [
                                        {
                                            "pimStaticRPEntryPol": {
                                                "attributes": {"rpIp": "5.5.5.5"},
                                                "children": [
                                                    {
                                                        "pimRPGrpRangePol": {
                                                            "children": [
                                                                {
                                                                    "rtdmcRsFilterToRtMapPol": {
                                                                        "attributes": {
                                                                            "tDn": "uni/tn-tenant1/rtmap-rm1",
                                                                        },
                                                                    },
                                                                },
                                                            ],
                                                        },
                                                    },
                                                ],
                                            },
                                        },
                                        {
                                            "pimStaticRPEntryPol": {
                                                "attributes": {"rpIp": "5.5.5.6"},
                                                "children": [
                                                    {
                                                        "pimRPGrpRangePol": {
                                                            "children": [
                                                                {
                                                                    "rtdmcRsFilterToRtMapPol": {
                                                                        "attributes": {
                                                                            "tDn": "uni/tn-tenant1/rtmap-rm1",
                                                                        },
                                                                    },
                                                                },
                                                            ],
                                                        },
                                                    },
                                                ],
                                            },
                                        },
                                    ],
                                },
                            },
                        ],
                    },
                },
            ],
        },
    })


def test_route_target_state_absent_does_not_affect_other_children(render):
    vrf = {
        "name": "vrf1",
        "tags": [{"name": "tag1", "value": "value1"}],
        "contracts": [{"name": "c1", "type": "consumer"}],
        "ipv4_route_targets": [
            {"name": "65000:1", "type": "export"},
            {"name": "65000:2", "type": "import", "state": "absent"},
        ],
    }
    body = render("vrf.json.j2", vrf_name="vrf1", vrf=vrf)

    assert_matches(body, {
        "fvCtx": {
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
                    "vzAny": {
                        "children": [
                            {
                                "vzRsAnyToCons": {
                                    "attributes": {
                                        "tnVzBrCPName": "c1",
                                        "status": "created,modified",
                                    },
                                },
                            },
                        ],
                    },
                },
                {
                    "bgpRtTargetP": {
                        "children": [
                            {
                                "bgpRtTarget": {
                                    "attributes": {
                                        "rt": "65000:1",
                                        "status": "created,modified",
                                    },
                                },
                            },
                            {
                                "bgpRtTarget": {
                                    "attributes": {
                                        "rt": "65000:2",
                                        "status": "deleted",
                                    },
                                },
                            },
                        ],
                    },
                },
            ],
        },
    })
