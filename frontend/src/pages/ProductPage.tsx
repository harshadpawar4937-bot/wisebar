import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import { track } from "../lib/analytics";
import { formatINR, nutritionText } from "../lib/format";
import { useShop } from "../shop";
import type { Product } from "../types";
import { ProductArt } from "../components/Brand";
import { Seo } from "../components/Seo";
import { useWishlist } from "./Catalog";

export function ProductPage() {
  const { slug = "" } = useParams();
  const shop = useShop();
  const navigate = useNavigate();
  const wish = useWishlist();
  const [product, setProduct] = useState<Product | null>(null);
  const [qty, setQty] = useState(1);
  const [pin, setPin] = useState("");
  const [pinMessage, setPinMessage] = useState("");
  const [missing, setMissing] = useState(false);
  useEffect(() => {
    api<Product>(`/products/${slug}`).then((row) => { setProduct(row); track("product_view", { slug }); }).catch(() => setMissing(true));
  }, [slug]);
  if (missing) return <p className="px-4 py-20">That product is not in the catalogue.</p>;
  if (!product) return <div className="mx-auto max-w-6xl px-4 py-10"><div className="h-96 animate-pulse rounded-3xl bg-cream-200" /></div>;
  const max = shop.config?.commerce.max_qty_per_line || 10;
  async function add(buyNow = false) {
    try {
      await api("/cart/items", { method: "POST", body: JSON.stringify({ product_id: product!.id, quantity: qty }) });
      track("add_to_cart", { slug: product!.slug, quantity: qty });
      await shop.refresh();
      if (buyNow) navigate("/checkout");
      else shop.setCartOpen(true);
    } catch (error) {
      shop.notify(error instanceof ApiError ? error.message : "Could not add this product.");
    }
  }
  async function checkPin(event: FormEvent) {
    event.preventDefault();
    const result = await api<{ message: string }>("/pincode/check", { method: "POST", body: JSON.stringify({ pincode: pin }) });
    setPinMessage(result.message);
  }
  const facts = [
    ["Protein", nutritionText(product.nutrition.protein_g, " g"), product.nutrition.protein_g, 40],
    ["Energy", nutritionText(product.nutrition.calories_kcal, " kcal"), product.nutrition.calories_kcal, 500],
    ["Carbs", nutritionText(product.nutrition.carbs_g, " g"), product.nutrition.carbs_g, 60],
    ["Sugar", nutritionText(product.nutrition.sugar_g, " g"), product.nutrition.sugar_g, 40],
    ["Fat", nutritionText(product.nutrition.fat_g, " g"), product.nutrition.fat_g, 30],
    ["Fibre", nutritionText(product.nutrition.fibre_g, " g"), product.nutrition.fibre_g, 20],
  ] as const;
  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <Seo title={product.seo_title || `${product.name} · WISEBAR`} description={product.seo_description || product.description} path={`/products/${product.slug}`} jsonLd={product.purchasable && product.price_inr ? { "@context": "https://schema.org", "@type": "Product", name: product.name, sku: product.sku, description: product.description, offers: { "@type": "Offer", priceCurrency: "INR", price: product.price_inr, availability: "https://schema.org/InStock" } } : undefined} />
      <p className="text-sm text-ink/60"><Link to="/">Home</Link> / <Link to={`/${product.category_slug}`}>{product.category_name}</Link> / {product.flavor}</p>
      <div className="mt-6 grid items-start gap-10 lg:grid-cols-2">
        <div className="lg:sticky lg:top-24">
          {product.image_url ? <img src={product.image_url} alt={`${product.name} pack`} className="w-full rounded-[32px]" /> : <ProductArt family={product.flavor_family} className="w-full rounded-[32px]" />}
          <p className="mt-2 text-xs text-ink/50">Packaging concept until studio photography is supplied.</p>
        </div>
        <div>
          <p className="spec">{product.purchasable ? "On sale" : "Specification pending"}</p>
          <h1 className="mt-2 font-display text-5xl">{product.name}</h1>
          <p className="mt-2 text-lg">{product.flavor}</p>
          <p className="mt-4 font-display text-3xl">{formatINR(product.price_inr)}</p>
          <p className="mt-4 max-w-xl text-ink/80">{product.description}</p>
          <p className="mt-4 text-sm">Protein / serving · <span className="font-display text-xl">{nutritionText(product.nutrition.protein_g, "g")}</span></p>
          <div className="mt-6 flex items-center gap-3">
            <button aria-label="Decrease" onClick={() => setQty((value) => Math.max(1, value - 1))} className="h-10 w-10 rounded-full border">−</button>
            <span>{qty}</span>
            <button aria-label="Increase" onClick={() => setQty((value) => Math.min(max, value + 1))} className="h-10 w-10 rounded-full border">+</button>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button onClick={() => add(false)} className="rounded-full bg-pine-900 px-5 py-3 text-sm font-semibold text-cream-50">Add to cart</button>
            <button onClick={() => add(true)} className="rounded-full border border-pine-900 px-5 py-3 text-sm font-semibold">Buy now</button>
            <button onClick={() => wish(product.id)} className="rounded-full px-4 py-3 text-sm underline">Save</button>
          </div>
          <form onSubmit={checkPin} className="mt-6 flex gap-2">
            <label className="sr-only" htmlFor="pin">Pincode</label>
            <input id="pin" inputMode="numeric" pattern="\d{6}" required value={pin} onChange={(event) => setPin(event.target.value)} placeholder="Pincode" className="rounded-full border border-cream-200 px-4 py-3 text-sm" />
            <button className="rounded-full bg-cream-200 px-4 py-3 text-sm">Check delivery</button>
          </form>
          {pinMessage && <p className="mt-2 text-sm">{pinMessage}</p>}
          <ul className="mt-6 grid grid-cols-2 gap-2 text-xs text-ink/70">
            <li>Specs published before sale</li>
            <li>No invented nutrition</li>
            <li>FSSAI shown when licensed</li>
            <li>Pause or cancel subscriptions</li>
          </ul>
          <Story product={product} facts={facts} />
        </div>
      </div>
      <div className="fixed inset-x-0 bottom-14 z-30 flex items-center justify-between gap-3 border-t border-cream-200 bg-cream-50 px-4 py-3 md:hidden">
        <span className="font-display">{formatINR(product.price_inr)}</span>
        <button onClick={() => add(false)} className="rounded-full bg-pine-900 px-4 py-2 text-sm text-cream-50">Add to cart</button>
      </div>
    </div>
  );
}

