# Auditor 1.2 implementation plan

Goal: maintain a reusable, explicitly invoked auditor in private Git, separate target-specific data, and require completed diagnostic coverage rather than document-only closure. The approved discussion in this chat is the design input.

- [x] Curate generic source only; keep historical target data, local credentials, installation receipts and product runs outside Git.
- [x] Update contract/runbook for target profiles, environment readiness, dynamic comprehensive coverage, escalation, user-owned limits, fixture disposition and reconciled diagnosis.
- [x] Strengthen existing recorder gates for restored-good evidence, approved retention and diagnostic completion without requiring the product to pass.
- [x] Add safe owned-profile refresh and an update workflow; preserve explicit-only discovery.
- [x] Put the target profile and activation instructions in the target documentation worktree, without credentials or product changes.
- [x] Run regression tests and independent behavioral exercises using fabricated local fixtures; inspect evidence and resolve blocking findings.
- [x] Create a private remote, publish only reviewed generic files, refresh the installed embedded contract, and verify actual desktop role loading.

Constraints: no target-product audit; no live staging/provider/infra operations; no product fixes; Pstack retains workflow ownership. No invented total deadline/spend cap. No changes in the shared target checkout.
