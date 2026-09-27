from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = None
    referral_code: str | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ProfileIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    phone: str | None = None


class AddressIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    phone: str = Field(min_length=10, max_length=20)
    line1: str = Field(min_length=4, max_length=240)
    line2: str | None = None
    city: str = Field(min_length=2, max_length=120)
    state: str = Field(min_length=2, max_length=120)
    pincode: str = Field(pattern=r"^\d{6}$")
    is_default: bool = False


class CheckoutIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    phone: str = Field(pattern=r"^[6-9]\d{9}$")
    email: EmailStr
    address: str = Field(min_length=4, max_length=400)
    city: str = Field(min_length=2, max_length=120)
    state: str = Field(min_length=2, max_length=120)
    pincode: str = Field(pattern=r"^\d{6}$")


class CartItemIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=50)


class CartQtyIn(BaseModel):
    quantity: int = Field(ge=1, le=50)
    saved_for_later: bool | None = None


class CouponIn(BaseModel):
    code: str = Field(min_length=2, max_length=40)


class QuizIn(BaseModel):
    occasion: str | None = None
    taste: str | None = None
    protein: str | None = None
    budget: str | None = None


class LeadIn(BaseModel):
    company: str = Field(min_length=2, max_length=200)
    name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    phone: str = Field(pattern=r"^[6-9]\d{9}$")
    employee_count: str = Field(min_length=1, max_length=40)
    requirement: str = Field(min_length=2, max_length=80)
    expected_quantity: str = Field(min_length=1, max_length=80)
    message: str = Field(min_length=4, max_length=2000)


class ContactIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    phone: str | None = None
    topic: str = Field(min_length=2, max_length=80)
    message: str = Field(min_length=4, max_length=2000)


class NewsletterIn(BaseModel):
    email: EmailStr


class TrackIn(BaseModel):
    number: str = Field(min_length=4, max_length=24)
    phone: str = Field(pattern=r"^[6-9]\d{9}$")


class PincodeIn(BaseModel):
    pincode: str = Field(pattern=r"^\d{6}$")


class ReviewIn(BaseModel):
    product_id: int
    rating: int = Field(ge=1, le=5)
    body: str = Field(min_length=8, max_length=2000)


class SubscriptionIn(BaseModel):
    cadence_days: int
    product_ids: list[int] = Field(min_length=1, max_length=12)


class EventIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    payload: dict = Field(default_factory=dict)


class ResetRequestIn(BaseModel):
    email: EmailStr


class ResetConfirmIn(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    password: str = Field(min_length=8, max_length=128)


class OrderStatusIn(BaseModel):
    status: str


class ProductIn(BaseModel):
    sku: str = Field(min_length=3, max_length=64)
    slug: str = Field(min_length=3, max_length=160)
    name: str = Field(min_length=2, max_length=200)
    flavor: str = Field(min_length=2, max_length=120)
    flavor_family: str = Field(min_length=2, max_length=40)
    category_slug: str
    description: str = Field(min_length=8, max_length=4000)
    status: str = "draft"
    purchasable: bool = False
    is_featured: bool = False
    sort_order: int = 0
    price_inr: float | None = None
    mrp_inr: float | None = None
    pack_size: int | None = None
    net_quantity: str | None = None
    serving_size: str | None = None
    ingredients: str | None = None
    allergens: str | None = None
    storage: str | None = None
    fssai_license: str | None = None
    manufacturer: str | None = None
    customer_care: str | None = None
    protein_g: float | None = None
    calories_kcal: float | None = None
    carbs_g: float | None = None
    sugar_g: float | None = None
    fat_g: float | None = None
    fibre_g: float | None = None
    occasions: list[str] = Field(default_factory=list)
    dietary_labels: list[str] = Field(default_factory=list)
    image_url: str | None = None
    lab_report_url: str | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    available: int = 0


class PostIn(BaseModel):
    slug: str = Field(min_length=3, max_length=180)
    title: str = Field(min_length=3, max_length=220)
    excerpt: str = Field(min_length=8, max_length=600)
    body: str = Field(min_length=20)
    category: str = Field(min_length=2, max_length=60)
    status: str = "draft"
    published_at: str | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    og_image: str | None = None
    canonical_url: str | None = None


class FaqIn(BaseModel):
    question: str = Field(min_length=4, max_length=300)
    answer: str = Field(min_length=4)
    sort_order: int = 0
    published: bool = True


class CouponCreate(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    type: str
    value: float
    active: bool = True
    expires_at: str | None = None
    min_subtotal: float | None = None
    usage_limit: int | None = None


class BundleIn(BaseModel):
    slug: str
    name: str
    description: str
    price_inr: float | None = None
    active: bool = True
    product_ids: list[int] = Field(default_factory=list)


class PageIn(BaseModel):
    title: str
    body: str
    notice: str | None = None
    seo_title: str | None = None
    seo_description: str | None = None


class SettingIn(BaseModel):
    value: dict
