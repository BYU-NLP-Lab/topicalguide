# Opportunities

Observations from working through the test suite, the `/api` endpoint, the
Backbone front end and the import pipeline. Each item says what is wrong, how
it was verified, and why it matters.

Items marked **[verified]** were reproduced directly; the rest are readings of
the code that still deserve a confirming test before acting.

The numbered sections below are grouped by **subject** — correctness,
security, performance and so on. The table that follows groups the same items
by **impact**, which is the order to actually work in. Section numbers are
stable and referenced from commit messages, so nothing is renumbered when
priorities change.

---

## Priorities

### Tier 1 — do first: security and silent data loss

| Item | Why now |
| --- | --- |
| **2.4** front-end CVEs — **all 15 cleared** | Bootstrap 5.3.8, jQuery 3.7.1, jQuery UI 1.13.3, lodash replaced by Underscore. Kept in Tier 1 as the record of how it was done and what it cost. |
| **4.4** `/bertopic-viz` access control — **fixed** | It served private datasets and let their names be enumerated. Kept here because it is the argument for 4.1: the bug was found by measuring coverage, not by reading code. |
| **1.1** falsy metadata | Any `0`, `False` or `""` silently reads back as absent. Corrupts data in every view, the fix is a few lines, and 4.5 says where the tests go. |
| **1.6** 1.76M orphaned rows | If the import pipeline is producing these, the bug is far bigger than one database. Investigate before repairing. |

### Tier 2 — hours of work, disproportionate payoff

| Item | Why |
| --- | --- |
| **0.9** empty state names a file that does not exist | One line. It is the first thing a new user reads. |
| **0.1** two finished visualizations switched off | The code is written. Uncomment, run the browser tests, find out. |
| **0.2** Topics Over Time draws `NaN` bars | The signature view of a 235-year corpus renders nothing visible even after you select a topic, and starts blank besides. |
| **5.1, 5.2** README onboarding | The documented install path cannot work on a fresh clone. |
| **2.2** `DEBUG` leaks every SQL query into API responses | Small change, removes an information-disclosure footgun. |

### Tier 3 — substantial, and where the durable value is

| Item | Why |
| --- | --- |
| **4.1** no test for the import pipeline | 571 statements at **0%**, plus all 16 metrics that run on every import. The largest gap, and now cheap to close. |
| **0.4** five recoverable topic metrics | Cheapest route to showing a user which topics are worth reading. |
| **1.3, 1.4, 1.5, 1.5b** error handling | 26 bare excepts, failures that render as content, and unguarded DOM lookups in async callbacks. Hides the next bug. |
| **1.2, 4.3** `/api` error contract | Failure reported two incompatible ways, neither with a usable status code. |
| **3.1, 3.2** N+1 queries and dead cache | One request can issue hundreds of queries; the cache never engages and never invalidates. |
| **2.1** front-end upgrades — **done** except D3 | Bootstrap 5, jQuery 3, jQuery UI 1.13, Underscore. D3 stays at v3 deliberately: no advisory, and v4+ rewrites all six visualizations. |
| **5.3, 5.4** architecture note and README rewrite | Half the README no longer describes this project. |
| **5.5** nothing to look at on a fresh clone | Decide demo database vs `make demo` before reaching for Git LFS. |
| **2.3, 4.2** CI follow-ups — **coverage done** | `pytest-cov` declared and `--cov` in the CI run. Remaining: split the ML deps. |
| **2.5** Python 3.11 → 3.13 | Independent of Django, and removes half the work from the 6.2 LTS jump in April 2027. |

### Tier 4 — the research programme

Sections **6** and **7**, plus the product proposals in **0.3, 0.5, 0.6, 0.7,
0.8**. These are weeks of work and change what the tool *is* rather than
whether it works.

**6.1** — document and passage embeddings — is the one foundational build:
6.2, 6.3, 6.5 and 7.6 are all blocked on it, and the libraries are already
installed. After that, **7.4** (researcher-defined semantic axes) is the
highest expressive-power-to-effort item in this document — two centroids and a
projection. **7.1** (embedding token occurrences rather than word types, for
word senses) is the most distinctive, because the schema already records every
occurrence with its context offset and its own topic assignment, which is
exactly what type-level topic browsers throw away.

### Decided, not to be re-litigated

**2.5** — stay on Django **5.2 LTS** and go straight to **6.2 LTS** in April
2027. Django 6.1's support ends four months *earlier* than 5.2's, so upgrading
to it would shorten the security horizon, and 6.x additionally requires Python
3.12+. Revisit early only if an advisory has no 5.2 fix.

---

## 0. Making the app more useful

The engineering items below keep the app working. These are about what it lets
a researcher *find*. The tool's purpose is to make a topic model interrogable —
so the highest-value gaps are the places where the data is already in the
database and the interface does not let anyone reach it.

### 0.1 Two finished visualizations are switched off **[verified]**

```
visualize/static/scripts/topic_embeddings_view.js:147:// globalViewModel.addViewClass([], TopicEmbeddingsView);
visualize/static/scripts/visualizations/force_view.js:435:// globalViewModel.addViewClass([], ForceView);
```

A topic-embeddings view and a force-directed topic graph are both written and
both commented out of the navigation. `extract_embeddings.py` exists to feed
the first. Whatever the reason they were disabled, this is the cheapest
insight-per-effort item in the file: find out what is broken, fix it, and two
more ways of seeing the model come back. Start by re-enabling them behind the
new browser tests — `tests/selenium/test_spa.py` will say immediately whether
they render.

### 0.2 Topics Over Time is blank by default, and broken once you use it **[verified]**

Two separate problems, the second worse than the first.

**It draws bars with no geometry.** Selecting a topic appends the right number
of `rect.bar` elements with valid `x` and `width`, but **`y="NaN"` and
`height="NaN"`**, so nothing is visible. One selection produced 546 severe
browser console errors (`<rect> attribute height: Expected length, "NaN"`).

```
bars: 3
  x=0    y=NaN  w=171  h=NaN
  x=190  y=NaN  w=171  h=NaN
  x=380  y=NaN  w=171  h=NaN
```

The bars are positioned from `yScale(yInfo.min)` at
`topics_over_time_view.js:844`; `yInfo.min` appears not to be set in that state,
so the initial `y` and the transitioned `height` are both NaN. That last step is
a hypothesis — the symptom above is measured.

