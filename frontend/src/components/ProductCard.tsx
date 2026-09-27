import { Link } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import { track } from "../lib/analytics";
import { discountLabel, formatINR, nutritionText } from "../lib/format";
import { useShop } from "../shop";
import type { Product } from "../types";
import { ProductArt } from "./Brand";

export function ProductCard({ product }: { product: Product }) {
  const shop = useShop();
  const off = discountLabel(product.price_inr, product.mrp_inr);
  async function quickAdd() {
    try {
      await api("/cart/items", { method: "POST", body: JSON.stringify({ product_id: product.id, quantity: 1 }) });
      track("add_to_cart", { slug: product.slug });
      await shop.refresh();
      shop.setCartOpen(true);
    } catch (error) {
      shop.notify(error instanceof ApiError ? error.message : "Could not add this product.");
    }
  }
  return (
    <article className="flex flex-col rounded-[28px] bg-cream-100 p-3 shadow-card">
      <Link to={`/products/${product.slug}`} className="relative block overflow-hidden rounded-3xl bg-pine-900">
        {product.image_url ? <img src={product.image_url} alt="" className="aspect-[4/5] w-full object-cover" /> : <ProductArt family={product.flavor_family} className="aspect-[4/5] w-full" />}
        <span className="absolute left-3 top-3 rounded-full bg-cream-50 px-3 py-1 text-xs">{product.purchasable ? "On sale" : "Proposed"}</span>
      </Link>
      <div className="flex flex-1 flex-col px-2 pb-2 pt-4">
        <h3 className="font-display text-2xl leading-none">{product.name}</h3>
        <p className="mt-1 text-sm text-ink/70">{product.flavor}</p>
        <dl className="mt-4 grid grid-cols-3 gap-2 text-xs">
          <Spec k="Protein" v={nutritionText(product.nutrition.protein_g, "g")} />
          <Spec k="Serving" v={product.serving_size || "Pending"} />
          <Spec k="Energy" v={nutritionText(product.nutrition.calories_kcal, " kcal")} />
        </dl>
        <div className="mt-4 flex items-end justify-between">
          <p className="font-display text-lg">{formatINR(product.price_inr)}{product.mrp_inr && product.price_inr && <span className="ml-2 text-sm text-ink/50 line-through">{formatINR(product.mrp_inr)}</span>}</p>
          {off && <span className="text-xs">{off}</span>}
        </div>
        <p className="mt-1 text-xs text-ink/60">{product.review_count ? `${product.rating_avg} · ${product.review_count} reviews` : "No reviews yet"}</p>
        <div className="mt-4 grid grid-cols-2 gap-2">
          <button onClick={quickAdd} className="rounded-full bg-pine-900 py-2 text-sm text-cream-50">{product.purchasable ? "Quick add" : "Not for sale yet"}</button>
          <Link to={`/products/${product.slug}`} className="rounded-full border border-pine-900 py-2 text-center text-sm">View product</Link>
        </div>
      </div>
    </article>
  );
}

function Spec({ k, v }: { k: string; v: string }) {
  return <div><dt className="spec text-pine-800">{k}</dt><dd className="mt-1 font-display text-sm">{v}</dd></div>;
}
