# Research work TODO: one closed feature per development day

**Owner:** Grok Bot  
**Objective:** Turn `scplay-grok-bot` from a working gameplay prototype into a reproducible research instrument for evaluating asynchronous LLM macro-strategy in StarCraft II.  
**Cadence:** Close at least one independently testable feature on every development day.  
**Plan length:** 30 development days (six five-day milestones).

This backlog implements the research direction in [`RESEARCH_ROADMAP.md`](RESEARCH_ROADMAP.md). The initial research question is:

> Does an asynchronous LLM macro-advisor improve strategic decision quality and instruction compliance over a fixed scripted controller, without degrading real-time responsiveness?

## Daily definition of done

A daily feature may be marked complete only when all applicable items are true:

- [ ] The feature has one clearly described user or research outcome.
- [ ] Implementation, tests, and documentation are complete in the same change.
- [ ] Relevant automated checks pass locally.
- [ ] A small evidence artifact is recorded: test output, sample fixture, screenshot, or validated example run.
- [ ] No API key, raw private chat, personal path, or other secret is committed.
- [ ] Existing unrelated work remains untouched.
- [ ] The checkbox for that day is updated with the completion date and commit or PR reference.

Use this completion format:

```text
Completed: YYYY-MM-DD | Commit/PR: <reference> | Evidence: <test, fixture, or artifact>
```

If the planned item is blocked, close another ready feature from the same milestone. A planning note, partial implementation, or failing test does not count as the day's closed feature.

## Milestone 1 — Freeze the research contract

### Day 1 — Versioned research protocol

- [x] Add `docs/PROTOCOL_V1.md` defining the primary hypothesis, primary endpoint, exploratory metrics, unit of analysis, exclusions, and T0/T1/T2 conditions.
- **Acceptance:** The protocol clearly states that T1 banter cannot be interpreted as strategic model control.
- **Evidence:** Documentation link check and reviewer checklist.
- Completed: 2026-09-14 | Commit/PR: 4e73338 | Evidence: tests/test_protocol_v1.py (9 passed); evidence/day01_protocol_v1/; docs/PROTOCOL_V1_REVIEW_CHECKLIST.md

### Day 2 — Condition registry

- [x] Add a machine-readable registry for experimental conditions, including controller tier, map, opponent, mode, chaos, real-time setting, and decision cadence.
- **Acceptance:** Invalid or ambiguous combinations—especially chaos mixed with confirmatory matches—are rejected.
- **Evidence:** Passing valid and invalid registry fixtures.
- Completed: 2026-09-15 | Commit/PR: pending authorization | Evidence: tests/test_condition_registry.py; tests/fixtures/conditions/; evidence/day02_condition_registry/

### Day 3 — Log schema v2

- [x] Define versioned JSON Schemas for the run manifest, gameplay events, chat events, snapshots, and LLM decisions.
- **Acceptance:** Every record has `schema_version`, `run_id`, an ordered sequence identifier, game-loop time, source, and event type.
- **Evidence:** All committed example records validate against their schemas.
- Completed: 2026-09-16 | Commit/PR: 8d841e7 | Evidence: tests/test_schema_v2.py; tests/fixtures/schema_v2/; schemas/v2/; evidence/day03_log_schema_v2/

### Day 4 — Reproducible run manifest

- [x] Generate a per-run manifest containing Git SHA/dirty state, SC2 and Python package versions, map checksum, seed, controller version, prompt hash, provider/model snapshot, parameters, and timing policy.
- **Acceptance:** Two launches with the same configuration produce the same configuration fingerprint while retaining unique run IDs.
- **Evidence:** Automated manifest unit test and example manifest.
- Completed: 2026-09-17 | Commit/PR: (filled after push) | Evidence: tests/test_run_manifest.py; tests/fixtures/manifests/example_run_manifest.json; evidence/day04_run_manifest/

### Day 5 — Repository research validator

- [ ] Add one local command that validates configuration, schemas, manifests, JSONL records, privacy rules, and required artifacts.
- **Acceptance:** It exits nonzero with actionable errors for malformed, incomplete, or privacy-unsafe fixtures.
- **Evidence:** Clean validation output plus at least one expected-failure test.

## Milestone 2 — Repair telemetry integrity

### Day 6 — Correct game-loop and iteration capture

- [ ] Persist the actual `on_step(iteration)` value and SC2 game-loop value in snapshots and events.
- **Acceptance:** A fixture or controlled run contains monotonically increasing, nonzero values after startup.
- **Evidence:** Regression test covering the previous all-zero behavior.

### Day 7 — Source-aware chat deduplication

- [ ] Give outbound bot messages stable IDs and reconcile their SC2 loopback records without deleting genuine repeated human messages.
- **Acceptance:** A bot message appears once in the analytical transcript while retaining source provenance.
- **Evidence:** Tests for bot loopback, legitimate repetition, and two speakers sending identical text.

### Day 8 — Defensive episode logging

- [ ] Replace timer-window `defense_counter` spam with explicit episode start, response, update, and end transitions.
- **Acceptance:** One threat produces one correlated episode with duration and outcome, not repeated events every frame.
- **Evidence:** State-machine tests using a simulated threat timeline.

