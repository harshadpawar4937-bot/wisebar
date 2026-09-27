# QA

Automated coverage is in `backend/tests/test_api.py` and `frontend/src/lib/format.test.ts`. The cases below are the full pass before a production launch. A case is done only when the result matches the expected column, including the honest empty states.

## Functional

| Case | Expected |
| --- | --- |
| Register, login, logout | Session cookie is HttpOnly. `/auth/me` follows it. |
| Password reset | Same public message whether or not the email exists. Email sends only after SMTP is set. |
| Browse bars and muesli | Only rows in the database. |
| Search, filter, sort | Bound parameters. Unpriced products sort last on price sorts. |
| Product detail | Pending fields stay pending. Lab report link only with a URL. |
| Wishlist | Account list matches saved products. |
| Cart quantity, remove, save for later | Server cart. Over-max quantity is rejected. |
| Coupon | Unknown, expired, and duplicate use are rejected. No coupons are seeded. |
| Build a box | Subtotal stays pending while any item has no price. Add fails until purchasable. |
| Checkout | 409 while selling is off or the gateway is missing. |
| Payment success and failure | Webhook signature required. Failed provider call cancels the order and restocks. |
| Order cancel and refund | Illegal status jumps are rejected. Stock is released once. |
| Subscription | Rejected until selling is on and every item is purchasable. Pause, skip, cancel. |
| Review | Rejected without a paid order. Hidden until approved. |
| Corporate and contact forms | Stored. Invalid email is 422. |
| Admin CRUD | Customer token gets 403. Incomplete purchasable save gets 400 with `missing`. |
| Journal | Drafts are not on `/blog`. |
| SEO | `/api/sitemap.xml` lists products and articles. |

## Negative

| Case | Expected |
| --- | --- |
| Bad email, mobile, pincode | 422 from the API, message on the form. |
| Empty cart checkout | 400 once selling is on; 409 before that. |
| Quantity 0, negative, or huge | 422. |
| Out-of-stock add | 409. |
| Archived product still in a cart | Rejected at checkout. |
| Duplicate webhook | `mark_paid` is idempotent. |
| Unauthenticated admin | 401. |
| Search payload `' OR 1=1 --` | 200 and a list, not a server error. |
| HTML in a corporate message | Stored as text and rendered as text. |

## Viewports

375, 390, 414, 768, 1024, 1280, 1440, 1920. Check the bottom bar, the sticky add-to-cart, the cart drawer, and that no section scrolls sideways.

## Definition of done

No broken route, no console error on the main paths, no layout overflow, no checkout that pretends to charge, no fake nutrition, no secrets in the frontend bundle, no dead control without an explanation.
