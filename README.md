# TradePass MVP

A working first-version B2B shipment-documentation and preliminary compliance workflow app. This repository includes a FastAPI backend and React/Vite frontend.

## Included
- Company registration, login, JWT auth, and protected `/me` endpoint.
- Company-scoped shipment create/list/get/update/archive, with per-company unique shipment references.
- Private local document upload/download, document review metadata, and tenant checks.
- Preliminary rule-based checks for missing invoice/packing list, expired dates, and supported reference/product mismatches.
- Dashboard summary backed by API data.
- Revocable/expiring buyer share tokens and limited read-only shipment summaries.
- Pytest API tests for auth, shipment tenant isolation, company-scoped references, and validation.

## Run locally on Windows
1. Install Python 3.10+ and Node.js 20+.
2. In `backend`, create and activate a venv, install dependencies, and copy `.env.example` to `.env`.
3. Default backend storage is SQLite for easy local development. Configure Supabase in `.env` only when ready.
4. Run `uvicorn app.main:app --reload` from `backend`.
5. In `frontend`, run `npm install`, copy `.env.example` to `.env`, then `npm run dev`.
6. Open `http://localhost:5173`. API docs are at `http://127.0.0.1:8000/docs`.

## Tests
From `backend`, activate the venv and run `pytest -q`. Tests use a local SQLite database and do not touch your Supabase database.

## Security checklist before using Supabase/deployment
- **Rotate the database password** that appeared in the earlier uploaded ZIP. Treat it as exposed.
- Create a new random `SECRET_KEY` and keep it in local `.env` / deployment secrets.
- Never commit `.env`, database files, uploads, or credentials.
- Use private managed object storage and configure backups/retention before production. Current local upload storage is for development, not multi-instance production.
- Add Alembic migrations before changing a populated database schema. `create_all()` only creates missing tables; it does not migrate existing columns/constraints.
- Add malware scanning and stricter content-type/file-signature validation before public production uploads.
- Add rate limiting, email verification, password reset, audit logs, and stronger session/revocation policy before production.

## Important compliance note
The rules are preliminary operational checks only. They do not establish document authenticity, guarantee legal compliance, or replace qualified advice. Actual requirements depend on product, destination, and circumstances.

## Current MVP limitations
- OCR/AI extraction is not implemented; users can enter reviewed field metadata manually. The data model separates extracted and reviewed fields to support future providers.
- Share links are created as tokens and the frontend supports `/share/:token`; the API returns the token, so the user must copy/build the URL in the frontend workflow. The first frontend currently creates the URL from the current frontend origin.
- Local file storage is not appropriate for production multi-instance deployments; replace with private Supabase Storage or another private object store.
