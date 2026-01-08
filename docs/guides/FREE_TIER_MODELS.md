# Free Tier Model Configuration

SecBrain is configured to use **100% FREE tier models** across all AI providers. This document explains the free tier choices and how to maximize your free usage.

## ✅ Current Configuration (All FREE)

### Default Models (models.yaml)

| Component | Provider | Model | Status |
|-----------|----------|-------|--------|
| **Worker** | Together AI | `meta-llama/Llama-3.2-3B-Instruct-Turbo` | ✅ FREE tier |
| **Advisor** | Together AI | `meta-llama/Meta-Llama-3-8B-Instruct-Turbo` | ✅ FREE tier |
| **Research** | Perplexity | `sonar` | ✅ FREE tier (unlimited with PRO) |

### Your PRO Subscriptions

Since you have:
- ✅ **Perplexity PRO** → Unlimited API calls with `sonar` model
- ✅ **Google PRO** → Can use Gemini models for free (see premium config)
- ✅ **GitHub Student Developer Pack** → Includes credits for various services

## 🎯 Provider Details

### Together AI (Primary - FREE Tier)

**Free Tier Includes:**
- `meta-llama/Llama-3.2-1B-Instruct-Turbo` (smallest)
- `meta-llama/Llama-3.2-3B-Instruct-Turbo` (default worker)
- `meta-llama/Meta-Llama-3-8B-Instruct-Turbo` (default advisor)
- Rate limits: Generous free tier limits

**Setup:**
```bash
export TOGETHER_API_KEY=your-key-here
```

Get your key: https://api.together.xyz/settings/api-keys

### Perplexity (Research - FREE with PRO)

**Free Tier:**
- `sonar` model (fast, efficient)
- With PRO subscription: **Unlimited API calls**

**Setup:**
```bash
export PERPLEXITY_API_KEY=pplx-your-key-here
```

Get your key: https://www.perplexity.ai/settings/api

### Google Gemini (Optional Advisor - FREE with PRO)

**Free with PRO Subscription:**
- `gemini-2.0-flash-exp` (fast, efficient)
- `gemini-1.5-flash` (alternative)
- Higher quality advisor decisions

**To enable (edit models.yaml):**
```yaml
advisor:
  provider: gemini
  model: gemini-2.0-flash-exp
```

**Setup:**
```bash
export GOOGLE_API_KEY=AIza-your-key-here
```

Get your key: https://aistudio.google.com/app/apikey

## 🔄 Alternative Free Providers

### Groq (FREE - Fast Inference)

Groq offers **free tier** with rate limits. Extremely fast inference.

**Free Models:**
- `llama-3.2-1b-preview`
- `llama-3.2-3b-preview`
- `gemma2-9b-it`

**To enable (uncomment in models.yaml):**
```yaml
worker:
  provider: openai_compatible
  model: llama-3.2-3b-preview
  base_url: https://api.groq.com/openai/v1
```

**Setup:**
```bash
export GROQ_API_KEY=your-key-here
```

Get your key: https://console.groq.com/keys

### OpenRouter (FREE Models Available)

OpenRouter provides access to multiple providers with **free tier models** (using `:free` suffix).

**Free Models:**
- `meta-llama/llama-3.2-3b-instruct:free`
- `meta-llama/llama-3.1-8b-instruct:free`
- Many others with `:free` suffix

**To enable (uncomment in models.yaml):**
```yaml
worker:
  provider: openai_compatible
  model: meta-llama/llama-3.2-3b-instruct:free
  base_url: https://openrouter.ai/api/v1
```

**Setup:**
```bash
export OPENROUTER_API_KEY=your-key-here
```

Get your key: https://openrouter.ai/keys

### OpenAI (Credits via GitHub Student Pack)

While OpenAI has no permanent free tier, the **GitHub Student Developer Pack** provides credits.

**Cheapest Models (if using credits):**
- `gpt-4o-mini` (cheapest, best value)

