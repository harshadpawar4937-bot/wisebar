from __future__ import annotations

import secrets
from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.models import (
    AuditLog,
    Cart,
    CartItem,
    Coupon,
    Inventory,
    Order,
    OrderItem,
    Product,
    ProductVariant,
    Setting,
)
from app.serialize import missing_spec, money

ORDER_TRANSITIONS = {
    "new": {"confirmed", "cancelled"},
    "confirmed": {"processing", "cancelled"},
    "processing": {"packed", "cancelled"},
    "packed": {"shipped"},
    "shipped": {"delivered"},
    "delivered": {"refunded"},
    "cancelled": set(),
    "refunded": set(),
}


def setting(db: Session, key: str) -> dict:
    row = db.get(Setting, key)
    return dict(row.value) if row else {}


def audit(db: Session, email: str, action: str, entity: str, entity_id: str, detail: dict | None = None) -> None:
    db.add(AuditLog(actor_email=email, action=action, entity=entity, entity_id=str(entity_id), detail=detail or {}))


def selling_enabled(db: Session) -> bool:
    return bool(setting(db, "commerce").get("selling_enabled"))


def max_qty(db: Session) -> int:
    return int(setting(db, "commerce").get("max_qty_per_line") or 10)


def cart_by_token(db: Session, token: str | None) -> Cart:
    if token:
        cart = db.query(Cart).filter_by(token=token).one_or_none()
        if cart:
            return cart
    cart = Cart(token=secrets.token_urlsafe(24))
    db.add(cart)
    db.flush()
    return cart


def sync_variant(db: Session, product: Product) -> None:
    variant = db.query(ProductVariant).filter_by(product_id=product.id).one_or_none()
    if variant is None:
        variant = ProductVariant(product_id=product.id, sku=product.sku, label="Standard")
        db.add(variant)
    variant.sku = product.sku
    variant.price_inr = product.price_inr
    variant.mrp_inr = product.mrp_inr


def apply_purchasable(product: Product, inventory: Inventory | None, want: bool) -> None:
    if not want:
        product.purchasable = False
        product.spec_status = "pending_verification" if missing_spec(product, inventory) else "verified_unpublished"
        return
    missing = missing_spec(product, inventory)
    if missing:
        raise HTTPException(
            status_code=400,
            detail={"message": "A product can go on sale only with a complete verified specification and stock.", "missing": missing},
        )
    product.purchasable = True
    product.status = "active"
    product.spec_status = "verified"


def active_products(db: Session):
    return (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.variants), joinedload(Product.inventory))
        .filter(Product.status != "archived")
    )


def quote_cart(db: Session, cart: Cart) -> dict:
    commerce = setting(db, "commerce")
    threshold = commerce.get("free_shipping_threshold_inr")
    shipping_fee = commerce.get("shipping_fee_inr")
    lines = []
    subtotal = Decimal("0")
    priced = True
    for item in cart.items:
        if item.saved_for_later:
            continue
        product = item.product
        unit = product.price_inr
        line_total = None
        if unit is None or not product.purchasable:
            priced = False
        else:
            line_total = Decimal(str(unit)) * item.quantity
            subtotal += line_total
        lines.append(
            {
                "id": item.id,
                "product_id": product.id,
                "slug": product.slug,
                "name": product.name,
                "flavor": product.flavor,
                "flavor_family": product.flavor_family,
                "quantity": item.quantity,
                "saved_for_later": False,
                "purchasable": product.purchasable,
                "unit_price_inr": money(unit),
                "line_total_inr": money(line_total) if line_total is not None else None,
                "image_url": product.image_url,
            }
        )
    saved = [
        {
            "id": item.id,
            "product_id": item.product.id,
            "slug": item.product.slug,
            "name": item.product.name,
            "flavor": item.product.flavor,
            "flavor_family": item.product.flavor_family,
            "quantity": item.quantity,
            "saved_for_later": True,
        }
        for item in cart.items
        if item.saved_for_later
    ]
    discount = Decimal("0")
    coupon_note = None
    if cart.coupon_code:
        coupon = db.query(Coupon).filter_by(code=cart.coupon_code).one_or_none()
        if coupon is None or not coupon.active:
            coupon_note = "That coupon is not active."
        elif not priced:
            coupon_note = "Coupons apply once every item in the cart has a verified price."
        else:
            ok, reason, discount = coupon_discount(coupon, subtotal)
            coupon_note = None if ok else reason
            if not ok:
                discount = Decimal("0")
    shipping = None
    progress = None
    if threshold is None or shipping_fee is None:
        shipping_message = "A free-shipping threshold has not been set yet."
    elif not priced:
        shipping_message = "Shipping is calculated once prices are published."
    else:
        threshold_d = Decimal(str(threshold))
        if subtotal >= threshold_d:
            shipping = Decimal("0")
            shipping_message = "This order qualifies for free shipping."
            progress = 1
        else:
            shipping = Decimal(str(shipping_fee))
            remaining = threshold_d - subtotal
            shipping_message = f"Add ₹{remaining:.0f} more for free shipping."
            progress = float(subtotal / threshold_d) if threshold_d else 0
    total = None
    if priced and shipping is not None:
        total = subtotal - discount + shipping
    return {
        "id": cart.id,
        "items": lines,
        "saved": saved,
        "coupon_code": cart.coupon_code,
        "coupon_note": coupon_note,
        "priced": priced and bool(lines),
        "subtotal_inr": money(subtotal) if lines else None,
        "discount_inr": money(discount) if priced else None,
        "shipping_inr": money(shipping) if shipping is not None else None,
        "total_inr": money(total) if total is not None else None,
        "shipping_message": shipping_message,
        "shipping_progress": progress,
        "selling_enabled": selling_enabled(db),
    }