Caveat worth checking first: the test fixture gives every topic identical token
counts in every document, so the y domain is degenerate. Confirm against a real
corpus before concluding the view is broken for actual data.

`test_topics_over_time_bars_have_real_geometry` records this as a strict xfail,
so fixing the view turns the test green and fails the run until the marker is
removed. Its sibling `test_topics_over_time_draws_a_bar_per_year_for_a_topic`
passes throughout, because it counts elements rather than measuring them —
which is precisely how this stayed invisible.

**It also starts empty.** The view loads with no topic selected and an empty
plot; you must know to multi-select from the topics list before anything is
drawn at all.

This is the app's most distinctive view — a 235-year corpus of State of the
Union addresses is *about* change over time — and its default state shows a
blank chart. Preselecting a handful of topics would fix the immediate problem;
preselecting the **most interesting** ones would make it a discovery tool. Rank
topics by change over the time axis (variance across years, or first-half
versus second-half proportion) and show the top few by default, so opening the
view immediately answers "what shifted?" rather than waiting to be asked.

### 0.3 The corpus carries metadata the interface never uses **[verified]**

Every SOTU document ships with:

```
address_number, title, author_name, month, president_name, year, day
```

`president_name` is the obvious comparative axis for this corpus and nothing
groups by it. The 2D-plots view offers metadata on each axis but has no notion
of *faceting* — no "colour by president", no small multiples, no
side-by-side. Topics Over Time filters metadata down to time-related names
only, so `president_name` is invisible there by construction.

"Which topics distinguish this president from the others?" is the question this
dataset invites, and today it cannot be asked. Grouping and colouring by a
categorical metadata field would open it up, and it is additive — the existing
axes keep working.

### 0.4 Topic quality is not surfaced, and the metrics that would show it are gone

These metrics were never computed — a distinction worth being precise about,
since "topic coherence exists but is not displayed" and "topic coherence does
not exist" call for very different work.

Nine metric modules sat commented out of their registries for years, written
against the pre-4.2 `add_metric()` protocol and against models that no longer
exist: `TopicMetric`, `topic.topicword_set`, `word.ngram`, `word.type`. They
could not have run. They have been removed from the tree and remain in git
history — `git log --diff-filter=D -- import_tool/metric/`.

What they measured, and what reviving each would take:

| module | computed | blocker beyond the schema |
| --- | --- | --- |
| `topic/coherence` | average pairwise PMI over a topic's top 10 words | needed an external SQLite co-occurrence database via `kwargs['counts']`, not in this repo |
| `topic/pairwise/coherence` | the same PMI between topics | same external database (imported `compute_pmi` from the above) |
| `topic/alpha` | per-topic LDA alpha | parsed a Mallet `state_file` passed as a kwarg |
| `topic/sentiment` | topic sentiment | shelled out to an external tool via `Popen` |
| `topic/attribute_entropy` | entropy of a topic over document metadata values | none — pure ORM, the most straightforward to rewrite |
| `topic/subset_document_entropy` | document entropy per metadata subset | none — pure ORM; emitted one metric per attribute value |
| `topic/subset_token_count` | token count per metadata subset | none — pure ORM; same shape as above |
| `document/pairwise/topic_correlation` | cosine similarity between documents' topic vectors | none — NumPy plus ORM |
| `document/pairwise/word_correlation` | cosine similarity between documents' word vectors | none — NumPy plus ORM |

The point stands regardless: the topics table shows only "% of Corpus" and
"% of Topic", so a user has no way to tell a coherent topic from model noise —
the first judgement anyone makes when reading a topic model.

The five "none" rows are ordinary rewrites against `compute_metric(database_id,
dataset_db, analysis_db)`, following any live module such as
`topic/token_count.py` as a template. `attribute_entropy` is the natural first
one: pure ORM, and it directly serves the faceting in 0.3.

For coherence specifically, prefer reimplementing over reviving. NPMI computed
over the corpus itself is self-contained and needs no external counts database,
which is what made the original unrunnable even before the schema moved. That
also connects it to 6.8, where coherence becomes the basis for comparing whole
analyses rather than just ranking topics within one.

### 0.5 Analyses cannot be compared

The global selectors pin exactly one dataset and one analysis. Mallet, BERTopic
and random analyses are all supported (`import_tool/analysis/interfaces/`), and
the README documents running LDA at 20 and 100 topics — but there is no way to
put two analyses beside each other. "Is 20 topics or 100 topics the better
model here?" and "does BERTopic find something LDA missed?" are the questions a
researcher actually has, and both require two analyses on screen at once.

Even a modest version helps: a second analysis selector and a view that aligns
topics between the two by shared top words.

### 0.6 Topic naming schemes are richer than the default suggests

Four namers exist — `top_n`, `tf_itf`, `llm_namer`, `bertopic_namer` — and the
UI has a "Topic Names" selector for switching between them. The default is
`Top3`, three raw top words, which is the least informative of the four.

`generate_llm_topic_names.py` produces an `LLM-10words` scheme but must be run
manually per analysis, so most datasets never get it. Running a namer as part
of the analysis pipeline, and defaulting to the most readable scheme available,
would change the first impression of every topic from `alpha beta gamma` to
something a reader can actually use. Comparing schemes side by side is also a
legitimate research view in itself.

### 0.7 No way to get the numbers out

The only export in the app is "Download as SVG" on the 2D plot
(`2dplots_view.js:39`). There is no CSV or JSON export of the topics table, the
document-topic proportions, or the time series — the numbers a researcher needs
to put a finding in a paper.

The `/api` endpoint already returns all of it as JSON, so this is mostly a
matter of exposing a download that hands over the response the current view
already fetched. Worth pairing with a stable citation link: the URL hash
already encodes dataset, analysis, topic, document and settings, so a
"copy link to this view" affordance would make findings shareable and
reproducible at no modelling cost.

### 0.8 There is no document search

Topics can be filtered by word. Documents cannot be searched at all — no
full-text query, no metadata filter. On a 238-document corpus that is
survivable; on anything larger the documents table is a wall. The single
document view has topic and word highlighting, which is the good half of the
feature; the missing half is finding the document you want to highlight.

### 0.9 The empty state gives a command that does not exist **[verified]**

`datasets_view.js:11`, shown when the database has no datasets:

> No datasets yet. Import one using `python topicalguide.py -h`.

There is no `topicalguide.py`. The importer is `tg.py`. This is the very first
thing a new user sees, and it sends them to a file that is not there. One-line
fix; disproportionate effect on first impressions.

---

