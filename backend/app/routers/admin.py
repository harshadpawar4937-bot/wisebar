from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import admin_user, mutate
from app.models import (
    AnalyticsEvent,
    AuditLog,
    BlogPost,
    Bundle,
    BundleItem,
    Category,
    ContactMessage,
    CorporateLead,
    Coupon,
    Faq,
    Inventory,
    NewsletterSubscriber,
    Order,
    Page,
    Product,
    ProductVariant,
    Review,
    Subscription,
    RewardRule,
    Setting,
    User,
)
from app.schemas import BundleIn, CouponCreate, FaqIn, OrderStatusIn, PageIn, PostIn, ProductIn, SettingIn
from app.serialize import money, product_dict
from app.services import apply_purchasable, audit, move_order, release_reservation, sync_variant

router = APIRouter(prefix="/admin")


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    paid = db.query(Order).filter(Order.payment_status == "paid")
    revenue = paid.with_entities(func.coalesce(func.sum(Order.total_inr), 0)).scalar()
    order_count = paid.count()
    customers = db.query(User).filter_by(role="customer").count()
    aov = None if order_count == 0 else round(float(revenue) / order_count, 2)
    repeat = None
    if customers:
        buyers = db.query(Order.user_id).filter(Order.payment_status == "paid", Order.user_id.isnot(None)).group_by(Order.user_id).having(func.count(Order.id) > 1).count()
        paying = db.query(Order.user_id).filter(Order.payment_status == "paid", Order.user_id.isnot(None)).distinct().count()
        repeat = round(buyers / paying, 3) if paying else None
    return {
        "revenue_inr": money(revenue) if order_count else None,
        "orders": order_count,
        "customers": customers,
        "products": db.query(Product).filter(Product.status != "archived").count(),
        "subscriptions": db.query(Subscription).count(),
        "aov_inr": aov,
        "repeat_purchase_rate": repeat,
        "open_leads": db.query(CorporateLead).filter_by(status="new").count(),
        "pending_reviews": db.query(Review).filter_by(status="pending").count(),
        "low_stock": db.query(Inventory).filter(Inventory.available <= Inventory.low_stock_threshold).count(),
    }


