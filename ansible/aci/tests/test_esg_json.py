from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render):
    esg = {"name": "esg1", "vrf": "vrf1", "state": "absent"}
    body = render("esg.json.j2", esg_name="esg1", esg=esg)

    assert_matches(body, {
        "fvESg": {
            "attributes": {
                "status": "deleted",
            },
            "children": ABSENT,
        },
    })


def test_state_present_minimal_renders_scope_only(render):
    esg = {"name": "esg1", "vrf": "vrf1", "state": "present"}
    body = render("esg.json.j2", esg_name="esg1", esg=esg)

    assert_matches(body, {
        "fvESg": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
                "prefGrMemb": "exclude",
            },
            "children": [
                {"fvRsScope": {"attributes": {"tnFvCtxName": "vrf1", "status": "created,modified"}}},
            ],
        },
    })


def test_state_undefined_at_root_does_not_crash(render):
    # Regression test: this used to raise "'dict object' has no attribute
    # 'state'" once the task's `when:` was switched to has_nested_state,
    # which lets this task run without esg.state ever being set.
    esg = {"name": "esg1", "vrf": "vrf1"}
    body = render("esg.json.j2", esg_name="esg1", esg=esg)

    assert_matches(body, {
        "fvESg": {
            "attributes": {"status": "created,modified", "descr": ""},
            "children": [{"fvRsScope": {}}],
        },
    })


def test_state_undefined_at_root_still_renders_nested_tag_state(render):
    esg = {
        "name": "esg1", "vrf": "vrf1",
        "tags": [{"name": "tag1", "value": "value1", "state": "absent"}],
    }
    body = render("esg.json.j2", esg_name="esg1", esg=esg)

    assert_matches(body, {
        "fvESg": {
            "children": [
                {"fvRsScope": {}},
                {"tagAnnotation": {"attributes": {"key": "tag1", "status": "deleted"}}},
            ],
        },
    })


def test_description_and_preferred_group_member_overrides(render):
    esg = {
        "name": "esg1", "vrf": "vrf1",
        "description": "my esg",
        "preferred_group_member": "include",
    }
    body = render("esg.json.j2", esg_name="esg1", esg=esg)

    assert_matches(body, {
        "fvESg": {
            "attributes": {
                "descr": "my esg",
                "prefGrMemb": "include",
            },
        },
    })


def test_tags_render_with_state(render):
    esg = {
        "name": "esg1", "vrf": "vrf1",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render("esg.json.j2", esg_name="esg1", esg=esg)

    assert_matches(body, {
        "fvESg": {
            "children": [
                {"fvRsScope": {}},
                {"tagAnnotation": {"attributes": {"key": "tag1", "status": "created,modified"}}},
                {"tagAnnotation": {"attributes": {"key": "tag2", "status": "deleted"}}},
            ],
        },
    })


def test_epg_selector_renders_match_epg_dn(render):
    esg = {"name": "esg1", "vrf": "vrf1", "epgs": [{"name": "epg1"}]}
    body = render(
        "esg.json.j2", esg_name="esg1", esg=esg,
        ap={"name": "ap1"}, tenant={"name": "t1"},
    )

    assert_matches(body, {
        "fvESg": {
            "children": [
                {"fvRsScope": {}},
                {
                    "fvEPgSelector": {
                        "attributes": {
                            "name": "epg1",
                            "matchEpgDn": "uni/tn-t1/ap-ap1/epg-epg1",
                            "status": "created,modified",
                        },
                    },
                },
            ],
        },
    })


def test_epg_selector_state_absent_does_not_affect_other_selectors(render):
    esg = {"name": "esg1", "vrf": "vrf1", "epgs": [
        {"name": "epg1", "state": "absent"},
        {"name": "epg2"},
    ]}
    body = render(
        "esg.json.j2", esg_name="esg1", esg=esg,
        ap={"name": "ap1"}, tenant={"name": "t1"},
    )

    assert_matches(body, {
        "fvESg": {
            "children": [
                {"fvRsScope": {}},
                {"fvEPgSelector": {"attributes": {"name": "epg1", "matchEpgDn": "uni/tn-t1/ap-ap1/epg-epg1", "status": "deleted"}}},
                {"fvEPgSelector": {"attributes": {"name": "epg2", "matchEpgDn": "uni/tn-t1/ap-ap1/epg-epg2", "status": "created,modified"}}},
            ],
        },
    })


def test_contracts_consumer_and_provider_with_state(render):
    esg = {"name": "esg1", "vrf": "vrf1", "contracts": [
        {"name": "c1", "type": "consumer"},
        {"name": "c2", "type": "provider", "state": "absent"},
    ]}
    body = render("esg.json.j2", esg_name="esg1", esg=esg)

    assert_matches(body, {
        "fvESg": {
            "children": [
                {"fvRsScope": {}},
                {"fvRsCons": {"attributes": {"tnVzBrCPName": "c1", "status": "created,modified"}}},
                {"fvRsProv": {"attributes": {"tnVzBrCPName": "c2", "status": "deleted"}}},
            ],
        },
    })


def test_contract_state_absent_does_not_affect_other_children(render):
    esg = {
        "name": "esg1", "vrf": "vrf1",
        "epgs": [{"name": "epg1"}],
        "contracts": [
            {"name": "c1", "type": "consumer"},
            {"name": "c2", "type": "provider", "state": "absent"},
        ],
    }
    body = render(
        "esg.json.j2", esg_name="esg1", esg=esg,
        ap={"name": "ap1"}, tenant={"name": "t1"},
    )

    assert_matches(body, {
        "fvESg": {
            "children": [
                {"fvRsScope": {"attributes": {"status": "created,modified"}}},
                {"fvEPgSelector": {"attributes": {"status": "created,modified"}}},
                {"fvRsCons": {"attributes": {"status": "created,modified"}}},
                {"fvRsProv": {"attributes": {"status": "deleted"}}},
            ],
        },
    })