function Story({ product, facts }: { product: Product; facts: readonly (readonly [string, string, number | null, number])[] }) {
  return (
    <div className="mt-12 space-y-10">
      <section>
        <h2 className="font-display text-3xl">Taste</h2>
        <p className="mt-2 text-ink/75">{product.flavor} is the working flavour name. Tasting notes will be written from the finished recipe, not before it.</p>
      </section>
      <section>
        <h2 className="font-display text-3xl">Protein</h2>
        <p className="mt-2 text-ink/75">{product.nutrition.status === "verified" ? `${product.nutrition.protein_g} g protein in the published serving.` : "The protein figure stays blank until the panel is verified."}</p>
      </section>
      <section>
        <h2 className="font-display text-3xl">Ingredients</h2>
        {product.ingredients ? <p className="mt-2">{product.ingredients}</p> : <p className="mt-2 text-ink/60">Formulation not yet published.</p>}
        {!!product.ingredient_rows?.length && (
          <ul className="mt-3 space-y-2">{product.ingredient_rows.map((row) => <li key={row.name} className="rounded-2xl bg-cream-100 p-3"><strong>{row.name}</strong>{row.note ? ` — ${row.note}` : ""}</li>)}</ul>
        )}
      </section>
      <section>
        <h2 className="font-display text-3xl">Nutrition</h2>
        <p className="text-xs text-ink/50">Per serving{product.serving_size ? ` · ${product.serving_size}` : ""}. Not a percent of daily intake.</p>
        <ul className="mt-4 space-y-3">
          {facts.map(([label, value, amount, scale]) => (
            <li key={label}>
              <div className="flex justify-between text-sm"><span>{label}</span><span>{value}</span></div>
              <div className="mt-1 h-2 rounded-full bg-cream-200">{amount != null && <div className="h-full rounded-full bg-pine-700" style={{ width: `${Math.min(100, (amount / scale) * 100)}%` }} />}</div>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-xs text-ink/40">Bar length is the published number against a fixed page scale (40 g, 500 kcal, 60 g). It is not a daily-value claim.</p>
      </section>
      <section>
        <h2 className="font-display text-3xl">Lifestyle</h2>
        <p className="mt-2 text-ink/75">{product.occasions.length ? `Merchandised for ${product.occasions.join(", ")}. That is a shelf choice, not a health instruction.` : "Occasion tags have not been set."}</p>
      </section>
      <section className="rounded-3xl bg-cream-100 p-5 text-sm">
        <h2 className="font-display text-2xl">Know what you eat</h2>
        <dl className="mt-4 space-y-2">
          <Row k="Net quantity" v={product.net_quantity} />
          <Row k="Allergens" v={product.allergens} />
          <Row k="Storage" v={product.storage} />
          <Row k="Manufacturer" v={product.manufacturer} />
          <Row k="FSSAI" v={product.fssai_license} />
          <Row k="Customer care" v={product.customer_care} />
          <Row k="Batch" v={product.batches?.[0]?.batch_number || null} />
        </dl>
        {product.lab_report_url ? <a className="mt-4 inline-flex underline" href={product.lab_report_url}>View report</a> : <p className="mt-4 text-ink/50">No lab report is on file.</p>}
      </section>
      <section>
        <h2 className="font-display text-3xl">Reviews</h2>
        {product.reviews?.length ? product.reviews.map((review) => (
          <article key={review.id} className="mt-3 rounded-2xl border border-cream-200 p-4">
            <p className="text-sm">{review.author_name} · {review.rating}/5 {review.verified_purchase && "· Verified purchase"}</p>
            <p className="mt-1">{review.body}</p>
          </article>
        )) : <p className="mt-2 text-ink/60">No approved reviews yet.</p>}
      </section>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string | null | undefined }) {
  return <div className="flex justify-between gap-4 border-b border-cream-200 py-2"><dt>{k}</dt><dd className="text-right">{v || "Pending verification"}</dd></div>;
}
