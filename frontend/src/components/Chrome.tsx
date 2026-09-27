import { FormEvent, useEffect, useState, type ReactNode } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { api, ApiError } from "../lib/api";
import { track } from "../lib/analytics";
import { formatINR } from "../lib/format";
import { useShop } from "../shop";
import type { Cart, Product } from "../types";
import { Mark, ProductArt } from "./Brand";

const links = [
  ["/protein-bars", "Bars"],
  ["/protein-muesli", "Muesli"],
  ["/bundles", "Bundles"],
  ["/build-your-box", "Build a Box"],
  ["/journal", "Journal"],
  ["/corporate", "Corporate"],
] as const;

export function Header() {
  const shop = useShop();
  const [open, setOpen] = useState(false);
  const count = shop.cart?.items.reduce((sum, item) => sum + item.quantity, 0) ?? 0;
  return (
    <header className="sticky top-0 z-40 border-b border-cream-200 bg-cream-50">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
        <Link to="/" className="flex items-center gap-2 font-display text-lg font-semibold tracking-tight" aria-label="WISEBAR home">
          <Mark className="h-8 w-8 text-pine-900" />
          WISEBAR™
        </Link>
        <nav className="hidden items-center gap-6 text-sm lg:flex" aria-label="Primary">
          {links.map(([to, label]) => (
            <NavLink key={to} to={to} className={({ isActive }) => isActive ? "font-semibold text-pine-800" : "text-ink/80"}>{label}</NavLink>
          ))}
        </nav>
        <div className="flex items-center gap-1">
          <IconButton label="Search" onClick={() => shop.setSearchOpen(true)}>⌕</IconButton>
          <Link to="/account" className="rounded-full px-3 py-2 text-sm" aria-label="Account">{shop.user ? shop.user.name.split(" ")[0] : "Account"}</Link>
          <IconButton label={`Cart, ${count} items`} onClick={() => shop.setCartOpen(true)}>{count > 0 ? count : "Bag"}</IconButton>
          <button className="rounded-full px-3 py-2 text-sm lg:hidden" aria-expanded={open} aria-label="Menu" onClick={() => setOpen((value) => !value)}>Menu</button>
        </div>
      </div>
      {open && (
        <nav className="grid gap-2 border-t border-cream-200 px-4 py-3 lg:hidden" aria-label="Mobile">
          {links.map(([to, label]) => <Link key={to} to={to} onClick={() => setOpen(false)} className="rounded-xl px-2 py-2">{label}</Link>)}
        </nav>
      )}
    </header>
  );
}

function IconButton({ children, label, onClick }: { children: ReactNode; label: string; onClick: () => void }) {
  return <button type="button" aria-label={label} onClick={onClick} className="rounded-full px-3 py-2 text-sm">{children}</button>;
}

export function Announcement() {
  const { config } = useShop();
  const [hidden, setHidden] = useState(() => sessionStorage.getItem("wise-announce") === "1");
  if (hidden || !config) return null;
  return (
    <div className="bg-pine-900 px-4 py-2 text-center text-sm text-cream-50">
      <span>{config.home.announcement}</span>
      <button className="ml-3 underline" onClick={() => { sessionStorage.setItem("wise-announce", "1"); setHidden(true); }}>Dismiss</button>
    </div>
  );
}

