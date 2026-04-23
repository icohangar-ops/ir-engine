# Setup

## Python

Use Python 3.9+.

## Optional packages

- `openai` is not required for the default OpenAI path in this repo because the server calls the Responses API over HTTP
- `akshare`
- `tushare`
- `google-generativeai` if using the Gemini-backed chat path

## Environment variables

Copy `.env.example` and populate only the keys you plan to use:

- `FRED_API_KEY`
- `ALPHAVANTAGE_API_KEY`
- `ZYLA_METALS_API_KEY`
- `TUSHARE_TOKEN`
- `CUBICZAN_INFERENCE_BACKEND`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`

Default inference configuration:

- `CUBICZAN_INFERENCE_BACKEND=openai`
- `OPENAI_MODEL=gpt-5.2`

If you want to switch back to Gemini later, set:

- `CUBICZAN_INFERENCE_BACKEND=gemini`
- `GEMINI_API_KEY=...`

`Veris` is currently integrated as a local memory/export target. No Veris API key is required by this codebase unless you later add a separate Veris-hosted service path.

## Start the server

```bash
python cubiczan_server.py --port 8000
```

## Notes

- the system is designed to degrade gracefully when optional providers are unavailable
- provider failures are returned as structured warnings where possible
- Veris exports are generated locally from the scenario engine and can be pasted or written into a Veris workflow
- no secrets should be committed to the repository
