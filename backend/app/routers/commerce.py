from __future__ import annotations

import hashlib
import hmac

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.database import get_db
from app.deps import current_user, load_cart, mutate, optional_user
from app.models import CartItem, Order, Payment, Product, Subscription, User
from app.schemas import CartItemIn, CartQtyIn, CheckoutIn, CouponIn, SubscriptionIn, TrackIn
from app.serialize import money, product_dict
from app.services import max_qty, place_order, quote_cart, renewal_date, selling_enabled, setting, suggest_products

router = APIRouter()


@router.get("/cart")
def get_cart(db: Session = Depends(get_db), cart=Depends(load_cart)):
    suggestions = [product_dict(db, row) for row in suggest_products(db, cart)]
    payload = quote_cart(db, cart)
    payload["suggestions"] = suggestions
    return payload


@router.post("/cart/items")
def add_item(body: CartItemIn, db: Session = Depends(get_db), cart=Depends(load_cart), _: None = Depends(mutate)):
    product = db.query(Product).filter(Product.id == body.product_id, Product.status != "archived").one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    if not product.purchasable:
        raise HTTPException(status_code=409, detail="This product is not for sale until its specification and price are verified.")
    limit = max_qty(db)
    if body.quantity > limit:
        raise HTTPException(status_code=400, detail=f"Maximum quantity per product is {limit}.")
    existing = next((item for item in cart.items if item.product_id == product.id and not item.saved_for_later), None)
    if existing:
        existing.quantity = min(limit, existing.quantity + body.quantity)
    else:
        db.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=body.quantity))
    db.commit()
    return get_cart(db, _reload(db, cart.id))


