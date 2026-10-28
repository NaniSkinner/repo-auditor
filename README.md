# Watson — Repository Auditor

A personal, explicitly invoked Codex custom agent for brownfield repository assessment and trustworthy verification. The mandatory contract is embedded in the installed profile; the skill supplies supporting procedures. Actual installed Pstack workflows own investigation, delegation, verification construction and evaluation. This repository does not vendor Pstack or create another controller.

Invoke the installed custom role `repo-auditor` and `$repo-audit` from a target repository's Codex app chat. Give it the live purpose and an explicit target-profile path. Dedicated dispatch must select the actual role; a worker name is insufficient. Unsupported profile dispatch stops unless the user explicitly permits parent execution.

## Separate reusable instructions from target data

- `repo-audit/`: generic contract, runbook, evidence helper and explicit-only entry skill.
- `templates/`: blank target preparation and per-run ledger examples.
- `tests/`: fabricated local regression fixtures; no target product data.
- `docs/`: maintained implementation, update and evaluation notes.

Target profiles belong with the target repository's guidance. Product reports, screenshots, actual accounts, proprietary source, corpus material, chat histories, credentials and installed local receipts do not belong in this generic repository. Private visibility does not replace that separation.

## Install and update

On a new machine, use Python 3.9+ and the checked-in installer with a source checkout, a different new installation destination, a user skills root and a personal agents root:

```sh
python3 scripts_install.py --source /path/to/checkout --destination /path/to/installed-source --skills-root /path/to/user/.agents/skills --agents-root /path/to/user/.codex/agents
```

Install refuses existing paths. The symlink is `repo-audit`; the generated custom profile is `repo-auditor.toml`. A manifest-backed copy includes only declared package files. The installation receipt records local ownership and hashes and stays untracked.

The installer exports curated files, without Git history. Keep the canonical source checkout in Git. When source checkout and installation destination differ, promote only the reviewed manifest-listed files and manifest to the destination, preserving its local `installation.json`, before refresh. A source pull alone does not update a separate installation.

For an existing owned installation after a deliberate source update:

```sh
python3 scripts_install.py --source /path/to/installed-source --refresh
python3 /path/to/installed-source/repo-audit/scripts/audit.py self-check
```

Refresh refuses a profile modified outside the ownership receipt and rolls back the profile if receipt publication fails. It does not overwrite global Codex instructions, connector configuration, permissions or Pstack. Restart the app when role discovery has not refreshed. Validate actual role/contract loading on the client rather than assuming self-check proves dispatch.

## Validate

```sh
python3 -m unittest discover -s tests -v
```

Use the built-in Skill Creator validation for the skill frontmatter. `audit.py doctor` records installed workflow resources; it proves file availability, not workflow compliance. `audit.py validate` checks structural/freshness constraints. `--require-completion --require-review` checks recorded comprehensive diagnostic completion, allowing conclusive product defects and explicitly accepted exceptions. `--require-runtime` separately requires all selected behavior PASS. Independent semantic evidence review is still necessary.

No product audit, provider call, deployment, background job or external message is authorized by installing this package. Profiles inherit actual parent permissions; instructions and hashes do not create a sandbox.

See [maintenance](docs/maintaining.md) and [1.2 validation](docs/verification-1.2.md).

Watson is the human-facing name for the existing repo-auditor profile and $repo-audit entry. Personal routing in ~/.codex/AGENTS.md maps explicit Watson/Audit Agent requests here. The explicit-only skill policy and mandatory audit contract remain unchanged.
