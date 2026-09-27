from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.database import get_db
from app.deps import ensure_csrf, load_cart, mutate, optional_user
from app.models import AnalyticsEvent, BlogPost, Bundle, Category, ContactMessage, CorporateLead, Faq, NewsletterSubscriber, Page, Product, Review, User
from app.schemas import ContactIn, EventIn, LeadIn, NewsletterIn, PincodeIn, QuizIn, ReviewIn
from app.security import rate_limit as limit
from app.serialize import product_dict
from app.services import quote_cart, recommend, setting

router = APIRouter()


def public_config(db: Session) -> dict:
    commerce = setting(db, "commerce")
    return {
        "home": setting(db, "home"),
        "story": setting(db, "story"),
        "merchandising": setting(db, "merchandising"),
        "commerce": {
            "selling_enabled": bool(commerce.get("selling_enabled")),
            "free_shipping_threshold_inr": commerce.get("free_shipping_threshold_inr"),
            "shipping_fee_inr": commerce.get("shipping_fee_inr"),
            "max_qty_per_line": commerce.get("max_qty_per_line") or 10,
        },
        "company": setting(db, "company"),
        "payments_configured": get_settings().payments_configured,
        "ga_measurement_id": get_settings().ga_measurement_id or None,
        "storage_configured": get_settings().storage_configured,
    }


def user_brief(user: User | None) -> dict | None:
    if user is None:
        return None
    return {"id": user.id, "name": user.name, "email": user.email, "phone": user.phone, "role": user.role, "referral_code": user.referral_code, "points_balance": user.points_balance}


@router.get("/session")
def session(request: Request, response: Response, db: Session = Depends(get_db), user: User | None = Depends(optional_user), cart=Depends(load_cart)):
    return {"csrf": ensure_csrf(request, response), "user": user_brief(user), "cart": quote_cart(db, cart), "config": public_config(db)}


@router.get("/categories")
def categories(db: Session = Depends(get_db)):
    rows = db.query(Category).order_by(Category.id).all()
    return [{"slug": row.slug, "name": row.name, "tagline": row.tagline, "description": row.description} for row in rows]


def _filtered(db: Session, category: str | None, flavor: str | None, q: str | None, dietary: str | None, availability: str | None, min_protein: float | None, max_protein: float | None, min_price: float | None, max_price: float | None, max_calories: float | None, pack_size: int | None, sort: str):
    query = db.query(Product).options(joinedload(Product.category), joinedload(Product.variants), joinedload(Product.inventory)).filter(Product.status != "archived")
    if category:
        query = query.join(Category).filter(Category.slug == category)
    if flavor:
        query = query.filter(Product.flavor == flavor)
    if q:
        like = f"%{q.replace('%', '').replace('_', '')}%"
        query = query.filter(or_(Product.name.ilike(like), Product.flavor.ilike(like), Product.sku.ilike(like), Product.ingredients.ilike(like), Product.description.ilike(like)))
    if pack_size:
        query = query.filter(Product.pack_size == pack_size)
    if min_protein is not None:
        query = query.filter(Product.protein_g.isnot(None), Product.protein_g >= min_protein)
    if max_protein is not None:
        query = query.filter(Product.protein_g.isnot(None), Product.protein_g <= max_protein)
    if min_price is not None:
        query = query.filter(Product.price_inr.isnot(None), Product.price_inr >= min_price)
    if max_price is not None:
        query = query.filter(Product.price_inr.isnot(None), Product.price_inr <= max_price)
    if max_calories is not None:
        query = query.filter(Product.calories_kcal.isnot(None), Product.calories_kcal <= max_calories)
    if availability == "in_stock":
        query = query.filter(Product.purchasable.is_(True))
    elif availability == "coming_soon":
        query = query.filter(Product.purchasable.is_(False))
    rows = query.all()
    if dietary:
        rows = [row for row in rows if dietary in (row.dietary_labels or [])]
    if sort == "newest":
        rows.sort(key=lambda row: row.created_at or datetime.min, reverse=True)
    elif sort == "price_asc":
        rows.sort(key=lambda row: (row.price_inr is None, float(row.price_inr or 0)))
    elif sort == "price_desc":
        rows.sort(key=lambda row: (row.price_inr is None, -(float(row.price_inr or 0))))
    else:
        rows.sort(key=lambda row: row.sort_order)
    return rows


