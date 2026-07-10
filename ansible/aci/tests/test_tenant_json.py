from helpers import ABSENT, assert_matches


def test_state_absent_deletes_and_omits_children(render):
    tenant = {"name": "tenant1", "state": "absent"}
    body = render("tenant.json.j2", tenant_name="tenant1", tenant=tenant)

    assert_matches(body, {
        "fvTenant": {
            "attributes": {
                "status": "deleted",
                "descr": "",
            },
            "children": ABSENT,
        },
    })


def test_state_present_with_description_and_tags(render):
    tenant = {
        "name": "tenant1",
        "state": "present",
        "description": "my tenant",
        "tags": [
            {"name": "tag1", "value": "value1"},
            {"name": "tag2", "value": "value2", "state": "absent"},
        ],
    }
    body = render("tenant.json.j2", tenant_name="tenant1", tenant=tenant)

    assert_matches(body, {
        "fvTenant": {
            "attributes": {
                "status": "created,modified",
                "descr": "my tenant",
            },
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


def test_state_undefined_at_root_does_not_crash(render):
    # Regression test: this used to raise "'dict object' has no attribute
    # 'state'" once the task's `when:` was switched to has_nested_state,
    # which lets this task run without tenant.state ever being set.
    tenant = {"name": "tenant1"}
    body = render("tenant.json.j2", tenant_name="tenant1", tenant=tenant)

    assert_matches(body, {
        "fvTenant": {
            "attributes": {
                "status": "created,modified",
                "descr": "",
            },
            "children": [],
        },
    })


def test_state_undefined_at_root_still_renders_nested_tag_state(render):
    tenant = {
        "name": "tenant1",
        "tags": [{"name": "tag1", "value": "value1", "state": "absent"}],
    }
    body = render("tenant.json.j2", tenant_name="tenant1", tenant=tenant)

    assert_matches(body, {
        "fvTenant": {
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


def test_default_description_can_be_overridden_via_role_var(render):
    tenant = {"name": "tenant1"}
    body = render(
        "tenant.json.j2",
        tenant_name="tenant1",
        tenant=tenant,
        tenant_default_description="fallback descr",
    )

    assert_matches(body, {
        "fvTenant": {
            "attributes": {
                "descr": "fallback descr",
            },
        },
    })
