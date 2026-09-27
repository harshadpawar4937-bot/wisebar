from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session, joinedload

from app.config import Settings, get_settings
from app.database import get_db
from app.models import Cart, CartItem, Product, User
from app.security import csrf_ok, read_token
from app.services import cart_by_token


def settings_dep() -> Settings:
    return get_settings()


def optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get("wise_session")
    if not token:
        return None
    payload = read_token(token)
    if not payload:
        return None
    return db.get(User, int(payload["sub"]))


def current_user(user: User | None = Depends(optional_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in to continue.")
    return user


def admin_user(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access is required.")
    return user


def load_cart(request: Request, response: Response, db: Session = Depends(get_db)) -> Cart:
    cart = cart_by_token(db, request.cookies.get("wise_cart"))
    if request.cookies.get("wise_cart") != cart.token:
        secure = not get_settings().debug
        response.set_cookie("wise_cart", cart.token, httponly=True, samesite="lax", secure=secure, max_age=60 * 60 * 24 * 30, path="/")
    db.commit()
    db.refresh(cart)
    return (
        db.query(Cart)
        .options(
            joinedload(Cart.items).joinedload(CartItem.product).joinedload(Product.category),
            joinedload(Cart.items).joinedload(CartItem.product).joinedload(Product.inventory),
        )
        .filter_by(id=cart.id)
        .one()
    )


def mutate(request: Request) -> None:
    csrf_ok(request)


def ensure_csrf(request: Request, response: Response) -> str:
    token = request.cookies.get("wise_csrf") or secrets.token_urlsafe(32)
    if request.cookies.get("wise_csrf") != token:
        secure = not get_settings().debug
        response.set_cookie("wise_csrf", token, httponly=False, samesite="lax", secure=secure, path="/")
    return token
