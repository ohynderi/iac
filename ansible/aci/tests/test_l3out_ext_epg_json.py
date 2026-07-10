from helpers import assert_matches


def test_no_external_epgs_renders_empty_children(render):
    l3out = {"name": "l3out1"}
    body = render("l3out_ext_epg.json.j2", l3out_name="l3out1", l3out=l3out)

    assert_matches(body, {"l3extOut": {"attributes": {"name": "l3out1"}, "children": []}})


def test_external_epg_renders_with_defaults(render):
    l3out = {"name": "l3out1", "external_epgs": [{"name": "ext1"}]}
    body = render("l3out_ext_epg.json.j2", l3out_name="l3out1", l3out=l3out)

    assert_matches(body, {
        "l3extOut": {
            "children": [
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
    l3out = {"name": "l3out1", "external_epgs": [{"name": "ext1", "description": "my ext epg"}]}
    body = render("l3out_ext_epg.json.j2", l3out_name="l3out1", l3out=l3out)

    assert_matches(body, {
        "l3extOut": {"children": [{"l3extInstP": {"attributes": {"descr": "my ext epg"}}}]},
    })


def test_external_epg_state_absent(render):
    l3out = {"name": "l3out1", "external_epgs": [{"name": "ext1", "state": "absent"}]}
    body = render("l3out_ext_epg.json.j2", l3out_name="l3out1", l3out=l3out)

    assert_matches(body, {
        "l3extOut": {"children": [{"l3extInstP": {"attributes": {"status": "deleted"}}}]},
    })


def test_subnet_renders_with_all_flags_off(render):
    l3out = {"name": "l3out1", "external_epgs": [
        {"name": "ext1", "subnets": [{"ip": "0.0.0.0/0"}]},
    ]}
    body = render("l3out_ext_epg.json.j2", l3out_name="l3out1", l3out=l3out)

    assert_matches(body, {
        "l3extOut": {"children": [{"l3extInstP": {"children": [
            {"l3extSubnet": {"attributes": {
                "ip": "0.0.0.0/0",
                "aggregate": "",
                "scope": "",
                "status": "created,modified",
            }}},
        ]}}]},
    })


def test_subnet_aggregate_flags(render):
    l3out = {"name": "l3out1", "external_epgs": [
        {"name": "ext1", "subnets": [{
            "ip": "0.0.0.0/0", "agg_export": True, "agg_inport": True, "agg_shared": True,
        }]},
    ]}
    body = render("l3out_ext_epg.json.j2", l3out_name="l3out1", l3out=l3out)

    assert_matches(body, {
        "l3extOut": {"children": [{"l3extInstP": {"children": [
            {"l3extSubnet": {"attributes": {"aggregate": "export-rtctrl,inport-rtctrl,shared-rtctrl"}}},
        ]}}]},
    })


def test_subnet_scope_flags(render):
    l3out = {"name": "l3out1", "external_epgs": [
        {"name": "ext1", "subnets": [{
            "ip": "0.0.0.0/0", "export_route_ctrl": True, "external_epg": True,
            "shared_route_ctrl": True, "shared_security_import": True,
        }]},
    ]}
    body = render("l3out_ext_epg.json.j2", l3out_name="l3out1", l3out=l3out)

    assert_matches(body, {
        "l3extOut": {"children": [{"l3extInstP": {"children": [
            {"l3extSubnet": {"attributes": {
                "scope": "export-rtctrl,import-security,shared-rtctrl,shared-security",
            }}},
        ]}}]},
    })


def test_subnet_state_absent_does_not_affect_other_subnets(render):
    l3out = {"name": "l3out1", "external_epgs": [
        {"name": "ext1", "subnets": [
            {"ip": "0.0.0.0/0", "state": "absent"},
            {"ip": "10.0.0.0/8"},
        ]},
    ]}
    body = render("l3out_ext_epg.json.j2", l3out_name="l3out1", l3out=l3out)

    assert_matches(body, {
        "l3extOut": {"children": [{"l3extInstP": {"children": [
            {"l3extSubnet": {"attributes": {"ip": "0.0.0.0/0", "status": "deleted"}}},
            {"l3extSubnet": {"attributes": {"ip": "10.0.0.0/8", "status": "created,modified"}}},
        ]}}]},
    })


def test_external_epg_state_absent_does_not_affect_other_epgs(render):
    l3out = {"name": "l3out1", "external_epgs": [
        {"name": "ext1", "state": "absent"},
        {"name": "ext2"},
    ]}
    body = render("l3out_ext_epg.json.j2", l3out_name="l3out1", l3out=l3out)

    assert_matches(body, {
        "l3extOut": {"children": [
            {"l3extInstP": {"attributes": {"name": "ext1", "status": "deleted"}}},
            {"l3extInstP": {"attributes": {"name": "ext2", "status": "created,modified"}}},
        ]},
    })