### Day 9 — Crash-safe match finalization

- [ ] Record `complete`, `aborted`, or `crashed` status and safely finalize/index partial runs after interrupts or exceptions.
- **Acceptance:** Interrupted runs remain discoverable but are excluded from confirmatory datasets by default.
- **Evidence:** Forced-exception test with a valid partial manifest.

### Day 10 — Replay capture and artifact hashing

- [ ] Save the SC2 replay for each eligible match and hash the replay, manifest, chat, and play logs.
- **Acceptance:** The validator detects a changed or missing artifact.
- **Evidence:** Replay-path fixture and tamper-detection test; a real replay is optional for offline CI.

## Milestone 3 — Privacy and reproducible data products

### Day 11 — Portable path handling

- [ ] Store repository-relative or logical artifact paths instead of absolute host paths in manifests and indexes.
- **Acceptance:** Exported fixtures contain no home-directory or machine-specific path.
- **Evidence:** Path-leak regression test.

### Day 12 — Consent and publication tiers

- [ ] Add `private`, `aggregate_only`, and `public_redacted` consent states with pseudonymous participant IDs.
- **Acceptance:** Runs without explicit publication consent cannot enter a public export.
- **Evidence:** Export-policy tests for all three tiers.

### Day 13 — Deterministic chat redaction

- [ ] Implement a reviewable redaction pipeline for human chat and sensitive local metadata.
- **Acceptance:** Public exports retain analytical structure while removing configured sensitive fields and text patterns.
- **Evidence:** Golden input/output fixtures; original private logs remain unchanged.

### Day 14 — Dataset exporter v2

- [ ] Export validated match-level bundles that join records to their manifest, preserve run boundaries, exclude incomplete runs by default, and create train/validation/test splits by match.
- **Acceptance:** No event from one match can leak across splits through line-level randomization.
- **Evidence:** Deterministic export test over several fixtures.

### Day 15 — Frozen dataset manifest

- [ ] Generate a dataset manifest containing included run IDs, selection criteria, schema versions, file hashes, creation time, and license/consent status.
- **Acceptance:** Rebuilding from unchanged inputs produces the same content fingerprint.
- **Evidence:** Reproducibility and tamper-detection tests.

## Milestone 4 — Nonblocking LLM macro-advisor

### Day 16 — Asynchronous planner interface

- [ ] Introduce a provider-independent background planner queue so gameplay never awaits a network request inside `on_step()`.
- **Acceptance:** A deliberately slow mock provider does not block control-loop iterations.
- **Evidence:** Timing test with a slow provider fixture.

### Day 17 — Temporal observation summarizer

- [ ] Produce bounded single-frame and multi-frame summaries containing economy, army, tech, threats, recent actions, uncertainty, and current instruction mode.
- **Acceptance:** Identical state histories produce identical summaries within a fixed token/character budget.
- **Evidence:** Golden summary fixtures.

### Day 18 — Structured macro-action contract

- [ ] Define bounded actions for economy priority, unit mix, expansion, technology, defense posture, attack posture, horizon, confidence, and rationale.
- **Acceptance:** Provider output is parsed into a typed contract; unknown actions and out-of-range values fail closed.
- **Evidence:** Parser tests covering valid, malformed, adversarial, and extra-field responses.

### Day 19 — Action validator, expiry, and fallback

- [ ] Validate actions against mode rules and game state, attach a TTL, drop stale responses, and fall back to the scripted controller.
- **Acceptance:** `defense_only` cannot authorize prohibited movement, and no late decision is applied.
- **Evidence:** Policy and stale-response tests.

### Day 20 — Deterministic macro executor and decision trace

- [ ] Translate accepted macro-actions into deterministic controller targets and log observation hash, prompt hash, response ID, latency, usage, proposed action, validation result, applied time, and expiry.
- **Acceptance:** Each proposal is traceable to exactly one applied, rejected, expired, or failed outcome.
- **Evidence:** End-to-end mocked decision trace test.

## Milestone 5 — Measurement and evaluation

### Day 21 — Deterministic gameplay metrics

- [ ] Compute instruction violations, time-to-counter, episode outcome, survival time, economy/army efficiency, accepted-action rate, stale-response rate, and control-loop timing.
- **Acceptance:** Metrics are derived from validated logs without an LLM judge.
- **Evidence:** Golden metric fixtures with hand-calculated expected values.

### Day 22 — Versioned scoring rubric

- [ ] Replace free-form chat critique with a versioned structured rubric covering compliance, adaptation, coherence, language-action alignment, outcome, and uncertainty.
- **Acceptance:** Every score cites event or replay evidence and distinguishes unavailable evidence from a zero score.
- **Evidence:** Schema validation and scored example fixture.

### Day 23 — Blinded evaluator adapter

- [ ] Add evaluator provenance, prompt/input hashes, model snapshot, parameters, token usage, and blinded condition labels.
- **Acceptance:** The evaluator cannot infer the tested provider from ordinary condition metadata, and outputs are reproducible artifacts.
- **Evidence:** Metadata-redaction and provenance tests using mock providers.

