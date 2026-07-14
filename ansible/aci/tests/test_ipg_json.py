from helpers import ABSENT, assert_matches


# ---------------------------------------------------------------------------
# ipg_access.json.j2
# ---------------------------------------------------------------------------

def test_access_state_absent_deletes_and_omits_children(render_fabric):
    ipg = {"name": "ipg1", "state": "absent"}
    body = render_fabric("ipg_access.json.j2", ipg_name="ipg1", ipg=ipg)

    assert_matches(body, {
        "infraAccPortGrp": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_access_state_present_minimal_renders_defaults(render_fabric):
    ipg = {"name": "ipg1", "state": "present"}
    body = render_fabric("ipg_access.json.j2", ipg_name="ipg1", ipg=ipg)

    assert_matches(body, {
        "infraAccPortGrp": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
            },
            "children": [
                {"infraRsStpIfPol": {"attributes": {"tnStpIfPolName": ""}}},
                {"infraRsMcpIfPol": {"attributes": {"tnMcpIfPolName": ""}}},
                {"infraRsAttEntP": {"attributes": {"tDn": ""}}},
                {"infraRsCdpIfPol": {"attributes": {"tnCdpIfPolName": ""}}},
                {"infraRsLldpIfPol": {"attributes": {"tnLldpIfPolName": ""}}},
                {"infraRsL2IfPol": {"attributes": {"tnL2IfPolName": ""}}},
                {"infraRsHIfPol": {"attributes": {"tnFabricHIfPolName": ""}}},
            ],
        },
    })


def test_access_state_undefined_at_root_does_not_crash(render_fabric):
    # Regression test: this used to raise "'dict object' has no attribute
    # 'state'" once the task's `when:` was switched to has_nested_state,
    # which lets this task run without ipg.state ever being set.
    ipg = {"name": "ipg1"}
    body = render_fabric("ipg_access.json.j2", ipg_name="ipg1", ipg=ipg)

    assert_matches(body, {
        "infraAccPortGrp": {
            "attributes": {"status": "created,modified"},
        },
    })


def test_access_description_override(render_fabric):
    ipg = {"name": "ipg1", "description": "my ipg"}
    body = render_fabric("ipg_access.json.j2", ipg_name="ipg1", ipg=ipg)

    assert_matches(body, {
        "infraAccPortGrp": {"attributes": {"descr": "my ipg"}},
    })


def test_access_policy_refs_override(render_fabric):
    ipg = {
        "name": "ipg1",
        "stp": "stp_pol",
        "mcp": "mcp_pol",
        "cdp": "cdp_pol",
        "lldp": "lldp_pol",
        "l2": "l2_pol",
        "ll": "ll_pol",
    }
    body = render_fabric("ipg_access.json.j2", ipg_name="ipg1", ipg=ipg)

    assert_matches(body, {
        "infraAccPortGrp": {
            "children": [
                {"infraRsStpIfPol": {"attributes": {"tnStpIfPolName": "stp_pol"}}},
                {"infraRsMcpIfPol": {"attributes": {"tnMcpIfPolName": "mcp_pol"}}},
                {"infraRsAttEntP": {"attributes": {"tDn": ""}}},
                {"infraRsCdpIfPol": {"attributes": {"tnCdpIfPolName": "cdp_pol"}}},
                {"infraRsLldpIfPol": {"attributes": {"tnLldpIfPolName": "lldp_pol"}}},
                {"infraRsL2IfPol": {"attributes": {"tnL2IfPolName": "l2_pol"}}},
                {"infraRsHIfPol": {"attributes": {"tnFabricHIfPolName": "ll_pol"}}},
            ],
        },
    })


def _find_child(children, key):
    return next(c[key] for c in children if key in c)


def test_access_aaep_binding_renders_tdn(render_fabric):
    ipg = {"name": "ipg1", "aaep": "aaep1"}
    body = render_fabric("ipg_access.json.j2", ipg_name="ipg1", ipg=ipg)
    ref = _find_child(body["infraAccPortGrp"]["children"], "infraRsAttEntP")

    assert_matches(ref, {"attributes": {"tDn": "uni/infra/attentp-aaep1"}})