## 1. Correctness

### 1.1 `MetadataValue.value()` treats 0, False and "" as missing **[verified]**

`visualize/models.py:73` picks the populated column with truthiness tests:

```python
if self.float_value:  result = self.float_value
if self.text_value:   ...
if self.int_value:    ...
if self.bool_value:   ...
```

So any *falsy* stored value reads back as `None`:

| stored              | `value()` returns |
| ------------------- | ----------------- |
| `int` 0             | `None`            |
| `bool` False        | `None`            |
| `float` 0.0         | `None`            |
| `text` ""           | `None`            |

A boolean metadata field can therefore never report `False`, and any count,
score or year of zero silently disappears from the API and every view. The
same block raises "MetadataValues cannot be of more than one type" by counting
truthy columns, so it also mis-detects when a legitimate zero is present.

Fix by testing `is not None` per column, ideally driven off the
`MetadataType.datatype` that is already stored rather than by guessing from the
columns.

### 1.2 `/api` reports failure two different ways, both with the wrong status

`visualize/api.py:99` raises out of `filter_request` *before* the `try`, so an
unknown query key escapes as an unhandled exception (HTTP 500). A failure
inside `query_datasets` is caught at line 129 and returned as
`{"error": "..."}` with **HTTP 200**. A client cannot tell success from failure
by status code, and the two paths disagree with each other.

Decide on one contract — 400 for a bad request, 500 for a genuine fault, error
detail in the body — and apply it to both paths. `tests/visualize/test_api.py`
already pins the current behaviour, so the tests will need updating with it.

### 1.3 `Document.get_content()` cannot distinguish an error from content

`visualize/models.py:235` catches every exception and returns the literal
string `'Error occurred while trying to access content.'`. That string then
flows into the API and renders in the documents table as though it were the
document. A missing file, a permissions problem and a document that genuinely
contains that sentence are indistinguishable, and nothing is logged.

This was visible in the browser tests before the fixture wrote real files to
disk: three documents rendered the error text as their preview and every
assertion still passed.

### 1.4 26 bare `except:` clauses **[verified]**

`grep -rn "except:" --include="*.py" . | grep -v venv` returns 26 across 10
files, including `import_tool/basic_tools.py` (three),
`import_tool/analysis/utilities.py`, `import_tool/analysis/bigram_finder.py`,
`visualize/models.py` and `visualize/root.py`. A bare `except:` swallows
`KeyboardInterrupt` and `SystemExit`, so a long import cannot be interrupted
cleanly, and it hides the kind of argument bug described in 1.5.

Narrow them to the exception actually expected, and log what was swallowed.

### 1.5 Audit for more wrong-argument bugs of the kind already found

`get_all_files_from_directory` passed its `recursive` flag to `os.walk`'s
`followlinks` parameter, so the walk always recursed and `is_recursive=False`
was silently ignored by `GenericDataset`, `JsonDataset` and
`WikipediaDataset` (fixed in commit f609af3). The existing test passed
throughout because it only ever asserted inclusion, never exclusion.

That shape — a flag accepted, threaded through several layers, and never
asserted against — is worth grepping for deliberately. Every boolean parameter
in `import_tool/` that no test exercises in its non-default state is a
candidate.

### 1.5b The chord view measured an element that may not exist **[verified]**

Found by the console guard, on CI rather than locally, which is the whole point
of that test:

```
chord_view.js 249  Uncaught TypeError:
    Cannot read properties of undefined (reading 'getBoundingClientRect')
```

`$("#chord-controls").get(0).getBoundingClientRect()` runs inside the callback
that receives the pairwise metric data. If the element is not in the DOM at that
moment — the view is disposed when the user navigates away before the data
arrives — `.get(0)` is `undefined` and the throw takes the whole render with it.

Fixed by checking before measuring, so a disposed view aborts cleanly instead
of throwing. Worth noting as a pattern rather than a one-off: **any DOM lookup
inside an async callback in these views has the same shape**, because
`changeView` disposes the current view while its requests may still be in
flight. 1.5 asks for an audit of wrong-argument bugs; this is the sibling
audit, for unguarded lookups after an await.

### 1.6 The dev database has 1.76 million foreign key violations **[verified]**

Found during the Django 5.2 upgrade and not caused by it. `working/tg.sqlite3`
(gitignored, 1 GB, last modified December 2025) fails `PRAGMA
foreign_key_check` with **1,762,639** violations. The sample is uniform: rows
in `visualize_analysismetadatavalue` whose `analysis_id` points at a
`visualize_analysis` row that does not exist — `analysis_id` 1, while the table
holds six analyses.

The visible symptom is that any command opening a SQLite schema editor against
it fails:

```
$ python manage.py sqlmigrate visualize 0002
django.db.utils.IntegrityError: The row in table 'visualize_analysismetadatavalue'
with primary key '1' has an invalid foreign key ...
```

Against a clean database the same command succeeds and prints `-- (no-op)`, so
the migration is fine and the data is not.

The question worth answering is whether a delete path in the import pipeline
can orphan rows — `tg.py remove-metrics`, or re-importing and re-analysing a
dataset. Django cascades in Python, so deletes issued as raw SQL or as bulk
operations that bypass the ORM are the usual cause, and 1.7 million of them
suggests something systematic rather than a one-off.

Investigate read-only first: group the violations by table to see whether only
`analysismetadatavalue` is affected, and check whether SQLite foreign keys were
even enforced when the rows were written — Django enables them per connection,
so data written by another tool may never have been checked. Do not repair the
file without asking; it is working data with no backup in the repository.

---

## 2. Security and operations

### 2.1 Vendored front-end libraries — **scanning and upgrades done**

Everything the app loads in the browser is committed under `visualize/static/`
rather than installed, and `visualize/static/VENDOR.md` is the inventory.
Versions there were read from each file's own banner, not inferred from
filenames.

**Scanning — done.** Because they were vendored blobs with no manifest,
Dependabot could not see them at all, and every alert this repository had ever
raised was Python. `/package.json` now declares them, and
`.github/dependabot.yml` enables npm and github-actions alongside pip. What
that exposed is 2.4.

Note the limitation that makes this easy to misread: **a Dependabot PR against
`package.json` edits one line of JSON and does not update the committed file.**
It is a notification, not a fix, and npm pull requests are disabled for that
reason — alerts stay on.

