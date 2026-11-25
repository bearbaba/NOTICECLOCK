# NOTICECLOCK — Studionet walkthrough

The ten workflow calls were executed on 25 November 2026; see [captured evidence](evidence.md).

Deploy NoticeClock (no args); deploy DeadlineLedger(anchor_address=NoticeClock address). Use two distinct wallets A and B and fresh IDs.

1. A: NoticeClock.freeze_case("nc-first", "The notice must be submitted within five business days after receipt.", "RECEIPT", "2026-11-02", "[\"2026-11-05\"]")
2. A: compile_deadline("nc-first"). Expect 2026-11-10.
3. A: DeadlineLedger.open_obligation("nc-obligation", "nc-first", B address)
4. B: accept_obligation("nc-obligation"). Expect OPEN.
5. B: NoticeClock.freeze_case("nc-next", "The notice must be submitted within seven business days after receipt.", "RECEIPT", "2026-11-02", "[\"2026-11-05\"]")
6. B: compile_deadline("nc-next"). Expect 2026-11-12.
7. B: DeadlineLedger.propose_extension("nc-obligation","nc-extension","nc-next"). Active deadline stays Nov 10.
8. A: resolve_extension("nc-obligation","nc-extension",true). Active deadline Nov 12, revision 2; history retains Nov 10.
9. A: file_notice("nc-obligation","nc-notice","2026-11-11","Synthetic notice reference N-001")
10. B: resolve_notice("nc-obligation","nc-notice",true). Expect ON_TIME. Without extension the date would be LATE.
11. Read get_obligation, get_extension, get_notice and both anchor certificates. Record all finalized tx and readbacks.

Negative checks: owner cannot self-accept; proposer cannot self-approve; wrong trigger, shorter deadline, review certificate, reused case, wrong wallet, and extension after filing fail closed. Date is a mutually attested claim, not proof of actual receipt. All data public; use test data only.
