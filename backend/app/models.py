from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def now() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="customer")
    referral_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    referred_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    points_balance: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Address(Base):
    __tablename__ = "addresses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    phone: Mapped[str] = mapped_column(String(20))
    line1: Mapped[str] = mapped_column(String(240))
    line2: Mapped[Optional[str]] = mapped_column(String(240), nullable=True)
    city: Mapped[str] = mapped_column(String(120))
    state: Mapped[str] = mapped_column(String(120))
    pincode: Mapped[str] = mapped_column(String(6))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    tagline: Mapped[str] = mapped_column(String(240))
    description: Mapped[str] = mapped_column(Text)
    products: Mapped[list["Product"]] = relationship(back_populates="category")


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    flavor: Mapped[str] = mapped_column(String(120))
    flavor_family: Mapped[str] = mapped_column(String(40))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    purchasable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    price_inr: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    mrp_inr: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    pack_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    net_quantity: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    serving_size: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    ingredients: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    allergens: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    storage: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fssai_license: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    customer_care: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    protein_g: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    calories_kcal: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    carbs_g: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    sugar_g: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    fat_g: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    fibre_g: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    occasions: Mapped[list] = mapped_column(JSON, default=list)
    dietary_labels: Mapped[list] = mapped_column(JSON, default=list)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    lab_report_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    seo_title: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    seo_description: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    spec_status: Mapped[str] = mapped_column(String(40), default="pending_verification")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)
    category: Mapped[Category] = relationship(back_populates="products")
    variants: Mapped[list["ProductVariant"]] = relationship(back_populates="product")
    inventory: Mapped[Optional["Inventory"]] = relationship(back_populates="product", uselist=False)


class ProductVariant(Base):
    __tablename__ = "product_variants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True)
    label: Mapped[str] = mapped_column(String(80), default="Standard")
    price_inr: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    mrp_inr: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    product: Mapped[Product] = relationship(back_populates="variants")


class Ingredient(Base):
    """Structured ingredient rows. Empty until a formulation is published."""

    __tablename__ = "ingredients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Allergen(Base):
    __tablename__ = "allergens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))


class Inventory(Base):
    __tablename__ = "inventory"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), unique=True)
    available: Mapped[int] = mapped_column(Integer, default=0)
    reserved: Mapped[int] = mapped_column(Integer, default=0)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=10)
    product: Mapped[Product] = relationship(back_populates="inventory")


class Batch(Base):
    __tablename__ = "batches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    batch_number: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    manufacturing_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    expiry_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)


class Cart(Base):
    __tablename__ = "carts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    coupon_code: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)
    items: Mapped[list["CartItem"]] = relationship(back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    saved_for_later: Mapped[bool] = mapped_column(Boolean, default=False)
    cart: Mapped[Cart] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    email: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(160))
    phone: Mapped[str] = mapped_column(String(20))
    address_line: Mapped[str] = mapped_column(String(400))
    city: Mapped[str] = mapped_column(String(120))
    state: Mapped[str] = mapped_column(String(120))
    pincode: Mapped[str] = mapped_column(String(6))
    status: Mapped[str] = mapped_column(String(32), default="new")
    payment_status: Mapped[str] = mapped_column(String(32), default="unpaid")
    payment_method: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    subtotal_inr: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    discount_inr: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    shipping_inr: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total_inr: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    coupon_code: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    stock_settled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    name: Mapped[str] = mapped_column(String(200))
    sku: Mapped[str] = mapped_column(String(64))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price_inr: Mapped[float] = mapped_column(Numeric(10, 2))
    order: Mapped[Order] = relationship(back_populates="items")


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    provider: Mapped[str] = mapped_column(String(40), default="razorpay")
    provider_order_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    provider_payment_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="created")
    amount_inr: Mapped[float] = mapped_column(Numeric(10, 2))
    raw: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    cadence_days: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="active")
    items: Mapped[list] = mapped_column(JSON, default=list)
    next_renewal: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Coupon(Base):
    __tablename__ = "coupons"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    type: Mapped[str] = mapped_column(String(20))
    value: Mapped[float] = mapped_column(Numeric(10, 2))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    min_subtotal: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, default=0)


class Bundle(Base):
    __tablename__ = "bundles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    price_inr: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    items: Mapped[list["BundleItem"]] = relationship(back_populates="bundle", cascade="all, delete-orphan")


class BundleItem(Base):
    __tablename__ = "bundle_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bundle_id: Mapped[int] = mapped_column(ForeignKey("bundles.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    bundle: Mapped[Bundle] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()


class Wishlist(Base):
    __tablename__ = "wishlists"
    __table_args__ = (UniqueConstraint("user_id", "product_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    author_name: Mapped[str] = mapped_column(String(160))
    rating: Mapped[int] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class BlogPost(Base):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(220))
    excerpt: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(32), default="draft")
    published_at: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    seo_title: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    seo_description: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    og_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    canonical_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    author: Mapped[str] = mapped_column(String(120), default="WISEBAR Journal")


class Page(Base):
    __tablename__ = "pages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    notice: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    seo_title: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    seo_description: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)


class Faq(Base):
    __tablename__ = "faqs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question: Mapped[str] = mapped_column(String(300))
    answer: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    published: Mapped[bool] = mapped_column(Boolean, default=True)


class CorporateLead(Base):
    __tablename__ = "corporate_leads"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company: Mapped[str] = mapped_column(String(200))
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(20))
    employee_count: Mapped[str] = mapped_column(String(40))
    requirement: Mapped[str] = mapped_column(String(80))
    expected_quantity: Mapped[str] = mapped_column(String(80))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class ContactMessage(Base):
    __tablename__ = "contact_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    topic: Mapped[str] = mapped_column(String(80))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Referral(Base):
    __tablename__ = "referrals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    referrer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    referred_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    code: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="invited")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class RewardRule(Base):
    __tablename__ = "reward_rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event: Mapped[str] = mapped_column(String(40), unique=True)
    points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str] = mapped_column(Text, default="")


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_email: Mapped[str] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(80))
    entity: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str] = mapped_column(String(64), default="")
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)


class PasswordReset(Base):
    __tablename__ = "password_resets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(128))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
