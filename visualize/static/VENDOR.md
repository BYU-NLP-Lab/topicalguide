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
| jQuery | 3.7.1 | 2023 | `scripts/libs/jquery-3.7.1.min.js` | yes |
| jQuery UI | 1.13.3 | 2024 | `jquery-ui/` | yes |
| Backbone | 1.1.2 | 2014 | `scripts/libs/backbone.min.js` | yes |
| Underscore | 1.13.8 | 2024 | `scripts/libs/underscore.min.js` | yes |
| D3 | 3.4.11 | 2014 | `scripts/libs/d3.v3.min.js` | yes |
| d3-tip | 0.6.3 | 2013 | `scripts/libs/d3.tip.v0.6.3.js` | **no** — npm's `d3-tip` starts at 0.6.7 |
| d3.layout.cloud | unknown | — | `scripts/libs/d3.layout.cloud.js` | **no** — the file carries no version banner |
| Bootstrap | 5.3.8 | 2025 | `bootstrap5/` | yes |
| Glyphicons Halflings | from Bootstrap 3.4.1 | 2019 | `styles/glyphicons.css`, `fonts/` | n/a — extracted, not a package |

Two entries cannot be expressed in `package.json` because the exact vendored
version does not exist in the npm registry. Declaring a nearby version instead
would be worse than declaring nothing: Dependabot would report on a release
this project does not actually ship, and a version *newer* than reality would
hide real advisories. They are listed here so the gap is visible rather than
silent, and they need checking by hand. (jQuery UI joined the declarable set
when it moved from 1.11.0 to 1.13.3, which is on npm.)

## Known exposure

jQuery was upgraded 1.11.1 → 3.7.1, clearing CVE-2015-9251, CVE-2019-11358 and
CVE-2020-11023 — XSS and prototype pollution reachable through `html()` and
`append()`, which the Backbone views use on `/api` data throughout. jQuery UI
moved 1.11.0 → 1.13.3 in the same change, because 1.11 predates jQuery 3
support and the two are a pair.

Bootstrap was migrated **3.2.0 → 3.4.1 → 5.3.8**, clearing all eight of its
advisories, including CVE-2024-6485 and CVE-2025-1647, which had no fix
available anywhere in the 3.x line.

jQuery was upgraded 1.11.1 → 3.7.1, clearing CVE-2015-9251, CVE-2019-11358 and
CVE-2020-11023 — XSS and prototype pollution reachable through `html()` and
`append()`, which the Backbone views use on `/api` data throughout. jQuery UI
moved 1.11.0 → 1.13.3 in the same change, because 1.11 predates jQuery 3
support and the two are a pair.

Lodash 2.4.1 was **replaced by Underscore**, removing five advisories including
a critical prototype-pollution one. Lodash could not simply be upgraded:
Backbone 1.1.2 calls `_.any`, which lodash 4 renamed to `_.some`, so loading
lodash 4 kills the app on boot. Backbone is written against Underscore anyway —
lodash was always a substitution here. The only application code that had to
change was one `_.forOwn` call, which became `_.each`.

Bootstrap Toggle is gone. It was a Bootstrap 3-only plugin with no version 5
equivalent, used for one switch; that is now Bootstrap 5's own form-switch.

D3 remains at v3.4.11. It has no open advisory, and v3 → v4+ restructures every
module, so it would touch all six visualizations for no security gain.

## Upgrading one of these

The procedure that keeps the manifest and the shipped file in step:

1. Download the official dist and confirm its version banner really is what you
   asked for.
2. Replace the files under `visualize/static/`.
3. Update the `<script>`/`<link>` tags in `visualize/templates/root.html` if the
   filename carries a version.
4. Update the table above.
5. Run `pytest tests/selenium`. Four tests exist specifically for this, because
   a broken library often still renders an approximately correct page and the
   rendered-output assertions alone are not sufficient evidence:
   `test_no_severe_console_errors` visits every view and fails on any severe
   browser console message; `test_bootstrap_javascript_is_functional` drives a
   Bootstrap plugin through its own API; `test_jquery_ui_slider_initialises`
   and `test_bootstrap_toggle_initialises` check the two third-party widgets,
   which are the pieces most sensitive to a jQuery or Bootstrap version
   change.
6. Bump the version in `/package.json` in the **same commit**.

D3 remains at v3.4.11. It has no open advisory, and v3 → v4+ restructures
every module, so it would touch all six visualizations for no security gain.

The browser suite is what makes any of this attemptable: work one library at a
time and let the tests say what broke. See TASKS.md 2.1.
