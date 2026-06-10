# Configuration, API, and Environment Spec

## .env.example

```bash
# OpenAI
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL_EXTRACT=gpt-5.5
OPENAI_MODEL_WRITE=gpt-5.5
OPENAI_MODEL_FAST=gpt-5.4-mini

# Gemini
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL_EXTRACT=gemini-3-pro
GEMINI_MODEL_FAST=gemini-3-flash

# Optional external services
SEMANTIC_SCHOLAR_API_KEY=
CROSSREF_MAILTO=
GROBID_URL=http://localhost:8070

# Runtime
CACHE_DIR=.cache
OUTPUT_DIR=outputs
MAX_PAPER_CHUNK_TOKENS=12000
MAX_REPAIR_RETRIES=2
ENABLE_WEB_SEARCH=false
ENABLE_GROBID=false
```

## requirements.txt

```text
pydantic>=2.7
python-dotenv>=1.0
pymupdf>=1.24
pandas>=2.2
numpy>=1.26
pyyaml>=6.0
bibtexparser>=1.4
rich>=13.7
tenacity>=8.2
orjson>=3.10
openai>=2.0.0
google-genai>=1.0.0
langgraph>=0.2.0
scikit-learn>=1.4
rapidfuzz>=3.6
latexcodec>=2.0
```

Make `langgraph` optional if implementing a simple custom workflow.

## Model provider interface

```python
class LLMProvider(Protocol):
    def generate_text(self, prompt: str, *, model: str, temperature: float = 0.2) -> str: ...
    def generate_json(self, prompt: str, schema: dict, *, model: str, temperature: float = 0.0) -> dict: ...
```

## OpenAI client requirements

- Load `OPENAI_API_KEY` from environment.
- Support structured JSON outputs.
- Log model name, token usage, and cost estimate if available.
- Retry transient API errors with exponential backoff.

Pseudo-code:

```python
from openai import OpenAI
client = OpenAI()

response = client.responses.create(
    model=model,
    input=prompt,
    text={
        "format": {
            "type": "json_schema",
            "name": "paper_extraction",
            "schema": schema,
            "strict": True,
        }
    },
)
```

## Gemini client requirements

- Load `GEMINI_API_KEY` from environment.
- Support JSON schema / structured output.
- Use Gemini as verifier/critic or writing alternative.

Pseudo-code:

```python
from google import genai
from google.genai import types
client = genai.Client()

response = client.models.generate_content(
    model=model,
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
        temperature=0.0,
    ),
)
```

## Routing policy

`configs/models.yaml` should define:

```yaml
routes:
  metadata:
    primary: openai.extract
    verifier: gemini.fast
  method_extraction:
    primary: openai.extract
    verifier: gemini.extract
  benchmark_extraction:
    primary: openai.extract
    verifier: gemini.fast
  taxonomy_proposal:
    primary: openai.write
    critic: gemini.extract
  drafting:
    primary: openai.write
    critic: gemini.extract
  refinement:
    primary: openai.write
    critic: gemini.fast
```

## Caching

Cache key:

```python
sha256(json.dumps({
    "provider": provider,
    "model": model,
    "schema_version": schema_version,
    "prompt": prompt,
    "input_hash": input_hash,
}, sort_keys=True).encode()).hexdigest()
```

Cache files:

```text
.cache/llm/<cache_key>.json
```

## Security

- Never commit `.env`.
- Provide `.env.example` only.
- Do not log API keys.
- Redact keys from exceptions.
- Store paper text locally only.
