from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render):
    contract = {"name": "c1", "state": "absent"}
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
                "scope": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_state_present_minimal_renders_empty_children_with_defaults(render):
    contract = {"name": "c1", "state": "present"}
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
                "scope": "context",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_does_not_crash(render):
    # Regression test: this used to raise "'dict object' has no attribute
    # 'state'" once the task's `when:` was switched to has_nested_state,
    # which lets this task run without contract.state ever being set.
    contract = {"name": "c1"}
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
                "scope": "context",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_still_renders_nested_tag_state(render):
    contract = {
        "name": "c1",
        "tags": [{"name": "tag1", "value": "value1", "state": "absent"}],
    }
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
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


def test_description_and_scope_overrides(render):
    contract = {"name": "c1", "description": "my contract", "scope": "tenant"}
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
            "attributes": {
                "descr": "my contract",
                "scope": "tenant",
            },
        },
    })


def test_tags_render_with_state(render):
    contract = {
        "name": "c1",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
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


def test_tags_and_subjects_together(render):
    # Regression test: the comma between the tags loop and the subjects loop
    # is only emitted when both lists are non-empty.
    contract = {
        "name": "c1",
        "tags": [{"name": "tag1", "value": "value1"}],
        "subjects": [{"name": "s1"}],
    }
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1"}}},
                {"vzSubj": {"attributes": {"name": "s1"}}},
            ],
        },
    })


def test_subject_renders_with_defaults(render):
    contract = {"name": "c1", "subjects": [{"name": "s1"}]}
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
            "children": [
                {
                    "vzSubj": {
                        "attributes": {
                            "name": "s1",
                            "status": "created,modified",
                            "descr": "",
                            "revFltPorts": "yes",
                        },
                        "children": [],
                    },
                },
            ],
        },
    })


def test_subject_description_and_reverse_filter_port_overrides(render):
    contract = {
        "name": "c1",
        "subjects": [{
            "name": "s1",
            "description": "my subject",
            "reverse_filter_port": "no",
        }],
    }
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
            "children": [
                {
                    "vzSubj": {
                        "attributes": {
                            "descr": "my subject",
                            "revFltPorts": "no",
                        },
                    },
                },
            ],
        },
    })


def test_subject_state_absent_omits_attributes_and_children(render):
    contract = {
        "name": "c1",
        "subjects": [{
            "name": "s1",
            "state": "absent",
            "description": "my subject",
            "filters": [{"name": "f1", "action": "permit"}],
        }],
    }
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
            "children": [
                {
                    "vzSubj": {
                        "attributes": {
                            "status": "deleted",
                            "descr": ABSENT,
                            "revFltPorts": ABSENT,
                        },
                        "children": [
                            {"vzRsSubjFiltAtt": {"attributes": {"status": "created,modified"}}},
                        ],
                    },
                },
            ],
        },
    })


def test_subject_state_absent_does_not_affect_other_subjects(render):
    contract = {
        "name": "c1",
        "subjects": [
            {"name": "s1", "state": "absent"},
            {"name": "s2"},
        ],
    }
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
            "children": [
                {"vzSubj": {"attributes": {"name": "s1", "status": "deleted"}}},
                {"vzSubj": {"attributes": {"name": "s2", "status": "created,modified", "descr": ""}}},
            ],
        },
    })


def test_filter_renders_with_action_and_both_directive_flags(render):
    contract = {
        "name": "c1",
        "subjects": [{
            "name": "s1",
            "filters": [{"name": "f1", "action": "permit", "log": True, "policy_compression": True}],
        }],
    }
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
            "children": [
                {
                    "vzSubj": {
                        "children": [
                            {
                                "vzRsSubjFiltAtt": {
                                    "attributes": {
                                        "tnVzFilterName": "f1",
                                        "status": "created,modified",
                                        "action": "permit",
                                        "directives": "log,no_stats",
                                    },
                                },
                            },
                        ],
                    },
                },
            ],
        },
    })


def test_filter_log_only(render):
    contract = {
        "name": "c1",
        "subjects": [{"name": "s1", "filters": [{"name": "f1", "action": "permit", "log": True}]}],
    }
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
            "children": [
                {
                    "vzSubj": {
                        "children": [
                            {"vzRsSubjFiltAtt": {"attributes": {"directives": "log"}}},
                        ],
                    },
                },
            ],
        },
    })


