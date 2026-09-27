from __future__ import annotations

import secrets

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import (
    BlogPost,
    Bundle,
    BundleItem,
    Category,
    Faq,
    Inventory,
    Page,
    Product,
    ProductVariant,
    RewardRule,
    Setting,
    User,
)
from app.security import hash_password

DISCLAIMER = (
    "General food education. This is not medical, dietary, or disease advice, "
    "and it is not a claim about any WISEBAR product."
)


def seed(db: Session) -> None:
    if db.query(Category).count():
        _ensure_admin(db)
        db.commit()
        return
    bars = Category(
        slug="protein-bars",
        name="Protein Bars",
        tagline="Protein that goes where you go.",
        description="Portable protein for wherever the day takes you.",
    )
    muesli = Category(
        slug="protein-muesli",
        name="Protein Muesli",
        tagline="Start strong. Stay fueled.",
        description="Start the day with a protein-rich bowl.",
    )
    db.add_all([bars, muesli])
    db.flush()

    drafts = [
        dict(sku="WB-BAR-COCOA", slug="cocoa-crunch-bar", name="Cocoa Crunch Bar", flavor="Cocoa Crunch", flavor_family="cocoa", category=bars, sort_order=1, occasions=["work", "travel", "evening"], description="A proposed cocoa-flavoured protein bar. The recipe, nutrition panel, allergens, and price will be published before this product is offered for sale."),
        dict(sku="WB-BAR-PEANUT", slug="peanut-date-bar", name="Peanut Date Bar", flavor="Peanut Date", flavor_family="nut", category=bars, sort_order=2, occasions=["work", "pre-workout", "post-workout", "travel"], description="A proposed peanut-and-date protein bar. Nothing on this page is a finished specification."),
        dict(sku="WB-BAR-BERRY", slug="mixed-berry-bar", name="Mixed Berry Bar", flavor="Mixed Berry", flavor_family="fruit", category=bars, sort_order=3, occasions=["work", "travel", "evening"], description="A proposed berry-flavoured protein bar, listed so the catalogue structure is ready. Formulation is still open."),
        dict(sku="WB-MUE-GRAIN", slug="classic-grain-muesli", name="Classic Grain Muesli", flavor="Classic Grain", flavor_family="grain", category=muesli, sort_order=4, occasions=["morning"], description="A proposed high-protein muesli. Bowl size, grains, and nutrition will be published with the first batch record."),
        dict(sku="WB-MUE-SEED", slug="nut-seed-muesli", name="Nut & Seed Muesli", flavor="Nut & Seed", flavor_family="seed", category=muesli, sort_order=5, occasions=["morning", "evening"], description="A proposed nut-and-seed muesli. Ingredients are not listed because they are not final."),
    ]
    products = {}
    for row in drafts:
        category = row.pop("category")
        product = Product(
            category_id=category.id,
            is_featured=True,
            status="draft",
            purchasable=False,
            spec_status="pending_verification",
            dietary_labels=[],
            **row,
        )
        db.add(product)
        db.flush()
        db.add(ProductVariant(product_id=product.id, sku=product.sku, label="Standard"))
        db.add(Inventory(product_id=product.id, available=0, reserved=0, low_stock_threshold=10))
        products[product.slug] = product

    bundles = [
        ("starter-box", "Starter Box", "A first assortment of bars. Contents stay editable; price stays empty until each included product has a verified price.", ["cocoa-crunch-bar", "peanut-date-bar"], 1),
        ("breakfast-snack", "Breakfast + Snack", "Muesli for the morning and a bar for later. A pairing, not a priced offer yet.", ["classic-grain-muesli", "cocoa-crunch-bar"], 2),
        ("fitness-box", "Fitness Box", "Bars tagged for days that include training. No performance claim is attached.", ["peanut-date-bar", "mixed-berry-bar"], 3),
        ("office-box", "Office Box", "A shareable bar assortment for a desk or a pantry shelf.", ["cocoa-crunch-bar", "mixed-berry-bar", "peanut-date-bar"], 4),
        ("family-box", "Family Box", "Bars and muesli together, for a household that wants both.", ["classic-grain-muesli", "nut-seed-muesli", "cocoa-crunch-bar"], 5),
    ]
    for slug, name, description, slugs, order in bundles:
        bundle = Bundle(slug=slug, name=name, description=description, price_inr=None, sort_order=order)
        db.add(bundle)
        db.flush()
        for product_slug in slugs:
            db.add(BundleItem(bundle_id=bundle.id, product_id=products[product_slug].id, quantity=1))

    db.add_all(
        [
            Setting(key="home", value=_home()),
            Setting(key="commerce", value={
                "selling_enabled": False,
                "max_qty_per_line": 10,
                "free_shipping_threshold_inr": None,
                "shipping_fee_inr": None,
                "currencies": ["INR"],
            }),
            Setting(key="merchandising", value={
                "box_sizes": [6, 12, 18, 24],
                "subscription_cadence_days": [15, 30, 45, 60],
                "occasion_map": {
                    "morning": {"categories": ["protein-muesli"]},
                    "work": {"categories": ["protein-bars"]},
                    "pre-workout": {"categories": ["protein-bars"]},
                    "post-workout": {"categories": ["protein-bars"]},
                    "travel": {"categories": ["protein-bars"]},
                    "evening": {"categories": ["protein-bars", "protein-muesli"]},
                },
                "ticker_live": ["Smart Snacking", "For Everyday Life", "Bars & Muesli", "Work, Train, Move", "Know What You Eat"],
                "ticker_when_verified": ["High Protein", "Real Ingredients", "Great Taste", "Smart Snacking", "Everyday Fuel"],
                "claims_verified": False,
            }),
            Setting(key="company", value={
                "legal_name": None,
                "support_email": None,
                "phone": None,
                "instagram": None,
                "facebook": None,
                "youtube": None,
                "linkedin": None,
                "serviceable_pincodes": [],
            }),
            Setting(key="story", value=_story()),
        ]
    )
    for event, note in (
        ("purchase", "Points per completed purchase. Leave empty until the rate is decided."),
        ("review", "Points for an approved review."),
        ("referral", "Points when an invited order is paid. One reward per new customer."),
        ("birthday", "Points on a stored birthday. Requires a date the customer chooses to share."),
        ("challenge", "Occasional campaign points. Configure per campaign, do not leave a standing rate by accident."),
    ):
        db.add(RewardRule(event=event, points=None, active=False, note=note))

    faqs = [
        ("When can I buy WISEBAR?", "Sale opens after each product shows a price, a full nutrition panel, allergen and ingredient lists, and an FSSAI licence. Until then the catalogue is a preview."),
        ("Are the protein numbers on the site final?", "No number is final unless the product page marks the panel as verified. Empty fields mean the lab or the formulation is not published yet."),
        ("Do you ship across India?", "Shipping zones, fees, and a free-shipping threshold will be published before the first order. The pincode check uses that list and will not invent a delivery date."),
        ("Can I pause a subscription?", "Yes. The plan is pause, skip, or cancel with no lock-in. A subscription cannot start until selling and payments are both switched on."),
        ("Do you offer corporate orders?", "Yes. Send a quote request with your company, headcount, and what you need. The team replies with pricing rather than an automatic checkout."),
        ("How do reviews get on the site?", "Only reviews from customers, held for moderation, are published. Verified purchase is marked only when the review matches a paid order."),
    ]
    for index, (question, answer) in enumerate(faqs):
        db.add(Faq(question=question, answer=answer, sort_order=index))

    db.add_all([_page(*row) for row in _pages()])
    db.add_all(_posts())
    _ensure_admin(db)
    db.commit()


