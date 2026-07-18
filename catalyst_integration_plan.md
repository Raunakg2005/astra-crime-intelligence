# Astra — Zoho Catalyst Integration & Production Strategy

This document outlines the deployment configuration updates, critical security/bug fixes, and the integration strategy for Zoho Catalyst services on the Astra platform. Use this as a reference for sync-ups and task division.

---

## 1. Blocker & Workspace Fixes (Completed)

We have resolved two critical blockers and cleaned up the repository workspace:

### 🔒 Blocker 1: Exposed Groq API Key
* **Issue:** The live `GROQ_API_KEY` was committed inside `app-config.json`.
* **Fix:** Replaced with `"YOUR_GROQ_API_KEY"` in `app-config.json` and committed/pushed the change.
* **Teammate Action Required:**
  1. **Rotate Key:** Log in to the Groq Console, delete/revoke the compromised key, and generate a new one.
  2. **Catalyst Config:** Log in to the Zoho Catalyst Console, navigate to **AppSail > astra-backend > Settings > Environment Variables**, and add `GROQ_API_KEY` securely there. **Do not commit it to Git again.**

### 🛠️ Blocker 2: AppSail Startup Crash (`ModuleNotFoundError`)
* **Issue:** Uvicorn was configured to boot from the root directory (`backend.appsail_ml.app:app`), which caused import crashes because Python could not resolve flat imports like `import analytics` and `import db` that live in `backend/appsail_ml/`.
* **Fix:** Updated the AppSail command in `app-config.json` to point the app directory directly to the backend folder:
  ```json
  "command": "uvicorn app:app --app-dir backend/appsail_ml --host 0.0.0.0 --port $X_ZOHO_CATALYST_LISTEN_PORT --workers 1"
  ```
  This resolves paths correctly and allows the FastAPI server to boot without crashing.

### 🧹 Workspace Cleanup
* **`client/` Scaffold:** Removed the leftover "Hello World" scaffold directory in the root. Our frontend is served directly from the compiled `frontend/dist/` folder.
* **Vite Clutter:** Configured `frontend/tsconfig.node.json` to emit transpiled build files (`vite.config.js` / `vite.config.d.ts`) directly into `node_modules/.tmp/` instead of cluttering the root frontend source directory.

---

## 2. Strategic Zoho Catalyst Service Integration

For a production-grade application and to maximize datathon compliance, we are using a hybrid approach that integrates Catalyst services natively without breaking the analytical core.

### 📊 Database: SQLite + Catalyst Data Store (Hybrid Model)
* **The Reality:** The analytics engine requires complex **7-table JOIN queries** (DBSCAN clustering, Graph algorithms, etc.). Zoho Catalyst Data Store's Query Language (ZQL) does not support multi-table joins of this complexity. Migrating all 27 tables would break the app.
* **The Strategy:**
  * **Analytics:** Keep using the local SQLite database (`ksp.db` ~26MB) inside the AppSail container for all heavy analytical read queries.
  * **Catalyst Data Store:** Create a single table in the Catalyst Data Store named `AuditLogs` or `UserActivity`.
  * **Code Integration:** Add a simple hook in `db.py` or FastAPI endpoints using `zcatalyst-sdk` to write a log row (e.g. `timestamp`, `user_id`, `action_queried`) to the Catalyst Data Store whenever an official performs an action.
  * *Why:* Proves native Catalyst Data Store integration for the judges, maintains security audits, and keeps the core analytics functioning.

### 🔑 Authentication: Catalyst User Authentication
* **The Strategy:** Enable **Catalyst Authentication** in the Zoho Console to secure the web application. 
  * Catalyst automatically protects the Web Client hosted path and redirects unauthenticated traffic to a default login screen.
  * **Code Integration:** We will load the Catalyst JS SDK on the frontend (`frontend/src/`) to fetch the logged-in user session, display their profile details in the dashboard header, and implement a logout flow.

### 📁 Deployment Package Optimization
* **Change:** Removed `backend/ml` from the ignore list in `catalyst.json` but explicitly ignored `backend/ml/mlruns`.
* **Why:** The analytics server requires `nlp.py` and `features.py` from the `backend/ml/` folder at runtime to prepare model features. Ignoring the whole folder caused runtime crashes on prediction endpoints. The actual size of `backend/ml/` is under 1.5MB (excluding mlflow runs).

---

## 3. Next Steps & Deployment Flow

1. **Local Clean Build:** Run `npm run build` in the `frontend` folder to make sure the latest React build is compiled into `frontend/dist`.
2. **Deploy Baseline:** Run `catalyst deploy` from the root directory to host the frontend (Web Client) and backend (AppSail).
3. **Configure API Gateway (Zoho Console):**
   Set up two routing rules to bridge frontend and backend:
   * Route `/api/{path}` to `AppSail (astra-backend)` at `/api/{path}`
   * Route `/health` to `AppSail (astra-backend)` at `/health`
4. **Wire up Audit Logs & Authentication UI:** I will draft the Python code for writing audit logs to Catalyst and the React code for reading user session state.
