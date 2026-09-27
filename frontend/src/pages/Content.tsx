import { FormEvent, useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api, ApiError } from "../lib/api";
import { track } from "../lib/analytics";
import { useShop } from "../shop";
import type { PageDoc, Post, Product, User } from "../types";
import { RichText } from "../components/RichText";
import { Seo } from "../components/Seo";
import { ProductCard } from "../components/ProductCard";

export function AboutPage() {
  const { config } = useShop();
  return (
    <div className="mx-auto max-w-3xl px-4 py-16">
      <Seo title="About · WISEBAR" description="Why WISEBAR exists, told only from what the company has published." path="/about" />
      <p className="spec">About</p>
      <h1 className="mt-2 font-display text-6xl">Why WISE?</h1>
      <p className="mt-4 text-lg text-ink/75">Smart protein for ordinary days — work, training, travel, breakfast. The chapters below stay short until the founders put their own account on record.</p>
      <ol className="mt-10 space-y-8">
        {config?.story.chapters.map((chapter) => (
          <li key={chapter.id}><h2 className="font-display text-3xl">{chapter.title}</h2><p className="mt-2 text-ink/75">{chapter.body}</p></li>
        ))}
      </ol>
    </div>
  );
}

export function JournalPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [category, setCategory] = useState("");
  useEffect(() => { api<Post[]>(`/blog${category ? `?category=${encodeURIComponent(category)}` : ""}`).then(setPosts); }, [category]);
  const categories = ["Protein", "Breakfast", "Fitness", "Lifestyle", "Nutrition", "Recipes", "WISEBAR Stories"];
  return (
    <div className="mx-auto max-w-6xl px-4 py-12">
      <Seo title="Journal · WISEBAR" description="Food education from WISEBAR. Not medical advice." path="/journal" />
      <h1 className="font-display text-6xl">Journal</h1>
      <div className="mt-6 flex flex-wrap gap-2">{categories.map((item) => <button key={item} onClick={() => setCategory(item === category ? "" : item)} className={`rounded-full px-3 py-1 text-sm ${category === item ? "bg-pine-900 text-cream-50" : "border"}`}>{item}</button>)}</div>
      <div className="mt-8 grid gap-4 md:grid-cols-3">
        {posts.map((post) => <Link key={post.slug} to={`/journal/${post.slug}`} className="rounded-3xl bg-cream-100 p-5"><p className="spec">{post.category}</p><h2 className="mt-2 font-display text-2xl">{post.title}</h2><p className="mt-2 text-sm">{post.excerpt}</p></Link>)}
      </div>
      {posts.length === 0 && <p className="mt-6 text-sm">No published articles in that category yet.</p>}
    </div>
  );
}

export function JournalPostPage() {
  const { slug = "" } = useParams();
  const [post, setPost] = useState<Post | null>(null);
  const [missing, setMissing] = useState(false);
  useEffect(() => { api<Post>(`/blog/${slug}`).then(setPost).catch(() => setMissing(true)); }, [slug]);
  if (missing) return <p className="px-4 py-16">Article not found.</p>;
  if (!post) return null;
  return (
    <article className="mx-auto max-w-2xl px-4 py-12">
      <Seo title={post.seo_title || post.title} description={post.seo_description || post.excerpt} path={`/journal/${post.slug}`} jsonLd={{ "@context": "https://schema.org", "@type": "Article", headline: post.title, datePublished: post.published_at, author: post.author }} />
      <p className="spec">{post.category}</p>
      <h1 className="mt-2 font-display text-5xl">{post.title}</h1>
      <p className="mt-3 text-sm text-ink/60">{post.author}{post.published_at ? ` · ${post.published_at}` : ""}</p>
      <div className="mt-8">{post.body && <RichText text={post.body} />}</div>
    </article>
  );
}

export function CorporatePage() {
  const { notify } = useShop();
  const [done, setDone] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const body = Object.fromEntries(new FormData(event.currentTarget).entries());
    try {
      await api("/corporate/leads", { method: "POST", body: JSON.stringify(body) });
      track("corporate_lead");
      setDone(true);
    } catch (error) {
      notify(error instanceof ApiError ? error.message : "Could not send the enquiry.");
    }
  }
  return (
    <div className="mx-auto grid max-w-6xl gap-10 px-4 py-12 lg:grid-cols-2">
      <Seo title="Corporate · WISEBAR" description="Better snacking for better workdays." path="/corporate" />
      <div>
        <p className="spec">Corporate</p>
        <h1 className="mt-2 font-display text-5xl">Better snacking for better workdays.</h1>
        <p className="mt-4 text-ink/75">Make smarter snacking part of the workday. Corporate boxes, wellness packs, bulk orders, custom branding, event hampers, and pantry supply — quoted by the team, not checked out blindly.</p>
      </div>
      {done ? <p className="rounded-3xl bg-cream-100 p-6">Request received. Someone will reply with a quote. This is not an order.</p> : (
        <form onSubmit={submit} className="grid gap-3">
          <input name="company" required placeholder="Company" className="rounded-2xl border px-4 py-3" />
          <input name="name" required placeholder="Your name" className="rounded-2xl border px-4 py-3" />
          <input name="email" type="email" required placeholder="Work email" className="rounded-2xl border px-4 py-3" />
          <input name="phone" required pattern="[6-9][0-9]{9}" placeholder="Mobile" className="rounded-2xl border px-4 py-3" />
          <input name="employee_count" required placeholder="Employee count" className="rounded-2xl border px-4 py-3" />
          <input name="requirement" required placeholder="Requirement" className="rounded-2xl border px-4 py-3" />
          <input name="expected_quantity" required placeholder="Expected quantity" className="rounded-2xl border px-4 py-3" />
          <textarea name="message" required minLength={4} placeholder="Message" className="rounded-2xl border px-4 py-3" />
          <button className="rounded-full bg-pine-900 py-3 text-cream-50">Request corporate quote</button>
        </form>
      )}
    </div>
  );
}