**Upgrades — done.** Bootstrap 3.2.0 → **5.3.8**, jQuery 1.11.1 → **3.7.1**,
jQuery UI 1.11.0 → **1.13.3**, lodash 2.4.1 → **Underscore 1.13.8**, and
bootstrap-toggle removed in favour of Bootstrap 5's form-switch.

**What is deliberately left:**

- **D3 3.4.11.** No open advisory, and v3 → v4+ restructures every module,
  which would touch all six visualizations for no security gain.
- **Backbone 1.1.2.** No open advisory. Worth noting it is the constraint that
  forced Underscore over lodash, and it would need to move before lodash could
  ever come back.
- **d3-tip 0.6.3 and d3.layout.cloud**, which cannot be declared in
  `package.json` at all — the exact versions are not in the npm registry, and
  the second carries no version banner. They are listed in `VENDOR.md` so the
  gap stays visible, and they need checking by hand.

### 2.2 `DEBUG` puts every SQL query in the API response body

`visualize/api.py:144` attaches `query_count`, `queries` and `total_time` to
each response when `DEBUG` is true. That is useful in development and an
information disclosure if `DEBUG` is ever true in a deployment — it exposes
schema and query structure to any caller. Gate it on an explicit setting
(`TG_API_DIAGNOSTICS`) rather than on `DEBUG`, so switching `DEBUG` on to chase
a bug in a shared environment does not also start publishing the query log.

### 2.3 CI — **done**, with one follow-up

`.github/workflows/tests.yml` now runs on every push and pull request:
install, build `settings.py` from the template via
`scripts/bootstrap_settings.py`, `manage.py check`, then `pytest`.

Two decisions worth keeping: CI sets `TG_REQUIRE_BROWSER`, which turns "Chrome
could not start" from a skip into a failure, because a green run that silently
skipped all 20 browser tests is worse than a red one; and it builds
`settings.py` with the same script a new developer runs, so the onboarding path
in 5.1 cannot rot unnoticed again.

**Follow-ups:** the workflow installs the full `requirements.txt`, which pulls
torch and the rest of the ML stack on every cache miss, though nothing the
tests touch needs it. Installing everything is deliberate — it also verifies
the README's install instructions — but if CI proves slow, split the file
rather than trimming the CI install. See 5.5.

The Node 20 deprecation warning is resolved: `actions/checkout` and
`actions/setup-python` are now on v7, merged from Dependabot with CI green on
both.

**Default branch renamed `master` → `main`.** The workflow lists
`branches: [main, master]` during the transition, because the push trigger is
the only branch-filtered part and renaming first would have stopped CI firing
on every push while still showing green from the last old run. GitHub redirects
`master` to `main` for fetches and clones, so existing checkouts keep working,
but the repository has 13 forks whose owners should re-point at their
convenience:

```
git branch -m master main
git fetch origin --prune
git branch -u origin/main main
git remote set-head origin -a
```

Drop `master` from the workflow trigger once that has settled.

### 2.4 The manifest exposed 15 front-end alerts; all are now cleared **[verified]**

Adding `/package.json` made Dependabot raise **15 alerts on libraries it had
never been able to scan** — one critical, two high, twelve medium. Before the
manifest existed the repository reported zero open alerts, which is the measure
of how much 2.1 was hiding.

| Change | Cleared | Cost |
| --- | --- | --- |
| Bootstrap 3.2.0 → 3.4.1 | 6 | drop-in dist swap |
| lodash 2.4.1 → **Underscore 1.13.8** | 5, incl. the critical | one call site |
| jQuery 1.11.1 → 3.7.1, jQuery UI → 1.13.3 | 3 | no application code |
| Bootstrap 3.4.1 → **5.3.8** | 2 | the migration below |

Three findings worth keeping.

**The lodash advisories were not reachable, but that was beside the point.**
None of `_.defaultsDeep`, `_.merge`, `_.set` or `_.zipObjectDeep` appears in
application code, and the three `_.template` calls compile hard-coded markup.
The blocker on upgrading was not how the app used lodash but how **Backbone**
did: lodash 4 renamed `_.any` to `_.some`, and Backbone 1.1.2 still calls it, so
lodash 4 killed the app on boot. Underscore — what Backbone is written against
— was the fix, not a workaround.

**An upgrade can hide a break.** Bootstrap 3.4's sanitizer, added upstream to
fix this very advisory class, stripped the `onclick` attributes the favourites
view generated. The injection was neutralised and the links stopped working at
the same time, and neither was visible without opening the popover and reading
the DOM. The underlying fault was ours: those handlers were built by
concatenating corpus-derived favourite keys into a script string, which an
ordinary English possessive is enough to break. Fixed by carrying the type in a
class and the key in the link text, read back by a delegated listener.

**Screenshots caught what the tests could not.** The Bootstrap 5 migration
introduced four visual regressions that 55 passing tests did not notice —
stacked global selectors, a stacked filter form, stacked footer pills, and
underlined links everywhere. One of them was not merely cosmetic: the taller
header overflowed the fixed 160px body padding and covered the page, so clicks
on the documents table were being intercepted by the navbar.

Migration notes, for the next framework move: dual-classing first (adding the
Bootstrap 5 name beside the Bootstrap 3 one wherever 5's name did not exist in
3) took the class renames out of the risky step entirely, and extracting
Glyphicons into a standalone stylesheet took another 35 changes out of it.
What remained was structural — the navbar, the JS API, and the two plugins
Bootstrap 5 has no equivalent for.

### 2.5 Django: stay on 5.2 LTS and wait for 6.2 **[decided]**

Dependabot proposes Django 6.1. It was declined deliberately; this records why,
so the PR is not merged reflexively when it reappears.

| Release | Support ends |
| --- | --- |
| **5.2 LTS** — what this project runs | **April 2028** |
| 6.0 | April 2027 |
| 6.1 | **December 2027** |
| **6.2 LTS** — ships April 2027 | **April 2030** |

**Moving to 6.1 would shorten the security horizon by four months rather than
extend it.** That inverts the usual reason to upgrade, and it is the whole
argument. This repository went roughly four years between Django upgrades; a
release with a 15-month window does not suit that cadence, whereas an LTS does.

There is a second cost. **Django 6.x requires Python ≥ 3.12**, while CI and the
development environment both run 3.11 — so 6.1 is two upgrades, not one.

**The plan: go 5.2 → 6.2 directly in April 2027.** One hop, LTS to LTS,
supported to 2030, skipping 6.0 and 6.1 entirely.

