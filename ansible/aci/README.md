# ACI IaC (Ansible)

Ansible automation that pushes a declarative "intent" (YAML files, validated against
`schema.json`) to a Cisco ACI fabric via the APIC REST API. It manages three layers:

- **fabric** – access-layer/infra policies (VLAN pools, domains, AAEP, interface
  policies, interface policy groups, leaf/leaf-interface profiles)
- **node** – per-switch interface selectors that bind physical ports to an interface
  policy group
- **tenant** – tenant objects (VRFs, bridge domains, contracts/filters, application
  profiles/EPGs, L3Outs)

## How it works (`iac.yml`)

1. Initializes accumulators: `intent`, `successful_calls`, `failed_calls`, and
   `ipg_to_type_map`.
2. Recursively finds every `*.yml`/`*.yaml` file under `aci_cfg_directory` and deep-merges
   them (`combine(recursive=True, list_merge='append')`) into a single `intent` dict.
   This lets you split configuration across as many files/subfolders as you like.
3. Validates the merged `intent` against `schema.json` (draft-07 JSON Schema, via
   `ansible.utils.validate`). The play fails fast if the intent doesn't conform.
4. Builds `ipg_to_type_map`: for every fabric interface policy group, records whether it's
   `accportgrp`/`accbundle` and whether it's a `node`- or `link`-level LAG. The **node**
   role's interface-selector template uses this map to compute the correct `tDn` for a
   port's policy group (it can't tell from the node config alone).
5. Runs the three roles in order — `fabric` → `node` → `tenant` — each gated by an
   `enable_*_role` boolean.
6. Prints `successful_calls` and `failed_calls` (dn + status, or dn + error + payload).

Each role/task is independently toggleable via `import_<task>_task` vars in
`roles/<role>/vars/main.yml`, and every generated object name can be wrapped with a
`<x>_name_prefix`/`<x>_name_suffix` (also in `vars/main.yml`) — useful for namespacing
when multiple pipelines/environments share a fabric.

Templates also pull fallback values for optional intent fields from `vars/main.yml`
instead of hardcoding them, mostly as `<x>_default_<field>` (e.g.
`epg_default_description`, `epg_default_preferred_group_member`,
`subject_default_action`). Two families of fields deviate from that naming pattern:

- The EPG domain-attachment/interface immediacy fields: `domain.resolution` /
  `domain.deployment` fall back to `domain_immediacy` / `domain_deployment`, and an
  interface's `deployment` field falls back to `interface_deployment`.
- The BD L2/L3 unknown-traffic and ARP-flood fields (`l2_unknown_unicast`,
  `l3_unknown_multicast`, `arp_flood`) don't have a single static default — each falls
  back to one of two `bd_default_<field>_routing_enabled` /
  `bd_default_<field>_routing_disabled` vars depending on whether `bd.unicast_routing`
  is set, preserving the coupling `bd.json.j2` originally had baked in before those
  fields were split out into independently overridable ones.

All of the above live in `roles/tenant/vars/main.yml`.

## The `state: present|absent` convention

Every object in the schema carries an optional `state`, and it can be set not just on
the object itself but on any of its children (a tag, a domain, a route-map, ...). The
Jinja templates map it as:

- `state: present` (or unset, defaulting to present) → APIC `status: created,modified`
  (and render the full body/children)
- `state: absent` → APIC `status: deleted` (skip the body — a bare delete)

**Task gating.** Most tasks still fire only when the item's own `state` is *defined*
(`when: <item>.state is defined`) — omit `state` entirely to leave an object untouched.
`epg.yml`, `ap.yml`, `tenant.yml`, and `bd.yml` have been migrated to the
`has_nested_state` filter (see below), which fires when `state` is defined *anywhere* in
the item's dict/list tree, not just at the root — needed because a single task/template
call renders the whole object (e.g. EPG + tags + domains + interfaces + contracts) in
one POST, so a change nested several levels down (e.g. `tags[1].state: absent`) would
otherwise never reach the template unless the object's own `state` also happened to be
set.

