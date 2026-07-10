from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render):
    epg = {"name": "epg1", "bd": "bd1", "state": "absent"}
    body = render("epg.json.j2", epg_name="epg1", epg=epg)

    assert_matches(body, {
        "fvAEPg": {
            "attributes": {
                "status": "deleted",
                "descr": "",
                "prefGrMemb": "exclude",
            },
            "children": ABSENT,
        },
    })


def test_state_present_minimal_renders_bd_child_only(render):
    epg = {"name": "epg1", "bd": "bd1", "state": "present"}
    body = render("epg.json.j2", epg_name="epg1", epg=epg)

    assert_matches(body, {
        "fvAEPg": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
                "prefGrMemb": "exclude",
            },
            "children": [
                {
                    "fvRsBd": {
                        "attributes": {
                            "tnFvBDName": "bd1",
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
    # which lets this task run without epg.state ever being set.
    epg = {"name": "epg1", "bd": "bd1"}
    body = render("epg.json.j2", epg_name="epg1", epg=epg)

    assert_matches(body, {
        "fvAEPg": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
            },
            "children": [
                {
                    "fvRsBd": {
                        "attributes": {
                            "tnFvBDName": "bd1",
                        },
                    },
                },
            ],
        },
    })


def test_description_and_preferred_group_member_overrides(render):
    epg = {
        "name": "epg1",
        "bd": "bd1",
        "description": "my epg",
        "preferred_group_member": "include",
    }
    body = render("epg.json.j2", epg_name="epg1", epg=epg)

    assert_matches(body, {
        "fvAEPg": {
            "attributes": {
                "descr": "my epg",
                "prefGrMemb": "include",
            },
        },
    })


def test_tags_render_with_state(render):
    epg = {
        "name": "epg1",
        "bd": "bd1",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render("epg.json.j2", epg_name="epg1", epg=epg)

    assert_matches(body, {
        "fvAEPg": {
            "children": [
                {"fvRsBd": {"attributes": {"tnFvBDName": "bd1"}}},
                {
                    "tagAnnotation": {
                        "attributes": {
                            "key": "tag1",
                            "status": "created,modified",
                        },
                    },
                },
                {
                    "tagAnnotation": {
                        "attributes": {
                            "key": "tag2",
                            "status": "deleted",
                        },
                    },
                },
            ],
        },
    })


def test_physical_domain_renders_without_immediacy(render):
    epg = {
        "name": "epg1",
        "bd": "bd1",
        "domains": [
            {"name": "phys1", "type": "physical"},
        ],
    }
    body = render("epg.json.j2", epg_name="epg1", epg=epg)

    assert_matches(body, {
        "fvAEPg": {
            "children": [
                {"fvRsBd": {"attributes": {"tnFvBDName": "bd1"}}},
                {
                    "fvRsDomAtt": {
                        "attributes": {
                            "tDn": "uni/phys-phys1",
                            "status": "created,modified",
                            "instrImedcy": ABSENT,
                            "resImedcy": ABSENT,
                        },
                    },
                },
            ],
        },
    })


def test_virtual_domain_uses_default_immediacy(render):
    epg = {
        "name": "epg1",
        "bd": "bd1",
        "domains": [
            {"name": "dvs1", "type": "virtual"},
        ],
    }
    body = render("epg.json.j2", epg_name="epg1", epg=epg)

    assert_matches(body, {
        "fvAEPg": {
            "children": [
                {"fvRsBd": {"attributes": {"tnFvBDName": "bd1"}}},
                {
                    "fvRsDomAtt": {
                        "attributes": {
                            "tDn": "uni/vmmp-VMware/dom-dvs1",
                            "resImedcy": "pre-provision",
                            "instrImedcy": "immediate",
                            "status": "created,modified",
                        },
                    },
                },
            ],
        },
    })


def test_virtual_domain_immediacy_overrides(render):
    epg = {
        "name": "epg1",
        "bd": "bd1",
        "domains": [
            {"name": "dvs1", "type": "virtual", "resolution": "immediate", "deployment": "lazy"},
        ],
    }
    body = render("epg.json.j2", epg_name="epg1", epg=epg)

    assert_matches(body, {
        "fvAEPg": {
            "children": [
                {"fvRsBd": {"attributes": {"tnFvBDName": "bd1"}}},
                {
                    "fvRsDomAtt": {
                        "attributes": {
                            "resImedcy": "immediate",
                            "instrImedcy": "lazy",
                        },
                    },
                },
            ],
        },
    })


def test_multiple_virtual_domains_have_independent_immediacy(render):
    # Regression test: resolution/deployment are per-domain, not per-epg --
    # setting them on one domain must not leak into a sibling domain that
    # relies on the role-var defaults.
    epg = {
        "name": "epg1",
        "bd": "bd1",
        "domains": [
            {"name": "dvs1", "type": "virtual", "resolution": "immediate", "deployment": "lazy"},
            {"name": "dvs2", "type": "virtual"},
        ],
    }
    body = render("epg.json.j2", epg_name="epg1", epg=epg)

    assert_matches(body, {
        "fvAEPg": {
            "children": [
                {"fvRsBd": {"attributes": {"tnFvBDName": "bd1"}}},
                {
                    "fvRsDomAtt": {
                        "attributes": {
                            "tDn": "uni/vmmp-VMware/dom-dvs1",
                            "resImedcy": "immediate",
                            "instrImedcy": "lazy",
                        },
                    },
                },
                {
                    "fvRsDomAtt": {
                        "attributes": {
                            "tDn": "uni/vmmp-VMware/dom-dvs2",
                            "resImedcy": "pre-provision",
                            "instrImedcy": "immediate",
                        },
                    },
                },
            ],
        },
    })


def test_interface_tdn_variants(render):
    epg = {
        "name": "epg1",
        "bd": "bd1",
        "interfaces": [
            {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "mode": "regular", "vlan": 100},
            {"pod": 1, "leaf_id": 101, "peer_leaf_id": 102, "ipg": "ipg1", "mode": "regular", "vlan": 101},
        ],
    }
    body = render("epg.json.j2", epg_name="epg1", epg=epg)

    assert_matches(body, {
        "fvAEPg": {
            "children": [
                {"fvRsBd": {"attributes": {"tnFvBDName": "bd1"}}},
                {
                    "fvRsPathAtt": {
                        "attributes": {
                            "tDn": "topology/pod-1/paths-101/pathep-[eth1/1]",
                            "encap": "vlan-100",
                            "mode": "regular",
                            "instrImedcy": "immediate",
                        },
                    },
                },
                {
                    "fvRsPathAtt": {
                        "attributes": {
                            "tDn": "topology/pod-1/protpaths-101-102/pathep-[ipg1]",
                            "encap": "vlan-101",
                            "mode": "regular",
                            "instrImedcy": "immediate",
                        },
                    },
                },
            ],
        },
    })


def test_interface_ipg_without_peer_leaf_id_renders_single_homed_tdn(render):
    epg = {
        "name": "epg1",
        "bd": "bd1",
        "interfaces": [
            {"pod": 1, "leaf_id": 101, "ipg": "ipg1", "mode": "regular", "vlan": 100},
        ],
    }
    body = render("epg.json.j2", epg_name="epg1", epg=epg)

    assert_matches(body, {
        "fvAEPg": {
            "children": [
                {"fvRsBd": {"attributes": {"tnFvBDName": "bd1"}}},
                {
                    "fvRsPathAtt": {
                        "attributes": {
                            "tDn": "topology/pod-1/paths-101/pathep-[ipg1]",
                        },
                    },
                },
            ],
        },
    })


def test_interface_without_matching_tdn_branch_omits_tdn(render):
    # Regression/documentation test: if an interface specifies neither
    # `port` nor `ipg` (or is missing `leaf_id`), none of the template's
    # tDn branches match, so the rendered payload silently has no tDn key
    # at all instead of erroring.
    epg = {
        "name": "epg1",
        "bd": "bd1",
        "interfaces": [
            {"pod": 1, "leaf_id": 101, "mode": "regular", "vlan": 100},
        ],
    }
    body = render("epg.json.j2", epg_name="epg1", epg=epg)

    assert_matches(body, {
        "fvAEPg": {
            "children": [
                {"fvRsBd": {"attributes": {"tnFvBDName": "bd1"}}},
                {
                    "fvRsPathAtt": {
                        "attributes": {
                            "tDn": ABSENT,
                        },
                    },
                },
            ],
        },
    })


def test_interface_deployment_override(render):
    epg = {
        "name": "epg1",
        "bd": "bd1",
        "interfaces": [
            {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "mode": "regular", "vlan": 100, "deployment": "lazy"},
        ],
    }
    body = render("epg.json.j2", epg_name="epg1", epg=epg)

    assert_matches(body, {
        "fvAEPg": {
            "children": [
                {"fvRsBd": {"attributes": {"tnFvBDName": "bd1"}}},
                {
                    "fvRsPathAtt": {
                        "attributes": {
                            "instrImedcy": "lazy",
                        },
                    },
                },
            ],
        },
    })


def test_domain_state_absent_does_not_affect_other_children(render):
    epg = {
        "name": "epg1",
        "bd": "bd1",
        "domains": [
            {"name": "phys1", "type": "physical"},
            {"name": "phys2", "type": "physical", "state": "absent"},
        ],
        "interfaces": [
            {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "mode": "regular", "vlan": 100},
        ],
        "contracts": [
            {"name": "web-to-app", "type": "consumer"},
        ],
    }
    body = render("epg.json.j2", epg_name="epg1", epg=epg)

    assert_matches(body, {
        "fvAEPg": {
            "children": [
                {"fvRsBd": {"attributes": {"tnFvBDName": "bd1"}}},
                {
                    "fvRsDomAtt": {
                        "attributes": {
                            "tDn": "uni/phys-phys1",
                            "status": "created,modified",
                        },
                    },
                },
                {
                    "fvRsDomAtt": {
                        "attributes": {
                            "tDn": "uni/phys-phys2",
                            "status": "deleted",
                        },
                    },
                },
                {
                    "fvRsPathAtt": {
                        "attributes": {
                            "status": "created,modified",
                        },
                    },
                },
                {
                    "fvRsCons": {
                        "attributes": {
                            "status": "created,modified",
                        },
                    },
                },
            ],
        },
    })


def test_interface_state_absent_does_not_affect_other_children(render):
    epg = {
        "name": "epg1",
        "bd": "bd1",
        "domains": [
            {"name": "phys1", "type": "physical"},
        ],
        "interfaces": [
            {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "mode": "regular", "vlan": 100},
            {"pod": 1, "leaf_id": 102, "port": "Eth1/2", "mode": "regular", "vlan": 101, "state": "absent"},
        ],
        "contracts": [
            {"name": "web-to-app", "type": "consumer"},
        ],
    }
    body = render("epg.json.j2", epg_name="epg1", epg=epg)

    assert_matches(body, {
        "fvAEPg": {
            "children": [
                {"fvRsBd": {"attributes": {"tnFvBDName": "bd1"}}},
                {
                    "fvRsDomAtt": {
                        "attributes": {
                            "status": "created,modified",
                        },
                    },
                },
                {
                    "fvRsPathAtt": {
                        "attributes": {
                            "tDn": "topology/pod-1/paths-101/pathep-[eth1/1]",
                            "status": "created,modified",
                        },
                    },
                },
                {
                    "fvRsPathAtt": {
                        "attributes": {
                            "tDn": "topology/pod-1/paths-102/pathep-[eth1/2]",
                            "status": "deleted",
                        },
                    },
                },
                {
                    "fvRsCons": {
                        "attributes": {
                            "status": "created,modified",
                        },
                    },
                },
            ],
        },
    })


def test_contract_state_absent_does_not_affect_other_children(render):
    epg = {
        "name": "epg1",
        "bd": "bd1",
        "domains": [
            {"name": "phys1", "type": "physical"},
        ],
        "interfaces": [
            {"pod": 1, "leaf_id": 101, "port": "Eth1/1", "mode": "regular", "vlan": 100},
        ],
        "contracts": [
            {"name": "web-to-app", "type": "consumer"},
            {"name": "app-to-db", "type": "provider", "state": "absent"},
        ],
    }
    body = render("epg.json.j2", epg_name="epg1", epg=epg)

    assert_matches(body, {
        "fvAEPg": {
            "children": [
                {"fvRsBd": {"attributes": {"tnFvBDName": "bd1"}}},
                {
                    "fvRsDomAtt": {
                        "attributes": {
                            "status": "created,modified",
                        },
                    },
                },
                {
                    "fvRsPathAtt": {
                        "attributes": {
                            "status": "created,modified",
                        },
                    },
                },
                {
                    "fvRsCons": {
                        "attributes": {
                            "tnVzBrCPName": "web-to-app",
                            "status": "created,modified",
                        },
                    },
                },
                {
                    "fvRsProv": {
                        "attributes": {
                            "tnVzBrCPName": "app-to-db",
                            "status": "deleted",
                        },
                    },
                },
            ],
        },
    })


def test_contracts_consumer_and_provider(render):
    epg = {
        "name": "epg1",
        "bd": "bd1",
        "contracts": [
            {"name": "web-to-app", "type": "consumer"},
            {"name": "app-to-db", "type": "provider"},
        ],
    }
    body = render("epg.json.j2", epg_name="epg1", epg=epg)

    assert_matches(body, {
        "fvAEPg": {
            "children": [
                {"fvRsBd": {"attributes": {"tnFvBDName": "bd1"}}},
                {
                    "fvRsCons": {
                        "attributes": {
                            "tnVzBrCPName": "web-to-app",
                            "status": "created,modified",
                        },
                    },
                },
                {
                    "fvRsProv": {
                        "attributes": {
                            "tnVzBrCPName": "app-to-db",
                            "status": "created,modified",
                        },
                    },
                },
            ],
        },
    })
