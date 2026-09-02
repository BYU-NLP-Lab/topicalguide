# Vendored front-end libraries

Every library the app uses in the browser is committed to this repository as a
built file. There is no npm install step, no bundler and no lockfile — the
`<script>` and `<link>` tags in `visualize/templates/root.html` point straight
at these paths.

## Why `/package.json` exists

Because the files are committed rather than installed, **Dependabot could not
see them at all**. Every alert this repository has ever raised was for a Python
package; the entire front end was unscanned. The `package.json` at the
repository root exists solely so Dependabot has a manifest to read. Nothing is
ever installed from it.

**A Dependabot pull request against `package.json` does not update the
vendored file.** It only edits that one line of JSON. Upgrading for real means
downloading the new build, replacing the file under `visualize/static/`,
updating the `<script>` tag if the filename carries a version, updating the row
in the table below, and running the browser tests. Treat such a PR as a
notification, not a fix.

## What is vendored

Versions were read from each file's own banner or embedded version string, not
inferred from filenames.

| Library | Version | Released | Path | In `package.json` |
| --- | --- | --- | --- | --- |
| jQuery | 1.11.1 | 2014 | `scripts/libs/jquery-1.11.1.min.js` | yes |
| jQuery UI | 1.11.0 | 2014 | `jquery-ui/` | **no** — 1.11.x was never published to npm under `jquery-ui` |
| Backbone | 1.1.2 | 2014 | `scripts/libs/backbone.min.js` | yes |
| Underscore | 1.13.8 | 2024 | `scripts/libs/underscore.min.js` | yes |
| D3 | 3.4.11 | 2014 | `scripts/libs/d3.v3.min.js` | yes |
| d3-tip | 0.6.3 | 2013 | `scripts/libs/d3.tip.v0.6.3.js` | **no** — npm's `d3-tip` starts at 0.6.7 |
| d3.layout.cloud | unknown | — | `scripts/libs/d3.layout.cloud.js` | **no** — the file carries no version banner |
| Bootstrap | 3.4.1 | 2019 | `bootstrap/` | yes |
| Bootstrap Toggle | 2.1.0 | — | `bootstrap-toggle/` | **no** — npm has 1.1.0, then 2.0.0 and 2.2.x |

Four entries cannot be expressed in `package.json` because the exact vendored
version does not exist in the npm registry. Declaring a nearby version instead
would be worse than declaring nothing: Dependabot would report on a release
this project does not actually ship, and a version *newer* than reality would
hide real advisories. They are listed here so the gap is visible rather than
silent, and they need checking by hand.

## Known exposure

jQuery below 3.5.0 carries CVE-2020-11022 and CVE-2020-11023: passing
attacker-influenced markup to `html()`, `append()` and similar can execute
script. The Backbone views build markup from `/api` data throughout, so this is
not a theoretical concern for this codebase.

Bootstrap was upgraded 3.2.0 → 3.4.1, clearing six XSS advisories
(CVE-2016-10735, CVE-2018-14040, CVE-2018-14042, CVE-2018-20676,
CVE-2018-20677, CVE-2019-8331). Two remain with no fix in the 3.x line —
CVE-2024-6485 (data-\* attributes) and CVE-2025-1647 (popover and tooltip) —
and clearing them means Bootstrap 4 or 5, a redesign. Note the app does call
`.popover()` in `router.js`, so the second is reachable.

Lodash 2.4.1 was **replaced by Underscore**, removing five advisories including
a critical prototype-pollution one. Lodash could not simply be upgraded:
Backbone 1.1.2 calls `_.any`, which lodash 4 renamed to `_.some`, so loading
lodash 4 kills the app on boot. Backbone is written against Underscore anyway —
lodash was always a substitution here. The only application code that had to
change was one `_.forOwn` call, which became `_.each`.

## Upgrading one of these

The procedure that keeps the manifest and the shipped file in step:

1. Download the official dist and confirm its version banner really is what you
   asked for.
2. Replace the files under `visualize/static/`.
3. Update the `<script>`/`<link>` tags in `visualize/templates/root.html` if the
   filename carries a version.
4. Update the table above.
5. Run `pytest tests/selenium`. Two tests exist specifically for this:
   `test_no_severe_console_errors` visits every view and fails on any severe
   browser console message, and `test_bootstrap_javascript_is_functional`
   drives a Bootstrap plugin through its own API. A broken library often still
   renders an approximately correct page, so the rendered-output assertions
   alone are not sufficient evidence.
6. Bump the version in `/package.json` in the **same commit**.

Upgrading is a real project, not a version bump — jQuery 1.x → 3.x removes
`.load()`, `.size()` and `.andSelf()` and changes deferred semantics, and D3 v3
→ v4+ restructures every module, which would touch all six visualizations. The
browser suite in `tests/selenium/` is what makes it attemptable: work one
library at a time and let the tests say what broke. See TASKS.md 2.1.