Because of this, any Jinja template whose task might run with its *own* `state` unset
must not compare it directly (`{% if epg.state == 'present' %}` raises "has no attribute
'state'" under Ansible's strict undefined). Guard it with `default('present')`
(`{% if epg.state | default('present') != 'absent' %}`), as `epg.json.j2` now does.

## Filter plugin: `has_nested_state` (`plugins/state_helpers.py`)

Loaded via `ansible.cfg` (`filter_plugins = ./plugins`, adjacent to `iac.yml` — Ansible
only auto-discovers a directory literally named `filter_plugins`, so a plain `plugins/`
folder needs this one line of config to be picked up).

`has_nested_state(data)` recursively walks a dict/list and returns `True` if a `state`
key exists anywhere in it. Used as the task gate instead of `<item>.state is defined`
when a single task/template renders an item's entire subtree, so a `state` set only on
a nested child still triggers the task:

```yaml
when:
  - epg | has_nested_state
```

It also accepts `include_keys` / `exclude_keys` (mutually exclusive) to restrict the
search to specific top-level branches of the item — useful when an object nests a
substructure owned/rendered by a different task, e.g. `ap.yml` and `tenant.yml` scope
to `include_keys=['tags']` since `ap` nests `epgs` (its own task) and `tenant` nests
almost everything else:

```yaml
when:
  - ap | has_nested_state(include_keys=['tags'])
```

The filters were also designed to support two separate tasks each rendering a
different slice of the same looped item (matching `exclude_keys`/`include_keys`
pairs, one per task) — `l3out.yml` used to be structured that way, with one task for
node/interface profiles and another for `external_epgs`, both looping over
`tenant.l3outs`. That's no longer needed: the two templates were merged (the
external-EPG rendering is now `{% include "l3out_ext_epg.json.j2" %}`'d directly into
`l3out.json.j2`, the same way `bgp_peer.json.j2` is included), so `l3out.yml` is back
to a single task with an unrestricted `has_nested_state` check.

The item's own root-level `state` key is always honored regardless of these filters.

## The wrapper task (`wrapper_api_call.yml`)

Every leaf task (`bd.yml`, `ipg.yml`, `intf.yml`, ...) sets `path`, `payload`, and `dn`,
then includes `wrapper_api_call.yml`, which:

