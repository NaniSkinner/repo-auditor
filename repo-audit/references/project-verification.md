# Establish repository-local verification

Discover existing project verification skills, control tools, feature maps, and CI/runtime recipes during baseline assessment. Read their actual instructions and helpers. Assess their freshness, isolation, evidence observers, and known limitations. Do not assume a skill works because its file exists.

When no trustworthy scripted path exists and setup is authorized, resolve and read Pstack's `create-verification-skill/SKILL.md` in full. It owns generation of `.agents/skills/verify-<app>/`, the grounded launch, doctor, drive, evidence, cleanup and helper instructions, and the per-feature map. Use its linked map examples rather than inventing a second format. Follow any repository-specific shared-skill symlink convention. Work in an isolated checkout. Do not edit the audited product during baseline.

The generated skill must run its own launch, doctor, mapped drive, evidence, and cleanup sequence. Check that evidence survives cleanup and no owned runtime remains. Unexecuted output is a draft. Retain a failing scenario as evidence of a product defect rather than changing the product or expected result to pass. Report a broken base precisely when product repair is outside authority.

For an existing map that needs upkeep, resolve and read `maintain-verification-skill/SKILL.md` in full. Its scope is the verification skill's directory. It distinguishes documentation drift, a harness gap, and a product regression. Its clean outcome requires source and live coverage of every mapped feature, with doctor, reset, residue cleanup, and retained evidence. Preserve its orchestration requirements and declared runtime fallbacks. Do not describe a risk-selected subset as a completed maintenance pass.

The global auditor's matrix adds scope, uncertainty, calibration, invalidation, and completion assessment across these project-specific verification paths. It does not replace them. Stop at a reviewable local artifact when publication is not authorized. Do not create recurring maintenance merely because the skill mentions a cadence.
