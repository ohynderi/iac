from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render):
    filter_ = {"name": "f1", "state": "absent"}
    body = render("filter.json.j2", filter_name="f1", filter=filter_)

    assert_matches(body, {
        "vzFilter": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_state_present_minimal_renders_empty_children_with_defaults(render):
    filter_ = {"name": "f1", "state": "present"}
    body = render("filter.json.j2", filter_name="f1", filter=filter_)

    assert_matches(body, {
        "vzFilter": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_does_not_crash(render):
    # Regression test: this used to raise "'dict object' has no attribute
    # 'state'" once the task's `when:` was switched to has_nested_state,
    # which lets this task run without filter.state ever being set.
    filter_ = {"name": "f1"}
    body = render("filter.json.j2", filter_name="f1", filter=filter_)

    assert_matches(body, {
        "vzFilter": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_still_renders_nested_tag_state(render):
    filter_ = {
        "name": "f1",
        "tags": [{"name": "tag1", "value": "value1", "state": "absent"}],
    }
    body = render("filter.json.j2", filter_name="f1", filter=filter_)

    assert_matches(body, {
        "vzFilter": {
            "children": [
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


def test_description_override(render):
    filter_ = {"name": "f1", "description": "my filter"}
    body = render("filter.json.j2", filter_name="f1", filter=filter_)

    assert_matches(body, {
        "vzFilter": {
            "attributes": {
                "descr": "my filter",
            },
        },
    })


def test_tags_render_with_state(render):
    filter_ = {
        "name": "f1",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render("filter.json.j2", filter_name="f1", filter=filter_)

    assert_matches(body, {
        "vzFilter": {
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


def test_tags_and_entries_together(render):
    # Regression test: the comma between the tags loop and the entries loop
    # is only emitted when both lists are non-empty.
    filter_ = {
        "name": "f1",
        "tags": [{"name": "tag1", "value": "value1"}],
        "entries": [{"name": "e1", "ethertype": "ip", "ip_protocol": "tcp", "from_port": 80, "to_port": 443}],
    }
    body = render("filter.json.j2", filter_name="f1", filter=filter_)

    assert_matches(body, {
        "vzFilter": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1"}}},
                {"vzEntry": {"attributes": {"name": "e1"}}},
            ],
        },
    })


def test_entry_renders_with_overrides(render):
    filter_ = {
        "name": "f1",
        "entries": [{
            "name": "e1",
            "description": "my entry",
            "ethertype": "ip",
            "ip_protocol": "tcp",
            "from_port": 80,
            "to_port": 443,
        }],
    }
    body = render("filter.json.j2", filter_name="f1", filter=filter_)

    assert_matches(body, {
        "vzFilter": {
            "children": [
                {
                    "vzEntry": {
                        "attributes": {
                            "name": "e1",
                            "status": "created,modified",
                            "descr": "my entry",
                            "etherT": "ip",
                            "prot": "tcp",
                            "dFromPort": "80",
                            "dToPort": "443",
                        },
                    },
                },
            ],
        },
    })


def test_entry_renders_with_defaults(render):
    filter_ = {"name": "f1", "entries": [{"name": "e1"}]}
    body = render("filter.json.j2", filter_name="f1", filter=filter_)

    assert_matches(body, {
        "vzFilter": {
            "children": [
                {
                    "vzEntry": {
                        "attributes": {
                            "descr": "",
                            "etherT": "unspecified",
                            "prot": "unspecified",
                            "dFromPort": "unspecified",
                            "dToPort": "unspecified",
                        },
                    },
                },
            ],
        },
    })


def test_entry_from_and_to_port_as_named_aliases(render):
    # from_port/to_port can be an integer or a named port alias string
    # (e.g. "https"); the template passes either through untouched.
    filter_ = {
        "name": "f1",
        "entries": [{"name": "e1", "from_port": "https", "to_port": "https"}],
    }
    body = render("filter.json.j2", filter_name="f1", filter=filter_)

    assert_matches(body, {
        "vzFilter": {
            "children": [
                {
                    "vzEntry": {
                        "attributes": {
                            "dFromPort": "https",
                            "dToPort": "https",
                        },
                    },
                },
            ],
        },
    })


def test_entry_from_and_to_port_as_integers(render):
    filter_ = {
        "name": "f1",
        "entries": [{"name": "e1", "from_port": 1024, "to_port": 65535}],
    }
    body = render("filter.json.j2", filter_name="f1", filter=filter_)

    assert_matches(body, {
        "vzFilter": {
            "children": [
                {
                    "vzEntry": {
                        "attributes": {
                            "dFromPort": "1024",
                            "dToPort": "65535",
                        },
                    },
                },
            ],
        },
    })


def test_entry_ip_protocol_as_raw_protocol_number(render):
    # ip_protocol can be a named protocol (e.g. "tcp") or a raw numeric
    # protocol string (e.g. "89" for OSPF); the template passes it through
    # untouched either way.
    filter_ = {
        "name": "f1",
        "entries": [{"name": "e1", "ip_protocol": "89"}],
    }
    body = render("filter.json.j2", filter_name="f1", filter=filter_)

    assert_matches(body, {
        "vzFilter": {
            "children": [
                {"vzEntry": {"attributes": {"prot": "89"}}},
            ],
        },
    })


def test_entry_ethertype_values(render):
    for ethertype in ["arp", "fcoe", "ipv4", "ipv6", "mac_security", "mpls_ucast", "trill"]:
        filter_ = {"name": "f1", "entries": [{"name": "e1", "ethertype": ethertype}]}
        body = render("filter.json.j2", filter_name="f1", filter=filter_)

        assert_matches(body, {
            "vzFilter": {
                "children": [
                    {"vzEntry": {"attributes": {"etherT": ethertype}}},
                ],
            },
        })


def test_entry_state_absent_omits_attributes_except_status(render):
    filter_ = {
        "name": "f1",
        "entries": [{"name": "e1", "state": "absent", "ethertype": "ip"}],
    }
    body = render("filter.json.j2", filter_name="f1", filter=filter_)

    assert_matches(body, {
        "vzFilter": {
            "children": [
                {
                    "vzEntry": {
                        "attributes": {
                            "name": "e1",
                            "status": "deleted",
                            "descr": ABSENT,
                            "etherT": ABSENT,
                            "prot": ABSENT,
                            "dFromPort": ABSENT,
                            "dToPort": ABSENT,
                        },
                    },
                },
            ],
        },
    })


def test_entry_state_absent_does_not_affect_other_entries(render):
    filter_ = {
        "name": "f1",
        "entries": [
            {"name": "e1", "state": "absent"},
            {"name": "e2", "ethertype": "ip"},
        ],
    }
    body = render("filter.json.j2", filter_name="f1", filter=filter_)

    assert_matches(body, {
        "vzFilter": {
            "children": [
                {"vzEntry": {"attributes": {"name": "e1", "status": "deleted"}}},
                {"vzEntry": {"attributes": {"name": "e2", "status": "created,modified", "etherT": "ip"}}},
            ],
        },
    })
