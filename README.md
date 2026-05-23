# betterdb-yt-collab

A RAG (Retrieval Augmented Generation) project using **Valkey/Redis** as a vector store & cache, **BetterDB** for Redis observability, **Groq** as the free LLM, and **FastAPI** as the API layer.

---

## 🧱 Tech Stack

| Component | Tool |
|---|---|
| Vector Store & Cache | Valkey (Redis-compatible) via Docker |
| LLM | Groq (`llama-3.3-70b-versatile`) — free tier |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` — local, free |
| API Framework | FastAPI + Uvicorn |
| Redis Observability | BetterDB Cloud + BetterDB Agent |
| Package Manager | `uv` |

---

## ⚙️ Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [uv](https://docs.astral.sh/uv/) installed
- A free [Groq API key](https://console.groq.com/)
- A free [BetterDB account](https://betterdb.com/)

---

## 🚀 Setup & Run

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/betterdb-yt-collab.git
cd betterdb-yt-collab
```

### 2. Create `.env` file

```env
GROQ_API_KEY="your_groq_api_key_here"
REDIS_URL="redis://localhost:6379"
```

### 3. Install dependencies

```bash
uv pip install -e .
uv pip install sentence-transformers
```

### 4. Start Valkey (Redis) via Docker

```bash
docker-compose up -d
```

Verify it's running:

```bash
docker compose ps
```

### 5. Start the BetterDB Agent

Go to your BetterDB dashboard → **Manage Connections → + Add Connection → Via Agent tab** → create a token, then run:

**On Mac/Linux:**
```bash
docker run -d \
  --name betterdb-agent-local \
  --add-host=host.docker.internal:host-gateway \
  -e VALKEY_HOST=host.docker.internal \
  -e VALKEY_PORT=6379 \
  -e BETTERDB_CLOUD_URL=wss://<your-app-name>.app.betterdb.com/agent/ws \
  -e BETTERDB_TOKEN=<your_agent_token> \
  betterdb/agent:1.4.0
```

**On Windows (PowerShell) — use backtick `` ` `` instead of `\`:**
```powershell
docker run -d `
  --name betterdb-agent-local `
  --add-host=host.docker.internal:host-gateway `
  -e VALKEY_HOST=host.docker.internal `
  -e VALKEY_PORT=6379 `
  -e BETTERDB_CLOUD_URL=wss://<your-app-name>.app.betterdb.com/agent/ws `
  -e BETTERDB_TOKEN=<your_agent_token> `
  betterdb/agent:1.4.0
```

> ⚠️ **Important:** Use `betterdb/agent:1.4.0` — the `latest` tag has a broken `zod` dependency.

Verify agent connected:

```bash
docker logs betterdb-agent-local
# Should show: [Agent] WebSocket connected, sending hello
```

### 6. Start the FastAPI server

```bash
uv run uvicorn rag.main:app --reload --port 8000
```

API will be live at: **http://127.0.0.1:8000**

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Redis ping + key counts per namespace |
| `POST` | `/ingest` | Upload a PDF → chunk → embed → store in Redis |
| `POST` | `/query` | Ask a question → RAG pipeline → LLM response |
| `GET` | `/stats` | Key counts + TTLs for all 4 Redis namespaces |

### Example: Ingest a PDF

```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@your_document.pdf"
```

### Example: Query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the leave policy?", "session_id": "user-1"}'
```

---

## 🗂️ Redis Key Namespaces

| Key Pattern | What's stored | TTL |
|---|---|---|
| `rag:doc:{sha256}` | PDF chunks + embeddings | None (intentional demo bug) |
| `semantic_cache:{md5}` | Cached LLM answers | None (intentional demo bug) |
| `rate_limit:user_{id}:minute` | Request counters | 60s (auto-reset) |
| `langchain:memory:session:{id}` | Conversation history | None (intentional demo bug) |

---

## 🐳 Useful Docker Commands

```bash
# Check running containers
docker compose ps

# View Valkey logs
docker compose logs valkey

# View BetterDB agent logs
docker logs betterdb-agent-local

# Stop everything
docker-compose down

# Restart BetterDB agent with a new token
docker rm -f betterdb-agent-local
docker run -d ... betterdb/agent:1.4.0
```

---

## 🧠 How It Works

```
PDF Upload  →  Extract text  →  Chunk (250 chars)  →  Embed (384 numbers)  →  Store in Redis
                                                                                      ↓
User Query  →  Embed query   →  Cache hit? (similarity ≥ 0.85)  →  YES: return cached answer
                                        ↓ NO
                               Retrieve top-3 similar chunks from Redis
                                        ↓
                               Send chunks + question to Groq LLM
                                        ↓
                               Store response in semantic cache
                                        ↓
                               Store in session memory
                                        ↓
                                  Return response
```

---

## 🔍 BetterDB Observability

BetterDB monitors your Redis/Valkey instance in real-time and shows:

- **Key browser** — all `rag:doc:*`, `semantic_cache:*`, `rate_limit:*` keys
- **TTL inspector** — which keys have no expiry (memory leaks)
- **Slowlog** — heavy `HGETALL` commands (the retrieval bottleneck)
- **Memory usage** — RAM consumed per namespace
- **Command rate** — Redis operations per second

The BetterDB Agent (Docker container) reads from your local Valkey and streams metrics to the BetterDB cloud dashboard over WebSocket — **without touching your app code**.
