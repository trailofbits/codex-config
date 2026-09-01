# Node and TypeScript

Use the repository's runtime, package manager, scripts, and lint configuration. For greenfield work
or when the project has no established choice:

- Use the current Node.js LTS release, ECMAScript modules, and `pnpm`.
- Use `oxlint`, `oxfmt`, Vitest, and `tsc --noEmit`.
- Enable `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`,
  `noImplicitOverride`, `noPropertyAccessFromIndexSignature`, `verbatimModuleSyntax`, and
  `isolatedModules`.
- Colocate `*.test.ts` files with the code they cover.
- Pin direct dependencies exactly and keep a lockfile.

For a new project, start with these compiler options and add the project's module, target, library,
and output settings:

```jsonc
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,
    "verbatimModuleSyntax": true,
    "isolatedModules": true
  }
}
```

For a new pnpm project, record supply-chain settings in the project configuration:

```yaml
# pnpm-workspace.yaml
minimumReleaseAge: 1440
strictDepBuilds: true
allowBuilds: {}
```

The release-age setting delays newly published versions by 24 hours. `strictDepBuilds` rejects
dependencies with unreviewed build scripts; add only reviewed packages to `allowBuilds`, or use
`pnpm approve-builds` after inspection. Preserve a stricter project or organization policy when
one exists. Run
`pnpm audit --audit-level=moderate` before adding or upgrading dependencies unless the project sets
a different threshold.

References: [pnpm dependency-resolution settings](https://pnpm.io/settings/dependency-resolution)
and [build settings](https://pnpm.io/settings/build).

Run package scripts when they exist rather than bypassing project configuration with raw tool
commands. Audit before adding dependencies, following the repository's configured threshold.
