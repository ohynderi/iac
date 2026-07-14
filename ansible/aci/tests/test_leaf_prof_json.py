from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render_fabric):
    leaf_prof = {"name": "lp1", "state": "absent"}
    body = render_fabric("leaf_prof.json.j2", leaf_prof_name="lp1", leaf_prof=leaf_prof)

    assert_matches(body, {
        "infraNodeP": {
            "attributes": {
                "status": "deleted",
                "descr": ABSENT,
            },
            "children": ABSENT,
        },
    })


def test_state_present_minimal_renders_empty_children(render_fabric):
    leaf_prof = {"name": "lp1", "state": "present"}
    body = render_fabric("leaf_prof.json.j2", leaf_prof_name="lp1", leaf_prof=leaf_prof)

    assert_matches(body, {
        "infraNodeP": {
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
    # which lets this task run without leaf_prof.state ever being set.
    leaf_prof = {"name": "lp1"}
    body = render_fabric("leaf_prof.json.j2", leaf_prof_name="lp1", leaf_prof=leaf_prof)

    assert_matches(body, {
        "infraNodeP": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
            },
            "children": [],
        },
    })


def test_description_override(render_fabric):
    leaf_prof = {"name": "lp1", "description": "my leaf profile"}
    body = render_fabric("leaf_prof.json.j2", leaf_prof_name="lp1", leaf_prof=leaf_prof)

    assert_matches(body, {
        "infraNodeP": {"attributes": {"descr": "my leaf profile"}},
    })


def test_leaf_block_renders_selector_and_node_block(render_fabric):
    leaf_prof = {"name": "lp1", "leaf_blocks": [{"name": "b1", "from_": 101, "to_": 105}]}
    body = render_fabric("leaf_prof.json.j2", leaf_prof_name="lp1", leaf_prof=leaf_prof)

    assert_matches(body, {
        "infraNodeP": {
            "children": [
                {
                    "infraLeafS": {
                        "attributes": {
                            "name": "b1",
                            "type": "range",
                            "status": "created,modified",
                        },
                        "children": [
                            {
                                "infraNodeBlk": {
                                    "attributes": {
                                        "name": "b1",
                                        "from_": "101",
                                        "to_": "105",
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


def test_leaf_block_state_absent_deletes_both_selector_and_node_block(render_fabric):
    # Regression test: the infraLeafS status check used to reference
    # `range.state` (a leftover/typo, `range` resolves to Jinja's builtin
    # range() function) instead of `block.state`, so it always rendered
    # "created,modified" even when the block was meant to be deleted.
    leaf_prof = {"name": "lp1", "leaf_blocks": [{"name": "b1", "from_": 101, "to_": 105, "state": "absent"}]}
    body = render_fabric("leaf_prof.json.j2", leaf_prof_name="lp1", leaf_prof=leaf_prof)

    assert_matches(body, {
        "infraNodeP": {
            "children": [
                {
                    "infraLeafS": {
                        "attributes": {"status": "deleted"},
                        "children": [
                            {"infraNodeBlk": {"attributes": {"status": "deleted"}}},
                        ],
                    },
                },
            ],
        },
    })


def test_leaf_blocks_render_with_state(render_fabric):
    # Regression test for the comma boundary between leaf_blocks entries:
    # rendering must produce valid JSON with exactly 2 infraLeafS children.
    leaf_prof = {
        "name": "lp1",
        "leaf_blocks": [
            {"name": "b1", "from_": 101, "to_": 101},
            {"name": "b2", "from_": 102, "to_": 102, "state": "absent"},
        ],
    }
    body = render_fabric("leaf_prof.json.j2", leaf_prof_name="lp1", leaf_prof=leaf_prof)

    assert len(body["infraNodeP"]["children"]) == 2


def test_leaf_interface_profile_binding_renders_tdn(render_fabric):
    leaf_prof = {"name": "lp1", "leaf_interface_profiles": [{"name": "lip1"}]}
    body = render_fabric("leaf_prof.json.j2", leaf_prof_name="lp1", leaf_prof=leaf_prof)

    assert_matches(body, {
        "infraNodeP": {
            "children": [
                {"infraRsAccPortP": {"attributes": {"tDn": "uni/infra/accportprof-lip1", "status": "created,modified"}}},
            ],
        },
    })


def test_leaf_interface_profile_binding_state_absent(render_fabric):
    leaf_prof = {"name": "lp1", "leaf_interface_profiles": [{"name": "lip1", "state": "absent"}]}
    body = render_fabric("leaf_prof.json.j2", leaf_prof_name="lp1", leaf_prof=leaf_prof)

    assert_matches(body, {
        "infraNodeP": {
            "children": [
                {"infraRsAccPortP": {"attributes": {"tDn": "uni/infra/accportprof-lip1", "status": "deleted"}}},
            ],
        },
    })


def test_leaf_blocks_and_leaf_interface_profiles_together(render_fabric):
    # Regression test for the comma boundary between the leaf_blocks group
    # and the leaf_interface_profiles group.
    leaf_prof = {
        "name": "lp1",
        "leaf_blocks": [{"name": "b1", "from_": 101, "to_": 101}],
        "leaf_interface_profiles": [{"name": "lip1"}],
    }
    body = render_fabric("leaf_prof.json.j2", leaf_prof_name="lp1", leaf_prof=leaf_prof)

    assert len(body["infraNodeP"]["children"]) == 2


def test_tags_render_with_state(render_fabric):
    leaf_prof = {
        "name": "lp1",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render_fabric("leaf_prof.json.j2", leaf_prof_name="lp1", leaf_prof=leaf_prof)

    assert_matches(body, {
        "infraNodeP": {
            "children": [
                {"tagAnnotation": {"attributes": {"key": "tag1", "value": "value1", "status": "created,modified"}}},
                {"tagAnnotation": {"attributes": {"key": "tag2", "value": "value2", "status": "deleted"}}},
            ],
        },
    })


def test_leaf_blocks_and_tags_together_no_interface_profiles(render_fabric):
    # Regression test: the comma-boundary check before the tags group used
    # to reference the nonexistent `leaf_prof.ranges` instead of
    # `leaf_prof.leaf_blocks`, so this combination produced invalid JSON.
    leaf_prof = {
        "name": "lp1",
        "leaf_blocks": [{"name": "b1", "from_": 101, "to_": 101}],
        "tags": [{"name": "tag1", "value": "value1"}],
    }
    body = render_fabric("leaf_prof.json.j2", leaf_prof_name="lp1", leaf_prof=leaf_prof)

    assert len(body["infraNodeP"]["children"]) == 2


def test_leaf_blocks_leaf_interface_profiles_and_tags_all_together(render_fabric):
    leaf_prof = {
        "name": "lp1",
        "leaf_blocks": [{"name": "b1", "from_": 101, "to_": 101}],
        "leaf_interface_profiles": [{"name": "lip1"}],
        "tags": [{"name": "tag1", "value": "value1"}],
    }
    body = render_fabric("leaf_prof.json.j2", leaf_prof_name="lp1", leaf_prof=leaf_prof)

    assert len(body["infraNodeP"]["children"]) == 3
