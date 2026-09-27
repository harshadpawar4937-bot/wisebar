import { FormEvent, useEffect, useState } from "react";
import { api, ApiError } from "../lib/api";
import { useShop } from "../shop";
import type { Product } from "../types";

type Dash = { revenue_inr: string | null; orders: number; customers: number; products: number; aov_inr: number | null; repeat_purchase_rate: number | null; open_leads: number; pending_reviews: number };

export function AdminPage() {
  const shop = useShop();
  const [tab, setTab] = useState("overview");
  if (!shop.ready) return null;
  if (!shop.user || shop.user.role !== "admin") {
    return (
      <form className="mx-auto grid max-w-sm gap-3 px-4 py-16" onSubmit={async (event) => {
        event.preventDefault();
        const body = Object.fromEntries(new FormData(event.currentTarget).entries());
        try {
          await api("/auth/login", { method: "POST", body: JSON.stringify(body) });
          await shop.refresh();
        } catch (error) {
          shop.notify(error instanceof ApiError ? error.message : "Login failed.");
        }
      }}>
        <h1 className="font-display text-4xl">Operator sign in</h1>
        <input name="email" type="email" required className="rounded-2xl border px-4 py-3" placeholder="Email" />
        <input name="password" type="password" required className="rounded-2xl border px-4 py-3" placeholder="Password" />
        <button className="rounded-full bg-pine-900 py-3 text-cream-50">Sign in</button>
      </form>
    );
  }
  const tabs = ["overview", "products", "orders", "journal", "leads", "reviews", "settings"];
  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="font-display text-4xl">WISEBAR admin</h1>
      <div className="mt-4 flex flex-wrap gap-2 text-sm">{tabs.map((item) => <button key={item} onClick={() => setTab(item)} className={`rounded-full px-3 py-1 capitalize ${tab === item ? "bg-pine-900 text-cream-50" : "border"}`}>{item}</button>)}</div>
      <div className="mt-6">{tab === "overview" && <Overview />}{tab === "products" && <Products />}{tab === "orders" && <Orders />}{tab === "journal" && <JournalAdmin />}{tab === "leads" && <Leads />}{tab === "reviews" && <Reviews />}{tab === "settings" && <Settings />}</div>
    </div>
  );
}

function Overview() {
  const [dash, setDash] = useState<Dash | null>(null);
  useEffect(() => { api<Dash>("/admin/dashboard").then(setDash); }, []);
  if (!dash) return null;
  const cards = [
    ["Revenue", dash.revenue_inr ?? "—"],
    ["Paid orders", String(dash.orders)],
    ["Customers", String(dash.customers)],
    ["Products", String(dash.products)],
    ["AOV", dash.aov_inr == null ? "—" : `₹${dash.aov_inr}`],
    ["Repeat rate", dash.repeat_purchase_rate == null ? "—" : String(dash.repeat_purchase_rate)],
    ["Open leads", String(dash.open_leads)],
    ["Reviews waiting", String(dash.pending_reviews)],
  ];
  return <div className="grid gap-3 sm:grid-cols-4">{cards.map(([label, value]) => <div key={label} className="rounded-2xl bg-cream-100 p-4"><p className="spec">{label}</p><p className="mt-2 font-display text-2xl">{value}</p></div>)}</div>;
}

