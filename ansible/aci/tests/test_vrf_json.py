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
