---
name: technical-writing
description: >-
  Write or revise durable technical prose such as READMEs, reports, findings,
  runbooks, design notes, and pull-request descriptions. Do not use for ordinary
  chat replies or code-only changes.
---

# Technical Writing

## Contents

- Source and audience
- Style
- Structure and claims
- Review

## Source and audience

- Write for the document's audience and decision. Use the requested format, the repository's
  terminology, and applicable templates. Base claims on the relevant source of truth.
- Verify facts that can change. Use absolute dates in durable prose and link to the narrowest
  authoritative source with short, descriptive link text.
- Describe the artifact as it exists now. Do not narrate discarded approaches or include history
  unless the audience needs it to understand a current decision.

## Style

- Lead with the consequence, result, or decision. Use plain, factual language, complete sentences,
  precise technical terms, and specific verbs.
- Prefer the everyday word when it preserves the meaning. Keep necessary domain terms instead of
  replacing them with approximate synonyms.
- Avoid comparative reframing such as “not just X, but Y,” mirrored sentence contrasts, default
  triads, sentence fragments, throat-clearing openings, hollow emphasis, and conclusions that only
  repeat the body.
- Avoid press-release filler, including “delve,” “underscore,” “bolster,” “foster,”
  “harness,” “leverage,” “utilize,” “pivotal,” “crucial,”
  “robust,” “seamless,” “intricate,” “meticulous,” “nuanced,”
  “multifaceted,” “holistic,” “testament,”
  “showcase,” “landscape,” “realm,” and “pave the way.”
- Do not use em dashes or `Bold term:` explanation lists. Use headings and lists only when they make
  the document easier to scan.
- Unpack dense noun stacks, prefer verbs to noun forms of verbs, and expand shorthand unless the
  audience routinely uses it. Keep modifiers and pronouns attached to unambiguous subjects.

## Structure and claims

- Use forward chronology for procedures and narratives. Keep prerequisites before the actions that
  depend on them and place warnings immediately before the risky step.
- State scope and limitations directly. Distinguish observed results, sourced facts, inferences,
  assumptions, and recommendations.
- Make every impact claim proportional to the evidence. A bug fix is a bug fix; do not label it
  critical, broad, or comprehensive without evidence.
- In a pull-request description, explain the resulting diff, its reason, and validation. Do not
  describe code or checks that are absent.

## Review

Before finishing, check facts, claims, links and paths, prerequisites, and project terminology. Run
applicable link, render, or documentation-build checks.
