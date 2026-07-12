# AI Freelancer Assistant — Complete (Day 1–5)

Day 1: Project Setup, Authentication & Dashboard
Day 2: Proposal Generator & Cover Letter Generator (Groq AI integration)
Day 3: Gig Description Generator & Smart Pricing Calculator
Day 4: Client Reply Generator, Invoice Generator, Contract Generator
Day 5: History, Profile, Settings & Deployment

This is the complete, final build of the project.

## Security Hardening (production readiness pass)

Added on top of the day-by-day build, since running this long-term needs more
than what a school-project timeline typically covers:

- **Rate limiting** (Flask-Limiter): login (15/min), registration (10/hour),
  password reset requests (5/hour), and every AI generation/regeneration route
  (20/hour) - stops brute-force login attempts and AI-credit-draining abuse.
  Uses in-memory storage by default (fine for a single instance); see the note
  in `extensions.py` if you scale to multiple workers/instances - you'd point
  it at Redis instead.
- **Real password reset**: token-based via `itsdangerous` (already a Flask
  dependency), tokens expire after 1 hour and are single-use in effect since
  they're tied to the current password hash context. No email provider is
  wired up, so the reset link is shown directly on the page instead of being
  emailed - swap that one block in `auth/routes.py` for a real email send
  (Flask-Mail, Resend, SendGrid, etc.) before this goes to real users.