def _ensure_admin(db: Session) -> None:
    settings = get_settings()
    email = settings.admin_email.strip().lower()
    if db.query(User).filter_by(email=email).one_or_none():
        return
    db.add(
        User(
            email=email,
            name="WISEBAR Admin",
            password_hash=hash_password(settings.admin_password),
            role="admin",
            referral_code="WISE-" + secrets.token_hex(3).upper(),
        )
    )


def _home() -> dict:
    return {
        "eyebrow": "WISEBAR shop · Bars and muesli",
        "hero_line_1": "Out the door.",
        "hero_line_2": "On the table.",
        "hero_support": "Protein bars for the bag. Muesli for the bowl. Pick a flavour and take it with you.",
        "announcement": "First release in preparation. Nutrition, prices, and regulatory details are published on each product before it can be sold.",
        "primary_cta": "Shop Protein Bars",
        "secondary_cta": "Explore Protein Muesli",
        "tertiary_cta": "Why WISEBAR?",
        "category_heading": "Choose your Wise.",
        "featured_heading": "Your everyday protein, without the everyday hassle.",
        "transparency_heading": "Know every ingredient. Love every bite.",
        "box_heading": "Your snacks. Your flavours. Your box.",
        "corporate_line": "Make smarter snacking part of the workday.",
        "newsletter_heading": "Get WISE about what you eat.",
        "newsletter_cta": "Join the Wise List",
        "occasions": [
            {"id": "morning", "title": "Morning", "copy": "A bowl on the table before the day starts.", "href": "/protein-muesli"},
            {"id": "work", "title": "Work", "copy": "A bar in the bag, between one thing and the next.", "href": "/protein-bars"},
            {"id": "pre-workout", "title": "Pre-workout", "copy": "Food you can eat before you train. No timing prescription.", "href": "/protein-bars"},
            {"id": "post-workout", "title": "Post-workout", "copy": "Something savoury or sweet after you move, if you want it.", "href": "/protein-bars"},
            {"id": "travel", "title": "Travel", "copy": "Protein that fits in a bag when the day is not at home.", "href": "/protein-bars"},
            {"id": "evening", "title": "Evening", "copy": "A planned snack instead of whatever happens to be nearby.", "href": "/protein-bars"},
        ],
    }


