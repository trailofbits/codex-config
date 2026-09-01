# Sequential Merge

Enter this phase only after external writes are authorized and the repository, PR set, and merge
method are confirmed.

1. Refresh each PR's state, checks, approvals, mergeability, head SHA, and dependency metadata. A
   stale or changed head must be re-evaluated.
2. Merge only PASS work units in the dependency order from discovery. Leave WARN and FAIL results
   open for human review.
3. Use the repository's permitted merge method and normal branch protections. Do not use an admin
   override, dismiss reviews, or bypass required checks unless the user explicitly authorizes that
   exact exception.
4. Verify GitHub reports the PR as merged, then update the local default branch.
5. Before the next merge, integrate the updated default branch into its isolated evaluation
   worktree and rerun the commands that established its PASS verdict. If the result changes, mark it
   skipped and continue without merging it.
6. For a batch, merge one PR at a time and repeat post-merge verification between members.

Stop merging if the default branch becomes unhealthy, a required check changes, or a PR no longer
matches its evaluated head SHA.
