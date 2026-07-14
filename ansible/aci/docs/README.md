# ACI IaC — Object Reference

One markdown file per Ansible task, documenting the ACI object it manipulates
(MIT class, parent/child relationships, input attributes and defaults, and a
config example). Organized by role, mirroring `roles/*/tasks/`.

**Adding or editing a doc?** See [STYLE_GUIDE.md](STYLE_GUIDE.md) for the
required structure, table conventions, and how to verify a doc against
`schema.json`/the Jinja templates before considering it done.

## Tenant role (`roles/tenant`)

- [Tenant](tenant/tenant.md) — `fvTenant`
- [Application Profile](tenant/ap.md) — `fvAp`
- [Endpoint Group (EPG)](tenant/epg.md) — `fvAEPg`
- [Endpoint Security Group (ESG)](tenant/esg.md) — `fvESg`
- [Bridge Domain](tenant/bd.md) — `fvBD`
- [VRF](tenant/vrf.md) — `fvCtx`
- [Contract](tenant/contract.md) — `vzBrCP`
- [Filter](tenant/filter.md) — `vzFilter`
- [L3Out](tenant/l3out.md) — `l3extOut`
- [Match Rule](tenant/match_rule.md) — `rtctrlSubjP`
- [Set Rule](tenant/set_rule.md) — `rtctrlAttrP`
- [Route Map](tenant/route_map.md) — `rtctrlProfile`
- [Multicast Route Map](tenant/mcast_route_map.md) — `pimRouteMapPol`

## Fabric role (`roles/fabric`)

- [VLAN Pool](fabric/vlan_pool.md) — `fvnsVlanInstP`
- [Domain](fabric/domain.md) — `physDomP` / `l3extDomP`
- [AAEP](fabric/aaep.md) — `infraAttEntityP`
- [Interface Policies](fabric/intf_pol.md) — `cdpIfPol` / `lldpIfPol` / `mcpIfPol` / `lacpLagPol` / `fabricHIfPol`
- [Interface Policy Group](fabric/ipg.md) — `infraAccPortGrp` / `infraAccBndlGrp`
- [Leaf Profile](fabric/leaf_prof.md) — `infraNodeP`
- [Leaf Interface Profile](fabric/leaf_intf_prof.md) — `infraAccPortP`
- [Interface Selector](fabric/intf_selector.md) — `infraHPortS`
- [VPC Protection Group](fabric/vpc_domain.md) — `fabricExplicitGEp`

## Node role (`roles/node`)

- [Interface Selector (per-node)](node/intf.md) — `infraHPortS`
- [Node Registration](node/register.md) — `fabricNodeIdentP`
- [Node Decommission](node/decommission.md) — `fabricRsDecommissionNode`