export function ContactPage() {
  const { notify, config } = useShop();
  const [done, setDone] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const body = Object.fromEntries(new FormData(event.currentTarget).entries());
    try {
      await api("/contact", { method: "POST", body: JSON.stringify(body) });
      setDone(true);
    } catch (error) {
      notify(error instanceof ApiError ? error.message : "Message failed.");
    }
  }
  return (
    <div className="mx-auto max-w-xl px-4 py-12">
      <Seo title="Contact · WISEBAR" description="Write to WISEBAR." path="/contact" />
      <h1 className="font-display text-5xl">Contact</h1>
      <p className="mt-3 text-sm text-ink/70">{config?.company.support_email ? config.company.support_email : "Messages are stored for the team. A public support email will be listed once it exists."}</p>
      {done ? <p className="mt-6">Received. Thank you.</p> : (
        <form onSubmit={submit} className="mt-6 grid gap-3">
          <input name="name" required placeholder="Name" className="rounded-2xl border px-4 py-3" />
          <input name="email" type="email" required placeholder="Email" className="rounded-2xl border px-4 py-3" />
          <input name="phone" placeholder="Mobile" className="rounded-2xl border px-4 py-3" />
          <input name="topic" required placeholder="Topic" className="rounded-2xl border px-4 py-3" />
          <textarea name="message" required minLength={4} placeholder="Message" className="rounded-2xl border px-4 py-3" />
          <button className="rounded-full bg-pine-900 py-3 text-cream-50">Send</button>
        </form>
      )}
    </div>
  );
}

export function FaqPage() {
  const [faqs, setFaqs] = useState<{ id: number; question: string; answer: string }[]>([]);
  useEffect(() => { api<typeof faqs>("/faqs").then(setFaqs); }, []);
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <Seo title="FAQ · WISEBAR" description="Questions about WISEBAR." path="/faq" jsonLd={{ "@context": "https://schema.org", "@type": "FAQPage", mainEntity: faqs.map((faq) => ({ "@type": "Question", name: faq.question, acceptedAnswer: { "@type": "Answer", text: faq.answer } })) }} />
      <h1 className="font-display text-5xl">FAQ</h1>
      <div className="mt-8 space-y-3">{faqs.map((faq) => <details key={faq.id} className="rounded-2xl bg-cream-100 p-4"><summary className="cursor-pointer font-medium">{faq.question}</summary><p className="mt-2 text-sm text-ink/75">{faq.answer}</p></details>)}</div>
    </div>
  );
}

export function LegalPage({ slug }: { slug: string }) {
  const [page, setPage] = useState<PageDoc | null>(null);
  useEffect(() => { api<PageDoc>(`/pages/${slug}`).then(setPage); }, [slug]);
  if (!page) return null;
  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <Seo title={page.seo_title || page.title} description={page.seo_description || page.title} path={`/${slug}`} />
      <h1 className="font-display text-5xl">{page.title}</h1>
      {page.notice && <p className="mt-4 rounded-2xl bg-mango/10 p-4 text-sm">{page.notice}</p>}
      <div className="mt-6"><RichText text={page.body} /></div>
      {slug === "shipping" && <TrackBox />}
    </div>
  );
}

function TrackBox() {
  const [result, setResult] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const body = Object.fromEntries(new FormData(event.currentTarget).entries());
    try {
      const order = await api<{ number: string; status: string; payment_status: string }>("/orders/track", { method: "POST", body: JSON.stringify(body) });
      setResult(`${order.number} · ${order.status} · payment ${order.payment_status}`);
    } catch (error) {
      setResult(error instanceof ApiError ? error.message : "Not found.");
    }
  }
  return (
    <form id="track" onSubmit={submit} className="mt-8 grid gap-2 rounded-3xl bg-cream-100 p-4">
      <h2 className="font-display text-2xl">Track an order</h2>
      <input name="number" required placeholder="Order number" className="rounded-2xl px-4 py-3" />
      <input name="phone" required pattern="[6-9][0-9]{9}" placeholder="Mobile" className="rounded-2xl px-4 py-3" />
      <button className="rounded-full bg-pine-900 py-3 text-cream-50">Track</button>
      {result && <p className="text-sm">{result}</p>}
    </form>
  );
}