function Products() {
  const { notify } = useShop();
  const [rows, setRows] = useState<Product[]>([]);
  const [current, setCurrent] = useState<Product | null>(null);
  function load() { api<Product[]>("/admin/products").then(setRows); }
  useEffect(load, []);
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!current) return;
    const form = new FormData(event.currentTarget);
    const num = (key: string) => { const value = String(form.get(key) || ""); return value === "" ? null : Number(value); };
    const text = (key: string) => { const value = String(form.get(key) || ""); return value === "" ? null : value; };
    const body = {
      sku: current.sku, slug: current.slug, name: String(form.get("name")), flavor: String(form.get("flavor")), flavor_family: current.flavor_family,
      category_slug: current.category_slug, description: String(form.get("description")), status: String(form.get("status")), purchasable: form.get("purchasable") === "on",
      is_featured: current.is_featured, sort_order: current.sort_order, price_inr: num("price_inr"), mrp_inr: num("mrp_inr"), available: Number(form.get("available") || 0),
      serving_size: text("serving_size"), net_quantity: text("net_quantity"), ingredients: text("ingredients"), allergens: text("allergens"), storage: text("storage"),
      fssai_license: text("fssai_license"), manufacturer: text("manufacturer"), customer_care: text("customer_care"),
      protein_g: num("protein_g"), calories_kcal: num("calories_kcal"), carbs_g: num("carbs_g"), sugar_g: num("sugar_g"), fat_g: num("fat_g"), fibre_g: num("fibre_g"),
      occasions: current.occasions, dietary_labels: current.dietary_labels, image_url: text("image_url"), lab_report_url: text("lab_report_url"), seo_title: text("seo_title"), seo_description: text("seo_description"),
    };
    try {
      await api(`/admin/products/${current.id}`, { method: "PATCH", body: JSON.stringify(body) });
      notify("Product saved.");
      load();
    } catch (error) {
      const payload = error instanceof ApiError ? error.payload as { detail?: { missing?: string[] } } : null;
      notify(payload?.detail?.missing ? `Still missing: ${payload.detail.missing.join(", ")}` : error instanceof ApiError ? error.message : "Save failed.");
    }
  }
  return (
    <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
      <ul className="space-y-2 text-sm">{rows.map((row) => <li key={row.id}><button onClick={() => setCurrent(row)} className="text-left underline">{row.name}</button></li>)}</ul>
      {current && (
        <form key={current.id} onSubmit={save} className="grid gap-2 md:grid-cols-2">
          <input name="name" defaultValue={current.name} className="rounded-xl border px-3 py-2" />
          <input name="flavor" defaultValue={current.flavor} className="rounded-xl border px-3 py-2" />
          <textarea name="description" defaultValue={current.description} className="md:col-span-2 rounded-xl border px-3 py-2" />
          <input name="price_inr" placeholder="Price INR" defaultValue={current.price_inr ?? ""} className="rounded-xl border px-3 py-2" />
          <input name="mrp_inr" placeholder="MRP INR" defaultValue={current.mrp_inr ?? ""} className="rounded-xl border px-3 py-2" />
          <input name="available" placeholder="Stock" defaultValue={current.inventory.available} className="rounded-xl border px-3 py-2" />
          <input name="serving_size" placeholder="Serving size" defaultValue={current.serving_size ?? ""} className="rounded-xl border px-3 py-2" />
          <input name="net_quantity" placeholder="Net quantity" defaultValue={current.net_quantity ?? ""} className="rounded-xl border px-3 py-2" />
          <input name="protein_g" placeholder="Protein g" defaultValue={current.nutrition.protein_g ?? ""} className="rounded-xl border px-3 py-2" />
          <input name="calories_kcal" placeholder="kcal" defaultValue={current.nutrition.calories_kcal ?? ""} className="rounded-xl border px-3 py-2" />
          <input name="carbs_g" placeholder="Carbs g" defaultValue={current.nutrition.carbs_g ?? ""} className="rounded-xl border px-3 py-2" />
          <input name="sugar_g" placeholder="Sugar g" defaultValue={current.nutrition.sugar_g ?? ""} className="rounded-xl border px-3 py-2" />
          <input name="fat_g" placeholder="Fat g" defaultValue={current.nutrition.fat_g ?? ""} className="rounded-xl border px-3 py-2" />
          <input name="fibre_g" placeholder="Fibre g" defaultValue={current.nutrition.fibre_g ?? ""} className="rounded-xl border px-3 py-2" />
          <textarea name="ingredients" placeholder="Ingredients" defaultValue={current.ingredients ?? ""} className="md:col-span-2 rounded-xl border px-3 py-2" />
          <textarea name="allergens" placeholder="Allergens" defaultValue={current.allergens ?? ""} className="rounded-xl border px-3 py-2" />
          <textarea name="storage" placeholder="Storage" defaultValue={current.storage ?? ""} className="rounded-xl border px-3 py-2" />
          <input name="fssai_license" placeholder="FSSAI licence" defaultValue={current.fssai_license ?? ""} className="rounded-xl border px-3 py-2" />
          <input name="manufacturer" placeholder="Manufacturer" defaultValue={current.manufacturer ?? ""} className="rounded-xl border px-3 py-2" />
          <input name="customer_care" placeholder="Customer care" defaultValue={current.customer_care ?? ""} className="rounded-xl border px-3 py-2" />
          <input name="image_url" placeholder="Image URL" defaultValue={current.image_url ?? ""} className="rounded-xl border px-3 py-2" />
          <input name="lab_report_url" placeholder="Lab report URL" defaultValue={current.lab_report_url ?? ""} className="rounded-xl border px-3 py-2" />
          <input name="seo_title" placeholder="SEO title" defaultValue={current.seo_title ?? ""} className="rounded-xl border px-3 py-2" />
          <input name="seo_description" placeholder="SEO description" defaultValue={current.seo_description ?? ""} className="rounded-xl border px-3 py-2" />
          <select name="status" defaultValue={current.status} className="rounded-xl border px-3 py-2"><option value="draft">draft</option><option value="active">active</option><option value="archived">archived</option></select>
          <label className="flex items-center gap-2 text-sm"><input name="purchasable" type="checkbox" defaultChecked={current.purchasable} /> Purchasable</label>
          <button className="rounded-full bg-pine-900 py-3 text-cream-50 md:col-span-2">Save product</button>
        </form>
      )}
    </div>
  );
}