def _story() -> dict:
    blank = "This chapter will be published when it can be told from WISEBAR’s own record. It is intentionally blank."
    return {
        "heading": "Why WISE?",
        "chapters": [
            {"id": "problem", "title": "The problem", "body": blank},
            {"id": "idea", "title": "The idea", "body": blank},
            {"id": "product", "title": "The product", "body": "Bars and muesli, formulated for ordinary days. Recipes stay unpublished until they are finished and checked."},
            {"id": "community", "title": "The community", "body": blank},
            {"id": "future", "title": "The future", "body": blank},
        ],
    }


def _page(slug: str, title: str, body: str) -> Page:
    return Page(
        slug=slug,
        title=title,
        notice="Draft for counsel. This is a structure, not a finished legal policy, and it is not legal advice.",
        seo_title=f"{title} · WISEBAR",
        seo_description=f"Draft {title.lower()} for WISEBAR. Pending legal review before launch.",
        body=body,
    )


def _pages() -> list[tuple[str, str, str]]:
    return [
        ("shipping", "Shipping", "Orders will ship only after a payment is confirmed and a serviceable pincode list is published.\n\n## What we will show before launch\n\n- Zones we deliver to\n- Fee, and the threshold for free shipping if there is one\n- How to read a tracking update\n\n## Tracking\n\nUse the order number and the mobile number from checkout. We will not guess a delivery date."),
        ("returns", "Returns", "A returns window, the condition of the pack, and the refund path will be written here before the first sale.\n\n## Until then\n\nDo not send product back to a guessed address. Write via the contact form and the team will answer once a process exists.\n\nPerishable food has rules that differ from apparel. The final policy has to follow those rules, not a generic template."),
        ("privacy", "Privacy", "We store account details, orders, and messages you send us so the shop can function.\n\n## What this draft covers\n\n- Account data: name, email, mobile, addresses\n- Order and payment references from the payment provider\n- Corporate enquiries and support messages\n- A first-party record of product and checkout events\n\n## What is not decided yet\n\nThe legal entity, retention periods, and the grievance contact will be added before launch. Analytics and advertising tags stay off until an ID is configured.\n\nPassword reset emails are sent only after an email provider is connected."),
        ("terms", "Terms", "These terms are a placeholder for the conditions of sale.\n\n## Commerce\n\nA product can be bought only when its page shows a price and a verified specification, and selling is switched on.\n\n## Accounts\n\nYou are responsible for the mobile number and address you enter. Referral rewards, if a programme opens, will follow published rules and may be reversed in cases of abuse.\n\n## Liability language\n\nTo be written by counsel. Nothing on the marketing pages is a medical claim."),
        ("cookies", "Cookies", "The shop uses a session cookie and a CSRF cookie so sign-in and the cart work.\n\n## Optional tags\n\nA measurement ID for analytics is read from the environment. If it is empty, no third-party analytics script is loaded.\n\nAdvertising cookies are not part of this build."),
    ]


