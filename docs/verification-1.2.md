# Version 1.2 verification record

## Regression and package checks

The release suite ran 57 tests successfully using `python3 -m unittest discover -s tests -q`. Coverage includes distinct good/broken/restored-good evidence, target-profile freshness and symlink changes, explicit approved retention, diagnostic completion with actual product FAIL, incomplete/excepted coverage, unchanged runtime PASS requirements, and installation ownership/rollback behavior. The suite uses fabricated temporary repositories and captures, with no provider or target-product access.

The Skill Creator frontmatter validator accepted the explicit-only skill. All local Markdown links resolve. Every declared package hash was checked against source bytes. Installation requires the explicit manifest; no broad directory-copy fallback exists. Tests prove that undeclared local target files are excluded and stale sources are refused. Relative installation roots are normalized and remain usable after changing working directory. Modified owned profiles are refused; receipt-publication failure restores the previous profile.

A fresh independent reviewer read the applicable installed Pstack verification-generation/upkeep resources and runtime contract, inspected package and target-profile requirements, ran the suite, and found no unresolved concrete defects after corrections. Relative install-root handling, an unmanifested copy fallback, macOS path alias normalization, and target-specific planning wording were corrected during review. Dependency doctor reported the actual installed resources available; availability is not proof of semantic compliance.

## Installed role and functional check

The reviewed contract/tool version 1.2.0 was promoted to the existing user-wide installation. Owned-profile refresh and installation self-check succeeded. A supported desktop `spawn_agent` call selected the actual `repo-auditor` custom role in a fresh context. Its before-file-read startup record identified embedded contract 1.2.0. The author separately inspected the generated profile and source hashes. Candidate-authored startup prose alone is not independent proof that every instruction was followed.

That role exercised a fabricated two-file CLI repository with three advertised operations. Eight separate captures covered save and read good/broken/restored-good trials, rename persistence, and supporting parser/store error probes. Save and read passed their declared scenarios. Rename printed success but preserved the previous value; both fresh-process output and the persisted JSON exposed the defect. Source remained clean and unchanged. Every owned synthetic store was removed, including after assertion failures; raw failure output was preserved.

A separate reviewer inspected the original fixture requirements and source, external oracle, all eight raw outputs and receipts, hashes, dependencies, fixture state and current matrix. No author verdict was supplied as the grading answer. The review accepted the conclusive diagnosis and calibration after reconciling an initially absent decision-trail reference. After recording independent review, basic receipt and comprehensive diagnostic completion with review both exited 0 (`RECEIPT_VALID`). Strict runtime with review exited 1 (`Required runtime coverage has unresolved claims`). The original pending-review gate failures remain in history. Diagnostic completion and all-PASS product readiness are evaluated separately; the real product failure remains visible.

This is an explicitly prompted functional smoke check. The candidate knew it was being evaluated and received explicit evidence requirements. It is not a blinded Pstack Eval, independent consistency estimate, multi-model comparison, or proof of exhaustive behavior across large repositories. Applicable Eval steps and the skipped blinding/model-diversity work are documented in the local independent review. Future instruction changes require fresh behavioral trials; the next target-product audit remains a separate authorized run.

## Limits

Hashes and structural gates detect drift and malformed receipts; they do not prove semantic truth, inventory completeness, approval authenticity, host isolation or absence of data exposure. Independent inspection of actual evidence and original requirements remains mandatory. No live product audit, staging request, provider call, infrastructure operation or repair was performed for this release. Local historical evaluation artifacts remain outside the tracked generic package.
