# Protocol v1 — Asynchronous LLM macro-advisor evaluation in StarCraft II

**Status:** Active research contract (Milestone 1 / Day 1)  
**Schema / protocol version:** `protocol_v1`  
**Implements:** [`RESEARCH_ROADMAP.md`](RESEARCH_ROADMAP.md), Day 1 of [`RESEARCH_WORK_TODO.md`](RESEARCH_WORK_TODO.md)  
**Platform:** `scplay-grok-bot` (Ubuntu · Steam Proton SC2 · burnysc2)

---

## 1. Primary research question

> Does an **asynchronous LLM macro-advisor** improve strategic decision quality and instruction compliance over a fixed scripted controller, without degrading real-time responsiveness?

This protocol defines how that question will be answered in controlled pilots. It does **not** authorize claims of provider superiority without completed, gated experiments.

---

## 2. Primary hypothesis (confirmatory)

**H1:** Under matched map, seed, opponent, race, and gameplay-instruction mode, a **T2** (asynchronous macro-advisor) controller yields **higher instruction-compliance score** and **no worse** control-loop responsiveness than a **T0** (scripted) controller.

Responsiveness is operationalized as: gameplay `on_step()` never awaits network inference (nonblocking planner; see Milestone 4). Compliance is scored from validated logs using deterministic metrics (Milestone 5), not from banter quality.

### Secondary / exploratory hypotheses

- **H2 (exploratory):** T2 improves time-to-counter and defensive-episode outcomes in `defense_only` relative to T0.
- **H3 (exploratory):** T1 (banter-only) may change chat metrics without changing strategic compliance relative to T0.
- **H4 (exploratory):** Provider A vs provider B differ on T2 endpoints under identical prompts and seeds.

H3 and H4 are **not** confirmatory under Protocol v1 until the Day 28 readiness gate passes and sample sizes are pre-registered in a pilot schedule.

---

## 3. Controller tiers (T0 / T1 / T2) — keep distinct

| Tier | Name | What the LLM does | What controls units |
|------|------|-------------------|---------------------|
| **T0** | Scripted | Nothing | Fixed `PlaybotSparBot` (and mode behavior flags) only |
| **T1** | Asynchronous banter | Optional chat lines / color commentary from an LLM | **Same scripted controller as T0** |
| **T2** | Asynchronous macro-advisor | Proposes bounded macro-actions on a background queue | Scripted micro + **validated** macro targets when accepted |

### Critical interpretation rule (acceptance criterion)

**T1 banter must never be interpreted as strategic model control.**

- A T1 match may show richer chat and still be strategically identical to T0.
- Chat quality, wit, or “sounding strategic” is **not** evidence that the model directed builds, attacks, or expansions.
- Confirmatory claims about LLM strategy require **T2** (or later) with logged `llm_decision` traces: proposal → validation → applied/rejected/expired.
- Leaderboards and papers using this protocol must label T1 as **language-only ablation**, not as an LLM policy.

---

## 4. Primary endpoint

**Primary endpoint:** Match-level **instruction-compliance score** (0–2 or continuous equivalent defined in the Day 22 rubric), derived from validated `play.jsonl` / mode rules, compared **T2 vs T0** within paired seeds.

**Co-primary constraint (safety):** No increase in control-loop blocking attributable to LLM I/O (T2 must remain nonblocking; measured in Day 16/21 timing metrics).

---

## 5. Exploratory metrics

| Metric | Role |
|--------|------|
| Time-to-counter / defensive-episode outcome | Adaptation |
| Survival time / townhall loss timeline | Defense integrity |
| Economy and army efficiency snapshots | Coherence |
| Accepted-action rate, stale-response rate (T2 only) | Advisor utility |
| Chat uniqueness / situational relevance | Language (esp. T1) |
| Outcome (W/L) and duration | Context only in v1 pilots |
| Human UX ratings (separate study) | Not mixed into autonomous leaderboard |

LLM-as-judge scores are exploratory and must be blinded and provenance-logged (Day 23); they do not replace deterministic compliance metrics.

---

## 6. Unit of analysis

- **Primary unit:** One **match / run** with a unique `run_id` (today’s `match_id` until live logger migration; contract in [`schemas/v2/`](../schemas/v2/) / [LOG_SCHEMA.md](LOG_SCHEMA.md)).
- **Pairing unit:** Same map + seed + opponent config + mode + chaos flag across controller tiers.
- **Reporting unit:** Condition cells with **N**, exclusions, and uncertainty — never a rank without sample size.