function Orders() {
  const [rows, setRows] = useState<{ number: string; status: string; payment_status: string; total_inr: string; name: string }[]>([]);
  function load() { api<typeof rows>("/admin/orders").then(setRows); }
  useEffect(load, []);
  return <ul className="space-y-3 text-sm">{rows.map((row) => <li key={row.number} className="rounded-2xl bg-cream-100 p-3">{row.number} · {row.name} · {row.status} · {row.payment_status} · {row.total_inr} <StatusButtons number={row.number} onDone={load} /></li>)}{rows.length === 0 && <li>No orders yet.</li>}</ul>;
}

function StatusButtons({ number, onDone }: { number: string; onDone: () => void }) {
  const { notify } = useShop();
  return <>{["confirmed", "processing", "packed", "shipped", "delivered", "cancelled", "refunded"].map((status) => <button key={status} className="ml-2 underline" onClick={async () => { try { await api(`/admin/orders/${number}`, { method: "PATCH", body: JSON.stringify({ status }) }); onDone(); } catch (error) { notify(error instanceof ApiError ? error.message : "Status change refused."); } }}>{status}</button>)}</>;
}

function JournalAdmin() {
  const [rows, setRows] = useState<{ id: number; title: string; status: string }[]>([]);
  useEffect(() => { api<typeof rows>("/admin/posts").then(setRows); }, []);
  return <ul className="text-sm">{rows.map((row) => <li key={row.id}>{row.title} · {row.status}</li>)}</ul>;
}

function Leads() {
  const [rows, setRows] = useState<{ id: number; company: string; name: string; requirement: string; status: string }[]>([]);
  useEffect(() => { api<typeof rows>("/admin/leads").then(setRows); }, []);
  return <ul className="space-y-2 text-sm">{rows.map((row) => <li key={row.id}>{row.company} · {row.name} · {row.requirement} · {row.status}</li>)}{rows.length === 0 && <li>No corporate leads yet.</li>}</ul>;
}

function Reviews() {
  const { notify } = useShop();
  const [rows, setRows] = useState<{ id: number; author_name: string; body: string; status: string }[]>([]);
  function load() { api<typeof rows>("/admin/reviews").then(setRows); }
  useEffect(load, []);
  return <ul className="space-y-3 text-sm">{rows.map((row) => <li key={row.id} className="rounded-2xl bg-cream-100 p-3">{row.author_name}: {row.body} <button className="ml-2 underline" onClick={async () => { await api(`/admin/reviews/${row.id}?status=approved`, { method: "PATCH" }); notify("Approved."); load(); }}>Approve</button></li>)}{rows.length === 0 && <li>No reviews in the queue. None are seeded.</li>}</ul>;
}

function Settings() {
  const { notify } = useShop();
  const [key, setKey] = useState("home");
  const [text, setText] = useState("");
  useEffect(() => { api<{ value: unknown }>(`/admin/settings/${key}`).then((row) => setText(JSON.stringify(row.value, null, 2))); }, [key]);
  return (
    <form onSubmit={async (event) => { event.preventDefault(); try { await api(`/admin/settings/${key}`, { method: "PUT", body: JSON.stringify({ value: JSON.parse(text) }) }); notify("Saved."); } catch { notify("That JSON could not be saved."); } }}>
      <select value={key} onChange={(event) => setKey(event.target.value)} className="rounded-xl border px-3 py-2">{["home", "commerce", "merchandising", "company", "story"].map((item) => <option key={item}>{item}</option>)}</select>
      <textarea value={text} onChange={(event) => setText(event.target.value)} className="mt-3 h-80 w-full rounded-2xl border p-3 font-mono text-xs" />
      <button className="mt-3 rounded-full bg-pine-900 px-5 py-3 text-sm text-cream-50">Save settings</button>
    </form>
  );
}
