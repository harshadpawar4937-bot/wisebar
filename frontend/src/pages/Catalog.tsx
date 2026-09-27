import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../lib/api";
import { track } from "../lib/analytics";
import { useShop } from "../shop";
import type { Product } from "../types";
import { ProductCard } from "../components/ProductCard";
import { Seo } from "../components/Seo";

export function CatalogPage({ category }: { category: "protein-bars" | "protein-muesli" }) {
  const [params, setParams] = useSearchParams();
  const [products, setProducts] = useState<Product[]>([]);
  const [all, setAll] = useState<Product[]>([]);
  const [compare, setCompare] = useState<number[]>([]);
  const sort = params.get("sort") || "featured";
  const flavor = params.get("flavor") || "";
  const q = params.get("q") || "";
  useEffect(() => {
    const query = new URLSearchParams({ category, sort });
    if (flavor) query.set("flavor", flavor);
    if (q) query.set("q", q);
    api<Product[]>(`/products?${query}`).then(setProducts).catch(() => setProducts([]));
    api<Product[]>(`/products?category=${category}`).then(setAll).catch(() => setAll([]));
  }, [category, sort, flavor, q]);
  const flavors = useMemo(() => Array.from(new Set(all.map((item) => item.flavor))), [all]);
  const priced = all.some((item) => item.price_inr);
  const protein = all.some((item) => item.nutrition.protein_g != null);
  const title = category === "protein-bars" ? "Protein Bars" : "Protein Muesli";
  const description = category === "protein-bars" ? "Protein that goes where you go." : "Start strong. Stay fueled.";
  function set(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value); else next.delete(key);
    setParams(next);
    track("filter", { category, key, value });
  }
  return (
    <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 lg:grid-cols-[220px_1fr]">
      <Seo title={`${title} · WISEBAR`} description={description} path={`/${category}`} />
      <aside className="space-y-4 text-sm">
        <h1 className="font-display text-4xl lg:hidden">{title}</h1>
        <label className="block"><span className="spec">Flavour</span>
          <select className="mt-2 w-full rounded-2xl border border-cream-200 px-3 py-2" value={flavor} onChange={(event) => set("flavor", event.target.value)}>
            <option value="">All listed flavours</option>
            {flavors.map((item) => <option key={item}>{item}</option>)}
          </select>
        </label>
        <label className="block"><span className="spec">Sort</span>
          <select className="mt-2 w-full rounded-2xl border border-cream-200 px-3 py-2" value={sort} onChange={(event) => set("sort", event.target.value)}>
            <option value="featured">Featured</option>
            <option value="newest">Newest</option>
            <option value="price_asc">Price, low to high</option>
            <option value="price_desc">Price, high to low</option>
          </select>
        </label>
        <p className="text-ink/60">{protein ? "Protein filters use verified grams." : "Protein and calorie filters appear once those values are published."}</p>
        <p className="text-ink/60">{priced ? "Price filters are on." : "No prices are published, so a price filter would hide the whole catalogue."}</p>
        <p className="text-ink/60">Dietary labels appear when a product is assigned one.</p>
      </aside>
      <div>
        <h1 className="hidden font-display text-6xl lg:block">{title}</h1>
        <p className="mt-2 max-w-xl text-ink/70">{description}</p>
        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          {products.map((product) => (
            <div key={product.id}>
              <ProductCard product={product} />
              <label className="mt-2 flex items-center gap-2 text-xs">
                <input type="checkbox" checked={compare.includes(product.id)} onChange={() => setCompare((current) => current.includes(product.id) ? current.filter((id) => id !== product.id) : [...current, product.id].slice(-3))} />
                Compare
              </label>
            </div>
          ))}
        </div>
        {products.length === 0 && <p className="mt-8">No products match. The catalogue only lists flavours that exist as records.</p>}
        {compare.length > 0 && <Compare ids={compare} products={all} onClear={() => setCompare([])} />}
      </div>
    </div>
  );
}

function Compare({ ids, products, onClear }: { ids: number[]; products: Product[]; onClear: () => void }) {
  const rows = products.filter((product) => ids.includes(product.id));
  const fields: [string, (product: Product) => string][] = [
    ["Protein", (product) => product.nutrition.protein_g == null ? "Pending" : `${product.nutrition.protein_g}g`],
    ["Energy", (product) => product.nutrition.calories_kcal == null ? "Pending" : `${product.nutrition.calories_kcal} kcal`],
    ["Price", (product) => product.price_inr || "Pending"],
    ["Allergens", (product) => product.allergens || "Pending"],
  ];
  return (
    <div className="fixed inset-x-0 bottom-16 z-30 border-t border-cream-200 bg-cream-50 p-4 md:bottom-0">
      <div className="mx-auto flex max-w-6xl items-start justify-between gap-4">
        <table className="text-sm">
          <thead><tr>{rows.map((product) => <th key={product.id} className="px-3 text-left"><Link to={`/products/${product.slug}`}>{product.flavor}</Link></th>)}</tr></thead>
          <tbody>
            {fields.map(([label, read]) => <tr key={label}><td className="pr-4 spec">{label}</td>{rows.map((product) => <td key={product.id} className="px-3 py-1">{read(product)}</td>)}</tr>)}
          </tbody>
        </table>
        <button onClick={onClear} className="text-sm underline">Clear</button>
      </div>
    </div>
  );
}

export function SearchPage() {
  const [params] = useSearchParams();
  const q = params.get("q") || "";
  const [products, setProducts] = useState<Product[]>([]);
  useEffect(() => { api<{ products: Product[] }>(`/search?q=${encodeURIComponent(q)}`).then((result) => setProducts(result.products)); }, [q]);
  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <Seo title={`Search · WISEBAR`} description="Search WISEBAR products." path={`/search?q=${encodeURIComponent(q)}`} />
      <h1 className="font-display text-4xl">{q ? `Results for “${q}”` : "Search"}</h1>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{products.map((product) => <ProductCard key={product.id} product={product} />)}</div>
      {q && products.length === 0 && <p className="mt-6">No products match that search.</p>}
    </div>
  );
}

export function useWishlist() {
  const shop = useShop();
  return async function toggle(productId: number) {
    const key = "wise-wish";
    const current = JSON.parse(localStorage.getItem(key) || "[]") as number[];
    const has = current.includes(productId);
    localStorage.setItem(key, JSON.stringify(has ? current.filter((id) => id !== productId) : [...current, productId]));
    if (shop.user) {
      await api(`/wishlist/${productId}`, { method: has ? "DELETE" : "POST" });
    }
    track("wishlist", { productId });
    shop.notify(has ? "Removed from wishlist." : "Saved to wishlist.");
  };
}