def coupon_discount(coupon: Coupon, subtotal: Decimal) -> tuple[bool, str, Decimal]:
    if coupon.expires_at and coupon.expires_at < date.today().isoformat():
        return False, "That coupon has expired.", Decimal("0")
    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
        return False, "That coupon has reached its usage limit.", Decimal("0")
    if coupon.min_subtotal is not None and subtotal < Decimal(str(coupon.min_subtotal)):
        return False, "The cart has not reached this coupon's minimum.", Decimal("0")
    if coupon.type == "percent":
        discount = (subtotal * Decimal(str(coupon.value)) / Decimal("100")).quantize(Decimal("0.01"))
    elif coupon.type == "fixed":
        discount = min(Decimal(str(coupon.value)), subtotal)
    else:
        return False, "This coupon is misconfigured.", Decimal("0")
    return True, "", discount


def suggest_products(db: Session, cart: Cart, limit: int = 3) -> list[Product]:
    ids = {item.product_id for item in cart.items}
    categories = {item.product.category_id for item in cart.items if not item.saved_for_later}
    query = active_products(db).filter(~Product.id.in_(ids or {0}))
    if categories:
        query = query.filter(Product.category_id.in_(categories))
    return query.order_by(Product.sort_order).limit(limit).all()


def place_order(db: Session, cart: Cart, payload: dict, user_id: int | None) -> Order:
    if not selling_enabled(db):
        raise HTTPException(status_code=409, detail="Checkout opens once selling is turned on and products have verified prices.")
    if not get_settings().payments_configured:
        raise HTTPException(status_code=409, detail="No payment gateway is configured. Add Razorpay credentials before taking payment.")
    active = [item for item in cart.items if not item.saved_for_later]
    if not active:
        raise HTTPException(status_code=400, detail="Your cart is empty.")
    subtotal = Decimal("0")
    prepared = []
    for item in active:
        product = item.product
        inventory = product.inventory
        if not product.purchasable or product.price_inr is None:
            raise HTTPException(status_code=409, detail=f"{product.name} is not for sale yet.")
        if item.quantity < 1 or item.quantity > max_qty(db):
            raise HTTPException(status_code=400, detail="Quantity is outside the allowed range.")
        available = (inventory.available if inventory else 0) - (inventory.reserved if inventory else 0)
        if item.quantity > available:
            raise HTTPException(status_code=409, detail=f"Not enough stock for {product.name}.")
        unit = Decimal(str(product.price_inr))
        subtotal += unit * item.quantity
        prepared.append((item, product, unit))
    discount = Decimal("0")
    if cart.coupon_code:
        coupon = db.query(Coupon).filter_by(code=cart.coupon_code, active=True).one_or_none()
        if coupon is None:
            raise HTTPException(status_code=400, detail="That coupon is not valid.")
        ok, reason, discount = coupon_discount(coupon, subtotal)
        if not ok:
            raise HTTPException(status_code=400, detail=reason)
    commerce = setting(db, "commerce")
    threshold = commerce.get("free_shipping_threshold_inr")
    fee = commerce.get("shipping_fee_inr")
    if threshold is None or fee is None:
        raise HTTPException(status_code=409, detail="Shipping rules are not configured yet.")
    shipping = Decimal("0") if subtotal >= Decimal(str(threshold)) else Decimal(str(fee))
    total = subtotal - discount + shipping
    order = Order(
        number="WB-" + secrets.token_hex(4).upper(),
        user_id=user_id,
        email=payload["email"],
        name=payload["name"],
        phone=payload["phone"],
        address_line=payload["address"],
        city=payload["city"],
        state=payload["state"],
        pincode=payload["pincode"],
        status="new",
        payment_status="pending",
        subtotal_inr=subtotal,
        discount_inr=discount,
        shipping_inr=shipping,
        total_inr=total,
        coupon_code=cart.coupon_code,
    )
    db.add(order)
    db.flush()
    for item, product, unit in prepared:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                name=product.name,
                sku=product.sku,
                quantity=item.quantity,
                unit_price_inr=unit,
            )
        )
        inventory = product.inventory
        inventory.available -= item.quantity
        inventory.reserved += item.quantity
    for item in list(active):
        db.delete(item)
    cart.coupon_code = None
    return order


