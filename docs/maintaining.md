# Maintain the auditor

Use Git as the canonical source and a private remote for recoverable history. Keep the installed skill pointing to a stable checkout; edit candidate changes in an isolated branch/worktree so experiments do not silently change the active agent.

For each meaningful contract/tooling update:

1. Record the behavior being corrected and the acceptance evidence.
2. Edit the canonical source, keeping target-specific data outside this repository.
3. Run affected regression checks and the package suite. Use fresh independent behavioral evaluations when instruction changes affect task completion, environment choice, authority or evidence.
4. Inspect actual artifacts and resolve blocking findings. A favorable self-report is not enough; repeated fresh trials measure consistency, while comparisons across versions measure improvement.
5. Commit/push the reviewed generic changes and promote the stable checkout. Regenerate the receipt-owned profile with `scripts_install.py --refresh`, run self-check and confirm actual client dispatch after contract changes.
6. Record the source commit and contract/tool versions in each audit's completion receipt.

Do not upload an existing local directory wholesale. Review initial and outgoing tracked files, including commit history, for credentials, target source/data, account references and historical reports. The package manifest inventories only maintained generic files; it is a fingerprint, not a security boundary. Preserve local private historical artifacts outside the tracked set. Do not add chat-only decisions to permanent instructions without a clear reusable behavioral reason.

The explicit-only skill remains user-wide and the profile remains personal, so moving source under Git does not change the app invocation. New repositories supply their own target profile and authority. No registry, cloud agent service or new orchestration layer is required.