@router.get("/products")
def list_products(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    rows = db.query(Product).options(joinedload(Product.category), joinedload(Product.variants), joinedload(Product.inventory)).order_by(Product.sort_order).all()
    return [product_dict(db, row) for row in rows]


@router.post("/products")
def create_product(body: ProductIn, db: Session = Depends(get_db), admin: User = Depends(admin_user), _: None = Depends(mutate)):
    _save_product(db, Product(), body)
    db.flush()
    audit(db, admin.email, "create", "product", str(body.sku), {})
    db.commit()
    return {"ok": True}


@router.patch("/products/{product_id}")
def update_product(product_id: int, body: ProductIn, db: Session = Depends(get_db), admin: User = Depends(admin_user), _: None = Depends(mutate)):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    _save_product(db, product, body)
    audit(db, admin.email, "update", "product", str(product_id), {"purchasable": body.purchasable})
    db.commit()
    return product_dict(db, product)


@router.post("/products/{product_id}/duplicate")
def duplicate_product(product_id: int, db: Session = Depends(get_db), admin: User = Depends(admin_user), _: None = Depends(mutate)):
    source = db.get(Product, product_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    copy = Product()
    for column in Product.__table__.columns:
        if column.name in {"id", "created_at", "updated_at"}:
            continue
        setattr(copy, column.name, getattr(source, column.name))
    suffix = secrets.token_hex(2)
    copy.sku = f"{source.sku}-{suffix}"
    copy.slug = f"{source.slug}-{suffix}"
    copy.purchasable = False
    copy.status = "draft"
    db.add(copy)
    db.flush()
    db.add(ProductVariant(product_id=copy.id, sku=copy.sku, label="Standard", price_inr=copy.price_inr, mrp_inr=copy.mrp_inr))
    db.add(Inventory(product_id=copy.id, available=0, reserved=0, low_stock_threshold=10))
    audit(db, admin.email, "duplicate", "product", str(copy.id), {"from": product_id})
    db.commit()
    return {"id": copy.id, "slug": copy.slug}


@router.delete("/products/{product_id}")
def archive_product(product_id: int, db: Session = Depends(get_db), admin: User = Depends(admin_user), _: None = Depends(mutate)):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    product.status = "archived"
    product.purchasable = False
    audit(db, admin.email, "archive", "product", str(product_id), {})
    db.commit()
    return {"ok": True}


def _save_product(db: Session, product: Product, body: ProductIn) -> None:
    category = db.query(Category).filter_by(slug=body.category_slug).one_or_none()
    if category is None:
        raise HTTPException(status_code=400, detail="Unknown category.")
    data = body.model_dump(exclude={"category_slug", "available", "purchasable"})
    for key, value in data.items():
        setattr(product, key, value)
    product.category_id = category.id
    if product.id is None:
        db.add(product)
        db.flush()
        db.add(Inventory(product_id=product.id, available=body.available, reserved=0, low_stock_threshold=10))
    inventory = db.query(Inventory).filter_by(product_id=product.id).one_or_none()
    if inventory is None:
        inventory = Inventory(product_id=product.id, available=body.available, reserved=0, low_stock_threshold=10)
        db.add(inventory)
    else:
        inventory.available = body.available
    apply_purchasable(product, inventory, body.purchasable)
    sync_variant(db, product)


@router.get("/orders")
def orders(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    rows = db.query(Order).options(joinedload(Order.items)).order_by(Order.created_at.desc()).limit(100).all()
    return [
        {
            "number": row.number,
            "status": row.status,
            "payment_status": row.payment_status,
            "total_inr": money(row.total_inr),
            "name": row.name,
            "email": row.email,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


@router.patch("/orders/{number}")
def update_order(number: str, body: OrderStatusIn, db: Session = Depends(get_db), admin: User = Depends(admin_user), _: None = Depends(mutate)):
    order = db.query(Order).options(joinedload(Order.items)).filter_by(number=number).one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found.")
    previous = order.status
    move_order(order, body.status)
    if body.status == "shipped":
        for item in order.items:
            inventory = db.query(Inventory).filter_by(product_id=item.product_id).one_or_none()
            if inventory:
                inventory.reserved = max(0, inventory.reserved - item.quantity)
    if body.status in {"cancelled", "refunded"}:
        release_reservation(db, order)
    audit(db, admin.email, "status", "order", number, {"from": previous, "to": body.status})
    db.commit()
    return {"number": order.number, "status": order.status, "payment_status": order.payment_status}


@router.get("/coupons")
def coupons(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    return [
        {"id": row.id, "code": row.code, "type": row.type, "value": float(row.value), "active": row.active, "used_count": row.used_count, "expires_at": row.expires_at}
        for row in db.query(Coupon).all()
    ]


@router.post("/coupons")
def create_coupon(body: CouponCreate, db: Session = Depends(get_db), admin: User = Depends(admin_user), _: None = Depends(mutate)):
    if body.type not in {"percent", "fixed"}:
        raise HTTPException(status_code=400, detail="Coupon type must be percent or fixed.")
    row = Coupon(code=body.code.strip().upper(), type=body.type, value=body.value, active=body.active, expires_at=body.expires_at, min_subtotal=body.min_subtotal, usage_limit=body.usage_limit)
    db.add(row)
    audit(db, admin.email, "create", "coupon", row.code, {})
    db.commit()
    return {"id": row.id}


@router.get("/leads")
def leads(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    rows = db.query(CorporateLead).order_by(CorporateLead.created_at.desc()).all()
    return [
        {"id": row.id, "company": row.company, "name": row.name, "email": row.email, "phone": row.phone, "requirement": row.requirement, "expected_quantity": row.expected_quantity, "status": row.status, "message": row.message, "employee_count": row.employee_count}
        for row in rows
    ]


@router.patch("/leads/{lead_id}")
def update_lead(lead_id: int, status: str, db: Session = Depends(get_db), admin: User = Depends(admin_user), _: None = Depends(mutate)):
    row = db.get(CorporateLead, lead_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Lead not found.")
    row.status = status
    audit(db, admin.email, "status", "lead", str(lead_id), {"status": status})
    db.commit()
    return {"ok": True}


@router.get("/reviews")
def reviews(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    rows = db.query(Review).order_by(Review.created_at.desc()).all()
    return [{"id": row.id, "author_name": row.author_name, "rating": row.rating, "body": row.body, "status": row.status, "product_id": row.product_id, "verified_purchase": row.verified_purchase} for row in rows]


@router.patch("/reviews/{review_id}")
def moderate(review_id: int, status: str, db: Session = Depends(get_db), admin: User = Depends(admin_user), _: None = Depends(mutate)):
    if status not in {"approved", "rejected", "pending"}:
        raise HTTPException(status_code=400, detail="Unknown review status.")
    row = db.get(Review, review_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Review not found.")
    row.status = status
    audit(db, admin.email, "moderate", "review", str(review_id), {"status": status})
    db.commit()
    return {"ok": True}


@router.get("/posts")
def posts(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    rows = db.query(BlogPost).order_by(BlogPost.id.desc()).all()
    return [{"id": row.id, "slug": row.slug, "title": row.title, "status": row.status, "category": row.category, "body": row.body, "excerpt": row.excerpt, "published_at": row.published_at, "seo_title": row.seo_title, "seo_description": row.seo_description} for row in rows]


@router.post("/posts")
def create_post(body: PostIn, db: Session = Depends(get_db), admin: User = Depends(admin_user), _: None = Depends(mutate)):
    row = BlogPost(**body.model_dump(), author="WISEBAR Journal")
    db.add(row)
    audit(db, admin.email, "create", "post", body.slug, {})
    db.commit()
    return {"id": row.id}


@router.patch("/posts/{post_id}")
def update_post(post_id: int, body: PostIn, db: Session = Depends(get_db), admin: User = Depends(admin_user), _: None = Depends(mutate)):
    row = db.get(BlogPost, post_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Article not found.")
    for key, value in body.model_dump().items():
        setattr(row, key, value)
    audit(db, admin.email, "update", "post", str(post_id), {})
    db.commit()
    return {"ok": True}


@router.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db), admin: User = Depends(admin_user), _: None = Depends(mutate)):
    row = db.get(BlogPost, post_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Article not found.")
    db.delete(row)
    audit(db, admin.email, "delete", "post", str(post_id), {})
    db.commit()
    return {"ok": True}


@router.get("/faqs")
def admin_faqs(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    return [{"id": row.id, "question": row.question, "answer": row.answer, "sort_order": row.sort_order, "published": row.published} for row in db.query(Faq).order_by(Faq.sort_order).all()]


@router.post("/faqs")
def create_faq(body: FaqIn, db: Session = Depends(get_db), admin: User = Depends(admin_user), _: None = Depends(mutate)):
    row = Faq(**body.model_dump())
    db.add(row)
    audit(db, admin.email, "create", "faq", "", {})
    db.commit()
    return {"id": row.id}


@router.patch("/faqs/{faq_id}")
def update_faq(faq_id: int, body: FaqIn, db: Session = Depends(get_db), admin: User = Depends(admin_user), _: None = Depends(mutate)):
    row = db.get(Faq, faq_id)
    if row is None:
        raise HTTPException(status_code=404, detail="FAQ not found.")
    for key, value in body.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return {"ok": True}


@router.get("/pages")
def pages(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    return [{"slug": row.slug, "title": row.title, "body": row.body, "notice": row.notice} for row in db.query(Page).all()]


@router.patch("/pages/{slug}")
def update_page(slug: str, body: PageIn, db: Session = Depends(get_db), admin: User = Depends(admin_user), _: None = Depends(mutate)):
    row = db.query(Page).filter_by(slug=slug).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Page not found.")
    for key, value in body.model_dump().items():
        setattr(row, key, value)
    audit(db, admin.email, "update", "page", slug, {})
    db.commit()
    return {"ok": True}


@router.get("/settings/{key}")
def get_setting(key: str, db: Session = Depends(get_db), _: User = Depends(admin_user)):
    row = db.get(Setting, key)
    if row is None:
        raise HTTPException(status_code=404, detail="Setting not found.")
    return {"key": key, "value": row.value}


@router.put("/settings/{key}")
def put_setting(key: str, body: SettingIn, db: Session = Depends(get_db), admin: User = Depends(admin_user), _: None = Depends(mutate)):
    if key not in {"home", "commerce", "merchandising", "company", "story"}:
        raise HTTPException(status_code=400, detail="Unknown settings document.")
    row = db.get(Setting, key)
    if row is None:
        row = Setting(key=key, value=body.value)
        db.add(row)
    else:
        row.value = body.value
    audit(db, admin.email, "update", "setting", key, {})
    db.commit()
    return {"ok": True}


@router.get("/bundles")
def bundles(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    rows = db.query(Bundle).options(joinedload(Bundle.items)).all()
    return [{"id": row.id, "slug": row.slug, "name": row.name, "description": row.description, "price_inr": None if row.price_inr is None else float(row.price_inr), "product_ids": [item.product_id for item in row.items], "active": row.active} for row in rows]


@router.post("/bundles")
def create_bundle(body: BundleIn, db: Session = Depends(get_db), admin: User = Depends(admin_user), _: None = Depends(mutate)):
    row = Bundle(slug=body.slug, name=body.name, description=body.description, price_inr=body.price_inr, active=body.active)
    db.add(row)
    db.flush()
    for product_id in body.product_ids:
        db.add(BundleItem(bundle_id=row.id, product_id=product_id, quantity=1))
    audit(db, admin.email, "create", "bundle", body.slug, {})
    db.commit()
    return {"id": row.id}


@router.get("/messages")
def messages(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    return [{"id": row.id, "name": row.name, "email": row.email, "topic": row.topic, "message": row.message} for row in db.query(ContactMessage).order_by(ContactMessage.created_at.desc()).limit(100).all()]


@router.get("/subscribers")
def subscribers(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    return [{"email": row.email, "created_at": row.created_at.isoformat()} for row in db.query(NewsletterSubscriber).all()]


@router.get("/audit")
def audit_log(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(100).all()
    return [{"actor": row.actor_email, "action": row.action, "entity": row.entity, "entity_id": row.entity_id, "created_at": row.created_at.isoformat()} for row in rows]


@router.get("/analytics")
def analytics(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    rows = db.query(AnalyticsEvent.name, func.count(AnalyticsEvent.id)).group_by(AnalyticsEvent.name).all()
    return {"events": [{"name": name, "count": count} for name, count in rows]}


@router.patch("/rewards/{event}")
def update_reward(event: str, points: int | None = None, active: bool = False, db: Session = Depends(get_db), admin: User = Depends(admin_user), _: None = Depends(mutate)):
    row = db.query(RewardRule).filter_by(event=event).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Reward rule not found.")
    row.points = points
    row.active = active
    audit(db, admin.email, "update", "reward", event, {"points": points, "active": active})
    db.commit()
    return {"ok": True}
