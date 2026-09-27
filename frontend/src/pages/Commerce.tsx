import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import { track } from "../lib/analytics";
import { formatINR } from "../lib/format";
import { useShop } from "../shop";
import type { Bundle, Product } from "../types";
import { ProductArt } from "../components/Brand";
import { Seo } from "../components/Seo";
import { Notice } from "../components/Ui";

const states = ["Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"];

export function BundlesPage() {
  const [bundles, setBundles] = useState<Bundle[]>([]);
  useEffect(() => { api<Bundle[]>("/bundles").then(setBundles); }, []);
  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <Seo title="Bundles · WISEBAR" description="WISEBAR bundles. Prices appear once an admin publishes them." path="/bundles" />
      <h1 className="font-display text-6xl">Bundles</h1>
      <p className="mt-3 max-w-xl text-ink/70">Starter, breakfast, fitness, office, and family. Contents are editable. A price shows only after it is stored.</p>
      <div className="mt-8 grid gap-4 md:grid-cols-2">
        {bundles.map((bundle) => (
          <article key={bundle.slug} className="rounded-[28px] bg-cream-100 p-6">
            <h2 className="font-display text-3xl">{bundle.name}</h2>
            <p className="mt-2 text-sm text-ink/75">{bundle.description}</p>
            <ul className="mt-4 text-sm">{bundle.items.map((item) => <li key={item.slug}><Link to={`/products/${item.slug}`}>{item.name}</Link> × {item.quantity}</li>)}</ul>
            <p className="mt-4 font-display">{bundle.price_inr ? formatINR(bundle.price_inr) : "Price configured in admin"}</p>
          </article>
        ))}
      </div>
    </div>
  );
}

export function BuildBoxPage() {
  const { config, notify, refresh, setCartOpen } = useShop();
  const [products, setProducts] = useState<Product[]>([]);
  const [size, setSize] = useState(6);
  const [picks, setPicks] = useState<number[]>([]);
  useEffect(() => { api<Product[]>("/products").then(setProducts); }, []);
  useEffect(() => { if (config?.merchandising.box_sizes[0]) setSize(config.merchandising.box_sizes[0]); }, [config]);
  const priced = picks.every((id) => products.find((product) => product.id === id)?.price_inr);
  const subtotal = priced ? picks.reduce((sum, id) => sum + Number(products.find((product) => product.id === id)?.price_inr || 0), 0) : null;
  function add(id: number) {
    if (picks.length >= size) return;
    setPicks((current) => [...current, id]);
  }
  async function build() {
    track("build_box", { size, count: picks.length });
    if (picks.length !== size) { notify(`Choose ${size} bars to fill the box.`); return; }
    try {
      for (const id of picks) await api("/cart/items", { method: "POST", body: JSON.stringify({ product_id: id, quantity: 1 }) });
      await refresh();
      setCartOpen(true);
    } catch (error) {
      notify(error instanceof ApiError ? error.message : "This box cannot be added until those products are for sale.");
    }
  }
  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <Seo title="Build your box · WISEBAR" description="Your snacks. Your flavours. Your box." path="/build-your-box" />
      <h1 className="font-display text-6xl">Your snacks. Your flavours. Your box.</h1>
      <div className="mt-6 flex flex-wrap gap-2">
        {(config?.merchandising.box_sizes || [6, 12, 18, 24]).map((value) => <button key={value} onClick={() => { setSize(value); setPicks([]); }} className={`rounded-full px-4 py-2 text-sm ${size === value ? "bg-pine-900 text-cream-50" : "border"}`}>{value}</button>)}
      </div>
      <div className="mt-6 grid grid-cols-6 gap-2 md:grid-cols-12">
        {Array.from({ length: size }).map((_, index) => <div key={index} className={`aspect-square rounded-2xl ${picks[index] ? "bg-pine-800" : "bg-cream-200"}`} />)}
      </div>
      <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {products.map((product) => (
          <button key={product.id} onClick={() => add(product.id)} className="rounded-3xl bg-cream-100 p-3 text-left">
            <ProductArt family={product.flavor_family} className="rounded-2xl" />
            <span className="mt-2 block font-display">{product.flavor}</span>
          </button>
        ))}
      </div>
      <div className="mt-6 flex items-center justify-between">
        <p>{subtotal == null ? "Subtotal pending — prices are not published yet." : formatINR(subtotal)}</p>
        <button onClick={build} className="rounded-full bg-lime px-5 py-3 text-sm font-semibold text-pine-950">Build my box</button>
      </div>
      <p className="mt-3 text-sm text-ink/60">{config?.commerce.free_shipping_threshold_inr ? `Free shipping from ₹${config.commerce.free_shipping_threshold_inr}.` : "Free-shipping progress appears once a threshold is set."}</p>
    </div>
  );
}

export function CheckoutPage() {
  const shop = useShop();
  const [message, setMessage] = useState("");
  const [order, setOrder] = useState<{ order_number: string; total_inr: string; payment_status: string } | null>(null);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const body = Object.fromEntries(form.entries());
    try {
      const result = await api<{ order_number: string; total_inr: string; payment_status: string }>("/orders/checkout", { method: "POST", body: JSON.stringify(body) });
      setOrder(result);
      track("purchase", { order: result.order_number });
      await shop.refresh();
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Checkout did not complete.");
    }
  }
  return (
    <div className="mx-auto max-w-xl px-4 py-12">
      <Seo title="Checkout · WISEBAR" description="WISEBAR checkout." path="/checkout" />
      <h1 className="font-display text-5xl">Checkout</h1>
      {!shop.config?.commerce.selling_enabled && <div className="mt-4"><Notice>Selling is off. You can review the form. An order is created only when prices, stock, shipping rules, and a payment gateway are all in place.</Notice></div>}
      {order ? (
        <div className="mt-6 rounded-3xl bg-cream-100 p-5">
          <p className="spec">Order {order.order_number}</p>
          <p className="mt-2">Amount {formatINR(order.total_inr)}</p>
          <p>Payment {order.payment_status}</p>
        </div>
      ) : (
        <form onSubmit={submit} className="mt-6 grid gap-3">
          <input name="name" required placeholder="Name" className="rounded-2xl border px-4 py-3" />
          <input name="phone" required pattern="[6-9][0-9]{9}" placeholder="Mobile" className="rounded-2xl border px-4 py-3" />
          <input name="email" type="email" required placeholder="Email" className="rounded-2xl border px-4 py-3" />
          <input name="address" required placeholder="Address" className="rounded-2xl border px-4 py-3" />
          <input name="city" required placeholder="City" className="rounded-2xl border px-4 py-3" />
          <select name="state" required className="rounded-2xl border px-4 py-3" defaultValue=""><option value="" disabled>State</option>{states.map((state) => <option key={state}>{state}</option>)}</select>
          <input name="pincode" required pattern="[0-9]{6}" placeholder="Pincode" className="rounded-2xl border px-4 py-3" />
          {message && <p className="text-sm text-berry">{message}</p>}
          <button className="rounded-full bg-pine-900 py-3 text-cream-50">Place order</button>
        </form>
      )}
      <p className="mt-4 text-xs text-ink/60">UPI, cards, net banking, and wallets are handled by the configured provider. No card data is stored here.</p>
    </div>
  );
}