@router.patch("/cart/items/{item_id}")
def update_item(item_id: int, body: CartQtyIn, db: Session = Depends(get_db), cart=Depends(load_cart), _: None = Depends(mutate)):
    item = next((row for row in cart.items if row.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Cart item not found.")
    limit = max_qty(db)
    if body.quantity > limit:
        raise HTTPException(status_code=400, detail=f"Maximum quantity per product is {limit}.")
    item.quantity = body.quantity
    if body.saved_for_later is not None:
        item.saved_for_later = body.saved_for_later
    db.commit()
    return get_cart(db, _reload(db, cart.id))


@router.delete("/cart/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db), cart=Depends(load_cart), _: None = Depends(mutate)):
    item = next((row for row in cart.items if row.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Cart item not found.")
    db.delete(item)
    db.commit()
    return get_cart(db, _reload(db, cart.id))


@router.post("/cart/coupon")
def apply_coupon(body: CouponIn, db: Session = Depends(get_db), cart=Depends(load_cart), _: None = Depends(mutate)):
    from app.models import Coupon

    code = body.code.strip().upper()
    coupon = db.query(Coupon).filter_by(code=code).one_or_none()
    if coupon is None or not coupon.active:
        raise HTTPException(status_code=400, detail="That coupon is not valid.")
    cart.coupon_code = code
    db.commit()
    payload = get_cart(db, _reload(db, cart.id))
    if payload.get("coupon_note"):
        cart.coupon_code = None
        db.commit()
        raise HTTPException(status_code=400, detail=payload["coupon_note"])
    return payload


@router.delete("/cart/coupon")
def remove_coupon(db: Session = Depends(get_db), cart=Depends(load_cart), _: None = Depends(mutate)):
    cart.coupon_code = None
    db.commit()
    return get_cart(db, _reload(db, cart.id))


def _reload(db: Session, cart_id: int):
    from app.models import Cart

    return (
        db.query(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.product))
        .filter_by(id=cart_id)
        .one()
    )


@router.post("/orders/checkout")
def checkout(body: CheckoutIn, db: Session = Depends(get_db), cart=Depends(load_cart), user: User | None = Depends(optional_user), _: None = Depends(mutate)):
    cart = _reload(db, cart.id)
    order = place_order(db, cart, body.model_dump(), user.id if user else None)
    db.flush()
    settings = get_settings()
    amount = int(round(float(order.total_inr) * 100))
    try:
        response = httpx.post(
            "https://api.razorpay.com/v1/orders",
            json={"amount": amount, "currency": "INR", "receipt": order.number},
            auth=(settings.razorpay_key_id, settings.razorpay_key_secret),
            timeout=20,
        )
        response.raise_for_status()
        remote = response.json()
    except httpx.HTTPError:
        from app.services import release_reservation

        order.status = "cancelled"
        order.payment_status = "failed"
        release_reservation(db, order)
        db.commit()
        raise HTTPException(status_code=502, detail="The payment provider did not accept this order. Nothing was charged.")
    db.add(Payment(order_id=order.id, provider="razorpay", provider_order_id=remote.get("id"), status="created", amount_inr=order.total_inr, raw={"id": remote.get("id")}))
    db.commit()
    return {
        "order_number": order.number,
        "status": order.status,
        "payment_status": order.payment_status,
        "total_inr": money(order.total_inr),
        "razorpay_order_id": remote.get("id"),
        "razorpay_key_id": settings.razorpay_key_id,
        "items": [{"name": item.name, "quantity": item.quantity, "unit_price_inr": money(item.unit_price_inr)} for item in order.items],
    }


@router.post("/orders/track")
def track(body: TrackIn, db: Session = Depends(get_db)):
    order = db.query(Order).options(joinedload(Order.items)).filter_by(number=body.number.strip().upper(), phone=body.phone).one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="No order matches that number and mobile.")
    return _order_out(order)


@router.get("/orders/mine")
def my_orders(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(Order).options(joinedload(Order.items)).filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    return [_order_out(row) for row in rows]


def _order_out(order: Order) -> dict:
    return {
        "number": order.number,
        "status": order.status,
        "payment_status": order.payment_status,
        "total_inr": money(order.total_inr),
        "created_at": order.created_at.isoformat(),
        "items": [{"name": item.name, "sku": item.sku, "quantity": item.quantity, "unit_price_inr": money(item.unit_price_inr)} for item in order.items],
        "shipping": {"city": order.city, "state": order.state, "pincode": order.pincode},
    }


@router.post("/payments/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.razorpay_webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook secret is not configured.")
    raw = await request.body()
    signature = request.headers.get("x-razorpay-signature", "")
    expected = hmac.new(settings.razorpay_webhook_secret.encode(), raw, hashlib.sha256).hexdigest()
    if not signature or not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")
    import json

    event = json.loads(raw.decode() or "{}")
    entity = (event.get("payload") or {}).get("payment", {}).get("entity", {})
    provider_order_id = entity.get("order_id")
    if event.get("event") == "payment.captured" and provider_order_id:
        payment = db.query(Payment).filter_by(provider_order_id=provider_order_id).one_or_none()
        if payment:
            order = db.get(Order, payment.order_id)
            from app.services import mark_paid

            payment.status = "captured"
            payment.provider_payment_id = entity.get("id")
            if order and order.status != "cancelled":
                mark_paid(db, order, entity.get("id"))
                for item in order.items:
                    from app.models import Inventory

                    inventory = db.query(Inventory).filter_by(product_id=item.product_id).one_or_none()
                    if inventory:
                        inventory.reserved = max(0, inventory.reserved - item.quantity)
            db.commit()
    return {"ok": True}


@router.get("/subscriptions")
def list_subscriptions(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(Subscription).filter_by(user_id=user.id).order_by(Subscription.created_at.desc()).all()
    return [_sub_out(row) for row in rows]


@router.post("/subscriptions")
def create_subscription(body: SubscriptionIn, db: Session = Depends(get_db), user: User = Depends(current_user), _: None = Depends(mutate)):
    if not selling_enabled(db):
        raise HTTPException(status_code=409, detail="Subscriptions open once selling is turned on.")
    cadences = setting(db, "merchandising").get("subscription_cadence_days") or []
    if body.cadence_days not in cadences:
        raise HTTPException(status_code=400, detail="Choose one of the published cadences.")
    products = db.query(Product).filter(Product.id.in_(body.product_ids), Product.purchasable.is_(True)).all()
    if len(products) != len(set(body.product_ids)):
        raise HTTPException(status_code=400, detail="Every subscription item has to be a product that is actually on sale.")
    row = Subscription(
        user_id=user.id,
        cadence_days=body.cadence_days,
        status="active",
        items=[{"product_id": product.id, "name": product.name, "slug": product.slug} for product in products],
        next_renewal=renewal_date(body.cadence_days),
    )
    db.add(row)
    db.commit()
    return _sub_out(row)


@router.patch("/subscriptions/{sub_id}")
def update_subscription(sub_id: int, action: str, db: Session = Depends(get_db), user: User = Depends(current_user), _: None = Depends(mutate)):
    row = db.query(Subscription).filter_by(id=sub_id, user_id=user.id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Subscription not found.")
    if action == "pause" and row.status == "active":
        row.status = "paused"
    elif action == "resume" and row.status == "paused":
        row.status = "active"
        row.next_renewal = renewal_date(row.cadence_days)
    elif action == "skip" and row.status == "active":
        row.next_renewal = renewal_date(row.cadence_days)
    elif action == "cancel":
        row.status = "cancelled"
    else:
        raise HTTPException(status_code=400, detail="Unsupported subscription action.")
    db.commit()
    return _sub_out(row)


def _sub_out(row: Subscription) -> dict:
    return {"id": row.id, "cadence_days": row.cadence_days, "status": row.status, "items": row.items, "next_renewal": row.next_renewal}