- **Secure cookies in production**: `SESSION_COOKIE_SECURE` is automatically
  on when `FLASK_ENV=production`, off in local dev (plain HTTP on
  `127.0.0.1` can't use secure cookies).
- **Proxy-aware** (`ProxyFix`): required for correct behavior behind
  Render/Railway/nginx, where HTTPS terminates at the platform's proxy, not at
  this app directly.
- **HSTS header** in production, telling browsers to only ever use HTTPS for
  this site once they've loaded it once securely.
- **Debug mode is environment-driven**: `DEBUG=True` only when
  `FLASK_ENV` isn't `production`. Flask's debugger allows arbitrary code
  execution if left on in production - this makes that mistake much harder to
  make by accident.
- **Logging**: rotating file log (`instance/app.log`, 1MB x 3 backups) in
  production, so a crash has a trail instead of vanishing into nothing.
- **Health check** at `/healthz` for uptime monitoring on your hosting
  platform.
- **Input validation gap fixed**: profile hourly rate now rejects negative
  values (was previously unbounded).
- **User enumeration protection**: forgot-password shows the same message
  whether or not the email is registered, so it can't be used to check which
  emails have accounts.

**Still intentionally out of scope** (flagging honestly rather than pretending
otherwise): email verification on signup, 2FA, encrypted-at-rest storage for
the per-user Groq API key field, and a Content-Security-Policy header (skipped
because this app's styling relies on inline `style=""` attributes throughout,
and a real CSP would need every one of those refactored into external CSS
first - doable, just a separate pass).

## What's included (Day 5)

- **Unified History** (`/history`): every proposal, cover letter, gig description,
  pricing calculation, client reply, invoice, and contract in one feed, filterable by type.
  Each module still has its own dedicated history page too (from earlier days) - this adds
  a combined view on top, it doesn't replace them.
- **Profile** (`/profile`): edit name, bio, skills, portfolio URL, phone, location, hourly
  rate; upload a profile picture (jpg/png/webp, 2MB max); change password with current-password
  verification.
- **Settings** (`/settings`): dark/light theme (fully functional - actually re-themes the
  whole app via CSS variables, not just a cosmetic toggle); a personal Groq API key that
  overrides the shared `.env` key for that user's own AI generations; language selector
  (English works today; Urdu option is present but interface translation isn't implemented -
  it's flagged honestly in the UI rather than faked); email notification preference (saved,
  but not wired to a real email sender yet since none was in scope).
- **Bug fix from Day 3/4:** `additional_charges` and `tax_percent` used `DataRequired`,
  which treats `0` as "empty" in WTForms (0 is falsy in Python) - so entering 0% tax or $0
  additional charges incorrectly failed validation. Fixed by switching to `InputRequired`
  (checks that a value was submitted, not that it's truthy) in `pricing/forms.py` and
  `invoices/forms.py`. Caught by testing the zero-value case specifically - worth knowing
  about if you see similar "This field is required" errors on a field that clearly has 0 in it.
- **Error handling:** custom 404 and 500 pages, automatic `db.session.rollback()` on server
  errors, a friendly message when an upload exceeds the 2MB limit instead of a raw crash.
- **Security:** `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` headers on
  every response; `SESSION_COOKIE_HTTPONLY` and `SESSION_COOKIE_SAMESITE=Lax`; upload size
  capped app-wide at 2MB; avatar uploads validated by extension and size before saving.
- **UX:** submit buttons show a "Working..." state while a request is in flight (most useful
  during AI generation, which can take a few seconds), so nothing looks unresponsive.
- **Deployment-ready:** `Procfile` (`web: gunicorn app:app`) for Render/Railway, `gunicorn`
  added to `requirements.txt`, and a proper `.gitignore` (excludes `.env`, the SQLite file,
  uploaded avatars, and Python cache directories).
- **`API_DOCUMENTATION.md`** — every route in the app, method, auth requirement, and purpose.
- Verified end-to-end with automated tests covering profile editing, avatar upload, password
  change + re-login, settings save, personal API key override actually being passed to the
  AI call, history filtering, 404 handling, and security headers - plus a full regression
  pass across every Day 1-4 feature to confirm nothing broke.

## What's included (Day 4)

- **Client Reply Generator** (`/client-replies`): paste the client's message, pick a tone,
  get an AI-drafted reply. Edit inputs, regenerate, manually edit + save, copy to clipboard,
  delete, full history. No PDF export - matches the spec, which only lists Copy/Save for this module.
- **Invoice Generator** (`/invoices`): structured invoice form (client details, project
  details, services, amount, tax %, due date). Auto-generates an invoice number
  (`INV-00001`, etc.) and produces a clean line-item PDF via ReportLab. **Deliberately does
  not use AI** for the calculation - the dollar amount is plain math (amount + tax%), so it
  never depends on the AI provider being reachable. Full history, edit, delete.
- **Contract Generator** (`/contracts`): client/freelancer details, project scope, timeline,
  payment terms, and optional extra terms go in; the AI drafts a complete, ready-to-send
  service agreement. Editable, regenerate, export as PDF, full history, delete.
- `pdf_service.py` gained `generate_invoice_pdf()` (proper table with subtotal/tax/total
  rows) and `generate_contract_pdf()` (reuses the same document style as proposals/cover
  letters).
- Dashboard sidebar, Quick Actions, and Recent Activity now cover all seven AI/document
  modules from Day 2-4.
- **Schema note:** `Invoice` gained `invoice_number` and `client_email` columns. If you're
  upgrading from the Day 3 zip, delete your local `instance/app.db` before running Day 4 so
  the new columns get created.
- Verified end-to-end with automated tests (client reply generation, invoice creation with
  exact tax-math verification, contract generation + PDF export, edit/regenerate/delete for
  all three) using mocked AI responses, since this build environment cannot reach
  api.groq.com directly. **Run one real test with your GROQ_API_KEY before submitting.**

## What's included (Day 3)

- **Gig Description Generator** (`/gigs`): one AI call returns three parsed sections -
  gig description, SEO keywords, and 3 FAQ pairs - each independently editable and saveable.
  Full history, regenerate, delete.
- **Smart Pricing Calculator** (`/pricing`): the dollar price itself is calculated with plain
  deterministic math (see `pricing_engine.py`) so it never depends on the AI being reachable -
  hourly rate x hours, adjusted by complexity/urgency multipliers, plus additional charges
  and tax. The AI is only used afterward for qualitative suggestions: recommended delivery
  time, market analysis, and improvement tips. Full history, edit & recalculate, delete.
- `ai_service.py` gained `parse_ai_sections()` - a shared parser for AI responses that need
  more than one field back (marked with `### SECTION_NAME` headers). Both Gig Descriptions
  and Pricing use it; any future module needing structured AI output can reuse it too.
- Dashboard sidebar and Quick Actions now link to the real Gig and Pricing modules; Recent
  Activity includes them too.
- **Schema note:** `GigDescription` gained a `features` column and `PricingHistory` gained
  `recommended_delivery_time`, `market_analysis`, `service_improvement_tips` columns. If you
  already ran the Day 2 zip and have an existing `instance/app.db`, delete it before running
  Day 3 so the new columns get created - there's no real data to lose at this stage.
- Verified end-to-end with automated tests (gig generation + section parsing, pricing
  calculation + math verification, edit/regenerate/delete) using mocked AI responses, since
  this build environment cannot reach api.groq.com directly. **Run one real test with your
  GROQ_API_KEY before submitting.**

## What's included (Day 2)

- `ai_service.py` — shared Groq API integration (used by every future AI module too)
- `pdf_service.py` — shared ReportLab PDF export (used by every future document module too)
- **Proposal Generator** (`/proposals`): create with AI, view, edit inputs, regenerate,
  manually edit + save generated text, copy to clipboard, delete, export as PDF, full history
- **Cover Letter Generator** (`/cover-letters`): same full feature set as above
- AI credit deducted by 1 each time content is generated or regenerated; dashboard
  "AI Credits" widget reflects it live
- Dashboard sidebar and Quick Actions now link to the real modules instead of
  "Coming Soon" placeholders for these two
- Verified end-to-end with an automated test (register → generate → regenerate →
  manual edit → PDF export → delete) using a mocked AI response, since this
  build environment cannot reach api.groq.com directly.
  **Run one real test with your GROQ_API_KEY before submitting.**

## What's included (Day 1)

- Flask app factory (`app.py`) using blueprints, ready to grow day by day
- SQLite database via SQLAlchemy, auto-created on first run
- User Registration, Login, Logout, Forgot Password (stub — no real email sender yet)
- Session management via Flask-Login
- Dashboard with widgets: Total Proposals, Cover Letters Created, Active Clients,
  Total Invoices, AI Credits, Recent Activity, Quick Actions
- **All Day 2–5 database tables already created** (Proposals, Cover Letters,
  Gig Descriptions, Pricing History, Client Replies, Invoices, Contracts) —
  empty for now, so the dashboard shows real counts and no schema migration
  is needed later
- Placeholder "Coming Soon" pages behind every Quick Action button, so nothing
  is a dead link while later days are being built
- Dark charcoal/slate UI with a green accent (no blue), matching a clean
  professional look

## Tech stack

- Backend: Python 3.10+, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF
- Database: SQLite (file-based, lives in `/instance/app.db`)
- Frontend: Server-rendered Jinja2 templates + plain CSS/JS (no build step)
- AI (wired in from Day 2): Groq API (`llama-3.3-70b-versatile`)

## Setup (local development)

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your .env file
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
# Then open .env and set SECRET_KEY and GROQ_API_KEY
# (get a free Groq key at https://console.groq.com/keys)

# 4. Run the app
python app.py
```

Visit **http://127.0.0.1:5000** — you'll land on the login page.
Click "Sign up" to create your first account; the dashboard opens right after.

The SQLite database file is created automatically at `instance/app.db` the first
time you run the app — nothing to configure. If you're upgrading from an earlier
day's zip, delete any existing `instance/app.db` first so the current schema
(which includes every day's columns) gets created fresh.

Note: each user can also set their own personal Groq key in **Settings** inside
the app, which overrides the shared `.env` key just for their own generations —
useful if multiple people use the same deployment.

## Project structure

```
ai_freelancer_assistant/
├── app.py                    # App factory, blueprint registration, error handlers
├── config.py                 # Config (reads .env)
├── extensions.py              # db, login_manager, csrf singletons
├── models.py                  # Every table: Users, UserProfile, Proposal, CoverLetter,
│                               # GigDescription, PricingHistory, ClientReply, Invoice, Contract
├── ai_service.py               # Groq API integration, credit deduction, multi-section parsing
├── pdf_service.py               # ReportLab PDF builders (proposal, cover letter, invoice, contract)
├── pricing_engine.py             # Deterministic pricing math (no AI dependency)
├── requirements.txt
├── .env.example
├── .gitignore
├── Procfile                    # For Render/Railway deployment
├── API_DOCUMENTATION.md
├── auth/                       # Register, Login, Logout, Forgot Password
├── dashboard/                  # Widgets, Quick Actions, Recent Activity
├── proposals/  cover_letters/  gigs/  pricing/            # Day 2-3 AI modules
├── client_replies/  invoices/  contracts/                 # Day 4 modules
├── user_profile/  settings/  history/                     # Day 5 modules
├── modules/                    # Now-empty "coming soon" fallback (kept for safety)
├── templates/
│   ├── base.html, app_base.html, _form_macros.html
│   ├── errors/                 # 404, 500
│   └── (one folder per module above)
├── static/
│   ├── css/style.css           # Dark + light theme (CSS variables)
│   ├── js/main.js
│   └── uploads/avatars/        # Profile picture uploads
└── instance/
    └── app.db                  # Created automatically on first run
```

## Deployment

The app is a standard Flask app with a SQLite database, ready for Render or Railway.

**Render / Railway (recommended for this project):**
1. Push the repo to GitHub (see the checklist below for what to exclude).
2. Create a new Web Service pointing at the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app` (already in the `Procfile`, most platforms detect it automatically)
5. Set environment variables in the platform's dashboard: `SECRET_KEY`, `GROQ_API_KEY`, `GROQ_MODEL`, `DATABASE_URL` (optional — defaults to SQLite).
6. **Important SQLite caveat:** most platforms' filesystems are ephemeral, meaning `instance/app.db` gets wiped on every redeploy. For a real production deployment, either (a) attach a persistent disk on Render and point `DATABASE_URL` at a path on it, or (b) switch to a managed Postgres database (Render/Railway both offer one) - Flask-SQLAlchemy makes that a one-line `DATABASE_URL` change, no code changes needed.

**Vercel:** possible but not recommended for this app - Vercel's serverless functions don't suit a stateful SQLite file well. Render or Railway is the simpler path for exactly this stack.

**Netlify:** static-site focused, not a fit for a Flask backend with a database. Skip it for this project.

## Day 1 checklist (per project spec)

- [x] User Registration
- [x] User Login
- [x] Forgot Password (stub, email sending optional per spec)
- [x] Dashboard with all required widgets
- [x] Database Connection
- [x] User Authentication
- [x] Session Management
- [x] Users, User Profiles tables
- [ ] Email Verification — marked Optional in the spec; not built yet

## Day 2 checklist (per project spec)

- [x] Proposal Generator: Create, Edit, Delete, Save, History, Copy, Export as PDF
- [x] Proposal Input: Client Name, Project Title, Description, Skills, Budget, Timeline, Tone
- [x] Cover Letter Generator: Job Title, Company Name, Experience, Skills, Portfolio URL
- [x] Generate with AI / Regenerate Content
- [x] Save History
- [x] AI Integration (Groq API, OpenAI-compatible endpoint)
- [x] Proposals, Cover Letters database tables
- [x] Working Proposal Generator
- [x] Working Cover Letter Generator
- [x] AI API Integration

## Day 3 checklist (per project spec)

- [x] Gig Description Generator: Service Category, Skills, Experience Level, Delivery Time, Features, Revisions
- [x] AI Generated Description, SEO Keywords, FAQ Suggestions
- [x] Pricing Calculator: Hourly Rate, Estimated Hours, Project Complexity, Urgency, Additional Charges, Tax
- [x] AI Suggestions: Suggested Price, Recommended Delivery Time, Market Analysis, Service Improvement Tips
- [x] Gig Descriptions, Pricing History database tables
- [x] Working Gig Generator
- [x] Smart Pricing Calculator
- [x] Database Integration

## Day 4 checklist (per project spec)

- [x] Client Reply Generator: Client Message Input, Reply Tone Selection, AI Generated Reply, Copy Response, Save Response
- [x] Invoice Generator: Client Details, Project Details, Services, Amount, Due Date, Tax, Generate Invoice, Download PDF
- [x] Contract Generator: Client Details, Freelancer Details, Project Scope, Timeline, Payment Terms, Terms & Conditions, AI Generated Contract, Export PDF
- [x] Invoices, Contracts, Client Replies database tables
- [x] Working Client Reply Generator
- [x] Invoice Generator
- [x] Contract Generator

## Day 5 checklist (per project spec)

- [x] History: Proposal, Cover Letter, Invoice, Contract, Gig History (per-module pages + one unified filterable feed)
- [x] User Profile: Edit Profile, Upload Profile Picture, Change Password, Account Settings
- [x] Application Settings: Theme Settings (functional dark/light), API Key Settings, Notification Settings, Language Settings (English implemented; Urdu flagged as not-yet-translated rather than faked)
- [x] Fully Responsive (existing CSS grid layouts flex down to mobile widths)
- [x] Error Handling (custom 404/500 pages, upload-too-large handling)
- [x] Loading Indicators (submit buttons show "Working..." during requests)
- [x] Form Validation (WTForms on every form; fixed a real DataRequired-vs-zero bug this round)
- [x] API Error Handling (`ai_service.AIGenerationError` surfaces clear messages instead of crashing)
- [x] Security Improvements (security headers, HttpOnly/SameSite cookies, upload validation, CSRF everywhere)
- [x] Final Testing (automated end-to-end tests for every module, plus full Day 1-4 regression)
- [x] Deployment prep: `Procfile`, `gunicorn`, `.gitignore`
- [x] Source Code (this zip)
- [x] Database File (created automatically - see caveat about ephemeral filesystems above)
- [x] API Documentation (`API_DOCUMENTATION.md`)
- [ ] GitHub Repository — you push this
- [ ] Live Demo Link — you deploy this (see Deployment section above)
- [ ] Demo Video (5-10 minutes) — you record this

## Final submission checklist (cumulative, Day 1–5)

- [ ] Push everything to GitHub with `.env` git-ignored (already handled by `.gitignore`) and `.env.example` kept in the repo
- [ ] Delete any local `instance/app.db` before your final push so a fresh one gets created for whoever clones it
- [ ] Deploy to Render or Railway following the steps above; note the live URL
- [ ] Set `SECRET_KEY` and `GROQ_API_KEY` as environment variables on the hosting platform (never commit them)
- [ ] Do one real end-to-end run with your actual Groq key locally or on the deployed link: register → generate a proposal, cover letter, gig description, pricing calculation, client reply, invoice, and contract → check history → edit profile → change theme
- [ ] Record the demo video walking through each Day 1-5 feature
- [ ] Final README pass: confirm the Day 1-5 checklists above still match what's actually in the repo
