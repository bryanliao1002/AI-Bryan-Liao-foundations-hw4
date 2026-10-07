# Campus Customs — Yale Apparel Shop with an AI Shopping Assistant

A full-stack storefront for **Campus Customs** (Yale apparel, 57 Broadway, New Haven):

- **Front end:** React + Vite + TypeScript (`frontend/`). Home, Shop (filters and sorting), product pages, About, log in / create account, and a floating chat assistant.
- **Back end:** Python FastAPI (`backend/main.py`) with a **PydanticAI** agent (`gpt-5.6-luna` via the Portkey gateway). The agent reads real prices and stock from a local SQLite database, puts matching products on the page, remembers logged-in customers, and logs every step to `output/audit_trail.json`.

Full system documentation is in [`output/harness.md`](output/harness.md).

---

## 1. Requirements

- **Python 3.11+** (developed on 3.14)
- **Node.js 20+** and npm (developed on Node 24)
- A **Portkey API key** for the model gateway
- The course **data pack** (not in this repo, see below)

## 2. Add the local data pack

The database and product images are **not committed** (they're git-ignored). Unzip the provided `data.zip` so it sits inside this folder like this:

```
hw4/
└── data/
    ├── campus_customs.db     # catalogue, inventory, users, chat_messages
    └── products/             # product images referenced by catalogue.image_file_path
```

## 3. Configure your API key

```bash
cp .env.example .env
```
Then edit `.env` and set your real values:

| Variable | Required | Purpose |
|---|---|---|
| `PORTKEY_API_KEY` | yes | Key for the Portkey gateway that serves `gpt-5.6-luna` |
| `AUTH_SECRET` | recommended | Signs login sessions. If unset, a random key is used and everyone is logged out on restart. |
| `OPENAI_MODEL`, `PORTKEY_BASE_URL` | no | Optional overrides |

`.env` is git-ignored. Never commit real keys.

## 4. Run the back end (terminal 1)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # installs hw4/requirements.txt
uvicorn main:app --reload --port 8000
```

Check it: <http://localhost:8000/api/health> should return `{"status":"ok"}`. API docs are at <http://localhost:8000/docs>.

On first start, the backend builds storefront copies of the product photos in the background (into `backend/.cache/`, git-ignored). The originals in `data/products/` are never modified.

## 5. Run the front end (terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Open **<http://localhost:5173>**. Vite forwards `/api` and `/media` requests to the backend on port 8000, so keep both running.

**Test account:** `test@campuscustoms.yale.edu` / `password`. You can also create a new account from **Create account**.

## 6. Things to try

- **Shop:** filter by category, "in stock in size", or price, and sort.
- **Chat** (bottom-right "Ask our assistant"):
  - "How many Basic Hoodie Big Yale do you have in medium, and how much is it?" → real stock and price, with a "✓ Price verified" badge.
  - "What hoodies do you have?" → hoodie cards appear on the page.
  - On a product page: "Do you have this in pink?" or "Is this in large?" → the assistant knows which product you mean and suggests similar in-stock items.
  - Log in, chat, reload or come back later → your conversation is restored.

## 7. Project layout

```
hw4/
├── AI_prompts.md            prompts used for each problem
├── README.md                this file
├── requirements.txt         Python dependencies
├── .env.example             placeholder config (copy to .env)
├── .gitignore               keeps data/, .env, venvs, node_modules, caches out of Git
├── frontend/                Vite + React + TypeScript app
├── backend/
│   ├── main.py              FastAPI app: products, images, auth, chat (uvicorn main:app)
│   ├── agent.py             PydanticAI agent setup, context, reply check, loop limits
│   ├── tools.py             read-only database tools the agent can call
│   ├── models.py            Pydantic / PydanticAI structured types
│   ├── prompts/prompt.md    system prompt: tone, tool rules, safety rules
│   ├── auth.py              signup / login / sessions
│   ├── chat_history.py      saved chats for logged-in customers
│   ├── audit.py             append-only audit trail
│   ├── images.py            storefront product photos
│   └── db.py                paths, .env loading, SQLite helper
├── output/
│   ├── harness.md           full system spec
│   ├── design.md            visual design write-up
│   ├── usability.md         usability improvements
│   ├── app_check.html       live app check with screenshots (open in a browser)
│   ├── app_check_images/
│   └── audit_trail.json     agent loop log (append-only)
└── data/                    local data pack, NOT in Git (see step 2)
```
