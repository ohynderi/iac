from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render_fabric):
    aaep = {"name": "aaep1", "state": "absent"}
    body = render_fabric("aaep.json.j2", aaep_name="aaep1", aaep=aaep)

    assert_matches(body, {
        "infraAttEntityP": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_state_present_minimal_renders_empty_children(render_fabric):
    aaep = {"name": "aaep1", "state": "present"}
    body = render_fabric("aaep.json.j2", aaep_name="aaep1", aaep=aaep)

    assert_matches(body, {
        "infraAttEntityP": {
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
    # which lets this task run without aaep.state ever being set.
    aaep = {"name": "aaep1"}
    body = render_fabric("aaep.json.j2", aaep_name="aaep1", aaep=aaep)

    assert_matches(body, {
        "infraAttEntityP": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_still_renders_nested_domain_state(render_fabric):
    aaep = {"name": "aaep1", "domains": [{"name": "dom1", "type": "physical", "state": "absent"}]}
    body = render_fabric("aaep.json.j2", aaep_name="aaep1", aaep=aaep)

    assert_matches(body, {
        "infraAttEntityP": {
            "children": [
                {
                    "infraRsDomP": {
                        "attributes": {
                            "tDn": "uni/phys-dom1",
                            "status": "deleted",
                        },
                    },
                },
            ],
        },
    })


def test_description_override(render_fabric):
    aaep = {"name": "aaep1", "description": "my aaep"}
    body = render_fabric("aaep.json.j2", aaep_name="aaep1", aaep=aaep)

    assert_matches(body, {
        "infraAttEntityP": {
            "attributes": {
                "descr": "my aaep",
            },
        },
    })


def test_tags_render_with_state(render_fabric):
    aaep = {
        "name": "aaep1",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render_fabric("aaep.json.j2", aaep_name="aaep1", aaep=aaep)

    assert_matches(body, {
        "infraAttEntityP": {
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
            ],
        },
    })


def test_domain_binding_physical_type(render_fabric):
    aaep = {"name": "aaep1", "domains": [{"name": "dom1", "type": "physical"}]}
    body = render_fabric("aaep.json.j2", aaep_name="aaep1", aaep=aaep)

    assert_matches(body, {
        "infraAttEntityP": {
            "children": [
                {"infraRsDomP": {"attributes": {"tDn": "uni/phys-dom1", "status": "created,modified"}}},
            ],
        },
    })


def test_domain_binding_l3_external_type(render_fabric):
    aaep = {"name": "aaep1", "domains": [{"name": "dom1", "type": "l3_external"}]}
    body = render_fabric("aaep.json.j2", aaep_name="aaep1", aaep=aaep)

    assert_matches(body, {
        "infraAttEntityP": {
            "children": [
                {"infraRsDomP": {"attributes": {"tDn": "uni/l3dom-dom1", "status": "created,modified"}}},
            ],
        },
    })


def test_domains_render_with_state(render_fabric):
    # Also a regression test for the double-comma bug: rendering must
    # produce valid JSON with exactly 2 domain children when there's more
    # than one.
    aaep = {
        "name": "aaep1",
        "domains": [
            {"name": "dom1", "type": "physical"},
            {"name": "dom2", "type": "l3_external", "state": "absent"},
        ],
    }
    body = render_fabric("aaep.json.j2", aaep_name="aaep1", aaep=aaep)

    assert_matches(body, {
        "infraAttEntityP": {
            "children": [
                {"infraRsDomP": {"attributes": {"tDn": "uni/phys-dom1", "status": "created,modified"}}},
                {"infraRsDomP": {"attributes": {"tDn": "uni/l3dom-dom2", "status": "deleted"}}},
            ],
        },
    })


def test_tags_and_domains_together(render_fabric):
    # Regression test: with the pre-fix template this combination would
    # have crashed (undefined `pool` variable) before the fix, and must
    # produce valid JSON with a comma between the tags group and the
    # domains group.
    aaep = {
        "name": "aaep1",
        "tags": [{"name": "tag1", "value": "value1"}],
        "domains": [{"name": "dom1", "type": "physical"}],
    }
    body = render_fabric("aaep.json.j2", aaep_name="aaep1", aaep=aaep)

    assert_matches(body, {
        "infraAttEntityP": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1"}}},
                {"infraRsDomP": {"attributes": {"tDn": "uni/phys-dom1"}}},
            ],
        },
    })


def test_domain_state_absent_does_not_affect_other_children(render_fabric):
    aaep = {
        "name": "aaep1",
        "tags": [{"name": "tag1", "value": "value1"}],
        "domains": [
            {"name": "dom1", "type": "physical"},
            {"name": "dom2", "type": "physical", "state": "absent"},
        ],
    }
    body = render_fabric("aaep.json.j2", aaep_name="aaep1", aaep=aaep)

    assert_matches(body, {
        "infraAttEntityP": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1", "status": "created,modified"}}},
                {"infraRsDomP": {"attributes": {"tDn": "uni/phys-dom1", "status": "created,modified"}}},
                {"infraRsDomP": {"attributes": {"tDn": "uni/phys-dom2", "status": "deleted"}}},
            ],
        },
    })


def test_epgs_omitted_when_not_defined(render_fabric):
    aaep = {"name": "aaep1"}
    body = render_fabric("aaep.json.j2", aaep_name="aaep1", aaep=aaep)

    assert_matches(body, {
        "infraAttEntityP": {
            "children": [],
        },
    })


def test_epg_binding_renders_with_defaults(render_fabric):
    aaep = {
        "name": "aaep1",
        "epgs": [
            {"tenant": "tenant1", "application_profile": "ap1", "epg": "epg1", "vlan": 30},
        ],
    }
    body = render_fabric("aaep.json.j2", aaep_name="aaep1", aaep=aaep)

    assert_matches(body, {
        "infraAttEntityP": {
            "children": [
                {
                    "infraProvAcc": {
                        "attributes": {},
                        "children": [
                            {
                                "infraRsFuncToEpg": {
                                    "attributes": {
                                        "tDn": "uni/tn-tenant1/ap-ap1/epg-epg1",
                                        "encap": "vlan-30",
                                        "mode": "regular",
                                        "instrImedcy": "lazy",
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


def test_epg_binding_mode_and_deployment_overrides(render_fabric):
    aaep = {
        "name": "aaep1",
        "epgs": [
            {
                "tenant": "tenant1", "application_profile": "ap1", "epg": "epg1",
                "vlan": 40, "mode": "untagged", "deployment": "immediate",
            },
        ],
    }
    body = render_fabric("aaep.json.j2", aaep_name="aaep1", aaep=aaep)

    assert_matches(body, {
        "infraAttEntityP": {
            "children": [
                {
                    "infraProvAcc": {
                        "children": [
                            {
                                "infraRsFuncToEpg": {
                                    "attributes": {
                                        "encap": "vlan-40",
                                        "mode": "untagged",
                                        "instrImedcy": "immediate",
                                    },
                                },
                            },
                        ],
                    },
                },
            ],
        },
    })


def test_epg_binding_mode_native(render_fabric):
    aaep = {
        "name": "aaep1",
        "epgs": [
            {"tenant": "tenant1", "application_profile": "ap1", "epg": "epg1", "vlan": 30, "mode": "native"},
        ],
    }
    body = render_fabric("aaep.json.j2", aaep_name="aaep1", aaep=aaep)

    assert_matches(body, {
        "infraAttEntityP": {
            "children": [
                {
                    "infraProvAcc": {
                        "children": [
                            {"infraRsFuncToEpg": {"attributes": {"mode": "native"}}},
                        ],
                    },
                },
            ],
        },
    })


def test_epg_bindings_render_with_state(render_fabric):
    # Also a regression test for the double-comma bug: rendering must
    # produce valid JSON with exactly 2 infraRsFuncToEpg children when
    # there's more than one epg binding.
    aaep = {
        "name": "aaep1",
        "epgs": [
            {"tenant": "t1", "application_profile": "ap1", "epg": "epg1", "vlan": 30, "mode": "regular"},
            {"tenant": "t1", "application_profile": "ap1", "epg": "epg2", "vlan": 40, "mode": "regular", "state": "absent"},
        ],
    }
    body = render_fabric("aaep.json.j2", aaep_name="aaep1", aaep=aaep)

    assert_matches(body, {
        "infraAttEntityP": {
            "children": [
                {
                    "infraProvAcc": {
                        "children": [
                            {"infraRsFuncToEpg": {"attributes": {"tDn": "uni/tn-t1/ap-ap1/epg-epg1", "status": "created,modified"}}},
                            {"infraRsFuncToEpg": {"attributes": {"tDn": "uni/tn-t1/ap-ap1/epg-epg2", "status": "deleted"}}},
                        ],
                    },
                },
            ],
        },
    })


def test_tags_domains_and_epgs_together(render_fabric):
    # Regression test for the comma boundary between the tags/domains
    # groups and the infraProvAcc block.
    aaep = {
        "name": "aaep1",
        "tags": [{"name": "tag1", "value": "value1"}],
        "domains": [{"name": "dom1", "type": "physical"}],
        "epgs": [
            {"tenant": "t1", "application_profile": "ap1", "epg": "epg1", "vlan": 30, "mode": "regular"},
        ],
    }
    body = render_fabric("aaep.json.j2", aaep_name="aaep1", aaep=aaep)

    assert_matches(body, {
        "infraAttEntityP": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1"}}},
                {"infraRsDomP": {"attributes": {"tDn": "uni/phys-dom1"}}},
                {"infraProvAcc": {"children": [{"infraRsFuncToEpg": {"attributes": {"tDn": "uni/tn-t1/ap-ap1/epg-epg1"}}}]}},
            ],
        },
    })