1. POSTs to the APIC via `cisco.aci.aci_rest` with `ignore_errors: yes` (so one bad
   object doesn't abort the whole run).
2. Appends `{dn, status}` to `successful_calls` or `{dn, error, payload}` to
   `failed_calls` depending on the result.

`payload` is rendered by a `.json.j2` template into JSON text, then piped through
`from_yaml | to_json` before being sent — this re-parses/re-serializes it so minor
template whitespace doesn't matter (JSON is valid YAML).

This wrapper is copy-pasted identically into `roles/fabric`, `roles/node`, and
`roles/tenant` (Ansible roles can't `include_tasks` across role boundaries without a
shared "common" role) — see review notes below for a drift between the copies.

## Repository layout

```
iac.yml                        # entry playbook (hosts: apic)
ansible.cfg                    # points filter_plugins at ./plugins
schema.json                    # JSON Schema (draft-07) for the merged intent
plugins/state_helpers.py       # has_nested_state filter (see below)
roles/
  fabric/tasks/                # leaf_prof, leaf_intf_prof, intf_pol, vlan_pool, domain, aaep, ipg
  fabric/templates/*.json.j2   # one template per fabric object type
  fabric/vars/main.yml         # import_*_task toggles + name prefix/suffix
  node/tasks/intf.yml          # interface selector (port -> IPG) per node
  node/templates/intf_selector.json.j2
  tenant/tasks/                # tenant, filter, contract, vrf, bd, ap, epg, l3out
  tenant/templates/*.json.j2
  tenant/vars/main.yml
```

Config intent itself is **not** stored in this repo — `iac.yml` reads it at runtime from
`aci_cfg_directory` (currently `/config/intent/`).

## Intent model (`schema.json`)

Top level:

| Key       | Required | Contents |
|-----------|----------|----------|
| `tenants` | yes      | array of tenant objects |
| `fabric`  | no       | leaf/interface profiles, VLAN pools, domains, AAEPs, interface policies (lldp/cdp/mcp/lag), interface policy groups |
| `nodes`   | no       | per-switch `id`, `sn`, `intf_profile`, `interfaces[]` (port/card → `intf_pol_group`) |

Tenant object nests: `vrfs`, `bridge_domains` (with `subnets`, `l3outs`), `filters`
(with `entries`), `contracts` (with `subjects`/filters), `application_profiles` (with
`epgs`, each with `domains`/`interfaces`/`contracts`; and `esgs`, each with a `vrf`,
member `epgs`, and `contracts`), and `l3outs` (with `external_epgs`,
`node_profiles`/routers/static routes/interface profiles).

Run `ansible-doc -t lookup ansible.utils.validate` / see `ansible.utils.jsonschema` for
how validation errors are reported.

## Requirements

- Ansible collections: `cisco.aci`, `ansible.utils`
- An inventory defining a host/group named `apic` (not included in this repo — supply
  your own, e.g. mounted alongside the intent directory)
- APIC credentials — note `wrapper_api_call.yml` has a commented-out `aci_login` anchor
  block; uncomment and wire it into the `cisco.aci.aci_rest` call (or supply
  host/username/password another way) before running against a real fabric.

## Running

```bash
ansible-playbook -i <inventory> iac.yml
```

Set `aci_cfg_directory`, `enable_fabric_role`, `enable_node_role`, `enable_tenant_role`
via `-e` to override the defaults in `iac.yml`.

## Testing

Template unit tests live under `tests/` and render `roles/tenant/templates/*.j2`
directly with Jinja2 (no Ansible/APIC required), asserting on the parsed JSON output.
The `render` fixture in `tests/conftest.py` auto-loads `roles/tenant/vars/main.yml`
(the `*_default_*` values) as base template context, so tests only need to pass the
`ap`/`epg`/etc. intent dict being tested.

Run with [`uv`](https://docs.astral.sh/uv/) — no project-wide install required:

```bash
uv run --with pytest --with jinja2 --with pyyaml pytest tests/ -v
```

## Review notes

A few things worth cleaning up or confirming before relying on this further:

1. **`ipg_access.json.j2` / `ipg_po.json.j2` always blank out STP, L2, and fabric
   hardware interface policies.** The templates render
   `infraRsStpIfPol`/`infraRsL2IfPol`/`infraRsHIfPol` children from `ipg.stp`,
   `ipg.l2`, `ipg.ll`, but `schema.json`'s `intf_policy_group` definition
   (`additionalProperties: false`) only allows `lldp`, `cdp`, `mcp`, `lag`, `aep`,
   `description`. Since those three fields can never be set, every run sends
   `tnStpIfPolName`/`tnL2IfPolName`/`tnFabricHIfPolName` as empty strings — silently
   resetting those associations on every apply, including ones configured out-of-band.
   Either add the fields to the schema or drop the children from the templates.
2. **`wrapper_api_call.yml` has drifted between roles.** In `roles/fabric` the
   `no_log: true` on the "failed call" fact is commented out, while `roles/node` and
   `roles/tenant` have it active. That means a failed fabric API call dumps its full
   payload to the console/log, but failed node/tenant calls don't — likely an oversight
   rather than an intentional inconsistency.
3. **`schema.json` requires `tenants` at the top level**, but every consumer
   (`intent.tenants | default([])` in `iac.yml`, `enable_tenant_role` toggle) treats it
   as optional. A fabric-only or node-only intent (no tenants at all) will fail schema
   validation even though the playbook itself supports that. Consider dropping
   `"required": ["tenants"]`.
4. **Small copy-paste artifacts:**
   - `roles/fabric/vars/main.yml` defines `import_dom_task: true` twice.
   - `roles/tenant/tasks/main.yml`'s tenant task has `import_tenant_task` repeated
     twice in its `when:` list.
   These are harmless (YAML/Ansible just uses the last value / a redundant condition)
   but worth trimming.
5. **`roles/node` doesn't follow the `import_<task>_task` toggle convention** used by
   `fabric`/`tenant` (`roles/node/vars/main.yml` is empty) and `main.yml` has
   commented-out includes for `leaf.yml` and `vpc_domain.yml` — standalone leaf
   management and VPC protection groups look like parked/incomplete work rather than
   deliberate scope.
6. **Pending uncommitted change:** `iac.yml` currently has `aci_cfg_directory` changed
   from `intent/` (relative) to `/config/intent/` (absolute) — consistent with reading
   intent from a mounted path (e.g. a container), but worth double-checking that's the
   intended deployment model before committing.
7. There's a sibling project, `ansible/aci_async/`, that looks like an async variant of
   this same automation (same role names) — not covered by this doc; worth checking
   whether it's meant to replace this one or is a separate experiment.
8. **`has_nested_state` rollout is now complete** across every tenant-role task that
   loops over intent objects: `epg.yml`, `ap.yml`, `tenant.yml`, `bd.yml`, `vrf.yml`,
   `contract.yml`, `filter.yml`, `l3out.yml`, `match_rule.yml`, `set_rule.yml`, and
   `route_map.yml` have all been switched from `<item>.state is defined` to the
   nested-tree check. `epg.yml`, `bd.yml`, `vrf.yml`, `contract.yml`, `filter.yml`,
   `l3out.yml`, `match_rule.yml`, `set_rule.yml`, and `route_map.yml` use it
   unrestricted, since every nested array in `epg`/`bd`/`vrf`/`contract`
   (tags, subjects, filters)/`filter` (tags, entries)/`l3out` (tags, protocols,
   external_epgs, node_profiles)/`match_rule` (tags, prefixes)/`set_rule`
   (tags, as_path)/`route_map` (tags, contexts) is something their own template
   renders. `ap.yml` and `tenant.yml` are scoped to `include_keys=['tags']` because
   `ap` nests `epgs` (handled by a separate task) and `tenant` nests virtually
   everything else, so unrestricted `has_nested_state` there
   would fire on unrelated nested changes. `l3out.yml` used to be a two-task
   `include_keys`/`exclude_keys` case (see above) before its templates were merged.