@router.get("/products")
def products(
    category: str | None = None,
    flavor: str | None = None,
    q: str | None = None,
    dietary: str | None = None,
    availability: str | None = None,
    min_protein: float | None = None,
    max_protein: float | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    max_calories: float | None = None,
    pack_size: int | None = None,
    sort: str = "featured",
    db: Session = Depends(get_db),
):
    rows = _filtered(db, category, flavor, q, dietary, availability, min_protein, max_protein, min_price, max_price, max_calories, pack_size, sort)
    return [product_dict(db, row) for row in rows]


@router.get("/products/{slug}")
def product_detail(slug: str, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.variants), joinedload(Product.inventory))
        .filter(Product.slug == slug, Product.status != "archived")
        .one_or_none()
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    data = product_dict(db, product)
    from app.models import Batch, Ingredient

    data["ingredient_rows"] = [
        {"name": row.name, "note": row.note} for row in db.query(Ingredient).filter_by(product_id=product.id).order_by(Ingredient.sort_order).all()
    ]
    data["batches"] = [
        {"batch_number": row.batch_number, "manufacturing_date": row.manufacturing_date, "expiry_date": row.expiry_date}
        for row in db.query(Batch).filter_by(product_id=product.id).all()
        if row.batch_number
    ]
    data["reviews"] = [
        {
            "id": row.id,
            "author_name": row.author_name,
            "rating": row.rating,
            "body": row.body,
            "verified_purchase": row.verified_purchase,
            "created_at": row.created_at.isoformat(),
        }
        for row in db.query(Review).filter_by(product_id=product.id, status="approved").order_by(Review.created_at.desc()).all()
    ]
    return data


@router.get("/search")
def search(q: str = Query(default=""), db: Session = Depends(get_db)):
    term = q.strip()
    if len(term) < 2:
        featured = db.query(Product).filter(Product.is_featured.is_(True), Product.status != "archived").order_by(Product.sort_order).limit(5).all()
        return {"query": term, "products": [product_dict(db, row) for row in featured], "suggestions": [row.flavor for row in featured], "categories": []}
    rows = _filtered(db, None, None, term, None, None, None, None, None, None, None, None, "featured")
    categories = db.query(Category).filter(Category.name.ilike(f"%{term}%")).all()
    return {
        "query": term,
        "products": [product_dict(db, row) for row in rows[:12]],
        "suggestions": [row.flavor for row in rows[:6]],
        "categories": [{"slug": row.slug, "name": row.name} for row in categories],
    }


@router.get("/bundles")
def bundles(db: Session = Depends(get_db)):
    rows = db.query(Bundle).options(joinedload(Bundle.items)).filter(Bundle.active.is_(True)).order_by(Bundle.sort_order).all()
    output = []
    for bundle in rows:
        output.append(
            {
                "slug": bundle.slug,
                "name": bundle.name,
                "description": bundle.description,
                "price_inr": None if bundle.price_inr is None else f"{bundle.price_inr:.2f}",
                "items": [
                    {"product_id": item.product_id, "slug": item.product.slug, "name": item.product.name, "flavor": item.product.flavor, "quantity": item.quantity, "flavor_family": item.product.flavor_family}
                    for item in bundle.items
                ],
            }
        )
    return output


@router.post("/recommendations")
def recommendations(body: QuizIn, db: Session = Depends(get_db)):
    result = recommend(db, body.model_dump())
    return {"notes": result["notes"], "products": [product_dict(db, row) for row in result["products"]]}


@router.get("/blog")
def blog(category: str | None = None, db: Session = Depends(get_db)):
    query = db.query(BlogPost).filter(BlogPost.status == "published")
    if category:
        query = query.filter(BlogPost.category == category)
    rows = query.order_by(BlogPost.published_at.desc()).all()
    return [_post_brief(row) for row in rows]


@router.get("/blog/{slug}")
def blog_post(slug: str, db: Session = Depends(get_db)):
    row = db.query(BlogPost).filter_by(slug=slug, status="published").one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Article not found.")
    data = _post_brief(row)
    data["body"] = row.body
    data["canonical_url"] = row.canonical_url
    data["og_image"] = row.og_image
    return data


def _post_brief(row: BlogPost) -> dict:
    return {
        "slug": row.slug,
        "title": row.title,
        "excerpt": row.excerpt,
        "category": row.category,
        "published_at": row.published_at,
        "seo_title": row.seo_title,
        "seo_description": row.seo_description,
        "author": row.author,
    }


