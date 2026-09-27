from __future__ import annotations

import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.deps import current_user, mutate, optional_user
from app.models import Address, PasswordReset, Product, Referral, RewardRule, User, Wishlist
from app.schemas import AddressIn, LoginIn, ProfileIn, RegisterIn, ResetConfirmIn, ResetRequestIn
from app.security import hash_password, hash_reset_token, make_token, rate_limit, verify_password
from app.serialize import product_dict

router = APIRouter()


def _session_cookie(response: Response, user: User) -> None:
    settings = get_settings()
    response.set_cookie(
        "wise_session",
        make_token(user.id, user.role),
        httponly=True,
        samesite="lax",
        secure=not settings.debug,
        max_age=60 * 60 * 24 * 14,
        path="/",
    )


def _brief(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "referral_code": user.referral_code,
        "points_balance": user.points_balance,
    }


@router.post("/auth/register")
def register(body: RegisterIn, request: Request, response: Response, db: Session = Depends(get_db), _: None = Depends(mutate)):
    rate_limit(request, "register", 8, 60)
    email = body.email.lower()
    if db.query(User).filter_by(email=email).one_or_none():
        raise HTTPException(status_code=409, detail="An account with that email already exists.")
    phone = _phone(body.phone) if body.phone else None
    referrer = None
    if body.referral_code:
        referrer = db.query(User).filter_by(referral_code=body.referral_code.strip().upper()).one_or_none()
    user = User(
        email=email,
        name=body.name.strip(),
        phone=phone,
        password_hash=hash_password(body.password),
        role="customer",
        referral_code="WISE-" + secrets.token_hex(3).upper(),
        referred_by_id=referrer.id if referrer else None,
    )
    db.add(user)
    db.flush()
    if referrer and referrer.id != user.id:
        db.add(Referral(referrer_id=referrer.id, referred_user_id=user.id, code=referrer.referral_code, status="signed_up"))
    db.commit()
    _session_cookie(response, user)
    return _brief(user)


@router.post("/auth/login")
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db), _: None = Depends(mutate)):
    rate_limit(request, "login", 10, 60)
    user = db.query(User).filter_by(email=body.email.lower()).one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    _session_cookie(response, user)
    return _brief(user)


@router.post("/auth/logout")
def logout(response: Response, _: None = Depends(mutate)):
    response.delete_cookie("wise_session", path="/")
    return {"ok": True}


@router.get("/auth/me")
def me(user: User | None = Depends(optional_user)):
    return _brief(user) if user else None


@router.post("/auth/forgot")
def forgot(body: ResetRequestIn, request: Request, db: Session = Depends(get_db), _: None = Depends(mutate)):
    rate_limit(request, "forgot", 6, 60)
    user = db.query(User).filter_by(email=body.email.lower()).one_or_none()
    payload = {"detail": "If an account exists, a reset will be sent once email delivery is configured."}
    if user:
        token = secrets.token_urlsafe(32)
        db.add(PasswordReset(user_id=user.id, token_hash=hash_reset_token(token), expires_at=datetime.utcnow() + timedelta(minutes=30)))
        db.commit()
        settings = get_settings()
        if settings.debug and not settings.smtp_host:
            payload["dev_reset_token"] = token
    return payload


@router.post("/auth/reset")
def reset_password(body: ResetConfirmIn, db: Session = Depends(get_db), _: None = Depends(mutate)):
    row = (
        db.query(PasswordReset)
        .filter_by(token_hash=hash_reset_token(body.token), used=False)
        .order_by(PasswordReset.id.desc())
        .one_or_none()
    )
    if row is None or row.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="This reset link is invalid or expired.")
    user = db.get(User, row.user_id)
    user.password_hash = hash_password(body.password)
    row.used = True
    db.commit()
    return {"ok": True}


@router.patch("/users/me")
def update_me(body: ProfileIn, db: Session = Depends(get_db), user: User = Depends(current_user), _: None = Depends(mutate)):
    user.name = body.name.strip()
    user.phone = _phone(body.phone) if body.phone else None
    db.commit()
    return _brief(user)


@router.get("/users/me/addresses")
def addresses(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(Address).filter_by(user_id=user.id).all()
    return [_address(row) for row in rows]


@router.post("/users/me/addresses")
def add_address(body: AddressIn, db: Session = Depends(get_db), user: User = Depends(current_user), _: None = Depends(mutate)):
    if body.is_default:
        db.query(Address).filter_by(user_id=user.id).update({"is_default": False})
    row = Address(user_id=user.id, **body.model_dump())
    db.add(row)
    db.commit()
    return _address(row)


@router.delete("/users/me/addresses/{address_id}")
def delete_address(address_id: int, db: Session = Depends(get_db), user: User = Depends(current_user), _: None = Depends(mutate)):
    row = db.query(Address).filter_by(id=address_id, user_id=user.id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Address not found.")
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.get("/wishlist")
def wishlist(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(Wishlist).filter_by(user_id=user.id).all()
    products = []
    for row in rows:
        product = db.get(Product, row.product_id)
        if product and product.status != "archived":
            products.append(product_dict(db, product))
    return products


@router.post("/wishlist/{product_id}")
def save_wishlist(product_id: int, db: Session = Depends(get_db), user: User = Depends(current_user), _: None = Depends(mutate)):
    product = db.get(Product, product_id)
    if product is None or product.status == "archived":
        raise HTTPException(status_code=404, detail="Product not found.")
    if not db.query(Wishlist).filter_by(user_id=user.id, product_id=product_id).one_or_none():
        db.add(Wishlist(user_id=user.id, product_id=product_id))
        db.commit()
    return {"ok": True}


@router.delete("/wishlist/{product_id}")
def drop_wishlist(product_id: int, db: Session = Depends(get_db), user: User = Depends(current_user), _: None = Depends(mutate)):
    row = db.query(Wishlist).filter_by(user_id=user.id, product_id=product_id).one_or_none()
    if row:
        db.delete(row)
        db.commit()
    return {"ok": True}


@router.get("/referrals")
def referrals(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(Referral).filter_by(referrer_id=user.id).all()
    return {"code": user.referral_code, "invites": [{"status": row.status, "created_at": row.created_at.isoformat()} for row in rows]}


@router.get("/rewards")
def rewards(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rules = db.query(RewardRule).order_by(RewardRule.id).all()
    return {
        "balance": user.points_balance,
        "rules": [{"event": row.event, "points": row.points, "active": row.active, "note": row.note} for row in rules],
    }


def _address(row: Address) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "phone": row.phone,
        "line1": row.line1,
        "line2": row.line2,
        "city": row.city,
        "state": row.state,
        "pincode": row.pincode,
        "is_default": row.is_default,
    }


def _phone(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if len(digits) != 10 or digits[0] not in "6789":
        raise HTTPException(status_code=400, detail="Enter a valid Indian mobile number.")
    return digits