Human sessions are a **separate** unit of analysis (participant × session) and must not be pooled into the autonomous-strategy leaderboard.

---

## 7. Experimental conditions (Protocol v1)

Machine-readable validation of these fields is implemented in the [condition registry](CONDITION_REGISTRY.md) (`scplay/conditions.py`).

### Required fixed factors for confirmatory T0/T2 contrasts

- Gameplay instruction mode (e.g. `defense_only` or `default`) identical within a pair
- Map identical within a pair
- Chaos **off** for confirmatory cells (chaos allowed only in exploratory / demo cells and must be labeled)
- Realtime policy documented (`realtime` true/false); headless/non-realtime preferred for autonomous pilots
- Race matchup documented (v1 default: Human or AI Terran vs Zerg bot, or bot-vs-built-in AI as in Day 26)

### Allowed controller levels

- T0 scripted  
- T1 banter-only (OpenAI or Claude or other) — **ablation / UX only**  
- T2 macro model A / T2 macro model B — strategy evaluation  

### Explicitly out of scope for Protocol v1 confirmatory analysis

- Full raw-action-space LLM control  
- Multi-agent public ladders  
- Fine-tuning claims from unreleased datasets  
- Provider superiority claims based solely on T1  

---

## 8. Exclusions

Exclude a run from confirmatory datasets when any of the following hold:

1. Run status is `aborted` or `crashed` (once Day 9 exists); incomplete runs excluded by default.
2. Chaos enabled in a cell labeled confirmatory.
3. Mode prompt / behavior flag mismatch or unknown mode.
4. Missing required artifacts (manifest, chat, play, or replay when required).
5. Schema validation failure (schema v2+).
6. Consent tier does not allow the intended analysis/export.
7. T1 run mistakenly labeled as T2 (or vice versa) in the condition registry.
8. Evidence of blocking LLM calls inside the control loop (fails timing policy).
9. Privacy-unsafe export contents (secrets, absolute personal paths, unredacted private human chat).

Exploratory analyses may include excluded runs only with explicit disclosure.

---

## 9. Provenance and reproducibility requirements

Every confirmatory run should eventually record (Milestone 1–2):

- Git SHA and dirty flag  
- Python / burnysc2 / SC2 version identifiers  
- Map identity and checksum when available  
- Seed, controller tier (T0/T1/T2), prompt hash, provider/model snapshot  
- Timing policy (nonblocking)  

Day 4 manifests (`scplay.run_manifest`) provide `config_fingerprint`; until live MatchLogger emits v2, use builder output or best-effort `match.json` notes and never invent missing fields.

---

## 10. Privacy, consent, and licensing

- Do not publish raw human chat without consent; prefer `private` / `aggregate_only` / `public_redacted` tiers (Day 12).
- Never commit API keys or credentials.
- Attribute Blizzard’s `s2client-proto` under its MIT `PROTOCOL_LICENSE`; treat game assets, maps, clients, and replay packs as separately licensed (AI/ML license for Blizzard packs).
- See `THIRD_PARTY_NOTICES.md` in the repository root.

---

## 11. Reporting rules

1. Distinguish **T0 / T1 / T2** in every table and figure.  
2. Never describe T1 results as “LLM strategy.”  
3. Do not claim provider superiority without controlled evidence meeting this protocol’s gates.  
4. Always report N, exclusions, and uncertainty with any ranking.  
5. Fail closed: invalid, stale, or policy-violating model actions are rejected, not silently applied (Day 18–19).  

---

## 12. Reviewer checklist

Use [`PROTOCOL_V1_REVIEW_CHECKLIST.md`](PROTOCOL_V1_REVIEW_CHECKLIST.md) before treating any result as Protocol v1 confirmatory.

---

## 13. Change control

Amendments that change endpoints, tiers, or exclusions require a new protocol version (`PROTOCOL_V2.md`) or a dated amendment section. Editorial clarifications may land in-place with a changelog note below.

### Changelog

| Date | Change |
|------|--------|
| 2026-09-15 | Initial Protocol v1 (Day 1 feature). |
| 2026-09-15 | Linked Day 2 condition registry (`CONDITION_REGISTRY.md`). |
