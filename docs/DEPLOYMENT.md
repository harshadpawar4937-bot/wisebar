# Deployment

## Frontend

Build with `npm run build` in `frontend/`. Host the `dist` folder on Vercel, Netlify, or Cloudflare.

Proxy `/api` to the FastAPI origin so the browser stays on one site and the session cookie works. On Vercel, a rewrite is enough:

```json
{ "rewrites": [{ "source": "/api/(.*)", "destination": "https://YOUR_API_HOST/api/$1" }] }
```

Set `CORS_ORIGINS` to the real site origin if the API is called cross-origin instead. Cookies then need `DEBUG=false` so `Secure` is set, and both sides on HTTPS.

## Backend

Run `uvicorn app.main:app --host 0.0.0.0 --port 8000` on Railway, Render, or AWS.

Environment, all required in production:

- `DATABASE_URL` — SQL Server connection string (`mssql+pyodbc://...`). Install the ODBC driver and `pip install -r requirements-mssql.txt`.
- `SECRET_KEY` — long random string.
- `DEBUG=false`
- `ADMIN_EMAIL`, `ADMIN_PASSWORD` — first operator, created once.
- `CORS_ORIGINS`
- `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` — leave empty until the account exists. Checkout will refuse to charge.
- `GA_MEASUREMENT_ID` — optional. Empty means no third-party tag.
- `S3_*` — optional. Empty means image upload stays unavailable and concept art is used.
- `SMTP_HOST`, `SMTP_FROM` — optional. Empty means password reset does not claim to send mail.

The app creates tables on startup. Point Razorpay’s webhook at `POST /api/payments/webhook`.

## SQL Server note

SQLite is the local default so the project runs on a laptop without a database server. The models use portable types (integers, numerics, strings, JSON). Confirm JSON support on the SQL Server version you deploy, or map those columns to `NVARCHAR` if you are on an older engine. Do that in `database.py` before the first production migration, not by editing product rows.

## Analytics events

The frontend posts to `/api/analytics/events` and, when a measurement id exists, also calls `gtag`. Event names: page view, product view, add to cart, remove from cart, begin checkout, purchase, wishlist, search, filter, coupon applied, subscription, build box, corporate lead, newsletter signup, recommendation click.
