# NOTICECLOCK — Consensus-verified deadline compiler

A reusable GenLayer primitive for turning one explicit notice clause into a deterministic date certificate. AI extracts the rule; it never computes the date. No frontend, oracle, external model API key or payments.

## Example (synthetic)
Deploy `contracts/NoticeClock.py` in [GenLayer Studio](https://studio.genlayer.com/), no constructor args. Use Studionet test tokens.
1. `freeze_case("notice-01", "The notice must be submitted within five business days after receipt.", "RECEIPT", "2026-11-02", "[\"2026-11-05\"]")`
2. `compile_deadline("notice-01")` from the same wallet. Wait for finality and successful execution.
3. Read `get_case("notice-01")` and `get_certificate("notice-01")`. Expected COMPILED, deadline 2026-11-10 (3,4,6,9,10 Nov).
4. `check_date("notice-01", "2026-11-10")` → ON_TIME; Nov 11 → LATE.
5. Freeze a second case with "Respond promptly." and the same event/calendar, compile; expected REVIEW and no deadline.

## State and consensus
Owner freezes exact clause, event kind, event date, explicit holiday list and fixed Saturday/Sunday weekends. A SHA-256 commitment binds all frozen fields. The owner can compile once. Leader extracts structured count, calendar/business basis, trigger, inclusion/exclusion and exact entire clause; deterministic checks validate literal count/unit, trigger and counting markers. Each validator independently reruns the same extraction and compares all canonical fields; fabricated, inconsistent or invalid proposals do not pass. Valid consensus REVIEW is persisted without a deadline. Mismatched frozen trigger also yields REVIEW. Calculation uses integer Gregorian arithmetic and excludes holidays only for business days. No system-clock access. Read-only date comparison does not assert that notice was actually sent.

## Bounds and trust
English, one unconditional rule, explicit calendar/business days, 1–366; numeric counts or words one–twenty; receipt/delivery/acceptance/dispatch; explicit inclusion or after/exclusion. Event years 2000–2099; holiday list up to 128 dates, no duplicates. No partial days, timezones, jurisdictions, rolling holidays, legal interpretation or external proof of receipt. Inputs and holiday calendar are wallet-attested claims, not proof of actual events. Consensus cannot guarantee source truth or eliminate correlated model errors. Use new case ID to correct inputs; historical records cannot be overwritten.

## Reproduce tests
`python -m pip install genvm-linter==0.11.1rc2 genlayer-test==0.30.0 "pytest>=8,<9"`
`genvm-lint lint contracts/NoticeClock.py`
`genvm-lint check contracts/NoticeClock.py`
`pytest -q tests/`
Direct-mode tests use mocked model output and replay independent validators; they do not prove live AI performance. See [evidence status](docs/evidence.md).