def move_order(order: Order, new_status: str) -> None:
    allowed = ORDER_TRANSITIONS.get(order.status, set())
    if new_status not in allowed:
        raise HTTPException(status_code=400, detail=f"Cannot move an order from {order.status} to {new_status}.")
    if new_status in {"shipped", "delivered"} and order.payment_status != "paid":
        raise HTTPException(status_code=400, detail="Ship and delivery require a paid order.")
    if new_status == "refunded" and order.payment_status not in {"paid", "refunded"}:
        raise HTTPException(status_code=400, detail="Only a paid order can be refunded.")
    order.status = new_status
    if new_status == "refunded":
        order.payment_status = "refunded"
    if new_status == "cancelled":
        order.payment_status = "failed" if order.payment_status == "pending" else order.payment_status


def release_reservation(db: Session, order: Order) -> None:
    if order.stock_settled or order.status not in {"cancelled", "refunded"}:
        return
    for item in order.items:
        inventory = db.query(Inventory).filter_by(product_id=item.product_id).one_or_none()
        if inventory is None:
            continue
        inventory.reserved = max(0, inventory.reserved - item.quantity)
        inventory.available += item.quantity
    order.stock_settled = True


def mark_paid(db: Session, order: Order, payment_id: str | None = None) -> None:
    if order.payment_status == "paid":
        return
    order.payment_status = "paid"
    order.status = "confirmed" if order.status == "new" else order.status
    if order.coupon_code:
        coupon = db.query(Coupon).filter_by(code=order.coupon_code).one_or_none()
        if coupon:
            coupon.used_count += 1
    if payment_id:
        order.payment_method = order.payment_method or "razorpay"


def recommend(db: Session, answers: dict) -> dict:
    merch = setting(db, "merchandising")
    occasion_map = merch.get("occasion_map", {})
    products = active_products(db).all()
    notes = []
    occasion = answers.get("occasion")
    taste = answers.get("taste")
    protein = answers.get("protein")
    budget = answers.get("budget")
    chosen = products
    if occasion and occasion in occasion_map:
        slugs = set(occasion_map[occasion].get("categories", []))
        chosen = [product for product in chosen if product.category and product.category.slug in slugs]
    if taste and taste != "any":
        chosen = [product for product in chosen if product.flavor_family == taste]
    if protein and protein != "any":
        if any(product.protein_g is None for product in chosen) or not chosen:
            notes.append("Protein filters apply once verified protein values are published. Showing matches by occasion and taste.")
        else:
            low, high = _range(protein)
            chosen = [product for product in chosen if low <= float(product.protein_g) <= high]
    if budget and budget != "any":
        if any(product.price_inr is None for product in chosen) or not chosen:
            notes.append("Budget filters apply once prices are published. Showing matches by occasion and taste.")
        else:
            low, high = _range(budget)
            chosen = [product for product in chosen if low <= float(product.price_inr) <= high]
    if not chosen:
        notes.append("Nothing in the current catalogue matches those choices. Here is what is listed today.")
        chosen = products
    return {"products": chosen, "notes": notes}


def _range(token: str) -> tuple[float, float]:
    if token.endswith("+"):
        return float(token[:-1]), 10**9
    low, high = token.split("-")
    return float(low), float(high)


def renewal_date(cadence_days: int) -> str:
    return (date.today() + timedelta(days=cadence_days)).isoformat()
