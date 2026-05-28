# genai-data-pipeline

**LLM-powered data pipeline** that classifies, summarizes, and enriches structured records using OpenAI GPT-4o-mini. Features async concurrent processing with rate-limit control and per-run token cost tracking.

## Architecture

```
data/input.json
      |
[run_pipeline()] — asyncio.gather with semaphore (max 5 concurrent)
      |
  per record:
  ├── classify  → category label
  ├── summarize → one-line summary
  └── enrich    → structured JSON fields
      |
data/output.json
```

## Features

- Async batch processing via `asyncio` + `asyncio.Semaphore` for rate-limit control
- - Three LLM calls per record: classification, summarization, enrichment
  - - Token usage tracking with USD cost estimation (GPT-4o-mini pricing)
    - - Dataclass-based result model with per-record error isolation
      - - Prompt template registry (`prompts.py`) for easy iteration
       
        - ## Project Structure
       
        - ```
          genai-data-pipeline/
          ├── pipeline.py      # Async orchestrator + LLM caller
          ├── prompts.py       # Prompt template registry
          ├── data/
          │   ├── input.json   # Sample input records
          │   └── output.json  # Enriched output (generated)
          └── requirements.txt
          ```

          ## Quick Start

          ```bash
          pip install openai
          export OPENAI_API_KEY=your_key_here
          python pipeline.py
          ```

          ## Sample Output

          ```json
          {
            "record_id": "tx_001",
            "category": "high_value_purchase",
            "summary": "Large electronics purchase from US-East region",
            "enriched_fields": { "risk_flag": false, "segment": "premium" }
          }
          ```

          ## Tech Stack

          `OpenAI GPT-4o-mini` · `asyncio` · `Python 3.11` · `LangChain-ready`
