# Deployment Guide for Lead Generation API

## Quick Start

### Using Clay HTTP Column

Once deployed, you can use the API in Clay's HTTP column with these settings:

**Endpoint:** `https://your-app-url.com/search`
**Method:** POST
**Headers:**
```json
{
  "Content-Type": "application/json"
}
```
**Body:**
```json
{
  "query": "superintendent at pebblebeach.com"
}
```

## GitHub + Replit CI/CD Setup

### 1. Create GitHub Repository
```bash
cd exa-lead-api
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/exa-lead-api.git
git push -u origin main
```

### 2. Connect Replit to GitHub
1. In Replit: Create new Repl → "Import from GitHub"
2. Paste your GitHub repo URL
3. Replit auto-syncs on every push to main!

### 3. Set Environment Variables in Replit:
- Go to Secrets tab
- Add:
  - `OPENROUTER_API_KEY`
  - `EXA_API_KEY`
  - `API_TOKEN` (optional, if using secure_api.py)

### 4. Deploy:
- Click "Run" to start
- Click "Deploy" for always-on URL
- Future updates: just `git push` from anywhere!

## Security Options

**Option A: No Auth (Default)**
- Use `simple_api.py` as main file
- Rely on URL obscurity
- Perfect for personal use

**Option B: Token Auth**
- Rename `secure_api.py` to `simple_api.py`
- Add `API_TOKEN` to Replit secrets
- In Clay, add header: `Authorization: Bearer your-token-here`

### Option 2: Deploy to Railway

1. **Create Railway Project:**
   - Go to [railway.app](https://railway.app)
   - New Project → Deploy from GitHub

2. **Upload Files:**
   - Push these files to your GitHub repo:
     - `simple_api.py`
     - `exa_local.py`
     - `requirements.txt`
     - `railway.json`
     - `Procfile`

3. **Set Environment Variables:**
   - In Railway dashboard → Variables
   - Add:
     - `OPENROUTER_API_KEY`
     - `EXA_API_KEY`

4. **Deploy:**
   - Railway will auto-deploy
   - Get your URL from Settings

## API Usage Examples

### Basic Search
```bash
curl -X POST https://your-api-url/search \
  -H "Content-Type: application/json" \
  -d '{"query": "general manager at golfknox.com"}'
```

### Health Check
```bash
curl https://your-api-url/health
```

## Response Format

The API returns comprehensive lead data including:
- Business information
- Contact details with emails (always provided)
- Employment verification status
- Phone numbers with type classification
- Confidence scores

## Clay Integration Tips

1. **Rate Limiting:** The API processes one request at a time, so use Clay's rate limiting features
2. **Error Handling:** Check the response status before processing results
3. **Field Mapping:** Map these key fields from the response:
   - `results.business.name`
   - `results.contacts[0].name`
   - `results.contacts[0].email`
   - `results.contacts[0].phone`
   - `results.contacts[0].title`

## Troubleshooting

- **502 Error:** Check environment variables are set
- **Timeout:** Complex queries may take 30-60 seconds
- **Empty Results:** Verify the business domain/query format