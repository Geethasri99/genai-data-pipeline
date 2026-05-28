"""
genai-data-pipeline/pipeline.py
LLM-powered pipeline: classify, summarize, and enrich structured records via OpenAI GPT.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any
import openai
from prompts import CLASSIFY_PROMPT, SUMMARIZE_PROMPT, ENRICH_PROMPT

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

openai.api_key = "OPENAI_API_KEY"
MODEL = "gpt-4o-mini"
MAX_CONCURRENT = 5
COST_PER_1K_INPUT  = 0.00015
COST_PER_1K_OUTPUT = 0.00060


@dataclass
class TokenUsage:
      prompt_tokens: int = 0
      completion_tokens: int = 0

    @property
    def cost_usd(self) -> float:
              return (
                            self.prompt_tokens  / 1000 * COST_PER_1K_INPUT +
                            self.completion_tokens / 1000 * COST_PER_1K_OUTPUT
              )

    def add(self, usage):
              self.prompt_tokens     += usage.prompt_tokens
              self.completion_tokens += usage.completion_tokens


@dataclass
class EnrichedRecord:
      record_id: str
      original: dict
      category: str      = ""
      summary: str       = ""
      enriched_fields: dict = field(default_factory=dict)
      error: str         = ""


async def call_llm(prompt: str, content: str, usage: TokenUsage) -> str:
      response = await asyncio.to_thread(
                openai.chat.completions.create,
                model=MODEL,
                messages=[
                              {"role": "system", "content": prompt},
                              {"role": "user",   "content": content},
                ],
                temperature=0.1,
                max_tokens=512,
      )
      usage.add(response.usage)
      return response.choices[0].message.content.strip()


async def process_record(record: dict, semaphore: asyncio.Semaphore, usage: TokenUsage) -> EnrichedRecord:
      result = EnrichedRecord(record_id=record.get("id", "unknown"), original=record)
      content = json.dumps(record, ensure_ascii=False)
      async with semaphore:
                try:
                              result.category = await call_llm(CLASSIFY_PROMPT, content, usage)
                              result.summary  = await call_llm(SUMMARIZE_PROMPT, content, usage)
                              enriched_raw    = await call_llm(ENRICH_PROMPT, content, usage)
                              result.enriched_fields = json.loads(enriched_raw)
except Exception as e:
            logger.error(f"Record {result.record_id} failed: {e}")
            result.error = str(e)
    return result


async def run_pipeline(records: list[dict]) -> list[EnrichedRecord]:
      semaphore = asyncio.Semaphore(MAX_CONCURRENT)
      usage = TokenUsage()
      start = time.time()
      logger.info(f"Processing {len(records)} records (max_concurrent={MAX_CONCURRENT})")
      tasks = [process_record(r, semaphore, usage) for r in records]
      results = await asyncio.gather(*tasks)
      elapsed = time.time() - start
      logger.info(f"Done in {elapsed:.1f}s | tokens={usage.prompt_tokens + usage.completion_tokens} | cost=${usage.cost_usd:.4f}")
      return list(results)


def load_records(path: str) -> list[dict]:
      with open(path) as f:
                return json.load(f)


def save_results(results: list[EnrichedRecord], path: str):
      with open(path, "w") as f:
                json.dump([r.__dict__ for r in results], f, indent=2)
            logger.info(f"Saved {len(results)} enriched records to {path}")


if __name__ == "__main__":
      records = load_records("data/input.json")
    results = asyncio.run(run_pipeline(records))
    save_results(results, "data/output.json")