### Day 24 — Human annotation workflow

- [ ] Add a lightweight annotation template and agreement report for double-scored samples.
- **Acceptance:** The workflow calculates an appropriate agreement statistic and records adjudication without overwriting original annotations.
- **Evidence:** Two-annotator sample and generated agreement report.

### Day 25 — Research report generator

- [ ] Generate tables with sample counts, exclusions, effect sizes, confidence intervals, latency distributions, and incomplete-run disclosures.
- **Acceptance:** The report never displays a rank without sample size and uncertainty.
- **Evidence:** Deterministic report snapshot generated from fixture data.

## Milestone 6 — Controlled pilot and public evidence

### Day 26 — Headless bot-versus-AI runner

- [ ] Add a non-realtime runner for scripted and macro-advisor conditions against the same built-in AI configuration.
- **Acceptance:** It records the same schema-v2 artifacts as interactive matches and requires no human input.
- **Evidence:** Offline runner test plus one locally validated smoke run when SC2 is available.

### Day 27 — Paired-seed experiment scheduler

- [ ] Schedule T0, T1, and T2 conditions in randomized order while pairing map, seed, race, and opponent difficulty.
- **Acceptance:** A generated schedule is balanced, deterministic from its scheduler seed, and resumable without duplicating completed runs.
- **Evidence:** Balance and resume tests.

### Day 28 — Research-readiness gate command

- [ ] Add a preflight command that blocks a pilot when schemas, provider configuration, condition balance, consent, artifact storage, or timing requirements are unsatisfied.
- **Acceptance:** The command produces a machine-readable pass/fail report with corrective actions.
- **Evidence:** Passing dry-run fixture and failures for each major gate.

### Day 29 — Manifest-driven GitHub results page

- [ ] Generate the public results table from a frozen, public-safe dataset manifest rather than manually maintained claims.
- **Acceptance:** The page displays condition definitions, N, exclusions, uncertainty, methodology, artifact version, and last generated date.
- **Evidence:** Static build check and screenshot or HTML snapshot.

### Day 30 — Pilot release bundle

- [ ] Produce a versioned pilot bundle containing protocol, frozen manifest, redacted data, results report, known limitations, dataset card, and license review checklist.
- **Acceptance:** A fresh checkout can validate the bundle using documented commands; no result is described as confirmatory unless the protocol gate was met.
- **Evidence:** Release-candidate validation log and checksum file.

## Pilot design after Day 30

Do not start the broad matrix in the original roadmap until the Day 28 readiness gate passes. The first controlled pilot should remain small enough to diagnose variance:

| Factor | Pilot levels |
|---|---|
| Controller | T0 scripted · T1 asynchronous banter · T2 macro model A · T2 macro model B |
| Maps | Two fixed maps |
| Seeds | Five paired seeds per map |
| Matches | 10 per condition; 40 total |
| Opponent | Same built-in AI race and difficulty within each block |
| Runtime | Headless/non-realtime; no chaos |
| Primary report | Paired outcome difference with uncertainty |

Human sessions should be a separate, counterbalanced UX study focused on workload, trust, usefulness, and enjoyment. They must not be mixed into the autonomous-strategy leaderboard.

## Deferred until the controlled pilot is credible

- [ ] Full raw-action-space LLM control.
- [ ] Multi-agent ladder and public rankings.
- [ ] Training or fine-tuning on collected traces.
- [ ] Public replay or dataset distribution before consent and license review.
- [ ] Claims about provider superiority based on banter-only conditions.

## Daily progress log

| Day | Date | Feature closed | Commit/PR | Evidence | Blockers or follow-up |
|---:|---|---|---|---|---|
| 1 | 2026-09-14 | Versioned research protocol (PROTOCOL_V1.md) | 4e73338 | evidence/day01_protocol_v1/pytest_output.txt (9 passed) | |
| 2 | 2026-09-15 | Condition registry (scplay/conditions.py) | pending authorization | evidence/day02_condition_registry/pytest_output.txt | |
| 3 | 2026-09-16 | Log schema v2 (schemas/v2 + scplay/schema_v2.py) | 8d841e7 | evidence/day03_log_schema_v2/pytest_output.txt | Live MatchLogger still v1; Day 4 manifests |
| 4 | 2026-09-17 | Reproducible run manifest (scplay/run_manifest.py) | (filled after push) | evidence/day04_run_manifest/pytest_output.txt | MatchLogger still v1; Day 5 validator |
| 5 | | | | | |
| 6 | | | | | |
| 7 | | | | | |
| 8 | | | | | |
| 9 | | | | | |
| 10 | | | | | |
| 11 | | | | | |
| 12 | | | | | |
| 13 | | | | | |
| 14 | | | | | |
| 15 | | | | | |
| 16 | | | | | |
| 17 | | | | | |
| 18 | | | | | |
| 19 | | | | | |
| 20 | | | | | |
| 21 | | | | | |
| 22 | | | | | |
| 23 | | | | | |
| 24 | | | | | |
| 25 | | | | | |
| 26 | | | | | |
| 27 | | | | | |
| 28 | | | | | |
| 29 | | | | | |
| 30 | | | | | |
