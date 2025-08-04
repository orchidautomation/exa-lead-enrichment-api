# Exa Lead Generation API

Personal API for local business lead enrichment, optimized for Clay integration.

## Setup

1. Clone this repo
2. Set environment variables in Replit/Railway:
   - `OPENROUTER_API_KEY`
   - `EXA_API_KEY`
3. Deploy automatically on push

## Usage

```bash
POST /search
{
  "query": "superintendent at pebblebeach.com"
}
```

No API key needed - this is your personal service. For added security in production, see `secure_api.py`.