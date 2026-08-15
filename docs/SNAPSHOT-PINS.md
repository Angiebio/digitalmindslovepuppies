# SNAPSHOT PINS — exact served deployments
**Retrieved 2026-08-15T21:17:32+00:00 · harness/pin_snapshots.py v1.0 · sources: Anthropic /v1/models, OpenRouter /v1/models + /endpoints, Spark vLLM /v1/models, ollama /api/tags**

Freeze rule: `scenarios/snapshot_pins.json` feeds `python -m scenarios.manifest --snapshot-pins`; the manifest freeze gate refuses PENDING pins and OpenRouter rows without a pinned upstream (fallbacks are off everywhere).

| requested model | route | pinned snapshot id | pinned upstream | live $/Mtok in | live $/Mtok out |
|---|---|---|---|---|---|
| `claude-opus-5` | anthropic_native | `claude-opus-5` | anthropic | n/a | n/a |
| `openai/gpt-5.6-sol` | openrouter | `openai/gpt-5.6-sol` | OpenAI | 5 | 30 |
| `openai/gpt-5.6-terra` | openrouter | `openai/gpt-5.6-terra` | OpenAI | 1 | 6 |
| `openai/gpt-5.6-luna` | openrouter | `openai/gpt-5.6-luna` | OpenAI | 0.1 | 0.6 |
| `google/gemini-3.1-pro-preview` | openrouter | `google/gemini-3.1-pro-preview` | Google | 2 | 12 |
| `moonshotai/kimi-k3` | openrouter | `moonshotai/kimi-k3` | Moonshot AI | 3 | 15 |
| `deepseek/deepseek-v4-pro` | openrouter | `deepseek/deepseek-v4-pro` | DeepSeek | 0.435 | 0.87 |
| `qwen/qwen3.5-397b-a17b` | openrouter | `qwen/qwen3.5-397b-a17b` | Alibaba | 0.39 | 2.34 |
| `claude-sonnet-4-6` | anthropic_native | `claude-sonnet-4-6` | anthropic | n/a | n/a |
| `x-ai/grok-4.6` | openrouter | `x-ai/grok-4.6` | xAI | 2 | 6 |
| `qwen/qwen3.8-27b` | openrouter | `qwen/qwen3.8-27b` | AkashML | 0.45 | 3.2 |
| `google/gemini-3.7-flash` | openrouter | `google/gemini-3.7-flash` | Google | 0.375 | 1.875 |
| `claude-haiku-4-5` | anthropic_native | `claude-haiku-4-5-20251001` | anthropic | n/a | n/a |
| `claude-fable-5` | anthropic_native | `claude-fable-5` | anthropic | n/a | n/a |
| `openai/gpt-4o` | openrouter | `openai/gpt-4o` | OpenAI | 2.5 | 10 |
| `claude-opus-4-6` | anthropic_native | `claude-opus-4-6` | anthropic | n/a | n/a |
| `claude-opus-4-8` | anthropic_native | `claude-opus-4-8` | anthropic | n/a | n/a |
| `claude-sonnet-4-5` | anthropic_native | `claude-sonnet-4-5-20250929` | anthropic | n/a | n/a |
| `claude-sonnet-5` | anthropic_native | `claude-sonnet-5` | anthropic | n/a | n/a |

## OpenRouter provider order (as returned; pin = chosen upstream)

- `openai/gpt-5.6-sol`: OpenAI, OpenAI, OpenAI, Azure, Azure, Azure, Amazon Bedrock
- `openai/gpt-5.6-terra`: OpenAI, OpenAI, OpenAI, Azure, Azure, Azure, Amazon Bedrock
- `openai/gpt-5.6-luna`: OpenAI, OpenAI, OpenAI, Azure, Azure, Azure, Amazon Bedrock
- `google/gemini-3.1-pro-preview`: Google, Google, Google, Google AI Studio, Google AI Studio, Google AI Studio
- `moonshotai/kimi-k3`: Morph, DigitalOcean, DeepInfra, Fireworks, Chutes, Together, Moonshot AI, Wafer, Modal, BaseTen, Phala, Sail Research, Morph
- `deepseek/deepseek-v4-pro`: StreamLake, Baidu, DeepSeek, GMICloud, DigitalOcean, Ionstream, CoreWeave, Novita, DeepInfra, Alibaba, SiliconFlow, Venice, AtlasCloud, BaseTen, Parasail, Together, Fireworks, Azure
- `qwen/qwen3.5-397b-a17b`: DigitalOcean, Alibaba, Chutes, DeepInfra, Parasail, AtlasCloud, Phala, Novita, StreamLake, GMICloud, Venice
- `x-ai/grok-4.6`: xAI, xAI, xAI, xAI
- `qwen/qwen3.8-27b`: AkashML
- `google/gemini-3.7-flash`: Google, Google, Google, Google AI Studio, Google AI Studio, Google AI Studio
- `openai/gpt-4o`: Azure, OpenAI

## Patient apparatus (never an evaluated subject)

- ModelPatient primary (apparatus, $0, NOT an evaluated subject): `qwen2.5:0.5b` at http://localhost:11434/v1 — source: ollama:http://localhost:11434/api/tags

## Price re-confirmation

All live OpenRouter prices match MODEL_SPECS exactly. No drift.