def _posts() -> list[BlogPost]:
    posts = [
        (
            "what-protein-does-in-a-day",
            "What protein is doing in an ordinary day",
            "Protein",
            "A plain-language look at protein as a nutrient, without a target stolen from someone else’s body.",
            f"""{DISCLAIMER}

## A nutrient, not a personality

Protein is one of the three energy-bearing nutrients, alongside carbohydrate and fat. People use the word as if it were a lifestyle. On a label it is simpler: grams, in a stated serving.

## Why the serving matters

A bar and a bowl are not the same eating occasion. Compare products on the same basis the pack uses — per serving, and per 100 g if the label shows it. A bigger number on a bigger serving is not automatically a different food.

## What this site will and will not say

When a WISEBAR specification is verified, the product page will show protein, calories, carbohydrate, sugar, fat, and fibre for that serving. Until those fields are filled from the real formulation, the page leaves them blank on purpose.

This article does not set a daily target for you. If you need one, that conversation belongs with a doctor or a qualified dietitian who knows your situation.
""",
        ),
        (
            "how-to-read-a-nutrition-label",
            "How to read a nutrition label without squinting",
            "Nutrition",
            "The few lines on an Indian food label that change what you think you are eating.",
            f"""{DISCLAIMER}

## Start with the serving

Everything in the panel hangs off the serving size and the net quantity. If you eat more than one serving, the rest of the numbers scale with that.

## Then the short list

Look at energy, protein, carbohydrate, total sugar, fat, and fibre. Sugar sitting inside carbohydrate is a subset, not a second meal. Ingredients are listed in descending order by weight — the first items are doing most of the work.

## Allergens are not a footnote

Milk, nuts, peanuts, soy, gluten, and the rest belong where you can see them before you buy. A brand that has not finished a formulation should say so, rather than guess the allergen line.

## Claims

Words like “high protein” are regulated claims, not decoration. They belong on a pack only when the numbers meet the rule that applies to that food. A marketing page should not get there first.
""",
        ),
        (
            "a-protein-breakfast-that-fits",
            "A protein breakfast that still fits a weekday",
            "Breakfast",
            "Ideas for mornings that are short, without pretending one bowl suits every person.",
            f"""{DISCLAIMER}

## The constraint is time

Most breakfasts fail the calendar, not the cookbook. A bowl of muesli with curd or milk, or a bar eaten with a drink you already like, is a pattern people can repeat. Repetition beats an elaborate plan you abandon on Wednesday.

## Build the bowl in pieces

A grain base, something for protein, and a fruit or nut you actually enjoy. Measure against the serving on the pack once, so “a bowl” means something.

## Bars are not a moral category

A bar is useful when you are not at a table. It is not a better breakfast than food you sit down for, and it is not a worse one. It is a format.

WISEBAR’s muesli and bars will spell out their own servings when the specifications are ready. Until then, use this as a way of thinking, not a menu.
""",
        ),
    ]
    output = []
    for slug, title, category, excerpt, body in posts:
        output.append(
            BlogPost(
                slug=slug,
                title=title,
                excerpt=excerpt,
                body=body.strip(),
                category=category,
                status="published",
                published_at="2026-09-01",
                seo_title=f"{title} · WISEBAR Journal",
                seo_description=excerpt,
                author="WISEBAR Journal",
            )
        )
    return output