**Revisit early only on this signal:** a security advisory against Django with
no fix available in the 5.2 series. That is exactly what forced 4.2 → 5.2 — all
six of 4.2's final advisories listed first-patched versions in 5.2.x — and it
is worth watching for rather than upgrading on cadence.

**Worth doing now, independently:** upgrade Python 3.11 → 3.13. It is
unrelated to Django, removes half the change from the eventual 6.2 jump, and
can be validated by CI today. The ceiling is 3.13 because BERTopic's
classifiers stop there — *not* numba, whose `requirements.txt` note is stale;
numba supports 3.14 now. Fix that comment while you are there.

The suite emits no Django deprecation warnings on either 4.2 or 5.2, so
nothing in the code obstructs whichever path is taken.

### 2.6 nltk dropped rather than pinned — **done**

Dependabot raised CVE-2026-81726 (High, CVSS 4.0 8.3): NLTK's model-artifact
APIs — `TransitionParser`, `AveragedPerceptron`, `PerceptronTagger` and the
maxent parameter APIs — use raw file operations on caller-controlled paths and
so read and write outside the sandbox roots even with `nltk.pathsec`
`ENFORCE=True`. It affects **every release through 3.10.3, which is still the
newest on PyPI**, so there was no fixed version to pin to. It is the fourth in
the same family, after CVE-2026-54293 (`nltk.data.load()`), CVE-2026-12074
(`FramenetCorpusReader.frame()`) and the downloader's arbitrary file overwrite.

The resolution was to remove the dependency: a case-insensitive grep across the
repository matched `nltk` on exactly one line — its own entry in
`requirements.txt`. Nothing imports it. The stopword lists are plain files in
`stopwords/` and tokenization is hand-rolled in `import_tool/`. It was also
uninstalled from the development `venv/`, where `pip show` listed no
`Required-by`, so nothing else lost a dependency.

The suite passes unchanged without it (61 passed, 1 xfailed) and got roughly
4× faster — 59s to 14s — because nltk's import is no longer paid for at
collection. Worth remembering as the general lesson: **an unused pinned
dependency is a recurring alert with no upside**, and the rest of
`requirements.txt` deserves the same grep.

---

## 3. Performance

### 3.1 Attribute lambdas run per object, defeating the prefetches

`query_datasets`, `query_analyses`, `query_topics` and `query_documents` build
a dict of attribute lambdas and call them inside a loop over the queryset.
Some are prefetched, but others are not: `document_count` runs
`dataset.metric_values.filter(metric__name='Document Count')[0]` per dataset,
and `analysis_count` runs a `COUNT` per dataset. Topic and document attributes
have the same shape at much larger N — the documents query is bounded by
`MAX_DOCUMENTS_PER_REQUEST = 500`, so a single request can issue hundreds of
follow-up queries.

The `DEBUG` diagnostics in 2.2 already report `query_count`; point it at the
2D-plots query (which asks for 1000 documents with metadata, metrics and
top_n_topics) to size the problem before optimising.

### 3.2 The response cache almost never engages, and is never invalidated

`visualize/api.py:139` caches only when the request took over a second, `DEBUG`
is false, the path is under Django's 250-character key limit, and the query is
not for all datasets or all analyses. In development `DEBUG` is true, so it is
dead code; in production the long tail of specific queries is exactly what
exceeds the key limit.

Nothing invalidates the cache when an import or analysis writes new data, so a
re-import can serve stale results until the entry expires. Key the cache on
`Dataset.last_updated`/`Analysis.last_updated` (both already exist as
`auto_now` fields) and the staleness problem goes away along with the need to
guess at which requests are worth caching.

---

## 4. Testing

61 tests: 12 on `/api`, 6 on `/bertopic-viz`, 18 unit tests, and 25 in the
browser. Coverage was measured rather than guessed, with

    pytest --cov=visualize --cov=import_tool --cov-report=term-missing

and the headline is **22%**. The distribution matters more than the number:

| Module | Coverage | Note |
| --- | --- | --- |
| `visualize/root.py` | 90% | fine |
| `import_tool/basic_tools.py` | 84% | fine |
| `visualize/api.py` | 69% | the uncovered part is error paths — 4.3 |
| `visualize/models.py` | 61% | the uncovered part is where 1.1 lives — 4.5 |
| `visualize/bertopic_viz.py` | 21% | was 9%; measuring it found a bug — 4.4 |
| `visualize/utils.py` | 18% | `reservoir_sample` — 4.5 |
| `import_tool/import_system_utilities.py` | **0%** | 571 statements — 4.1 |
| `import_tool/metric/**` | **0%** | all 16 live metrics — 4.1 |
| `import_tool/tokenizer/**` | **0%** | 4.1 |

### 4.1 The import and analysis pipeline has no tests

`tg.py` and `import_tool/` are the core product — tokenising, running the topic
model, writing the ORM rows — and nothing covers them end to end.
`import_system_utilities.py` is **571 statements at 0%**, and every one of the
**16 metrics that run automatically on every import** is untested.

This is the largest remaining gap, and it is now cheap to close: import the
four-document corpus already in `tests/import_tool/test_resources/`, run
`import_tool/analysis/interfaces/random_analysis.py` — which needs no MALLET —
and assert the resulting Dataset, Analysis, Topic and Document rows plus the
metrics that get written along the way.

Two bugs fixed in this repository lived on exactly this path and were found by
inspection rather than by a test: the dead `import_tool/metric/` tree, and
`metric/utilities.py` rewriting `DJANGO_SETTINGS_MODULE` to a deleted package
on every import.

Pairs with 5.5: the same fixture is what a `make demo` target would use.

### 4.2 Coverage measurement — **done and wired in**

The numbers above came from `pytest-cov`, which is now a declared dependency
(`requirements.txt`) and runs on every build: the CI step in
`.github/workflows/tests.yml` passes `--cov=visualize --cov=import_tool`. A
local run reproduces the same **22%** total over 3,480 statements.

Deliberately no `--cov-fail-under`. At 22% a threshold would either be set so
low it means nothing or would fail every build; revisit once 4.1 has covered
the import pipeline.

### 4.3 The API's own error paths are thinly covered

`tests/visualize/test_api.py` covers the happy paths and two rejections, which
is most of `api.py`'s missing 31%. Not covered: a malformed or out-of-range
`document_limit`, an unknown dataset name mixed with a known one, and the
`%`-unescaping branch of `filter_set_to_list` at `api.py:48`. Worth extending
alongside 1.2, since fixing the error contract touches this code anyway.