def test_access_aaep_undefined_does_not_crash(render_fabric):
    # Regression test: "{{ 'uni/infra/attentp-' + ipg.aaep if ipg.aaep ... }}"
    # used to raise UndefinedError under StrictUndefined when aaep was unset,
    # because ipg.aaep was evaluated before the truthy guard could apply.
    ipg = {"name": "ipg1"}
    body = render_fabric("ipg_access.json.j2", ipg_name="ipg1", ipg=ipg)
    ref = _find_child(body["infraAccPortGrp"]["children"], "infraRsAttEntP")

    assert_matches(ref, {"attributes": {"tDn": ""}})


def test_access_aaep_empty_string_renders_empty_tdn(render_fabric):
    ipg = {"name": "ipg1", "aaep": ""}
    body = render_fabric("ipg_access.json.j2", ipg_name="ipg1", ipg=ipg)
    ref = _find_child(body["infraAccPortGrp"]["children"], "infraRsAttEntP")

    assert_matches(ref, {"attributes": {"tDn": ""}})


def test_access_tags_render_with_state(render_fabric):
    ipg = {
        "name": "ipg1",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render_fabric("ipg_access.json.j2", ipg_name="ipg1", ipg=ipg)
    children = body["infraAccPortGrp"]["children"]

    assert len(children) == 9  # 7 fixed refs + 2 tags
    assert_matches(children[-2:], [
        {"tagAnnotation": {"attributes": {"key": "tag1", "value": "value1", "status": "created,modified"}}},
        {"tagAnnotation": {"attributes": {"key": "tag2", "value": "value2", "status": "deleted"}}},
    ])


def test_access_no_lag_ref_rendered(render_fabric):
    # infraAccPortGrp (single/access ports) has no LACP policy binding,
    # unlike infraAccBndlGrp (port-channel/vPC) - see ipg_po tests below.
    ipg = {"name": "ipg1"}
    body = render_fabric("ipg_access.json.j2", ipg_name="ipg1", ipg=ipg)
    rendered = {list(c.keys())[0] for c in body["infraAccPortGrp"]["children"]}

    assert "infraRsLacpPol" not in rendered


# ---------------------------------------------------------------------------
# ipg_po.json.j2 (shared by port-channel and vPC IPGs)
# ---------------------------------------------------------------------------

def test_po_state_absent_deletes_and_omits_children(render_fabric):
    ipg = {"name": "ipg1", "state": "absent"}
    body = render_fabric("ipg_po.json.j2", ipg_name="ipg1", ipg=ipg, ipg_lag_type="po")

    assert_matches(body, {
        "infraAccBndlGrp": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
                "lagT": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_po_state_present_minimal_renders_defaults(render_fabric):
    ipg = {"name": "ipg1", "state": "present"}
    body = render_fabric("ipg_po.json.j2", ipg_name="ipg1", ipg=ipg, ipg_lag_type="po")

    assert_matches(body, {
        "infraAccBndlGrp": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
                "lagT": "link",
            },
            "children": [
                {"infraRsStpIfPol": {"attributes": {"tnStpIfPolName": ""}}},
                {"infraRsMcpIfPol": {"attributes": {"tnMcpIfPolName": ""}}},
                {"infraRsAttEntP": {"attributes": {"tDn": ""}}},
                {"infraRsCdpIfPol": {"attributes": {"tnCdpIfPolName": ""}}},
                {"infraRsLldpIfPol": {"attributes": {"tnLldpIfPolName": ""}}},
                {"infraRsL2IfPol": {"attributes": {"tnL2IfPolName": ""}}},
                {"infraRsHIfPol": {"attributes": {"tnFabricHIfPolName": ""}}},
                {"infraRsLacpPol": {"attributes": {"tnLacpLagPolName": ""}}},
            ],
        },
    })


def test_po_state_undefined_at_root_does_not_crash(render_fabric):
    ipg = {"name": "ipg1"}
    body = render_fabric("ipg_po.json.j2", ipg_name="ipg1", ipg=ipg, ipg_lag_type="po")

    assert_matches(body, {
        "infraAccBndlGrp": {"attributes": {"status": "created,modified"}},
    })


def test_lag_type_po_renders_link(render_fabric):
    ipg = {"name": "ipg1"}
    body = render_fabric("ipg_po.json.j2", ipg_name="ipg1", ipg=ipg, ipg_lag_type="po")

    assert_matches(body, {"infraAccBndlGrp": {"attributes": {"lagT": "link"}}})


def test_lag_type_vpc_renders_node(render_fabric):
    ipg = {"name": "ipg1"}
    body = render_fabric("ipg_po.json.j2", ipg_name="ipg1", ipg=ipg, ipg_lag_type="vpc")

    assert_matches(body, {"infraAccBndlGrp": {"attributes": {"lagT": "node"}}})


def test_po_description_override(render_fabric):
    ipg = {"name": "ipg1", "description": "my po ipg"}
    body = render_fabric("ipg_po.json.j2", ipg_name="ipg1", ipg=ipg, ipg_lag_type="po")

    assert_matches(body, {"infraAccBndlGrp": {"attributes": {"descr": "my po ipg"}}})


def test_po_policy_refs_override(render_fabric):
    ipg = {
        "name": "ipg1",
        "stp": "stp_pol",
        "mcp": "mcp_pol",
        "cdp": "cdp_pol",
        "lldp": "lldp_pol",
        "l2": "l2_pol",
        "ll": "ll_pol",
        "lag": "lag_pol",
    }
    body = render_fabric("ipg_po.json.j2", ipg_name="ipg1", ipg=ipg, ipg_lag_type="po")

    assert_matches(body, {
        "infraAccBndlGrp": {
            "children": [
                {"infraRsStpIfPol": {"attributes": {"tnStpIfPolName": "stp_pol"}}},
                {"infraRsMcpIfPol": {"attributes": {"tnMcpIfPolName": "mcp_pol"}}},
                {"infraRsAttEntP": {"attributes": {"tDn": ""}}},
                {"infraRsCdpIfPol": {"attributes": {"tnCdpIfPolName": "cdp_pol"}}},
                {"infraRsLldpIfPol": {"attributes": {"tnLldpIfPolName": "lldp_pol"}}},
                {"infraRsL2IfPol": {"attributes": {"tnL2IfPolName": "l2_pol"}}},
                {"infraRsHIfPol": {"attributes": {"tnFabricHIfPolName": "ll_pol"}}},
                {"infraRsLacpPol": {"attributes": {"tnLacpLagPolName": "lag_pol"}}},
            ],
        },
    })


def test_po_aaep_binding_renders_tdn(render_fabric):
    ipg = {"name": "ipg1", "aaep": "aaep1"}
    body = render_fabric("ipg_po.json.j2", ipg_name="ipg1", ipg=ipg, ipg_lag_type="po")
    ref = _find_child(body["infraAccBndlGrp"]["children"], "infraRsAttEntP")

    assert_matches(ref, {"attributes": {"tDn": "uni/infra/attentp-aaep1"}})


def test_po_aaep_undefined_does_not_crash(render_fabric):
    # Regression test: same StrictUndefined crash as ipg_access, but for
    # the ipg_po template (shared by port-channel and vPC IPGs).
    ipg = {"name": "ipg1"}
    body = render_fabric("ipg_po.json.j2", ipg_name="ipg1", ipg=ipg, ipg_lag_type="po")
    ref = _find_child(body["infraAccBndlGrp"]["children"], "infraRsAttEntP")

    assert_matches(ref, {"attributes": {"tDn": ""}})


def test_po_tags_render_with_state(render_fabric):
    # Also a regression test for the trailing-comma bug that made every
    # infraAccBndlGrp attributes block invalid JSON in 100% of renders,
    # and for the tag/tags typo in the comma-boundary check before "children".
    ipg = {
        "name": "ipg1",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render_fabric("ipg_po.json.j2", ipg_name="ipg1", ipg=ipg, ipg_lag_type="po")
    children = body["infraAccBndlGrp"]["children"]

    assert len(children) == 10  # 8 fixed refs + 2 tags
    assert_matches(children[-2:], [
        {"tagAnnotation": {"attributes": {"key": "tag1", "value": "value1", "status": "created,modified"}}},
        {"tagAnnotation": {"attributes": {"key": "tag2", "value": "value2", "status": "deleted"}}},
    ])


def test_po_no_tags_renders_valid_json_with_no_trailing_comma(render_fabric):
    ipg = {"name": "ipg1"}
    body = render_fabric("ipg_po.json.j2", ipg_name="ipg1", ipg=ipg, ipg_lag_type="po")

    assert len(body["infraAccBndlGrp"]["children"]) == 8
