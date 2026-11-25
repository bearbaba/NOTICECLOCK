# NOTICECLOCK — Studionet evidence, 2026-11-25

## Evidence scope
The developer supplied Explorer transaction details for all ten workflow calls and Studio readbacks for the initial certificate and final obligation, extension and notice. All ten workflow calls reported FINALIZED, Accepted / MAJORITY_AGREE, successful execution, Normal mode, five initial validators. These are developer-captured records, not an independent RPC verification or security audit. Deployment transaction hashes, deployed-source comparison have not been captured here. Eight direct-mode regression tests passed in [CI run 45559475793](https://github.com/bearbaba/NOTICECLOCK/actions/runs/45559475793); AI and external reads are mocked in those tests.

## Contracts
- NoticeClock: [Studio](https://studio.genlayer.com/?import-contract=0x6BbDd0A177F5790fdc1E4De23A346B07998FE3dD) / [Explorer](https://explorer-studio.genlayer.com/address/0x6BbDd0A177F5790fdc1E4De23A346B07998FE3dD)
- DeadlineLedger: [Studio](https://studio.genlayer.com/?import-contract=0x93759542116020e91Ac93CE8e037e7A8Ec5905f5) / [Explorer](https://explorer-studio.genlayer.com/address/0x93759542116020e91Ac93CE8e037e7A8Ec5905f5)
- Source revision used in walkthrough: `488e3c73d286be11a6e8c324ccea9c6a72319677`.

## Workflow transaction records
| TX | Method | Signer | Contract | Hash | Reported result |
|---|---|---|---|---|---|
| 01 | freeze_case | A | NoticeClock | `0x44475538ab7a6c376daedaa4683fb2b22cc485536771165de8c85f57b5a10ba3` | FINALIZED / SUCCESS |
| 02 | compile_deadline | A | NoticeClock | `0xfcc6f907fcfc59d3d76261f46b638700653eb337dfa8ad7fef47e5ae39f3e690` | FINALIZED / SUCCESS |
| 03 | open_obligation | A | DeadlineLedger | `0x8c8c4a3648ebf46a9c7e7da74e196429831f8dcf84728105ce69116095936ddc` | FINALIZED / SUCCESS |
| 04 | accept_obligation | B | DeadlineLedger | `0xda81cc26e48a7d26395d372b5985d6a8520cc9567c681cdcd4c211068285094a` | FINALIZED / SUCCESS |
| 05 | freeze_case | B | NoticeClock | `0xb74e0fa2ffc60beee21565818b7118e8cb4f649a87b78e19485ff2fdf20a405b` | FINALIZED / SUCCESS |
| 06 | compile_deadline | B | NoticeClock | `0x69d060b59491bd9928b61f34ca23089f5b04b661bd7b9029e3dcc8694bb08d92` | FINALIZED / SUCCESS |
| 07 | propose_extension | B | DeadlineLedger | `0x64ace62f4a63d6892a7311c014b15728b16e25f371c24220c341312ce2819a31` | FINALIZED / SUCCESS |
| 08 | resolve_extension | A | DeadlineLedger | `0x627ddc816346150c82d6e2e141952f34d28d0e89b478a9374bfb7edca7d8c34d` | FINALIZED / SUCCESS |
| 09 | file_notice | A | DeadlineLedger | `0x2c3efefe59186a6ec935eb46df9aaebbd4d436dc0ed393813bc17832c6de9ef0` | FINALIZED / SUCCESS |
| 10 | resolve_notice | B | DeadlineLedger | `0x1b699a6ee6087de3f0478b6fa47b1718739981f21925c961df36abda4aa28b6d` | FINALIZED / SUCCESS |

Search the full hashes in [Explorer](https://explorer-studio.genlayer.com/). TX02 and TX06 additionally returned equivalence-principle outputs with independent consensus over BUSINESS, EXCLUDE_EVENT, RECEIPT and 5 / 7 days, respectively.

## Readback and reproduction
Use the Studio links above. Call NoticeClock.get_certificate("nc-first"), DeadlineLedger.get_obligation("nc-obligation"), get_extension("nc-extension"), get_notice("nc-notice"). No write or signature is required for these views. The original deadline Nov 10 and approved extension Nov 12 are preserved in revision history; the mutually attested Nov 11 notice is ON_TIME under revision 2. See [captured JSON](readbacks-2026-11-25.json).

The event, holiday and notice dates are synthetic claims. They do not establish actual receipt or actual sending time. No live unauthorized transaction has been executed in this evidence set. The ambiguity case below was executed live. The test suite covers negative paths, including wrong signer, self-approval, changed trigger, certificate mismatch and ambiguous/conditional rule.

## Live ambiguity test (negative path)

Wallet B froze `nc-review` with clause `Respond promptly.`, event RECEIPT, date 2026-11-02 and holidays `[]`.

| TX | Method | Hash | Reported result |
|---|---|---|---|
| 11 | freeze_case | `0xc1e0ef5fa0ecc729cc1fa690d6934f461c81596c19ba9cb0b5ec8314795f2602` | FINALIZED / Accepted / SUCCESS |
| 12 | compile_deadline | `0xd6b2e84a7d7af1b51946d80e300911664e4e5f12ea89883229150ecfd3bdb19f` | FINALIZED / Accepted / SUCCESS |

TX12 equivalence output: `{"status":"REVIEW"}`. Read `NoticeClock.get_certificate("nc-review")`: status REVIEW, empty deadline, reason AMBIGUOUS_OR_UNSUPPORTED. Full captured certificate is in the JSON evidence file. All 12 calls succeeded; the last two intentionally produce no valid deadline. This proves the tested ambiguity path, not all possible adversarial inputs.