export function AccountPage() {
  const shop = useShop();
  const [params] = useSearchParams();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [tab, setTab] = useState("profile");
  if (!shop.user) {
    return (
      <div className="mx-auto max-w-md px-4 py-12">
        <Seo title="Account · WISEBAR" description="Sign in to WISEBAR." path="/account" />
        <h1 className="font-display text-5xl">{mode === "login" ? "Sign in" : "Create account"}</h1>
        <form className="mt-6 grid gap-3" onSubmit={async (event) => {
          event.preventDefault();
          const body = Object.fromEntries(new FormData(event.currentTarget).entries());
          try {
            await api(mode === "login" ? "/auth/login" : "/auth/register", { method: "POST", body: JSON.stringify(body) });
            await shop.refresh();
          } catch (error) {
            shop.notify(error instanceof ApiError ? error.message : "Could not sign in.");
          }
        }}>
          {mode === "register" && <input name="name" required placeholder="Name" className="rounded-2xl border px-4 py-3" />}
          <input name="email" type="email" required placeholder="Email" className="rounded-2xl border px-4 py-3" />
          <input name="password" type="password" required minLength={8} placeholder="Password" className="rounded-2xl border px-4 py-3" />
          <button className="rounded-full bg-pine-900 py-3 text-cream-50">{mode === "login" ? "Sign in" : "Register"}</button>
        </form>
        <button className="mt-4 text-sm underline" onClick={() => setMode(mode === "login" ? "register" : "login")}>{mode === "login" ? "Need an account?" : "Have an account?"}</button>
        <Forgot />
      </div>
    );
  }
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <Seo title="Account · WISEBAR" description="Your WISEBAR account." path="/account" />
      <div className="flex items-center justify-between">
        <h1 className="font-display text-4xl">{shop.user.name}</h1>
        <button className="text-sm underline" onClick={async () => { await api("/auth/logout", { method: "POST" }); await shop.refresh(); }}>Log out</button>
      </div>
      {params.get("intent") === "subscribe" && <p className="mt-4 text-sm">Subscriptions can be started once selling is on and a product is purchasable. Pause, skip, and cancel stay available after that. No lock-in.</p>}
      <div className="mt-6 flex flex-wrap gap-2 text-sm">{["profile", "orders", "subscriptions", "wishlist", "addresses", "rewards", "referrals"].map((item) => <button key={item} onClick={() => setTab(item)} className={`rounded-full px-3 py-1 capitalize ${tab === item ? "bg-pine-900 text-cream-50" : "border"}`}>{item}</button>)}</div>
      <div className="mt-6"><AccountPanel tab={tab} user={shop.user} /></div>
    </div>
  );
}

function Forgot() {
  const { notify } = useShop();
  return (
    <form className="mt-8 grid gap-2" onSubmit={async (event) => {
      event.preventDefault();
      const email = new FormData(event.currentTarget).get("email");
      const result = await api<{ detail: string; dev_reset_token?: string }>("/auth/forgot", { method: "POST", body: JSON.stringify({ email }) });
      notify(result.dev_reset_token ? `Email is not configured. Dev reset token: ${result.dev_reset_token}` : result.detail);
    }}>
      <p className="text-sm">Forgot password</p>
      <input name="email" type="email" required placeholder="Email" className="rounded-2xl border px-4 py-3" />
      <button className="text-left text-sm underline">Send reset</button>
    </form>
  );
}

function AccountPanel({ tab, user }: { tab: string; user: User }) {
  const [data, setData] = useState<unknown>(null);
  useEffect(() => {
    const path = tab === "orders" ? "/orders/mine" : tab === "subscriptions" ? "/subscriptions" : tab === "wishlist" ? "/wishlist" : tab === "addresses" ? "/users/me/addresses" : tab === "rewards" ? "/rewards" : tab === "referrals" ? "/referrals" : "";
    if (!path) { setData(null); return; }
    api(path).then(setData).catch(() => setData(null));
  }, [tab]);
  if (tab === "profile") return <p className="text-sm">{user.email}<br />{user.phone || "No mobile stored"}<br />Wise Points: {user.points_balance}</p>;
  if (tab === "wishlist" && Array.isArray(data)) return <div className="grid gap-4 md:grid-cols-2">{(data as Product[]).map((product) => <ProductCard key={product.id} product={product} />)}{(data as Product[]).length === 0 && <p>No saved products on this account yet. A browser wishlist is kept on this device until you sign in and save again.</p>}</div>;
  return <pre className="overflow-auto rounded-2xl bg-cream-100 p-4 text-xs">{JSON.stringify(data ?? { referral_code: user.referral_code }, null, 2)}</pre>;
}

export function NotFoundPage() {
  return <div className="px-4 py-24 text-center"><h1 className="font-display text-5xl">That page is not on the menu.</h1><Link to="/" className="mt-4 inline-flex underline">Back home</Link></div>;
}
