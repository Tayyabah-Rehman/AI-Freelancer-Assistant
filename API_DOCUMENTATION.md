# API / Route Documentation — AI Freelancer Assistant

This is a server-rendered Flask app (not a JSON API), so "routes" here return HTML
pages rather than JSON. This document lists every route, its method, whether login
is required, and what it does - useful as the project's API/route reference.

All routes except Auth require an active login session (`@login_required`), and all
state-changing routes (POST) are CSRF-protected via Flask-WTF.

## Auth (`/`)
| Method | Route | Auth | Purpose |
|---|---|---|---|
| GET/POST | `/register` | No | Create a new account |
| GET/POST | `/login` | No | Log in |
| GET | `/logout` | Yes | Log out |
| GET/POST | `/forgot-password` | No | Password reset stub (no email sending wired up yet) |

## Dashboard
| Method | Route | Auth | Purpose |
|---|---|---|---|
| GET | `/` , `/dashboard` | Yes | Widgets, quick actions, recent activity |

## Proposals (`/proposals`)
| Method | Route | Purpose |
|---|---|---|
| GET | `/proposals/` | List all proposals |
| GET/POST | `/proposals/new` | Create + AI-generate a proposal |
| GET | `/proposals/<id>` | View one proposal |
| GET/POST | `/proposals/<id>/edit` | Edit proposal inputs |
| POST | `/proposals/<id>/regenerate` | Re-run AI generation |
| POST | `/proposals/<id>/save-content` | Save manually edited AI text |
| POST | `/proposals/<id>/delete` | Delete |
| GET | `/proposals/<id>/pdf` | Download as PDF |

## Cover Letters (`/cover-letters`)
Same route shape as Proposals (`list`, `new`, `<id>`, `<id>/edit`, `<id>/regenerate`,
`<id>/save-content`, `<id>/delete`, `<id>/pdf`).

## Gig Descriptions (`/gigs`)
Same shape as above. AI response is parsed into three fields: description, SEO
keywords, FAQs (see `ai_service.parse_ai_sections`). No PDF export (not in spec).

## Smart Pricing (`/pricing`)
| Method | Route | Purpose |
|---|---|---|
| GET | `/pricing/` | List all calculations |
| GET/POST | `/pricing/new` | Calculate price (deterministic math, no AI) + get AI suggestions |
| GET | `/pricing/<id>` | View one calculation with full breakdown |
| GET/POST | `/pricing/<id>/edit` | Edit inputs, recalculates + regenerates AI suggestions |
| POST | `/pricing/<id>/delete` | Delete |

The dollar price is always computed by `pricing_engine.calculate_price()` - never by
the AI - so it never depends on the AI provider being reachable.

## Client Replies (`/client-replies`)
Same shape as Proposals, minus PDF export (not in spec).

## Invoices (`/invoices`)
| Method | Route | Purpose |
|---|---|---|
| GET | `/invoices/` | List all invoices |
| GET/POST | `/invoices/new` | Create invoice (no AI call - pure data + math) |
| GET | `/invoices/<id>` | View with subtotal/tax/total breakdown |
| GET/POST | `/invoices/<id>/edit` | Edit |
| POST | `/invoices/<id>/delete` | Delete |
| GET | `/invoices/<id>/pdf` | Download line-item PDF |

## Contracts (`/contracts`)
Same shape as Proposals (full AI generation + regenerate + PDF export).

## Profile (`/profile`)
| Method | Route | Purpose |
|---|---|---|
| GET/POST | `/profile/` | Edit name, bio, skills, portfolio, phone, location, hourly rate, avatar |
| GET/POST | `/profile/password` | Change password |

Avatar uploads: jpg/png/webp only, 2MB max, saved to `static/uploads/avatars/`.

## Settings (`/settings`)
| Method | Route | Purpose |
|---|---|---|
| GET/POST | `/settings/` | Theme (dark/light), language (English only implemented), personal Groq API key override, email notification preference (stored, not yet wired to real email sending) |

## History (`/history`)
| Method | Route | Purpose |
|---|---|---|
| GET | `/history/` | Unified feed across all 7 document types |
| GET | `/history/?type=<slug>` | Filter by one type: `proposal`, `cover_letter`, `gig`, `pricing`, `client_reply`, `invoice`, `contract` |

## Error handling
- `404` → custom page, `templates/errors/404.html`
- `500` → custom page + automatic `db.session.rollback()`, `templates/errors/500.html`
- `413` (upload too large) → flash message + redirect back

## Notes on the AI integration itself
All AI calls go through `ai_service.call_groq()`, which hits Groq's OpenAI-compatible
endpoint (`https://api.groq.com/openai/v1/chat/completions`). If a user has set a
personal key in Settings, it's used instead of the app-wide `GROQ_API_KEY` from `.env`.
