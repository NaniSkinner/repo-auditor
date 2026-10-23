# Run a full repository audit

Use the mandatory contract for obligations and authority. This runbook organizes the work. Keep a checklist of these phases with evidence or a concrete blocked reason for each. Read the repository's own guidance before commands. Complete its read order where applicable.

## Frame and inventory

Record the live purpose, repository root, revision, environment, actors, fixtures, permitted effects, exclusions, output directory, user-specified total time/cost limits (or none), and stop condition. Inspect actual runtime capabilities before promising them. Name unsupported languages, platforms, or integrations. Use an isolated checkout for setup or source-writing work. Read-only inspection can use the current source without checking out another branch.

Create the baseline inventory. Read guidance, document map, source-of-truth material, service READMEs, package manifests, build commands, lockfiles, CI jobs, environment configuration names, test entry points, deployment topology, and relevant changes. Do not read secret values or excluded data. Record what was searched and omitted.

Before substantial exploration, record the delegation decision and coverage plan from delegation.md. Assign independent source investigations where useful and identify the coordinator's cross-boundary checks. Name the runtime owner and isolation requirements before any parallel driving. State budget, capacity, stop conditions and fallback. Revise the plan from observed gaps rather than automatically spawning another wave.

Produce an architecture map of entry points, contracts, actors, authorization boundaries, persistence, jobs, integrations, shared state, and deployment assumptions. Trace representative code paths. Cite file and symbol locators with the revision. Reconcile conflicts between intent and implementation.

## Map and prioritize workflows

Create the feature map from the implemented product and controlling requirements. For each journey record value, prerequisites, interface, owning code, downstream state, failure, cancellation, recovery, and verification route. Inventory all discovered important flows. Select deep verification using consequence, uncertainty, change exposure, and available authority. State the exclusions.

Write the live verification matrix and coverage commitment before execution. All discovered important domains need a verification route, not only user journeys. Priority orders required work; it cannot make all other flows optional. For every selected claim state the expected user outcome, environment, actor, inputs, initial state, source of truth, exact scenario, expected observation, false-pass risks, failure behavior, cleanup, and invalidation. Separate implementation facts from runtime proof. Ask only for unresolved product judgments or genuinely required access. Continue independent work.

## Establish reproducible execution

Inspect setup and command definitions. Document dependencies, configuration, authentication, fixtures, startup, readiness, reset, and cleanup. Confirm build identity and source revision. Use synthetic fixtures with known origin. Keep mutable data outside a pinned source checkout. Do not conflate a git worktree with a database or network sandbox.

Use the project's actual interface and observation tools. A CLI-only project needs no invented browser test. A frontend journey needs UI execution, plus permitted downstream evidence. A background pipeline needs bounded completion observation and recovery checks. Name any provider substitutes and what they cannot prove.

Initialize a run and finish its environment manifest before capturing evidence. Store dependency discovery and its receipt. Capture only inspected, authorized commands. For unsupported count parsers, retain the output and a separately reviewed outcome adapter. Do not label a command as a supported test run to bypass zero-test detection.

## Exercise the selected workflows

Run the happy path and relevant boundary cases. Cover authorization, validation, persisted readback, async completion, retry, duplication, cancellation, concurrency, partial failure, and recovery where the actual workflow calls for them. Prefer a small set of consequential scenarios to exhaustive low-value combinations. Do not silently drop requested coverage.

Keep command failures, observations, artifacts, and retries. Determine whether each failure belongs to the environment, observation method, product, or unresolved category. Inspect authoritative state after uncertain writes. Stop unsafe dependent work, ask the user for the smallest missing prerequisite, and continue independent authorized runtime checks as well as assessment. If all work awaits input, checkpoint as waiting rather than declaring completion.

## Calibrate and improve verification

Run known-good and known-broken cases with the same meaningful oracle. Use a controlled variant or disposable fixture. Require the intended assertion to fail for the intended reason. Restore state and rerun the good path. Capture each attempt separately.

If the oracle misses the fault, report a verification gap. Improve tooling only within setup authority and isolated ownership. Check callers, contracts, config propagation, and integration assumptions. Reverify each unit and affected flows. Product repairs require a separate task.

## Challenge the findings

Provide a fresh reviewer the authoritative purpose, scope, revision, source artifacts, matrix, and raw safe evidence. Ask whether each conclusion follows and which important flows or false-pass risks were missed. Do not supply the author's verdict as the answer to confirm. Use Pstack's appropriate review and coverage workflows within capacity and authority.

The lead reads the review artifacts, resolves disagreements against evidence, retains credible lone findings, and reports missing lanes. Record the review identity and method honestly. Do not claim different models unless the runtime proves them.

## Deliver and preserve

Reconcile source, runtime build, environment, dependency, actor, and fixture identity. Refresh only invalidated coverage. Finish cleanup or record explicitly approved retention, fixture IDs, ownership, review/removal conditions and recovery steps. Reconcile current matrix, diagnosis and detailed docs; preserve earlier states as historical. Sanitize outputs. Run the receipt gate and inspect semantics separately.

Return the baseline, feature map, verification matrix, evidence and command inventory, calibration, defects and reproductions, unrun checks, risks, cleanup, and next action. Recommend ship only within the declared scope and project release requirements. No audit result grants release authority.

When paused or compacted, persist a sanitized checkpoint. Include phase state, current identities, authority, unresolved writes, evidence IDs, pending checks, and cleanup. Reload the contract and inspect actual state on resume.

For comprehensive diagnosis, validate with `--require-completion --require-review`. Confirmed defects may satisfy executed diagnostic coverage; unresolved required checks need human-accepted exceptions. `--require-runtime` separately establishes fully passing selected behavior. The rollout owns separately authorized remediation, retesting and agreed extensions; it must not absorb unfinished required audit work to permit closure.