### 4.4 `/bertopic-viz` was 9% covered, and that hid an access control bug **[verified]**

Measuring coverage is what surfaced this. The route looked its dataset up with
`Dataset.objects.get(name=...)` where `/api` uses
`filter(..., public=True, visible=True)`, so the two disagreed about who may
see what. Demonstrated against a `public=False, visible=False` dataset:
`/api?datasets=*` returned `[]` while `/bertopic-viz/secret_corpus/...` got past
both lookups and failed only because the model file was absent — with the
pickle present it would have rendered the visualization for anyone. Its error
messages were also an enumeration oracle, giving three distinguishable answers
for "no such dataset", "private dataset" and "wrong analysis type".

Fixed, with six tests where there were none; three of them fail against the
previous code.

The endpoint is still only 21% covered, because the rest needs a real BERTopic
pickle to exercise. That is the one place where a fixture is genuinely
expensive, so it is reasonable to leave — but note the route calls
`pickle.load` on a file path built from `dataset.dataset_dir`. That path comes
from the database rather than the URL, so it is not attacker-controlled today;
it is worth keeping that way deliberately rather than by accident.

### 4.5 Two specific gaps worth closing before the big one

**`MetadataValue.set` and `value()` in `models.py`.** Uncovered, and precisely
where the falsy-value bug in 1.1 lives. Tests here do double duty: they pin the
current behaviour and then verify the fix. `tests/conftest.py`'s `set_metadata`
already takes a datatype, so a parametrised test over int/float/bool/text at
their zero values is a few lines.

**`visualize/utils.py` at 18%.** `reservoir_sample` is the document-sampling
path `/api` takes whenever `document_limit` is exceeded. Sampling code is easy
to get subtly wrong and hard to notice when it is — worth a test that fixes the
seed and asserts the sample size, that every index is in range, and that the
same seed gives the same sample.

## 5. Documentation and onboarding

### 5.1 The README's settings instructions cannot work on a fresh clone **[verified]**

`README.md:73` says:

> **For most users, the existing `settings.py` file should work without
> modification.**

But `topicalguide/settings.py` is listed in `.gitignore`, so a fresh clone has
no `settings.py` at all. Copying the template is **mandatory**, not the "if you
need to customize" step the README presents at line 60. The README also says to
"keep `DEBUG = True` (already set)" while the template ships `DEBUG = False`.

The template itself had drifted to Django 1.7 until commit 41eeebe, so this
path was doubly broken: the instructions were wrong *and* the file they pointed
at would not boot. Rewrite section 3 as a required step, and verify it the way
that commit did — copy the template over a scratch settings file, run
`manage.py check` and `pytest`.

### 5.2 The README sends users to a third-party site for a SECRET_KEY

`README.md` links to `miniwebtool.com/django-secret-key-generator` to generate
a production secret. Keys should not be minted by a third party. The template
now carries the local one-liner
(`django.core.management.utils.get_random_secret_key`); point the README at
that instead.

### 5.3 No architecture note

Nothing explains that the app is a Backbone single-page client rendering from
one `/api` endpoint, that views register themselves via
`globalViewModel.addViewClass`, or that the client caches API responses in
`localStorage` under the request URL. That last one is not a detail anyone
would guess — it made the browser tests order-dependent until the fixture
started clearing storage per test, and it means a developer chasing "stale
data" symptoms will look at Django before they look at the browser.

A short `docs/architecture.md` covering request flow, view registration and
client-side caching would save the next person the reconstruction.

### 5.4 The README has drifted well beyond its settings section

5.1 and 5.2 are specific errors. The file needs a full pass — it is 566 lines
and much of it no longer describes this project.

- It tells users to "switch `DBTYPE` to `'postgres'`" (line 186). **`DBTYPE`
  does not exist anywhere in the codebase** — not in the settings template, not
  in any `.py`. The whole POSTGRESQL section needs checking against how
  `DATABASES` is actually configured.
- It never mentions tests, though there are now 49 and CI runs them on every
  push. It needs a "Running the tests" section covering `pytest` and the
  environment variables the browser fixture honours: `HEADED`, `CHROMEDRIVER`,
  `TG_REQUIRE_BROWSER`, `TG_TEST_URL`, `TG_TEST_WAIT`.
- It never mentions `scripts/bootstrap_settings.py`, now the supported way to
  create `settings.py` and what CI runs.
- It says "Python 3.10 or higher" while `requirements.txt` notes BERTopic's
  numba dependency needs ≤ 3.13. State the supported window; CI runs 3.11.
- It says to `pip install openai` separately, but openai is in
  `requirements.txt`.
- Its import examples use `--number-of-topics 20` while
  `default_datasets/import_state_of_the_union.sh` uses 100.
- **Lines 269–566 are a forward-looking essay** — roughly half the file —
  that now overlaps and disagrees with sections 0, 6 and 7 here. Cut it,
  condense it, or move it into this document, so there is one place for
  proposals rather than two that contradict each other.

### 5.5 A fresh clone has nothing to look at

The database starts empty, so the app renders "No datasets yet" and none of the
six views can be seen without first running the full import and MALLET
analysis. That is a steep first five minutes for a tool whose value is visual.

Git LFS is the right mechanism for shipping a prebuilt database, but the sizing
decides the approach:

- `working/tg.sqlite3` is 1 GB. GitHub's free LFS tier is 1 GB of storage and
  1 GB/month of bandwidth, so one copy exhausts it, and every re-import stores
  another **full** 1 GB object — SQLite files do not delta-compress, and LFS
  deduplicates whole objects only.
- That file must not be published in any case: it is the one carrying the 1.76
  million foreign key violations in 1.6. Shipping it distributes the corruption
  to every clone.

Cheaper options to price first: a trimmed demo database (one dataset, one
20-topic analysis — likely tens of MB), or nothing binary at all. The corpus is
already in the repository, and `random_analysis.py` gives an analysis with no
MALLET dependency, so a `make demo` target could build a usable database in
seconds — which also exercises the pipeline that 4.1 wants tested.

A related follow-up from 2.3: splitting the optional ML packages into
`requirements-ml.txt` and the test tooling into `requirements-dev.txt` would
cut CI install time substantially. Check that Dependabot still picks up the new
files by name before splitting — dropping packages out of scanning would repeat
the blind spot in 2.1.

---

## 6. Discovery with modern ML

Everything above is a fix or an unlock of something already built. This section
is about capabilities the code does not have at all.

