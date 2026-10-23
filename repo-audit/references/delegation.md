# Plan bounded delegation

Read the common contract's delegation section. It owns the rules. This reference is the assignment format, not a replacement for Pstack's `swarm` workflow.

Before substantial work, persist the following in the run's assessment or a linked plan:

| Field | Required decision |
| --- | --- |
| Strategy | Single agent, source workers, runtime workers, independent review, or a justified combination. Explain why delegation helps or why it does not. |
| Coverage | User journeys and system boundaries assigned to each worker. Identify cross-boundary behavior the coordinator must reconcile. |
| Common instructions | Exact contract version, applicable repository guidance, resolved Pstack resources, source revision, authority and exclusions. Every worker reads the contract. |
| Worker scope | Purpose, entry points, allowed tools and effects, owned outputs, expected evidence, prerequisites, budget and stopping condition. |
| Runtime ownership | Who drives each product instance. Name isolated actors, fixtures, ports, processes and mutable state or schedule drives sequentially. |
| Resources | Available concurrency, user-specified time/cost limits (or none), queue order and conditions for another wave. No unlimited fan-out. |
| Review and integration | Who inspects artifacts, checks freshness, resolves contradictions and challenges the final evidence independently. |
| Fallback | Installed workflow fallback for unavailable profiles, tools, workers or safe isolation. Required missing evidence stays blocked or inconclusive. |

Use this brief shape for each delegate. Fill only observed identities and authorized effects. A worker may narrow scope but cannot broaden it.

```text
Assignment and purpose:
Authoritative requirements and repository guidance:
Read the common contract at <resolved path>, version <version>:
Read applicable installed Pstack resources at <resolved paths>:
Repository, revision, environment, actor and fixtures:
Allowed tools, effects and output ownership:
Forbidden paths, data, effects and delegated authority:
Expected evidence and result format:
Dependencies, actual user/host limits (or none), operation timeout and stop condition:
Isolation or sequential-execution rule:
```

Check the returned paths, commands and artifacts against the brief. A citation to a skill or a statement that it was read is not proof of following it. Inspect supported task evidence when exposed. Label reduced observability rather than scraping private history.

Do not include previous verdicts or the answer to confirm in an independent reviewer brief. Relevant factual requirements and raw safe observations still belong in the brief. Keep acceptance graders and hidden answers outside candidate write access during behavioral evaluation.

One owner may execute all coupled runtime scenarios. Source workers may identify checks without executing them. Every worker needs the shared constraints, but not identical tools, the full parent's conversation, or the complete audit assignment.

A worker deadline must derive from a real user/host constraint or a single operation's timeout. It cannot silently become the whole audit's completion deadline. Keep a blocker queue and dispatch independent in-scope work while the coordinator asks for missing input. Do not create a new autonomous controller or infer authority for recurring work.