@router.get("/pages/{slug}")
def page(slug: str, db: Session = Depends(get_db)):
    row = db.query(Page).filter_by(slug=slug).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Page not found.")
    return {"slug": row.slug, "title": row.title, "body": row.body, "notice": row.notice, "seo_title": row.seo_title, "seo_description": row.seo_description}


@router.get("/faqs")
def faqs(db: Session = Depends(get_db)):
    rows = db.query(Faq).filter_by(published=True).order_by(Faq.sort_order).all()
    return [{"id": row.id, "question": row.question, "answer": row.answer} for row in rows]


@router.post("/corporate/leads")
def corporate_lead(body: LeadIn, request: Request, db: Session = Depends(get_db), _: None = Depends(mutate)):
    limit(request, "corporate", 8, 60)
    lead = CorporateLead(status="new", **body.model_dump())
    db.add(lead)
    db.commit()
    return {"id": lead.id, "status": lead.status}


@router.post("/contact")
def contact(body: ContactIn, request: Request, db: Session = Depends(get_db), _: None = Depends(mutate)):
    limit(request, "contact", 8, 60)
    row = ContactMessage(**body.model_dump())
    db.add(row)
    db.commit()
    return {"id": row.id}


@router.post("/newsletter")
def newsletter(body: NewsletterIn, request: Request, db: Session = Depends(get_db), _: None = Depends(mutate)):
    limit(request, "newsletter", 8, 60)
    email = body.email.lower()
    if not db.query(NewsletterSubscriber).filter_by(email=email).one_or_none():
        db.add(NewsletterSubscriber(email=email))
        db.commit()
    return {"ok": True}


@router.post("/analytics/events")
def track(body: EventIn, request: Request, db: Session = Depends(get_db)):
    limit(request, "analytics", 60, 60)
    allowed = {
        "page_view", "product_view", "add_to_cart", "remove_from_cart", "begin_checkout", "purchase",
        "wishlist", "search", "filter", "coupon_applied", "subscription", "build_box", "corporate_lead",
        "newsletter_signup", "recommendation_click",
    }
    if body.name not in allowed:
        raise HTTPException(status_code=400, detail="Unknown event.")
    db.add(AnalyticsEvent(name=body.name, payload=body.payload))
    db.commit()
    return {"ok": True}


@router.post("/pincode/check")
def pincode(body: PincodeIn, db: Session = Depends(get_db)):
    company = setting(db, "company")
    zones = company.get("serviceable_pincodes") or []
    if not zones:
        return {"serviceable": None, "message": "Delivery zones are not published yet, so this pincode cannot be confirmed."}
    ok = body.pincode in zones
    return {"serviceable": ok, "message": "We deliver to this pincode." if ok else "This pincode is outside the published delivery list."}


@router.post("/reviews")
def create_review(body: ReviewIn, request: Request, db: Session = Depends(get_db), user: User | None = Depends(optional_user), _: None = Depends(mutate)):
    limit(request, "reviews", 6, 60)
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in to review a product you have purchased.")
    product = db.get(Product, body.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    from app.models import Order, OrderItem

    purchased = (
        db.query(OrderItem)
        .join(Order)
        .filter(Order.user_id == user.id, Order.payment_status == "paid", OrderItem.product_id == product.id)
        .first()
    )
    if purchased is None:
        raise HTTPException(status_code=403, detail="Reviews are open after a paid order for this product.")
    row = Review(user_id=user.id, product_id=product.id, author_name=user.name, rating=body.rating, body=body.body, status="pending", verified_purchase=True)
    db.add(row)
    db.commit()
    return {"id": row.id, "status": "pending"}


@router.get("/sitemap.xml")
def sitemap(db: Session = Depends(get_db)):
    paths = ["/", "/protein-bars", "/protein-muesli", "/bundles", "/build-your-box", "/about", "/journal", "/corporate", "/contact", "/faq", "/shipping", "/returns", "/privacy", "/terms", "/cookies"]
    paths += [f"/products/{row.slug}" for row in db.query(Product).filter(Product.status != "archived").all()]
    paths += [f"/journal/{row.slug}" for row in db.query(BlogPost).filter_by(status="published").all()]
    body = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>", "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">"]
    for path in paths:
        body.append(f"<url><loc>{path}</loc></url>")
    body.append("</urlset>")
    return Response("\n".join(body), media_type="application/xml")
