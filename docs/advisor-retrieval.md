# Advisor Retrieval Layer

I added retrieval after the deterministic advisor context pack and before any LLM answer generation.

The job of this layer is to find trusted background context from the project docs. The LLM should use this to explain concepts such as personal inflation, Bank Rate impact, forecasting validation, and the health score methodology.

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

## What It Searches

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

Each file has tags, for example:

- `cost-of-living-engine.md`: inflation, ONS, cost of living, personal inflation.
- `spend-forecasting.md`: forecasting, time series, backtesting, baseline.
- `financial-health-score.md`: health score, savings, debt, housing, benchmarks.

## How Chunking Works

I split each markdown file by headings.

Each chunk stores:

- `id`
- `title`
- `source`
- `heading_path`
- `text`
- `tags`
- token list used for scoring

This means citations point to a clear source and section, not a vague bundle of text.

## How Retrieval Works

For now, retrieval is local and dependency-free.

The scoring uses:

- token overlap between the question and chunk text
- simple inverse document frequency weighting
- phrase boosts for matching neighbouring words
- tag boosts for finance-specific concepts

I chose this before embeddings because the knowledge base is still small and mostly project-authored. It is easier to inspect and explain, and the tests can prove exactly which source should be retrieved for common questions.

## Why Not A Vector Database Yet

I do not need pgvector, Pinecone, or a hosted vector store for the first advisor.

The current knowledge base is small enough to load from markdown on demand. Once I add more official guidance, longer documents, or user-specific historical notes, then embeddings and a vector index will make more sense.

## Tests

The tests check that:

- markdown splits into heading chunks
- inflation questions retrieve the cost-of-living docs
- random train/test split questions retrieve the forecasting docs
- health score questions retrieve the health-score docs
- source filters restrict results
- the FastAPI endpoint returns citation-ready chunks

## How This Fits The RAG Advisor

The future answer flow should be:

```text
question
  -> advisor context pack
  -> retrieve relevant docs
  -> build guarded prompt
  -> LLM structured answer
```

The context pack supplies trusted user numbers. The retrieval layer supplies trusted explanation text. The LLM should only turn those into a clear answer with citations.