export function Footer() {
  const { config, notify } = useShop();
  const [email, setEmail] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      await api("/newsletter", { method: "POST", body: JSON.stringify({ email }) });
      track("newsletter_signup");
      setEmail("");
      notify("You're on the list. We'll write when there is something real to share.");
    } catch (error) {
      notify(error instanceof ApiError ? error.message : "Could not join the list.");
    }
  }
  const socials = [
    ["Instagram", config?.company.instagram],
    ["Facebook", config?.company.facebook],
    ["YouTube", config?.company.youtube],
    ["LinkedIn", config?.company.linkedin],
  ] as const;
  return (
    <footer className="bg-pine-950 text-cream-50">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-16 md:grid-cols-4">
        <div className="md:col-span-1">
          <p className="font-display text-3xl">Get WISE about what you eat.</p>
          <form onSubmit={submit} className="mt-4 flex gap-2">
            <label className="sr-only" htmlFor="newsletter">Email</label>
            <input id="newsletter" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email address" className="w-full rounded-full bg-white/10 px-4 py-3 text-sm" />
            <button className="rounded-full bg-lime px-4 py-3 text-sm font-semibold text-pine-950">Join</button>
          </form>
        </div>
        <FooterCol title="Shop" links={[["/protein-bars", "Bars"], ["/protein-muesli", "Muesli"], ["/build-your-box", "Build your box"], ["/bundles", "Bundles"]]} />
        <FooterCol title="Company" links={[["/about", "About"], ["/journal", "Journal"], ["/corporate", "Corporate"], ["/contact", "Contact"], ["/faq", "FAQ"]]} />
        <div>
          <FooterCol title="Customer care" links={[["/shipping", "Shipping"], ["/returns", "Returns"], ["/shipping#track", "Track order"], ["/contact", "Contact"]]} />
          <p className="spec mt-6 text-cream-200">Legal</p>
          <div className="mt-3 flex flex-col gap-2 text-sm text-cream-100">
            <Link to="/privacy">Privacy</Link><Link to="/terms">Terms</Link><Link to="/returns">Refunds</Link><Link to="/cookies">Cookies</Link>
          </div>
        </div>
      </div>
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-4 px-4 pb-8 text-sm text-cream-200">
        {socials.map(([label, href]) => href ? <a key={label} href={href}>{label}</a> : <span key={label}>{label} · not linked yet</span>)}
      </div>
      <p className="overflow-hidden px-4 pb-6 font-display text-[18vw] leading-none text-cream-50/10">WISEBAR</p>
    </footer>
  );
}

function FooterCol({ title, links }: { title: string; links: (readonly [string, string])[] }) {
  return (
    <div>
      <p className="spec text-cream-200">{title}</p>
      <div className="mt-3 flex flex-col gap-2 text-sm">
        {links.map(([to, label]) => <Link key={label} to={to}>{label}</Link>)}
      </div>
    </div>
  );
}

