# How to Write / Maintain These Docs

This is the authoring guide for `docs/`. It captures the conventions the
existing docs already follow, so new/edited docs stay consistent and don't
silently drift out of sync with `schema.json` and the Jinja templates (the
class of bug this guide exists to prevent — see "Verification" below).

## Scope and file layout

- **One markdown file per Ansible task file** (`roles/*/tasks/*.yml`), not
  per ACI MIT class. If a single task file manages several independent
  sibling MO types (e.g. `intf_pol.yml` renders `cdpIfPol`, `lldpIfPol`,
  `mcpIfPol`, `lacpLagPol`, `fabricHIfPol`), document all of them in that one
  file, each under its own `## <Name>` section — don't split into multiple
  files, and don't merge multiple unrelated task files into one doc.
- **Don't document** `wrapper_api_call.yml` or `main.yml` — they're plumbing,
  not ACI objects.
- **Location mirrors the role**: `docs/tenant/`, `docs/fabric/`, `docs/node/`,
  matching `roles/tenant/tasks/`, `roles/fabric/tasks/`, `roles/node/tasks/`.
- **`docs/README.md` is an index only** — one line per doc
  (`- [Title](path.md) — \`AciClass\``), grouped by role. Never put real
  content there; if you add a doc, add its index line.

## Required sections, in order

1. **H1 title** — human-readable object name (e.g. "Bridge Domain", not "BD").
2. **Metadata lines** (bold labels, one per line):
   ```
   **Task file:** `roles/<role>/tasks/<file>.yml`
   **Template:** `roles/<role>/templates/<file>.json.j2`
   **ACI MIT class:** `<AciClassName>`
   ```
   Use `**Templates:**`/`**ACI MIT classes:**` (plural) and list all of them
   when a task uses more than one template/class.