The framing question is what a researcher wants from a document collection:
*what is in here, what is unusual, and where is the evidence?* A topic model
answers the first. The app currently has no answer to the second or third, and
the ingredients for both are already in `requirements.txt` —
`sentence-transformers`, `umap-learn`, `hdbscan`, and an LLM client.

**What exists today, precisely.** `extract_embeddings.py` pulls
`topic_embeddings_` out of a pickled BERTopic model — *topic*-level vectors,
only for BERTopic analyses, stored on disk outside the database.
`llm_namer.py` calls an LLM to turn a topic's top words and a few sample
documents into a short name. That is the entire extent of embedding and LLM
use. There are **no document or passage embeddings, no vector index, and no
retrieval of any kind.**

That single absence is what limits most of what follows.

### 6.1 Semantic search over documents and passages

The only text-based entry point in the app is the topics view's exact-word
filter. A user who does not already know a corpus's vocabulary — its era's
idiom, its euphemisms, its spelling — cannot find anything.

Embedding documents (and the subdocuments the importer already produces) with
`sentence-transformers`, then searching by vector similarity, changes the entry
point from "which word appears" to "what is this about". At this corpus size a
NumPy matrix and a dot product suffice; no vector database is needed until the
collection is orders of magnitude larger.

Worth doing as **hybrid** retrieval — dense vectors plus BM25 — because
historical corpora are exactly where exact terms still matter: a user searching
for a specific phrase should not have it smoothed away by a nearest-neighbour
search.

This is the foundation for 6.2, 6.3 and 6.5, and the highest-value item in this
section.

### 6.2 Grounded question answering over the collection

With passage retrieval in place, the natural interface is a question:
"how did presidents talk about immigration between the wars?" Retrieve the
relevant passages, have an LLM answer *from those passages only*, and cite each
claim back to a document and offset.

The citation substrate already exists — `Document.get_key_word_in_context()`
returns character offsets, and the single-document view already highlights
spans — so answers can link into the exact passage rather than gesturing at a
document. That matters: an ungrounded summary is a liability in research, and a
cited one is evidence.

Keep the retrieved passages visible beside the answer, so the user can audit
what the model was given rather than trusting the prose.

### 6.3 A semantic map of the collection

The 2D-plots view positions documents on axes the user chooses — a metadata
field or a topic proportion. That answers a question you already have. It
cannot show you the shape of the collection.

Projecting document embeddings with UMAP (already a dependency, already used by
BERTopic internally) gives a map where proximity means similarity, clusters are
discovered rather than specified, and outliers are visible. Colour it by
metadata — president, era, party — and the comparative questions from 0.3
become visual. Cluster with HDBSCAN (also already a dependency) and you have a
second, embedding-native view of structure to set against the topic model's.

### 6.4 Topic summaries and representative passages, not just names

`llm_namer.py` produces a short label. The same retrieved context could produce
much more: a paragraph describing what the topic covers and how it is used, the
passages most representative of it, the passages most *atypical* of it, and a
note on how it shifts across the time axis.

A label tells you a topic exists. A summary with evidence tells you whether it
is worth your afternoon.

### 6.5 Contrastive analysis: what distinguishes these documents from those?

This is the question a comparative corpus invites and the app cannot answer at
all. Given two subsets — two presidents, two eras, two parties — report the
language that distinguishes them.

The established statistical method is log-odds with an informative Dirichlet
prior (Monroe, Colaresi and Quinn), which is well-behaved on the small,
unbalanced subsets this corpus produces and does not require any ML
infrastructure. Layering an LLM summary of the distinguishing terms on top
turns a word list into a readable characterisation.

Pairs naturally with 0.3's faceting: once a user can select a subset, the
obvious next affordance is comparing it to its complement.

### 6.6 Semantic drift: how a topic's meaning changes, not just its share

Topics Over Time plots how much a topic is discussed. It cannot show that the
*content* of a topic changed — that "defense" in 1850 and "defense" in 1985 are
different subjects wearing the same label. The README already names this as an
ambition, mentioning dynamic topic models and time slices.

Embedding a topic's contexts per era and tracking the trajectory would surface
the corpus's most interesting finding class: continuity of vocabulary masking
discontinuity of meaning. That is a genuine research contribution, not a
convenience feature, and this corpus's 235-year span is unusually well suited
to it.

### 6.7 Rank what is interesting, rather than waiting to be asked

Every view in the app is a query interface: the user must know what to look
for. Nothing volunteers a finding.

