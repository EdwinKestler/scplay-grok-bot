# Protocol v1 — reviewer checklist

Use before accepting a result as **Protocol v1 confirmatory**.

## Document integrity

- [ ] `docs/PROTOCOL_V1.md` is the cited contract version (`protocol_v1`).
- [ ] Primary hypothesis H1 is stated (T2 vs T0 on compliance + nonblocking constraint).
- [ ] T0, T1, and T2 are defined in a table and kept distinct.
- [ ] **Explicit rule present:** T1 banter cannot be interpreted as strategic model control.
- [ ] Primary endpoint, exploratory metrics, unit of analysis, and exclusions are listed.
- [ ] Chaos confirmatory exclusion is stated.
- [ ] Privacy / licensing constraints are referenced.

## Result labeling

- [ ] Controller tier labeled T0, T1, or T2 (not ambiguous “with LLM”).
- [ ] If T1: results framed as language/UX ablation only.
- [ ] If T2: decision traces (proposal → validation → outcome) available or deferred with disclosure.
- [ ] N, exclusions, and uncertainty reported; no rank without sample size.
- [ ] No provider-superiority claim without gated evidence.

## Artifact safety

- [ ] No API keys or secrets in artifacts.
- [ ] No unredacted private human chat in public materials.
- [ ] No unnecessary absolute personal host paths in public exports.

## Sign-off

| Role | Name | Date | Pass? |
|------|------|------|-------|
| Author | | | |
| Reviewer | | | |
