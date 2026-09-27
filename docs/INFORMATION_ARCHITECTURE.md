# WISEBAR™ information architecture

Locked before interface build. Routes, content ownership, and commerce rules below are the contract the frontend and API both follow.

## Brand job

Help a person choose a practical high-protein food (a bar or a muesli), understand exactly what is published about it, and — once a product is actually on sale — buy, subscribe, or enquire for a workplace.

Until a product has a verified specification and a price, it can be browsed and saved. It cannot be purchased.

## Audiences

| Audience | Primary jobs |
| --- | --- |
| Everyday shopper | Find a flavour, read the spec, buy or wait |
| Gift / household buyer | Build a box or pick a bundle |
| Workplace buyer | Request a corporate quote |
| Returning customer | Reorder, manage subscription, track an order |
| Operator | Publish products, prices, journal, reviews, and offers without a deploy |

## Sitemap

| URL | Purpose | Primary CTA |
| --- | --- | --- |
| `/` | Brand, category choice, discovery, education | Shop Protein Bars |
| `/protein-bars` | Filterable bar catalogue | View product |
| `/protein-muesli` | Filterable muesli catalogue | View product |
| `/products/:slug` | Decision page for one SKU | Add to cart, when purchasable |
| `/bundles` | Named combos | View included products |
| `/build-your-box` | Choose a size and flavours | Build my box |
| `/about` | Brand story, with unpublished chapters marked | Shop or contact |
| `/journal` | Education, not medical advice | Read an article |
| `/journal/:slug` | Article | Related reading |
| `/corporate` | Workplace snacking enquiry | Request corporate quote |
| `/contact` | Message the team | Send message |
| `/faq` | Published answers | Contact if unanswered |
| `/shipping` | Shipping policy and order tracking | Track order |
| `/returns` | Returns policy | Contact |
| `/privacy` | Privacy draft | — |
| `/terms` | Terms draft | — |
| `/cookies` | Cookie draft | — |
| `/account` | Profile, orders, subscriptions, wishlist, addresses, rewards, referrals | Sign in |
| `/checkout` | Address and payment handoff | Place order |
| `/search` | Shareable search results | Open a product |
| `/admin` | Operator console | Publish verified data |

Search also opens as a dialog from the header on every page.

## Global chrome

- Announcement: pre-sale status, dismissible for the session.
- Header: Bars, Muesli, Bundles, Build a Box, Journal, Corporate. Search, account, cart.
- Cart drawer: lines, quantities, save for later, free-shipping progress (only after a threshold is configured), suggestions from the real catalogue.
- Footer: Shop, Company, Customer care, Legal, social profiles that exist, newsletter.
- Mobile: same tasks, with a thumb-reachable bar for Shop, Search, Box, Account, and Cart.

## Homepage narrative

1. Hero — what WISEBAR is, and the two ways in.
2. Trust strip — positioning lines. Nutrition claims stay in reserve until specifications are verified.
3. Choose your Wise — bars vs muesli.
4. Featured products — spec cards, never invented numbers.
5. What’s inside — illustrative assembly, labelled as not a published recipe.
6. Know what you eat — the transparency pattern. Lab report link only if a file exists.
7. When you might want a snack — occasions, no health claims.
8. Product finder — occasion, taste, protein, budget. Recommends real SKUs only.
9. Build a box — teaser into the builder.
10. Bundles.
11. Subscribe & save — cadence, pause/skip/cancel, no lock-in.
12. Why WISE — timeline. Chapters stay blank until a real story is supplied.
13. Journal teaser.
14. Reviews and gallery — empty until real, permissioned material exists.
15. Newsletter and footer.

## Catalogue rules

- A flavour appears only if it exists as a product row.
- Filters for protein, calories, price, and diet are active only where products actually have those values.
- Sort: featured, newest, price low–high, price high–low. Unpriced products sort last on price sorts.
- Compare up to three products on fields the database holds.

## Product page

Above the fold: gallery, name, flavour, price or “Price pending”, protein highlight or “Pending verification”, quantity, add to cart, buy now, pincode check.

Below, on desktop the visual stays pinned while the story steps through taste, protein, ingredients, nutrition, and lifestyle.

Nutrition charts render stored numbers. Empty charts stay empty.

## Commerce rules

Selling is off until an operator turns it on.

A product becomes purchasable only when price, MRP, serving size, net quantity, ingredients, allergens, storage, FSSAI licence, manufacturer, customer-care contact, and a full nutrition panel are stored, and available stock is greater than zero.

Orders, subscriptions, and coupons read those records. Payment is handed to the configured gateway. No gateway keys, no charge.

## Content ownership

| Content | Edited in |
| --- | --- |
| Hero, ticker, box sizes, shipping threshold, claim set | Admin → Settings |
| Products, nutrition, prices, stock | Admin → Products |
| Bundles and coupons | Admin → Merchandising |
| Reviews | Admin → Reviews (approve or reject) |
| Journal | Admin → Journal |
| FAQs, policy pages | Admin → Content |
| Corporate leads | Admin → Leads |

## Account

Registration, login, logout, password reset (email send only when a provider is configured), profile, addresses, orders, subscriptions, wishlist, referral code, points balance. Points do not increment until an earn rule is stored.

## Search and recommendations

Search matches name, flavour, category, ingredient text, and SKU. The finder filters the same catalogue. It does not give medical or disease advice.

## Out of scope for launch data

Invented protein grams, calories, prices, ingredients, FSSAI numbers, lab reports, reviews, ratings, founder biography, and delivery promises. The interface has a slot for each. The slot stays empty until a person fills it.
