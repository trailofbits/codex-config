# GitHub Actions

Treat the repository's workflows, organization policy, and supported runners as authoritative.

- Pin third-party actions to full commit SHAs with a version comment. For checkout, set
  `persist-credentials: false` unless a later step explicitly needs the token-backed Git config.
- Grant the narrowest job or workflow `permissions` and avoid exposing secrets to pull-request code
  or untrusted reusable workflows.
- Do not interpolate pull-request titles, branch names, issue text, or other untrusted event fields
  directly into `run:` scripts. Assign the expression to `env:` and quote the environment variable
  in the script.
- Prefer `pull_request` to `pull_request_target`. Use `pull_request_target` only when the workflow
  needs base-repository privileges and never run or check out untrusted pull-request code in that
  privileged job.
- Keep runtime and tool versions synchronized with manifests and lockfiles. Verify current action
  releases and migration notes from upstream before changing a pin.
- Validate changed workflows with `actionlint` and scan them with `zizmor`. Fix every new warning or
  use the narrowest documented suppression with a reason.
- Configure Dependabot for each active ecosystem. Prefer grouped updates and a seven-day cooldown
  when organization policy does not specify another cadence.
- Use the `uv` ecosystem for Python repositories that commit `uv.lock` so dependency updates keep
  the manifest and lockfile synchronized.
