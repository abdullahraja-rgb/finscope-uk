# Advisor Retrieval Layer

The retrieval layer finds trusted background context from selected project docs. Advisor answers use these chunks to explain concepts such as personal inflation, Bank Rate impact, forecast validation, and financial-health scoring.

## Endpoint

```text
POST /api/v1/advisor/retrieve
```

Example request:

```json
{
  "question": "Why is inflation affecting my personal budget?",
  "max_chunks": 4
}
```

Example response shape:

```json
{
  "query": "Why is inflation affecting my personal budget?",
  "chunks": [
    {
      "id": "cost-of-living-engine.md:cost-of-living-engine:1",
      "title": "Cost Of Living Engine",
      "source": "cost-of-living-engine.md",
      "heading_path": ["Cost Of Living Engine"],
      "text": "...",
      "score": 1.23,
      "tags": ["inflation", "ons", "cost-of-living", "personal-inflation"]
    }
  ],
  "notes": []
}
```

## Search Corpus

The retriever reads selected markdown files from `docs/`:

- `advisor-context.md`
- `cost-of-living-engine.md`
- `financial-health-score.md`
- `rate-impact-engine.md`
- `recommendations-engine.md`
- `spend-forecasting.md`
- `transaction-categorisation.md`
- `dashboard-data-flow.md`
- `upload-analysis-flow.md`

Each file has finance-domain tags. Examples:

- `cost-of-living-engine.md`: inflation, ONS, cost of living, personal inflation.
- `spend-forecasting.md`: forecasting, time series, backtesting, baseline.
- `financial-health-score.md`: health score, savings, debt, housing, benchmarks.

## Chunking

Markdown files are split by headings. Each chunk stores:

- `id`
- `title`
- `source`
- `heading_path`
- `text`
- `tags`
- token list used for scoring

This gives citations a clear source and section.

## Retrieval Modes

Retrieval runs in one of two modes, chosen by `ADVISOR_RETRIEVAL_MODE`.

### Lexical mode

The default scorer uses:

- token overlap between the question and chunk text
- simple inverse document frequency weighting
- phrase boosts for neighbouring-word matches
- tag boosts for finance-specific concepts

Lexical mode is dependency-free and easy to test.

### Hybrid mode

Set `ADVISOR_RETRIEVAL_MODE=hybrid` to add a dense semantic signal:

- Chunks are embedded once with a local `fastembed` model and cached in memory.
- The question is embedded and compared to each chunk with cosine similarity.
- Lexical and dense rankings are combined with Reciprocal Rank Fusion.

Embeddings use `BAAI/bge-small-en-v1.5` by default. The corpus is small enough for in-memory vectors, so no vector database is needed yet.

If `fastembed` is unavailable or the model cannot load, retrieval falls back to lexical mode and records a note.

## Tests

The tests check that:

- markdown splits into heading chunks
- inflation questions retrieve cost-of-living docs
- random train/test split questions retrieve forecasting docs
- health-score questions retrieve health-score docs
- source filters restrict results
- the FastAPI endpoint returns citation-ready chunks

## Advisor Flow

```text
question
  -> advisor context pack
  -> retrieve relevant docs
  -> build guarded prompt
  -> structured advisor answer
```

The context pack supplies trusted user numbers. The retrieval layer supplies trusted explanation text.