**To enable (uncomment in models.yaml):**
```yaml
worker:
  provider: openai_compatible
  model: gpt-4o-mini
  base_url: https://api.openai.com/v1
```

**Setup:**
```bash
export OPENAI_API_KEY=sk-your-key-here
```

## 📊 Recommended Configurations

### Maximum Free Quality (Recommended)

Uses your PRO subscriptions for best free quality:

```yaml
worker:
  provider: openai_compatible
  model: meta-llama/Meta-Llama-3-8B-Instruct-Turbo  # Together AI free tier
  base_url: https://api.together.xyz/v1

advisor:
  provider: gemini
  model: gemini-2.0-flash-exp  # Google PRO (FREE for you)

research:
  provider: perplexity
  model: sonar  # Perplexity PRO (unlimited for you)
```

### Minimum Resource Usage

Smallest models, fastest inference:

```yaml
worker:
  provider: openai_compatible
  model: meta-llama/Llama-3.2-1B-Instruct-Turbo  # Smallest free model
  base_url: https://api.together.xyz/v1

advisor:
  provider: openai_compatible
  model: meta-llama/Llama-3.2-3B-Instruct-Turbo  # Small free model
  base_url: https://api.together.xyz/v1
```

### Groq Speed (Alternative)

For fastest inference with free tier:

```yaml
worker:
  provider: openai_compatible
  model: llama-3.2-3b-preview
  base_url: https://api.groq.com/openai/v1

advisor:
  provider: openai_compatible
  model: gemma2-9b-it
  base_url: https://api.groq.com/openai/v1
```

## 🚀 Quick Start

1. **Get API keys** (all free):
   ```bash
   export TOGETHER_API_KEY=your-together-key     # FREE tier
   export PERPLEXITY_API_KEY=pplx-your-key       # FREE with your PRO
   export GOOGLE_API_KEY=AIza-your-key           # FREE with your PRO
   ```

2. **Test with dry-run** (no API calls):
   ```bash
   secbrain run \
     --scope examples/dummy_target/scope.yaml \
     --program examples/dummy_target/program.json \
     --workspace ./targets/test \
     --dry-run
   ```

3. **Run with real API calls** (all free tier):
   ```bash
   secbrain run \
     --scope examples/dummy_target/scope.yaml \
     --program examples/dummy_target/program.json \
     --workspace ./targets/test
   ```

## 💡 Tips for Staying Free

1. **Use Together AI free tier models** (default config)
2. **Leverage your PRO subscriptions** (Perplexity, Google)
3. **Enable caching** - SecBrain automatically caches to reduce API calls
4. **Use dry-run mode** for testing configuration
5. **Monitor rate limits** - all free tiers have generous limits
6. **Switch providers** if you hit limits - multiple free options available

## ❓ Troubleshooting

### "Spend limit reached" Error

If you see this error:
1. Verify you're using free tier models (see list above)
2. Check if you've exceeded rate limits (wait 1 hour)
3. Switch to alternative free provider (Groq, OpenRouter)
4. Use local models (see `local` config in models.yaml)

### Rate Limit Errors

Free tiers have rate limits but are generous:
- Together AI: ~100-300 req/min (varies by model)
- Groq: ~30 req/min on free tier
- Perplexity PRO: Unlimited
- Google Gemini PRO: High limits

**Solution:** SecBrain has built-in rate limiting and caching to stay within limits.

## 📚 Additional Resources

- [Together AI Free Tier](https://docs.together.ai/docs/inference-models)
- [Groq Free Tier](https://console.groq.com/docs/rate-limits)
- [OpenRouter Free Models](https://openrouter.ai/docs#models)
- [Perplexity API](https://docs.perplexity.ai/)
- [Google AI Studio](https://ai.google.dev/)

---

**Summary:** SecBrain is configured to use 100% free tier models. With your PRO subscriptions, you have unlimited Perplexity research and access to high-quality Gemini models, all at no cost.
