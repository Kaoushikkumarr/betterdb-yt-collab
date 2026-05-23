# Step-by-Step Setup Guide

---

## Step 1: Prerequisites

- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Install [uv](https://docs.astral.sh/uv/)
- Get a free [Groq API key](https://console.groq.com/)
- Create a free [BetterDB account](https://betterdb.com/)

---

## Step 2: Install Project Dependencies

```bash
uv pip install -e .
uv pip install sentence-transformers
```

---

## Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY="your_groq_api_key_here"
REDIS_URL="redis://localhost:6379"
```

---

## Step 4: Start Valkey (Redis) via Docker

Make sure Docker Desktop is open and running (look for the 🐳 whale in your system tray).

```bash
docker-compose up -d
```

Check it's healthy:

```bash
docker compose ps
```

Expected output — STATUS should show `healthy`:
```
NAME                   IMAGE                    STATUS
betterdb-demo-valkey   valkey/valkey:8.1-alpine Up ... (healthy)
```

---

## Step 5: Start the BetterDB Agent

### 5.1 Get your agent token

1. Go to your BetterDB dashboard: `https://<your-app-name>.app.betterdb.com`
2. Navigate to **Manage Connections → + Add Connection → Via Agent tab**
3. Create a token — copy it

> ⚠️ Make sure you use the **Agent-type token** (not MCP type). The token payload
> should have `"type": "agent"`.

### 5.2 Run the agent container

**Mac / Linux:**
```bash
docker run -d \
  --name betterdb-agent-local \
  --add-host=host.docker.internal:host-gateway \
  -e VALKEY_HOST=host.docker.internal \
  -e VALKEY_PORT=6379 \
  -e BETTERDB_CLOUD_URL=wss://<your-app-name>.app.betterdb.com/agent/ws \
  -e BETTERDB_TOKEN=<your_agent_token_here> \
  betterdb/agent:1.4.0
```

**Windows (PowerShell) — use backtick `` ` `` NOT backslash `\`:**
```powershell
docker run -d `
  --name betterdb-agent-local `
  --add-host=host.docker.internal:host-gateway `
  -e VALKEY_HOST=host.docker.internal `
  -e VALKEY_PORT=6379 `
  -e BETTERDB_CLOUD_URL=wss://<your-app-name>.app.betterdb.com/agent/ws `
  -e BETTERDB_TOKEN=<your_agent_token_here> `
  betterdb/agent:1.4.0
```

> ⚠️ **Important notes:**
> - Use tag `1.4.0` — the `latest` tag has a missing `zod` dependency bug
> - `--add-host=host.docker.internal:host-gateway` is required on Windows/Linux so the container can reach your local Valkey
> - On Mac, `host.docker.internal` works without the `--add-host` flag

### 5.3 Verify the agent connected

```bash
docker logs betterdb-agent-local
```

Expected output:
```
BetterDB Agent v0.1.0
Connecting to valkey://host.docker.internal:6379
[Agent] Connecting to host.docker.internal:6379...
[Agent] Connected to Valkey/Redis
[Agent] Detected valkey 8.1.7
[Agent] Connecting to cloud: wss://<your-app-name>.app.betterdb.com/agent/ws
[Agent] WebSocket connected, sending hello
```

If you see `401 Unauthorized` → your token is wrong type (use Agent token, not MCP token).

---

## Step 6: Start the FastAPI Server

```bash
uv run uvicorn rag.main:app --reload --port 8000
```

> If `uvicorn` is not found, always use `uv run uvicorn ...` — not just `uvicorn`.

Server will be live at: **http://127.0.0.1:8000**

---

## Step 7: Test the API

### Check health

```bash
curl http://localhost:8000/health
```

### Ingest a PDF

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@your_document.pdf"
```

**Windows PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/ingest" `
  -Method POST `
  -Form @{ file = Get-Item ".\your_document.pdf" }
```

### Query the RAG pipeline

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the leave policy?", "session_id": "user-1"}'
```

**Windows PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/query" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"query": "What is the leave policy?", "session_id": "user-1"}'
```

### Check Redis key stats

```bash
curl http://localhost:8000/stats
```

---

## Step 8: View in BetterDB Dashboard

Open your BetterDB dashboard at `https://<your-app-name>.app.betterdb.com`

After ingesting a PDF and running queries, you'll see:

- `rag:doc:*` keys with **TTL = -1** (no expiry — intentional bug #1)
- `semantic_cache:*` keys with **TTL = -1** (no expiry — intentional bug #2)
- `langchain:memory:session:*` keys with **TTL = -1** (no expiry — intentional bug #3)
- `rate_limit:*` keys with **TTL = 60s** (correct behavior)
- **Slowlog** showing heavy `HGETALL` commands (intentional bottleneck #5)

---

## Troubleshooting

### Docker Desktop not running

```
open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
```

**Fix:** Open Docker Desktop from Start Menu and wait for it to fully start (whale icon stops animating).

---

### PowerShell line continuation error

```
Unexpected token 'name' in expression or statement.
```

**Fix:** PowerShell uses backtick `` ` `` for line continuation, not backslash `\`.

---

### BetterDB agent — 401 Unauthorized

```
[Agent] WS error: Unexpected server response: 401
```

**Fix:** Go to BetterDB dashboard → create a new **Agent-type token** (not MCP type) and re-run the container.

---

### `zod` module not found

```
Error: Cannot find module 'zod'
```

**Fix:** Use `betterdb/agent:1.4.0` instead of `betterdb/agent:latest`.

```powershell
docker rm -f betterdb-agent-local
# re-run with :1.4.0 tag
```

---

### `host.docker.internal` not found

```
[Agent] Valkey error: getaddrinfo ENOTFOUND host.docker.internal
```

**Fix:** Add `--add-host=host.docker.internal:host-gateway` to the `docker run` command.

---

### OpenAI quota exceeded

```
openai.RateLimitError: Error code: 429 — insufficient_quota
```

**Fix:** This project uses **Groq** (free) instead of OpenAI. Make sure your `.env` has `GROQ_API_KEY` set and `config.py` is pointing to Groq's base URL.

---

## Key Commands Reference

```bash
# Start Valkey
docker-compose up -d

# Stop Valkey
docker-compose down

# Check Valkey health
docker compose ps

# View Valkey logs
docker compose logs valkey

# Start BetterDB agent (PowerShell)
docker run -d `
  --name betterdb-agent-local `
  --add-host=host.docker.internal:host-gateway `
  -e VALKEY_HOST=host.docker.internal `
  -e VALKEY_PORT=6379 `
  -e BETTERDB_CLOUD_URL=wss://<your-app-name>.app.betterdb.com/agent/ws `
  -e BETTERDB_TOKEN=<your_agent_token_here> `
  betterdb/agent:1.4.0

# View agent logs
docker logs betterdb-agent-local

# Remove and re-run agent (new token)
docker rm -f betterdb-agent-local

# Start FastAPI server
uv run uvicorn rag.main:app --reload --port 8000
```
