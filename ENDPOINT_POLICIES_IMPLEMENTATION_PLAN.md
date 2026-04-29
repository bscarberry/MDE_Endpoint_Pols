# Endpoint Policies Implementation & Revision Plan

## Objective
Refactor the endpoint policy experience so the app only shows policies that appear in:

**Microsoft Defender > Endpoint > Configuration management > Endpoint security policies**

and specifically:
- includes **App Control for Business** policies,
- shows assignment target as **Group / All Devices / All Users / None**,
- surfaces settings in the UX (readable tables/sections, not raw JSON blobs).

---

## 1) Current-state assessment (what to fix first)

### Backend data scope issues
- `get_endpoint_security_policies()` currently combines policies from:
  - `deviceConfigurations`,
  - `intents` (beta),
  - `configurationPolicies` (beta).
- `get_all_policies_summary()` also pulls compliance/configuration/scripts and exposes them to the front end.

**Impact:** The UI currently displays many policies that are not strictly in Endpoint security policies.

### Assignment normalization gaps
- Assignment metadata is partially normalized into `assignmentCount` + `assignmentGroups`.
- Assignment target semantics are inferred late and inconsistently in UI.

**Impact:** The UX shows "N groups" instead of explicit target types (Group/All Devices/All Users/None).

### Policy settings UX gap
- Policy details modal falls back to raw `JSON.stringify(policy, null, 2)`.

**Impact:** Endpoint security settings are hard to read and difficult to compare.

---

## 2) Target architecture (high level)

### A. Create a dedicated Endpoint Security policy pipeline
Implement a dedicated backend path that returns only endpoint security policies:

- New GraphClient methods (or a consolidated selector):
  1. Fetch Endpoint Security templates/families and active policies tied to those templates.
  2. Include policy types that map to Endpoint Security in Intune UI, including **App Control for Business**.
  3. Exclude non-endpoint-security configuration/compliance/script artifacts.

- New PolicyManager contract:
  - `get_endpoint_security_policies_only()` (list)
  - `get_endpoint_security_policy_details(policy_id, policy_source)` (details + settings + assignments)

### B. Normalize assignment model in backend
For each policy, produce normalized assignment shape:

```json
{
  "assignmentSummary": "Group | All Devices | All Users | None",
  "assignmentTargets": [
    { "type": "group", "groupId": "...", "groupName": "..." },
    { "type": "allDevices" },
    { "type": "allUsers" }
  ]
}
```

Rules:
- If zero targets: `None`
- Any group target only: `Group`
- Any all-devices target present: include `All Devices`
- Any all-users target present: include `All Users`
- If mixed targets, return combined concise summary (e.g., `Group + All Devices`).

### C. Transform settings into UI-ready view models
Add backend transformation layer per policy source:

- `intents` settings -> grouped by category and setting display name/value.
- `configurationPolicies` settings -> flattened rows from setting instances.
- `deviceConfigurations` endpoint security payload -> curated key/value rows.

Return:

```json
{
  "settingsSections": [
    {
      "title": "Category Name",
      "rows": [
        { "name": "Setting", "value": "Enabled", "state": "configured" }
      ]
    }
  ]
}
```

---

## 3) Detailed implementation plan

## Phase 1 — Data scoping hardening
1. Add source filters that strictly identify Endpoint Security policies.
2. Add explicit inclusion logic for App Control for Business.
3. Stop mixing unrelated policy families into endpoint policy responses.
4. Keep old endpoints temporarily for compatibility, but add a new endpoint-first API path.

**Deliverable:** `/api/policies` (or a new `/api/endpoint-security/policies`) returns only Endpoint Security policies.

## Phase 2 — Assignment normalization
1. Introduce utility to parse `assignment.target.@odata.type` and map target types.
2. Resolve group IDs to names in batch as already done, but preserve target type metadata.
3. Add `assignmentSummary` and `assignmentTargets` to every policy in list + details response.

**Deliverable:** Table-ready assignment field with deterministic values and optional detailed chips/list.

## Phase 3 — Settings extraction and UX model
1. Implement source-specific parsers:
   - intents parser,
   - configurationPolicies parser,
   - deviceConfigurations parser.
2. Add a normalized `settingsSections` model.
3. Add defensive truncation/formatting for long values.

**Deliverable:** No raw JSON as primary settings view.

## Phase 4 — Front-end refactor (endpoint policy section)
1. Replace mixed policy list renderers with endpoint-security-only renderer.
2. Update table columns to include:
   - Policy name,
   - Endpoint security category,
   - Platform,
   - Assignment (Group/All Devices/All Users/None),
   - Last modified.
3. Add policy details modal sections:
   - Overview,
   - Assignments,
   - Settings sections (accordion/table).
4. Keep raw JSON behind optional “Debug payload” disclosure only.

**Deliverable:** Human-readable settings and assignment UX.

## Phase 5 — Validation and regression safety
1. Unit tests for:
   - endpoint policy classification,
   - App Control inclusion,
   - assignment normalization,
   - settings parsers.
2. Integration smoke tests for list + details endpoints.
3. Front-end checks for filtering/sorting and details rendering.

**Deliverable:** predictable behavior with coverage on critical transforms.

---

## 4) Acceptance criteria mapped to requirements

1. **Only show policies available in Endpoint Security Policies section**
   - Pass when endpoint list response excludes compliance policies, generic config profiles, and scripts.

2. **Include App Control for Business policies**
   - Pass when App Control for Business templates/policies are present and correctly categorized.

3. **Show assignment: Group, All Devices, All users, or none**
   - Pass when each policy has explicit assignmentSummary and details reflect exact targets.

4. **Show policy settings in UX, not raw JSON**
   - Pass when policy details render settings as labeled rows grouped by sections.

---

## 5) Proposed execution order for this repo

1. Backend classification + endpoint scoping first (GraphClient + PolicyManager).
2. Backend assignment normalization.
3. Backend settings transformation model.
4. Front-end table + details modal updates.
5. Tests and cleanup.

This order minimizes UI churn and lets front-end consume a stable contract.
