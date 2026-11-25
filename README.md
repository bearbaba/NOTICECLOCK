# NOTICECLOCK — Consensus-verified deadline compiler

A reusable GenLayer primitive for turning one explicit notice clause into a deterministic date certificate. AI extracts the rule; it never computes the date. No frontend, oracle, external model API key or payments.

## V2: two linked Intelligent Contracts

**NoticeClock** compiles grounded deadlines. **DeadlineLedger** reads the actual immutable case and certificate from the configured NoticeClock address, checks protocol and SHA-256 input binding, and creates a two-party obligation. The counterparty must accept it. Either signer may propose a new compiled certificate with the same original trigger and holiday calendar; only the other signer may approve. The deadline must move later. A notice freezes the active certificate and revision; the counterparty confirms ON_TIME/LATE or disputes it. No extension after filing. IDs and certificates cannot be reused. Maximum 32 revisions. This is a two-party attestation state machine, not trusted timestamps, legal advice or an oracle.

Deploy NoticeClock first, then DeadlineLedger with the actual NoticeClock address. Use the V2 sources together. See [V2 walkthrough](docs/v2-walkthrough.md).

## Studionet evidence — 25 November 2026

The developer's captured Explorer records show 10/10 successful finalized workflow transactions across both deployed contracts and two signers. Final Studio readbacks show revision 2, APPROVED extension, preserved original deadline (2026-11-10), new deadline (2026-11-12) and ON_TIME for the attested notice date 2026-11-11. See [full transaction evidence](docs/evidence.md) and [captured readbacks](docs/readbacks-2026-11-25.json). These are not an independent source audit or live adversarial test.

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
Direct-mode tests use mocked model output and replay independent validators; they do not prove live AI performance. See [Studionet evidence](docs/evidence.md).
