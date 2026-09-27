from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Inventory, Product, Review


def money(value) -> str | None:
    if value is None:
        return None
    return f"{Decimal(value):.2f}"


def num(value) -> float | None:
    if value is None:
        return None
    return float(value)


def review_stats(db: Session, product_id: int) -> tuple[float | None, int]:
    count, avg = db.query(func.count(Review.id), func.avg(Review.rating)).filter(
        Review.product_id == product_id, Review.status == "approved"
    ).one()
    if not count:
        return None, 0
    return round(float(avg), 2), int(count)


def product_dict(db: Session, product: Product) -> dict:
    rating, count = review_stats(db, product.id)
    inventory = product.inventory or db.query(Inventory).filter_by(product_id=product.id).one_or_none()
    nutrition_ready = all(
        getattr(product, field) is not None
        for field in ("protein_g", "calories_kcal", "carbs_g", "sugar_g", "fat_g", "fibre_g")
    )
    return {
        "id": product.id,
        "sku": product.sku,
        "slug": product.slug,
        "name": product.name,
        "flavor": product.flavor,
        "flavor_family": product.flavor_family,
        "category_slug": product.category.slug if product.category else None,
        "category_name": product.category.name if product.category else None,
        "description": product.description,
        "status": product.status,
        "purchasable": product.purchasable,
        "is_featured": product.is_featured,
        "price_inr": money(product.price_inr),
        "mrp_inr": money(product.mrp_inr),
        "pack_size": product.pack_size,
        "net_quantity": product.net_quantity,
        "serving_size": product.serving_size,
        "ingredients": product.ingredients,
        "allergens": product.allergens,
        "storage": product.storage,
        "fssai_license": product.fssai_license,
        "manufacturer": product.manufacturer,
        "customer_care": product.customer_care,
        "nutrition": {
            "protein_g": num(product.protein_g),
            "calories_kcal": num(product.calories_kcal),
            "carbs_g": num(product.carbs_g),
            "sugar_g": num(product.sugar_g),
            "fat_g": num(product.fat_g),
            "fibre_g": num(product.fibre_g),
            "status": "verified" if nutrition_ready else "pending_verification",
        },
        "occasions": product.occasions or [],
        "dietary_labels": product.dietary_labels or [],
        "image_url": product.image_url,
        "lab_report_url": product.lab_report_url,
        "seo_title": product.seo_title,
        "seo_description": product.seo_description,
        "spec_status": product.spec_status,
        "sort_order": product.sort_order,
        "rating_avg": rating,
        "review_count": count,
        "inventory": {
            "available": inventory.available if inventory else 0,
            "reserved": inventory.reserved if inventory else 0,
            "low_stock_threshold": inventory.low_stock_threshold if inventory else 0,
        },
        "variants": [
            {
                "id": variant.id,
                "sku": variant.sku,
                "label": variant.label,
                "price_inr": money(variant.price_inr),
                "mrp_inr": money(variant.mrp_inr),
            }
            for variant in product.variants
        ],
    }


SPEC_FIELDS = (
    "price_inr",
    "mrp_inr",
    "serving_size",
    "net_quantity",
    "ingredients",
    "allergens",
    "storage",
    "fssai_license",
    "manufacturer",
    "customer_care",
    "protein_g",
    "calories_kcal",
    "carbs_g",
    "sugar_g",
    "fat_g",
    "fibre_g",
)


def missing_spec(product: Product, inventory: Inventory | None) -> list[str]:
    missing = [field for field in SPEC_FIELDS if getattr(product, field) in (None, "")]
    if inventory is None or inventory.available <= 0:
        missing.append("inventory.available")
    return missing