Cheap, high-value additions in rough order of effort: rank topics by how much
their share changed over time (this alone fixes 0.2's blank default); flag
years or documents that introduced unusual language, via novelty against a
trailing window; detect bursts. A short "what stands out in this collection"
panel on the dataset page would change the app's posture from a browser into a
discovery tool — which is what the name promises.

### 6.8 Measure whether the models are any good

0.5 asks for analyses to be comparable in the interface; this asks for them to
be comparable *numerically*. Without that, choosing between 20 topics, 100
topics and BERTopic is guesswork.

Standard automated coherence (NPMI over a reference corpus) is the baseline.
An LLM-judged word-intrusion test — the human evaluation from Chang et al.,
automated — is a good modern complement, and cheap at this scale. Report both
per analysis, so model selection becomes evidence-based and so the effect of
future pipeline changes is measurable rather than felt.

### Notes on doing this well

- **Store embeddings in the database, versioned by model.** Today's topic
  vectors live in a pickle beside the analysis; embeddings that several
  features depend on need to be first-class rows, tagged with the model and
  revision that produced them, or results become irreproducible the first time
  a model is upgraded.
- **Keep the LLM out of the trusted path.** Use it to summarise, label and
  explain retrieved evidence — never as the source of a fact the user cannot
  check. Every generated statement should link to the passage behind it.
- **Pin and record model versions.** `llm_namer.py` hard-codes its model as a
  default argument. Generated names, summaries and evaluations should record
  which model produced them, or a corpus ends up with topic names from three
  different eras and no way to tell them apart.
- **Treat embedding cost as an import-time step.** Embedding a collection
  belongs in the `tg.py` pipeline next to tokenising and modelling, not in a
  request handler.

## 7. Beyond document embeddings: what else to embed

Section 6 assumes the obvious move — embed documents, search them. This section
is about the less obvious question: *what other objects are worth embedding?*
Several of these need no new data at all, only a different reading of the
schema that already exists.

**The asset nobody is using.** `WordToken` stores every token *occurrence* with
its document, its `token_index`, and a `start_index` character offset into the
source text. `WordTokenTopic` attaches the topic assignment to that
occurrence — not to the word type. `Document.get_key_word_in_context()` already
materialises the surrounding window for any occurrence.

So the database holds, for every word in the corpus: where it appeared, what
surrounded it, and which topic the model assigned *that instance*. Most topic
browsers keep only type-level counts. This one can support occurrence-level
work, and does not.

### 7.1 Embed occurrences, not word types — and get word senses for free

Embed each token occurrence in its context window. Cluster the occurrences of a
word and its senses separate out: "defense" splits into military, legal and
fiscal; "address" into speech and location; "state" into polity, condition and
the verb.

What that unlocks:

- **Topics described by senses rather than strings.** Two topics that both list
  "state" in their top words may be about entirely different things, and today
  nothing reveals that. Sense-resolved top words would.
- **Honest word statistics.** Every count in the app is type-level, so senses
  are silently pooled. Occurrence clustering makes "% of topic" and top-word
  lists say what they appear to say.
- **A sharper reading view.** The single-document view already highlights token
  spans; highlighting by *sense* rather than by string is a small change to a
  view that already exists.

The joins are already there. This is a genuinely distinctive capability, and
the schema was apparently built for it.

### 7.2 Diachronic embeddings: measure meaning change, don't infer it

6.6 proposes tracking semantic drift. The rigorous form: train or fine-tune a
separate embedding space per era, align consecutive spaces by orthogonal
Procrustes, then measure each word's displacement — the HistWords method
(Hamilton, Leskovec and Jurafsky).

The deliverable is a ranked list: *the words whose meaning moved most*, each
with its nearest neighbours in 1800 beside its nearest neighbours in 2000. On
a 235-year single-genre corpus with consistent form, that is close to an ideal
testbed — genre and register are held roughly constant, so displacement is
more plausibly meaning and less plausibly style.

This is the finding a historian would actually publish, and no view in the app
comes close to it today.

### 7.3 Embed presidents, eras and analyses — not just text

Documents are not the only objects with a position in semantic space.

- **Speakers.** A per-president embedding — pooled from their documents, or
  learned directly — gives a rhetorical similarity map. "Who does this
  president sound most like?" is immediately interesting, frequently
  surprising, and completely unavailable today.
- **Years and eras.** Embedding each time slice gives the corpus a trajectory
  through semantic space: where it moved fast, where it stalled, and which
  distant years *rhyme*. Finding that the early 1930s sit near 2008–09 is the
  kind of result that starts a paper.
- **Topics across analyses.** Embedding topics from different analyses into one
  space lets them be aligned by similarity — which is exactly the machinery
  0.5's side-by-side comparison needs. It answers "what did LDA-100 split that
  LDA-20 merged?" and "what did BERTopic find that LDA missed?" concretely
  rather than impressionistically.

### 7.4 Let researchers define their own axes

The most expressive idea here, and among the cheapest to build.

A semantic axis can be defined by its poles: supply a handful of example
passages (or word sets) for each end — optimistic ↔ pessimistic, concrete ↔
abstract, domestic ↔ foreign, conciliatory ↔ combative — take the difference of
the pole centroids, and project the whole corpus onto it.

That turns the 2D-plots view from a chooser over fixed fields into an
instrument the researcher configures: *pick your own two dimensions, by
example, and see where every document falls.* Related and equally cheap: a
**concept probe**, where a user supplies five passages exemplifying something
they cannot name precisely, and the corpus is scored and ranked by it. Search
by resemblance instead of by keyword, for concepts with no reliable keyword.

Both are a few dot products over precomputed vectors. The expressive range is
out of all proportion to the effort.

### 7.5 Separate what is said from how it is said

Embeddings mix content and style. Partial out speaker identity — train a probe
to predict the speaker, then project its direction out — and you get a content
space where similarity is not dominated by personal idiom. Keep the removed
component and you get a style space instead.

That distinction matters for the comparative question in 6.5: when two
presidents look different, is it because they addressed different subjects, or
because they addressed the same subjects differently? Nothing in the app can
currently tell those apart, and they are different findings.

### 7.6 Trace echoes and influence

State of the Union addresses are formulaic and self-referential; passages get
reused, paraphrased and answered across administrations. Passage-level
embeddings plus nearest-neighbour search across the whole corpus surfaces those
echoes — near-duplicates first, then paraphrases at a looser threshold.

"Which later address most closely echoes this passage?" is a question with a
concrete, checkable answer and an obvious route into a finding. It is nearly
free once 6.1 exists, and unlike most similarity features its results are
self-evidently interesting rather than requiring interpretation.

### 7.7 Score passages against their own era

With per-era spaces from 7.2, each passage can be scored against the era it
came from: which passages used language that had not yet settled into its
period's idiom, and which read as holdovers. Ranking a corpus by how *unusual
for its moment* each passage is gives a novelty detector that is native to the
collection rather than imported from a general-purpose model.

This pairs with 6.7 — it is a principled way to decide what "stands out" is
worth surfacing.

### 7.8 Interface ideas that fall out of any of the above

- **Query by example.** Select a span in the reading view, get the most similar
  passages across the collection. The selection affordance already exists.
- **Semantic diff.** Given two documents, or two subsets, show what each says
  that the other does not.
- **A reading tour.** Order a diversity-maximising path through the collection
  so a newcomer sees its range in ten documents rather than its first ten.

### Sequencing

7.4 and 7.6 are the quick wins once passage embeddings from 6.1 exist — days,
not weeks, and both produce visible results immediately. 7.1 and 7.3 need no
new modelling either, only occurrence-level and object-level embedding runs
over data already in the database. 7.2 and 7.5 are the research-grade items and
deserve their own design.

## Three things to carry forward

**4.1 is the largest coverage gap.** 61 tests cover `/api` and the single-page
app well; the import and analysis pipeline — the core product — is at 0%.

**0.4's five recoverable metrics are the cheapest way to make the topics table
say something useful.** Right now it shows only "% of Corpus" and "% of Topic",
so a reader cannot tell a coherent topic from noise.

**Measuring coverage found a bug, twice over.** The 9% file turned out to be
serving private datasets (4.4), and the uncovered half of `models.py` is
exactly where the falsy-value bug lives (1.1, 4.5). Low coverage is not only a
missing-tests problem; it marks the code nobody has looked at recently.
