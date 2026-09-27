# Production checklist

Do not take payment until every line is true.

- [ ] `DEBUG` is false and `SECRET_KEY` is not the sample value.
- [ ] Admin password has been changed. The sample password is not in use.
- [ ] Database is SQL Server, backed up, and not the SQLite file.
- [ ] HTTPS is on for the site and the API.
- [ ] Each SKU on sale has price, MRP, stock, serving, net quantity, ingredients, allergens, storage, FSSAI licence, manufacturer, customer care, and a full nutrition panel.
- [ ] Purchasable was accepted by the API (it rejects incomplete specs).
- [ ] `selling_enabled` is true only after the above.
- [ ] Shipping fee and free-shipping threshold are real numbers from the logistics quote.
- [ ] Serviceable pincodes are loaded, or the checker still says zones are unpublished.
- [ ] Razorpay keys and webhook secret are in the environment. A test payment and a failed payment have both been watched.
- [ ] Webhook rejects a bad signature.
- [ ] Legal pages have been replaced by counsel. The draft notice is gone.
- [ ] Founder chapters are either the real story or still explicitly unpublished.
- [ ] No review, rating, or gallery image was inserted by hand without a source.
- [ ] Ticker claims that need a lab (`High Protein`, `Great Taste`, and the rest of `ticker_when_verified`) are off until `claims_verified` is set on purpose.
- [ ] Support email and phone in company settings are monitored inboxes.
- [ ] SMTP is connected and a password reset was received.
- [ ] Object storage is connected if you are uploading pack shots.
- [ ] GA4 id, if used, matches the property you actually own.
- [ ] Rate limits and admin audit log were spot-checked.
- [ ] `pytest` is green. The shop was clicked through at 375 and 1440.
- [ ] Lighthouse was run on the production URL, not just the dev server.
