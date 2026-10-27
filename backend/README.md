# TradePass backend

## Local setup (Windows PowerShell)
```powershell
cd backend
py -m venv venv
.env\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs. Default `.env.example` uses SQLite for local development. To use Supabase, set `DATABASE_URL` to the current Session Pooler connection string from Supabase. Do not commit `.env`.

## Tests
```powershell
pip install -r requirements.txt
pytest -q
```

## Notes
- The app creates missing tables on startup for this MVP. `create_all()` does not migrate existing tables; use Alembic before evolving a populated production schema.
- Uploaded files use local private storage by default. Configure `STORAGE_DIR`; back up and protect that directory. This is a development storage adapter, not a managed production object store.
- Compliance checks are preliminary workflow checks, not legal advice or proof of authenticity.
- Rotate any database credentials that were included in earlier ZIPs.
