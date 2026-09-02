# Opportunities

Observations from working through the test suite, the `/api` endpoint, the
Backbone front end and the import pipeline. Each item says what is wrong, how
it was verified, and why it matters. Ordered roughly by value per unit of
effort within each section.

Items marked **[verified]** were reproduced directly; the rest are readings of
the code that still deserve a confirming test before acting.

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

### 0.2 Topics Over Time shows nothing until you know to ask **[verified]**

The view loads with **no topic selected** and an empty plot; you must know to
multi-select from the topics list before anything is drawn. The test
`test_topics_over_time_draws_a_bar_per_year_for_a_topic` documents exactly this.

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

**Correction to an earlier draft of this file.** This item originally said
these metrics were "computed but not surfaced", implying they only needed
reconnecting. They were not computed. Nine metric modules had been commented
out of their registries for years, and were written against the pre-4.2
`add_metric()` protocol and models that no longer exist — `TopicMetric`,
`topic.topicword_set`, `word.ngram`, `word.type`. They could not have run.
They have since been removed from the tree, and remain in git history — see
`git log --diff-filter=D -- import_tool/metric/`.

What was lost, and what reviving each would take:

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

### 1.4 27 bare `except:` clauses **[verified]**

`grep -rn "except:" --include="*.py" . | grep -v venv` returns 27, including
`import_tool/basic_tools.py` (three), `import_tool/analysis/utilities.py` and
`import_tool/analysis/bigram_finder.py`. A bare `except:` swallows
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

---

## 2. Security and operations

### 2.1 Vendored front-end libraries are a decade old **[verified]**

`visualize/static/scripts/libs/` ships jQuery **1.11.1** (2014), d3 v3,
Backbone and lodash as committed files with no manifest. jQuery below 3.5.0
carries known XSS advisories (CVE-2020-11022, CVE-2020-11023) in
`html()`/`append()` handling of untrusted markup — and the views build markup
from API data throughout.

Because these are vendored blobs rather than entries in a `package.json`,
**Dependabot does not see them at all**. The 6 open alerts on this repo are all
Python; the front end is an unscanned blind spot. Introducing a manifest (even
one that only records versions) would put them under the same scrutiny as the
Python dependencies.

### 2.2 `DEBUG` puts every SQL query in the API response body

`visualize/api.py:144` attaches `query_count`, `queries` and `total_time` to
each response when `DEBUG` is true. That is useful in development and an
information disclosure if `DEBUG` is ever true in a deployment — it exposes
schema and query structure to any caller. Gate it on an explicit setting
(`TG_API_DIAGNOSTICS`) rather than on `DEBUG`, so switching `DEBUG` on to chase
a bug in a shared environment does not also start publishing the query log.

### 2.3 No CI **[verified]**

There is no `.github/` directory. The 49-test suite added this session runs
only when someone remembers to run it. A workflow on push and pull request
would cost very little: `pip install -r requirements.txt` then `pytest`. Chrome
is preinstalled on GitHub's `ubuntu-latest` runners and the browser fixture
already falls back to Selenium Manager and honours `HEADLESS`, so the browser
tests need no extra setup.

This matters most for the Django 5.2 upgrade — that is exactly the change you
want a green run on before merging.

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

### 4.1 The import and analysis pipeline has no tests

`tg.py` and `import_tool/` are the core product — tokenising, running the topic
model, writing the ORM rows — and nothing covers them end to end. The unit
tests reach `basic_tools` and `GenericDataset`; everything downstream of
`import_system_utilities` is untested.

A small end-to-end test is now cheap to write: import the four-document
corpus already in `tests/import_tool/test_resources/`, run the smallest
analysis available, and assert the resulting Dataset/Analysis/Topic/Document
rows. That would also have caught the dead `import_tool/metric/` tree (task #1)
years ago.

### 4.2 No coverage measurement

Nothing reports what the 49 tests actually exercise. Adding `pytest-cov` and a
`--cov=visualize --cov=import_tool` run would show where the gaps are rather
than leaving it to intuition — useful input to 4.1 in particular.

### 4.3 The API's own error paths are thinly covered

`tests/visualize/test_api.py` covers the happy paths and two rejections. It
does not cover a malformed `document_limit`, an out-of-range int, an unknown
dataset name mixed with a known one, or unicode in the filter-set parser
(`filter_set_to_list` has a `%`-unescaping branch at `api.py:48` that nothing
exercises). Worth extending alongside 1.2, since fixing the error contract will
touch this code anyway.

---

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

## Where to start

If only a few of these get done:

1. **0.9** — the wrong command in the empty state. One line, and it is the
   first thing a new user reads.
2. **0.1** — re-enable the two finished visualizations. The code is written;
   the browser tests will tell you within minutes whether they still work.
3. **0.2** — default Topics Over Time to the topics that changed most. Turns
   the app's signature view from blank into an answer.
4. **2.3** — CI, before the Django upgrade rather than after.
5. **1.1** — the falsy-metadata bug. Small fix, and it silently corrupts any
   zero or `False` in the data.

And if there is appetite for one larger build: **6.1**, document and passage
embeddings with hybrid search. It is the missing foundation under semantic
search, grounded question answering, the semantic map and contrastive analysis
— four of the six discovery features in section 6 are blocked on it, and the
libraries are already installed.

Once that exists, **7.4** (researcher-defined semantic axes) is the highest
ratio of expressive power to effort in this document: a difference of two
centroids and a projection, and the 2D-plots view becomes an instrument the
researcher configures by example rather than a chooser over fixed fields.

The most *distinctive* item, in the sense that few tools could offer it, is
**7.1** — the database already records every token occurrence with its context
offset and its own topic assignment, which is exactly what word-sense work
needs and what type-level topic browsers throw away.

## Relationship to the session task list

- Task #1 (Python 2 → 3) overlaps 1.4 — several bare excepts sit in the same
  unmigrated modules — and its migrate-or-delete decision for
  `import_tool/metric/` should account for 0.4, which wants those metrics
  surfaced rather than deleted.
- Task #4 (Django 5.2) should land after 2.3 (CI), so the upgrade gets a green
  run before merge.
- Section 4.1 is the largest remaining coverage gap now that the SPA and API
  are covered.
