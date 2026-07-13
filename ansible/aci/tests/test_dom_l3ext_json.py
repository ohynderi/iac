from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render_fabric):
    dom = {"name": "dom1", "state": "absent"}
    body = render_fabric("dom_l3ext.json.j2", dom_name="dom1", dom=dom)

    assert_matches(body, {
        "l3extDomP": {
            "attributes": {
                "status": "deleted",
            },
            "children": ABSENT,
        },
    })


def test_state_present_minimal_renders_empty_children(render_fabric):
    dom = {"name": "dom1", "state": "present"}
    body = render_fabric("dom_l3ext.json.j2", dom_name="dom1", dom=dom)

    assert_matches(body, {
        "l3extDomP": {
            "attributes": {
                "status": "created,modified",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_does_not_crash(render_fabric):
    # Regression test: this used to raise "'dict object' has no attribute
    # 'state'" once the task's `when:` was switched to has_nested_state,
    # which lets this task run without dom.state ever being set.
    dom = {"name": "dom1"}
    body = render_fabric("dom_l3ext.json.j2", dom_name="dom1", dom=dom)

    assert_matches(body, {
        "l3extDomP": {
            "attributes": {
                "status": "created,modified",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_still_renders_vlan_pool(render_fabric):
    dom = {"name": "dom1", "vlan_pool": "pool1"}
    body = render_fabric("dom_l3ext.json.j2", dom_name="dom1", dom=dom)

    assert_matches(body, {
        "l3extDomP": {
            "children": [
                {"infraRsVlanNs": {"attributes": {"tDn": "uni/infra/vlanns-[pool1]-static"}}},
            ],
        },
    })


def test_tags_render_with_state(render_fabric):
    dom = {
        "name": "dom1",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render_fabric("dom_l3ext.json.j2", dom_name="dom1", dom=dom)

    assert_matches(body, {
        "l3extDomP": {
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


def test_vlan_pool_omitted_when_not_defined(render_fabric):
    dom = {"name": "dom1"}
    body = render_fabric("dom_l3ext.json.j2", dom_name="dom1", dom=dom)

    assert_matches(body, {
        "l3extDomP": {
            "children": [],
        },
    })


def test_vlan_pool_as_string_defaults_to_static(render_fabric):
    dom = {"name": "dom1", "vlan_pool": "pool1"}
    body = render_fabric("dom_l3ext.json.j2", dom_name="dom1", dom=dom)

    assert_matches(body, {
        "l3extDomP": {
            "children": [
                {"infraRsVlanNs": {"attributes": {"tDn": "uni/infra/vlanns-[pool1]-static"}}},
            ],
        },
    })


def test_vlan_pool_as_dict_with_allocation_mode_override(render_fabric):
    dom = {"name": "dom1", "vlan_pool": {"name": "pool1", "allocation_mode": "dynamic"}}
    body = render_fabric("dom_l3ext.json.j2", dom_name="dom1", dom=dom)

    assert_matches(body, {
        "l3extDomP": {
            "children": [
                {"infraRsVlanNs": {"attributes": {"tDn": "uni/infra/vlanns-[pool1]-dynamic"}}},
            ],
        },
    })


def test_vlan_pool_as_dict_without_allocation_mode_defaults_to_static(render_fabric):
    dom = {"name": "dom1", "vlan_pool": {"name": "pool1"}}
    body = render_fabric("dom_l3ext.json.j2", dom_name="dom1", dom=dom)

    assert_matches(body, {
        "l3extDomP": {
            "children": [
                {"infraRsVlanNs": {"attributes": {"tDn": "uni/infra/vlanns-[pool1]-static"}}},
            ],
        },
    })


def test_vlan_pool_as_string_has_no_delete_capability(render_fabric):
    # A bare string vlan_pool has no state of its own, so the relation
    # always renders created,modified.
    dom = {"name": "dom1", "vlan_pool": "pool1"}
    body = render_fabric("dom_l3ext.json.j2", dom_name="dom1", dom=dom)

    assert_matches(body, {
        "l3extDomP": {
            "children": [
                {"infraRsVlanNs": {"attributes": {"status": "created,modified"}}},
            ],
        },
    })


def test_vlan_pool_as_dict_state_absent_deletes_relation(render_fabric):
    dom = {"name": "dom1", "vlan_pool": {"name": "pool1", "state": "absent"}}
    body = render_fabric("dom_l3ext.json.j2", dom_name="dom1", dom=dom)

    assert_matches(body, {
        "l3extDomP": {
            "children": [
                {"infraRsVlanNs": {"attributes": {"tDn": "uni/infra/vlanns-[pool1]-static", "status": "deleted"}}},
            ],
        },
    })


def test_vlan_pool_as_dict_state_present(render_fabric):
    dom = {"name": "dom1", "vlan_pool": {"name": "pool1", "state": "present"}}
    body = render_fabric("dom_l3ext.json.j2", dom_name="dom1", dom=dom)

    assert_matches(body, {
        "l3extDomP": {
            "children": [
                {"infraRsVlanNs": {"attributes": {"status": "created,modified"}}},
            ],
        },
    })


def test_tags_and_vlan_pool_together(render_fabric):
    # Regression test: with the pre-fix template this combination raised a
    # JSON parse error (missing comma between the tags group and the
    # vlan_pool relation, since the condition checked a nonexistent
    # dom.ranges field instead of the vlan_pool relation).
    dom = {
        "name": "dom1",
        "tags": [{"name": "tag1", "value": "value1"}],
        "vlan_pool": "pool1",
    }
    body = render_fabric("dom_l3ext.json.j2", dom_name="dom1", dom=dom)

    assert_matches(body, {
        "l3extDomP": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1"}}},
                {"infraRsVlanNs": {"attributes": {"tDn": "uni/infra/vlanns-[pool1]-static"}}},
            ],
        },
    })