export function CartDrawer() {
  const shop = useShop();
  const reduced = useReducedMotion();
  const cart = shop.cart;
  const [suggestions, setSuggestions] = useState<Product[]>([]);
  useEffect(() => {
    if (!shop.cartOpen) return;
    api<Cart>("/cart").then((next) => setSuggestions(next.suggestions || [])).catch(() => setSuggestions([]));
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") shop.setCartOpen(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [shop.cartOpen]);
  return (
    <AnimatePresence>
      {shop.cartOpen && (
        <>
          <motion.button aria-label="Close cart" className="fixed inset-0 z-50 bg-pine-950/40" onClick={() => shop.setCartOpen(false)} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} />
          <motion.aside role="dialog" aria-label="Cart" className="fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col bg-cream-50 p-5" initial={reduced ? false : { x: 40, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: 40, opacity: 0 }}>
            <div className="flex items-center justify-between">
              <h2 className="font-display text-2xl">Your bag</h2>
              <button onClick={() => shop.setCartOpen(false)} className="rounded-full px-3 py-2 text-sm">Close</button>
            </div>
            <div className="mt-4 flex-1 space-y-4 overflow-auto">
              {cart && cart.items.length === 0 && <p className="text-sm text-ink/70">Nothing here yet. Products join the bag once they are actually for sale.</p>}
              {cart?.items.map((item) => <CartRow key={item.id} id={item.id} name={item.name} flavor={item.flavor} quantity={item.quantity} price={item.line_total_inr ?? null} family={item.flavor_family} />)}
              {!!cart?.saved.length && <h3 className="pt-4 font-display text-lg">Saved for later</h3>}
              {cart?.saved.map((item) => <CartRow key={item.id} id={item.id} name={item.name} flavor={item.flavor} quantity={item.quantity} price={null} family={item.flavor_family} saved />)}
              {!!suggestions.length && (
                <div>
                  <h3 className="font-display text-lg">Often chosen with these</h3>
                  <ul className="mt-2 space-y-1 text-sm">{suggestions.map((item) => <li key={item.id}><Link to={`/products/${item.slug}`} onClick={() => shop.setCartOpen(false)}>{item.name}</Link></li>)}</ul>
                </div>
              )}
            </div>
            <div className="border-t border-cream-200 pt-4 text-sm">
              <p>{cart?.shipping_message}</p>
              {cart?.shipping_progress != null && <div className="mt-2 h-1.5 rounded-full bg-cream-200"><div className="h-full rounded-full bg-pine-700" style={{ width: `${Math.min(100, cart.shipping_progress * 100)}%` }} /></div>}
              <p className="mt-3 font-display text-xl">{cart?.total_inr ? formatINR(cart.total_inr) : "Total pending"}</p>
              <Link to="/checkout" onClick={() => { shop.setCartOpen(false); track("begin_checkout"); }} className="mt-3 flex justify-center rounded-full bg-pine-900 py-3 text-cream-50">Checkout</Link>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

function CartRow({ id, name, flavor, quantity, price, family, saved = false }: { id: number; name: string; flavor: string; quantity: number; price: string | null; family: string; saved?: boolean }) {
  const shop = useShop();
  async function update(next: { quantity?: number; saved_for_later?: boolean; remove?: boolean }) {
    try {
      if (next.remove) await api(`/cart/items/${id}`, { method: "DELETE" });
      else await api(`/cart/items/${id}`, { method: "PATCH", body: JSON.stringify({ quantity: next.quantity ?? quantity, saved_for_later: next.saved_for_later }) });
      if (next.remove) track("remove_from_cart", { id });
      await shop.refresh();
    } catch (error) {
      shop.notify(error instanceof ApiError ? error.message : "Cart update failed.");
    }
  }
  return (
    <div className="flex gap-3">
      <ProductArt family={family} className="h-16 w-14 shrink-0 rounded-xl" />
      <div className="flex-1 text-sm">
        <p className="font-medium">{name}</p>
        <p className="text-ink/60">{flavor}</p>
        <div className="mt-2 flex gap-2">
          <button aria-label="Decrease quantity" onClick={() => quantity === 1 ? update({ remove: true }) : update({ quantity: quantity - 1 })}>−</button>
          <span>{quantity}</span>
          <button aria-label="Increase quantity" onClick={() => update({ quantity: quantity + 1 })}>+</button>
          <button onClick={() => update({ saved_for_later: !saved })}>{saved ? "Move to bag" : "Save"}</button>
          <button onClick={() => update({ remove: true })}>Remove</button>
        </div>
      </div>
      <p>{price ? formatINR(price) : "—"}</p>
    </div>
  );
}

export function SearchDialog() {
  const shop = useShop();
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [products, setProducts] = useState<Product[]>([]);
  useEffect(() => {
    if (!shop.searchOpen) return;
    const handle = window.setTimeout(() => {
      api<{ products: Product[] }>(`/search?q=${encodeURIComponent(q)}`).then((result) => setProducts(result.products)).catch(() => setProducts([]));
    }, 250);
    return () => window.clearTimeout(handle);
  }, [q, shop.searchOpen]);
  if (!shop.searchOpen) return null;
  return (
    <div className="fixed inset-0 z-50 bg-pine-950/40 p-4" role="dialog" aria-label="Search">
      <div className="mx-auto mt-16 max-w-xl rounded-3xl bg-cream-50 p-4">
        <input autoFocus value={q} onChange={(event) => setQ(event.target.value)} placeholder="Search name, flavour, ingredient, SKU" className="w-full rounded-2xl border border-cream-200 px-4 py-3" onKeyDown={(event) => { if (event.key === "Escape") shop.setSearchOpen(false); if (event.key === "Enter") { track("search", { q }); navigate(`/search?q=${encodeURIComponent(q)}`); shop.setSearchOpen(false); } }} />
        <ul className="mt-3 max-h-80 overflow-auto">
          {products.map((product) => (
            <li key={product.id}><Link className="block rounded-xl px-2 py-2 hover:bg-cream-100" to={`/products/${product.slug}`} onClick={() => shop.setSearchOpen(false)}>{product.name} · {product.flavor}</Link></li>
          ))}
          {q.length > 1 && products.length === 0 && <li className="px-2 py-6 text-sm">No products match that search.</li>}
        </ul>
        <button className="mt-2 text-sm underline" onClick={() => shop.setSearchOpen(false)}>Close</button>
      </div>
    </div>
  );
}

export function MobileBar() {
  const shop = useShop();
  const items = [
    ["/protein-bars", "Shop"],
    ["search", "Search"],
    ["/build-your-box", "Box"],
    ["/account", "Account"],
    ["cart", "Cart"],
  ] as const;
  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-5 border-t border-cream-200 bg-cream-50 py-2 text-center text-xs md:hidden" aria-label="Mobile">
      {items.map(([to, label]) => to === "search" ? (
        <button key={label} onClick={() => shop.setSearchOpen(true)}>{label}</button>
      ) : to === "cart" ? (
        <button key={label} onClick={() => shop.setCartOpen(true)}>{label}</button>
      ) : <Link key={label} to={to}>{label}</Link>)}
    </nav>
  );
}
