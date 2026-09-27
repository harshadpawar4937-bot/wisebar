# WISEBAR™

A direct-to-consumer shop for a high-protein food brand: bars, muesli, bundles, a build-your-box flow, subscriptions, corporate enquiries, a journal, and an operator console.

The catalogue ships as a **preview**. Protein, calories, ingredients, prices, FSSAI details, reviews, and the founder story are empty on purpose. The API refuses to mark a product purchasable until that specification is complete, and it refuses checkout until selling, shipping rules, and a payment gateway are all configured.

## Run it locally

Terminal one:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload --port 8000
```

Terminal two:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api` to port 8000.

Operator sign-in uses `ADMIN_EMAIL` and `ADMIN_PASSWORD` from `backend/.env`. Change both before anyone else can reach the machine. The admin UI is at `/admin`.

## Tests

```bash
cd backend && .venv/bin/pytest
cd frontend && npm test
```

## What lives where

| Path | Role |
| --- | --- |
| `frontend/` | React 18, Vite, TypeScript, Tailwind, Framer Motion, Lenis |
| `backend/` | FastAPI, SQLAlchemy |
| `docs/INFORMATION_ARCHITECTURE.md` | Routes and commerce rules |
| `docs/DESIGN_SYSTEM.md` | Colour, type, components |
| `docs/QA.md` | Test cases |
| `docs/DEPLOYMENT.md` | How to host it |
| `docs/PRODUCTION_CHECKLIST.md` | What has to be true before sale |

Local development uses SQLite. Production is aimed at Microsoft SQL Server: set `DATABASE_URL` to an `mssql+pyodbc://` URL and install `requirements-mssql.txt` plus the ODBC driver. The schema is created on startup.

## Publishing a real product

In `/admin`, open the product and fill price, MRP, stock, serving size, net quantity, ingredients, allergens, storage, FSSAI licence, manufacturer, customer care, and the full nutrition panel. Turn on **Purchasable**. The API rejects the save if any of those are missing.

Then, in settings → `commerce`, set `selling_enabled`, `free_shipping_threshold_inr`, and `shipping_fee_inr`. Add Razorpay keys to the environment. Checkout creates a provider order only after that. Webhooks need `RAZORPAY_WEBHOOK_SECRET`.

Nutrition claims in the ticker (`ticker_when_verified`) stay unused until `claims_verified` is true.

## Honesty rules baked into the code

- No seeded prices, grams, allergens, licences, batch numbers, or reviews.
- “View report” renders only when `lab_report_url` is stored.
- Ratings render only from approved reviews tied to a paid order.
- Wise Points rules exist as rows with null values until an operator sets them.
- Password reset does not pretend an email was sent. A dev token is returned only when `DEBUG=true` and SMTP is empty.
- Payment secrets are read from the environment, never from the frontend bundle.