def test_filter_policy_compression_only(render):
    contract = {
        "name": "c1",
        "subjects": [{"name": "s1", "filters": [{"name": "f1", "action": "permit", "policy_compression": True}]}],
    }
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
            "children": [
                {
                    "vzSubj": {
                        "children": [
                            {"vzRsSubjFiltAtt": {"attributes": {"directives": "no_stats"}}},
                        ],
                    },
                },
            ],
        },
    })


def test_filter_log_explicitly_false(render):
    contract = {
        "name": "c1",
        "subjects": [{"name": "s1", "filters": [{"name": "f1", "action": "permit", "log": False}]}],
    }
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
            "children": [
                {
                    "vzSubj": {
                        "children": [
                            {"vzRsSubjFiltAtt": {"attributes": {"directives": ""}}},
                        ],
                    },
                },
            ],
        },
    })


def test_filter_policy_compression_explicitly_false(render):
    contract = {
        "name": "c1",
        "subjects": [{"name": "s1", "filters": [{"name": "f1", "action": "permit", "policy_compression": False}]}],
    }
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
            "children": [
                {
                    "vzSubj": {
                        "children": [
                            {"vzRsSubjFiltAtt": {"attributes": {"directives": ""}}},
                        ],
                    },
                },
            ],
        },
    })


def test_filter_log_and_policy_compression_can_be_overridden_via_role_var(render):
    contract = {
        "name": "c1",
        "subjects": [{"name": "s1", "filters": [{"name": "f1", "action": "permit"}]}],
    }
    body = render(
        "contract.json.j2",
        contract_name="c1",
        contract=contract,
        subject_default_log=True,
        subject_default_policy_compression=True,
    )

    assert_matches(body, {
        "vzBrCP": {
            "children": [
                {
                    "vzSubj": {
                        "children": [
                            {"vzRsSubjFiltAtt": {"attributes": {"directives": "log,no_stats"}}},
                        ],
                    },
                },
            ],
        },
    })


def test_filter_directives_default_to_empty_string(render):
    contract = {
        "name": "c1",
        "subjects": [{"name": "s1", "filters": [{"name": "f1", "action": "permit"}]}],
    }
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
            "children": [
                {
                    "vzSubj": {
                        "children": [
                            {"vzRsSubjFiltAtt": {"attributes": {"directives": ""}}},
                        ],
                    },
                },
            ],
        },
    })


def test_filter_state_absent_omits_action_and_directives(render):
    contract = {
        "name": "c1",
        "subjects": [{
            "name": "s1",
            "filters": [{"name": "f1", "action": "permit", "log": True, "state": "absent"}],
        }],
    }
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
            "children": [
                {
                    "vzSubj": {
                        "children": [
                            {
                                "vzRsSubjFiltAtt": {
                                    "attributes": {
                                        "tnVzFilterName": "f1",
                                        "status": "deleted",
                                        "action": ABSENT,
                                        "directives": ABSENT,
                                    },
                                },
                            },
                        ],
                    },
                },
            ],
        },
    })


def test_multiple_filters_have_independent_directive_flags(render):
    # Regression test: directives used to be shared across all filters in a
    # subject (read from subject.directives). Each filter must derive its
    # own directives value independently from its own log/policy_compression flags.
    contract = {
        "name": "c1",
        "subjects": [{
            "name": "s1",
            "filters": [
                {"name": "f1", "action": "permit", "log": True},
                {"name": "f2", "action": "deny", "policy_compression": True},
            ],
        }],
    }
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
            "children": [
                {
                    "vzSubj": {
                        "children": [
                            {"vzRsSubjFiltAtt": {"attributes": {"tnVzFilterName": "f1", "directives": "log"}}},
                            {"vzRsSubjFiltAtt": {"attributes": {"tnVzFilterName": "f2", "directives": "no_stats"}}},
                        ],
                    },
                },
            ],
        },
    })


def test_filter_state_absent_does_not_affect_other_filters(render):
    contract = {
        "name": "c1",
        "subjects": [{
            "name": "s1",
            "filters": [
                {"name": "f1", "action": "permit", "state": "absent"},
                {"name": "f2", "action": "deny"},
            ],
        }],
    }
    body = render("contract.json.j2", contract_name="c1", contract=contract)

    assert_matches(body, {
        "vzBrCP": {
            "children": [
                {
                    "vzSubj": {
                        "children": [
                            {"vzRsSubjFiltAtt": {"attributes": {"tnVzFilterName": "f1", "status": "deleted"}}},
                            {"vzRsSubjFiltAtt": {"attributes": {"tnVzFilterName": "f2", "status": "created,modified", "action": "deny"}}},
                        ],
                    },
                },
            ],
        },
    })