3. **`## Description`** — a few sentences: what the object is for, and any
   non-obvious behavior (e.g. "the first subnet is always the preferred
   gateway", "posted as a child of a singleton this role doesn't manage").
4. **`## Object Relationships`** — a `mermaid graph TD` showing parent → this
   object → its children. Use a **solid arrow** (`-->`) for a child rendered
   by *this same template*, and a **dashed arrow** (`-.->`) plus a caption
   line ("Dashed edges are managed by their own separate tasks/docs") for a
   relationship that's schema-adjacent but actually handled by a different
   task (e.g. `tenant.md`'s `vrfs`/`bridge_domains`/etc., `ap.md`'s
   `epgs`/`esgs`).
5. **`## Attributes`** (or `## <Name>` per sibling object if the file covers
   several — see `intf_pol.md`/`l3out.md`) — see the table conventions below.
6. **`## Example`** — one realistic YAML snippet, rooted at the actual intent
   key (`tenants:`, `fabric:`, `nodes:`).

## Attribute tables

**Every table gets a one-line description directly above it** (after the
heading, before the table, no blank-line-separated paragraph needed): `` Root
object: `AciClass` `` for the top-level `## Attributes` table, `` Child
object: `AciClass` `` for a `###` child table (see "Child sections" below).
Add a second sentence when there's a genuinely non-obvious behavior worth
calling out (e.g. `bd.md`'s Subnets note that the first entry is always the
preferred gateway) — otherwise the one-liner is enough. Don't skip this even
when the class already appears in the heading text (e.g. `intf_pol.md`'s
per-policy `## Attributes — CDP (\`cdpIfPol\`)` headings still get their own
`Root object: \`cdpIfPol\`` line) — consistency across every table matters
more than avoiding the small repetition.

Exactly these five columns, in this order:

| Attribute | ACI Attribute | Required | Expected Value | Default |
|---|---|---|---|---|

- **Attribute**: the YAML config field name, backticked. **One row per
  field, always** — never combine multiple distinct config attributes into
  one row (e.g. `` `agg_export` / `agg_inport` / `agg_shared` ``), even if
  they share the exact same mapping/behavior. This was a real readability
  complaint — see git history on `l3out.md` for the before/after.
- **ACI Attribute**: the literal MO attribute this maps to, or one of:
  - `child `X.attr`` / `grandchild `X.attr`` — nested under a child/grandchild MO.
  - `folded into `Y` (`flag-value`)` — one of several booleans combined into
    a single flag-list attribute (e.g. `ctrl`).
  - `selects `X` vs `Y` (not a literal attribute)` — a `type`-style
    discriminator field that picks which child MO class to render.
  - `used to build `tDn` (...)` — contributes to a composed DN, not a
    standalone attribute.
  - `see [Label](#anchor)` — for array/object attributes (see "Child
    sections" below).
  - **Never restate possible values here** (no `` (`created,modified`/`deleted`) ``,
    no `` (`yes`/`no`) ``, no `` — `true`→ACI `on` `` etc.). That information
    belongs only in the Expected Value column — it caused visible
    duplication/clutter when mixed into this column.
- **Required**: `Yes`, `No`, `Yes, if <condition>`, or
  `Conditional (when <condition>)` — read off `schema.json`'s `required`
  array (and any `if`/`then` constraint) for that def, not guessed from the
  template.
- **Expected Value**: type / enum / format. Do **not** append `(required)`
  here — that's the Required column's job now.
- **Default**: the literal default (matching the `*_default_*` var in
  `vars/main.yml`), or `(omitted if unset)` / `(no binding if unset)` if
  there truly is none.

### Child sections (arrays and nested objects)

Any attribute whose value is an array or a nested object gets **its own**
`###` subsection with its own table — never inline its fields into the
parent table (this was the single most common defect found when auditing
these docs; see "Verification" below).

```markdown
| `subnets` | see [Subnets](#subnets) | No | array | `[]` |
...
### Subnets

Child object: `fvSubnet`

| Attribute | ACI Attribute | Required | Expected Value | Default |
|---|---|---|---|---|
| `ip` | `ip` | Yes | string | — |
```

- Start every child subsection with `Child object: \`AciClass\`` (one line,
  then a blank line, then the table).
- A shape reused at multiple nesting levels (`tags` → `tagAnnotation` is the
  universal example, present in nearly every doc) gets **one** subsection,
  referenced from every table that uses it — don't duplicate it per level.
- **Anchor links must resolve.** `[Label](#anchor)` requires `anchor` to be
  the actual slug of a heading in the same file (lowercase, spaces → hyphens,
  punctuation stripped). Keep headings for anything you intend to link to
  in **plain words** — no backticks, brackets, or parens — so the slug is
  unambiguous (`### Subnets`, not `### \`fvSubnet[]\` (\`l3extSubnet\`)`).
  If you want to name the ACI class in the heading area, put it as its own
  line right under the heading instead: `ACI MIT class: \`l3extInstP\`` (see
  `l3out.md`'s `## External EPGs` / `## Node Profiles` / `## Interface
  Profiles` for the pattern used when a file has several top-level sibling
  objects). If you can't make a clean anchor, don't force one — reference it
  in plain prose instead (`see "Foo" section below`) rather than a broken link.

## The `state` default-caveat callout

Almost every task gates on the `has_nested_state` filter
(`plugins/state_helpers.py`) rather than a plain `<item>.state is defined`
check. Whenever that's true for the task you're documenting:

1. Mark the `state` row's Default cell `` present (see caveat below) ``.
2. Immediately after the root table (before the first `###` child section),
   add:

   ```markdown
   > **`state` default caveat:** `present` is only the default *if the task actually
   > runs*. `roles/<role>/tasks/<file>.yml` gates on `<item> | has_nested_state`,
   > which is `True` only when a `state` key exists *somewhere* in the <object>'s
   > tree — on the <object> itself, or on any <list the actual nested fields that
   > count>. A(n) <object> with no `state` key anywhere is skipped entirely: not
   > created, updated, or touched.
   ```

   Tailor the "nested fields that count" list to what `has_nested_state`
   actually recurses into for that call:
   - **No `include_keys`/`exclude_keys`**: it recurses into *every* nested
     field, including ones handled by an entirely separate task if nothing
     excludes them (see `leaf_intf_prof.md`'s note about `interface_selectors`
     triggering a harmless no-op run of that task).
   - **`include_keys=[...]`**: only those top-level keys count — call out
     explicitly which sibling fields do *not* count and why (see
     `tenant.md`/`ap.md`).
   - **Compound `when:` with a parent-state check** (e.g. `epg.yml`/`esg.yml`
     gating on `ap.state`, `intf_selector.yml` gating on
     `leaf_intf_prof.state`): document both conditions and that deleting the
     parent skips this task even if the child has its own nested state.

For the few tasks that use a plain `state is defined`/`== 'present'`/`'absent'`
check instead (currently `register.yml`, `decommission.yml`) — **don't** add
this callout; instead state the actual gating condition directly (see how
`register.md`/`decommission.md` phrase "task only fires on `present`/`absent`").

## Verification (do this before considering an edit done)

Every real bug found while building these docs was caught by comparing the
doc against **`schema.json`** and the **Jinja template** directly, not by
proofreading the markdown in isolation. Concretely:

1. **Property completeness**: for the object's schema `$defs` entry, every
   property must appear in the doc as either its own row or a
   `see [X](#anchor)` reference row — in the *root* table AND in every
   nested `###` table. A property that's documented in a sibling section but
   never referenced from its actual parent table is the same bug as one
   that's missing outright (this happened three times in `l3out.md`:
   `external_epgs`/`node_profiles` missing from the root table,
   `interface_profiles` missing from the `node_profiles` table, and
   `l3extLIfP`'s own `name`/`state` missing entirely from what became the
   `interface_profiles` table).
2. **Template accuracy**: don't infer the "ACI Attribute" mapping or
   "Default" value from the schema alone — read the actual `.json.j2` and
   confirm what it renders. Several `state` rows were missing because a
   quick schema-only pass doesn't reveal that, say, `bgpPeerP` and
   `bgpRsPeerToProfile` both independently render their own `status`.
3. **Table structure**: after editing, check every table's row has the same
   number of *unescaped* pipes as its header — a naive `split('|')` will
   miscount cells containing an escaped alternator like `` `a` \| `b` ``.
   A quick way to check a single file:
   ```bash
   python3 -c "
   import re
   lines = [l.rstrip() for l in open('docs/path/to/file.md')]
   sep = re.compile(r'^\|(?:\s*-+\s*\|)+\$')
   i, n = 0, len(lines)
   while i < n:
       if lines[i].startswith('|') and i+1 < n and sep.match(lines[i+1]):
           hc = len(re.findall(r'(?<!\\\\)\|', lines[i])) - 1
           j = i + 2
           while j < n and lines[j].startswith('|'):
               c = len(re.findall(r'(?<!\\\\)\|', lines[j])) - 1
               if c != hc: print('MISMATCH', j+1, lines[j])
               j += 1
           i = j
       else:
           i += 1
   "
   ```
4. **Anchors resolve**: every `#anchor` in a `see [Label](#anchor)` must
   match a real heading's slug in the same file (see the anchor-hygiene
   rule above — this is trivial to satisfy if headings stay plain).
