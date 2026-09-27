import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion, useReducedMotion } from "framer-motion";
import { api } from "../lib/api";
import { track } from "../lib/analytics";
import { formatINR } from "../lib/format";
import { useShop } from "../shop";
import type { Bundle, Product } from "../types";
import { ProductArt } from "../components/Brand";
import { ProductCard } from "../components/ProductCard";
import { Seo } from "../components/Seo";

const stageColor: Record<string, string> = {
  cocoa: "bg-[#3B2418] text-[#F6E7C8]",
  nut: "bg-[#E39B2B] text-[#3B2418]",
  fruit: "bg-[#B94A48] text-[#FFF4F1]",
  grain: "bg-[#E7D3A4] text-[#12392C]",
  seed: "bg-[#134536] text-[#D6F25C]",
};

export function HomePage() {
  const { config, notify } = useShop();
  const reduced = useReducedMotion();
  const [products, setProducts] = useState<Product[]>([]);
  const [bundles, setBundles] = useState<Bundle[]>([]);
  const [email, setEmail] = useState("");
  useEffect(() => {
    api<Product[]>("/products?sort=featured").then((rows) => setProducts(rows.filter((row) => row.is_featured))).catch(() => undefined);
    api<Bundle[]>("/bundles").then(setBundles).catch(() => undefined);
  }, []);
  if (!config) return <div className="px-4 py-20 text-sm">Opening the shelf…</div>;
  const line1 = config.home.hero_line_1.includes("Smart Protein") ? "Out the door." : config.home.hero_line_1;
  const line2 = config.home.hero_line_2.includes("Smarter") ? "On the table." : config.home.hero_line_2;
  const support = config.home.hero_support.includes("High-protein bars and muesli made")
    ? "Protein bars for the bag. Muesli for the bowl. Pick a flavour and take it with you."
    : config.home.hero_support;
  const bars = products.filter((product) => product.category_slug === "protein-bars");
  const muesli = products.filter((product) => product.category_slug === "protein-muesli");
  return (
    <>
      <Seo title="WISEBAR™ — SMART PROTEIN. SMARTER EVERY DAY.." description={support} path="/" jsonLd={{ "@context": "https://schema.org", "@type": "Organization", name: "WISEBAR", slogan: "Out the door. On the table." }} />
      <section className="hero-mesh overflow-hidden">
        <div className="mx-auto grid max-w-6xl items-center gap-5 px-4 pb-6 pt-4 sm:grid-cols-2 sm:gap-8 sm:pb-10 lg:min-h-[calc(100svh-8rem)] lg:pb-16">
          <div>
            <p className="spec text-pine-700">The WISEBAR shelf</p>
            <h1 className="mt-2 font-display text-5xl font-semibold leading-[0.9] text-pine-950 sm:text-6xl lg:text-8xl">
              <motion.span className="block" initial={reduced ? false : { y: 28, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.6 }}>{line1}</motion.span>
              <motion.span className="mt-1 block text-pine-700" initial={reduced ? false : { y: 28, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ duration: 0.6, delay: 0.12 }}>{line2}</motion.span>
            </h1>
            <p className="mt-3 max-w-md text-base text-ink/80 sm:mt-5 sm:text-lg">{support}</p>
            <div className="mt-5 flex flex-wrap gap-3 sm:mt-8">
              <Link to="/protein-bars" className="rounded-full bg-lime px-5 py-3 text-sm font-semibold text-pine-950">Shop bars</Link>
              <Link to="/protein-muesli" className="rounded-full border border-pine-900 px-5 py-3 text-sm font-semibold">Shop muesli</Link>
            </div>
          </div>
          <HeroStage products={products} />
        </div>
      </section>

      <ProductMarquee products={products} />

      <section className="grid md:grid-cols-2">
        <AdCard
          href="/protein-bars"
          kicker="Bar drop"
          title="Protein that leaves with you."
          copy="Cocoa, peanut, berry. One bar, wherever the day goes."
          family={bars[0]?.flavor_family || "cocoa"}
          className="bg-[#3B2418] text-[#F6E7C8]"
          cta="Shop the bars"
        />
        <AdCard
          href="/protein-muesli"
          kicker="Breakfast drop"
          title="A bowl before the rush."
          copy="Grain and nut-seed muesli for the morning you actually sit down."
          family={muesli[0]?.flavor_family || "grain"}
          className="bg-[#E7D3A4] text-[#12392C]"
          cta="Shop the muesli"
          flip
        />
      </section>

      <section className="mx-auto max-w-6xl px-4 py-16">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="spec">On the shelf</p>
            <h2 className="mt-2 font-display text-4xl sm:text-5xl">Shop the flavours.</h2>
          </div>
          <Link to="/protein-bars" className="text-sm underline">All bars</Link>
        </div>
        <div className="mt-8 flex gap-4 overflow-x-auto pb-4 snap-x snap-mandatory md:grid md:grid-cols-3 md:overflow-visible">
          {products.map((product, index) => (
            <motion.div key={product.id} className="min-w-[260px] snap-start md:min-w-0" initial={reduced ? false : { opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.3 }} transition={{ delay: index * 0.06 }}>
              <ProductCard product={product} />
            </motion.div>
          ))}
        </div>
      </section>

      <section className="bg-pine-950 py-14 text-cream-50">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="font-display text-4xl">Pick by colour. Eat by mood.</h2>
          <div className="mt-6 flex gap-4 overflow-x-auto pb-2">
            {products.map((product) => (
              <Link key={product.id} to={`/products/${product.slug}`} className={`shelf-card flex w-64 shrink-0 flex-col rounded-[28px] p-4 ${stageColor[product.flavor_family] || "bg-pine-800"}`}>
                <ProductArt family={product.flavor_family} className="w-full rounded-2xl" />
                <p className="mt-4 font-display text-3xl leading-none">{product.flavor}</p>
                <p className="mt-2 text-sm opacity-80">{product.category_name}</p>
                <p className="mt-3 text-sm font-semibold">{formatINR(product.price_inr)}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl items-center gap-8 px-4 py-16 lg:grid-cols-2">
        <div>
          <p className="spec">Make a box</p>
          <h2 className="mt-2 font-display text-5xl">Your flavours. One box.</h2>
          <p className="mt-4 max-w-md text-ink/75">6, 12, 18, or 24. Mix the bars you want. The total appears once prices are published.</p>
          <Link to="/build-your-box" className="mt-6 inline-flex rounded-full bg-pine-900 px-5 py-3 text-sm font-semibold text-cream-50">Build my box</Link>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {(bars.length ? bars : products).slice(0, 3).map((product, index) => (
            <motion.div key={product.id} className="rounded-3xl bg-cream-100 p-2" animate={reduced ? undefined : { y: [0, -8, 0] }} transition={{ duration: 3.4 + index, repeat: Infinity, ease: "easeInOut" }}>
              <ProductArt family={product.flavor_family} className="rounded-2xl" />
            </motion.div>
          ))}
        </div>
      </section>

      <section className="bg-[#F3E6C4] py-14">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="font-display text-4xl">Bundles, ready to grab.</h2>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {bundles.map((bundle) => (
              <article key={bundle.slug} className="rounded-[28px] bg-cream-50 p-5">
                <p className="spec">Offer</p>
                <h3 className="mt-2 font-display text-2xl">{bundle.name}</h3>
                <p className="mt-2 text-sm text-ink/70">{bundle.description}</p>
                <ul className="mt-3 text-sm">{bundle.items.map((item) => <li key={item.slug}><Link className="underline" to={`/products/${item.slug}`}>{item.flavor}</Link></li>)}</ul>
                <p className="mt-4 font-display">{bundle.price_inr ? formatINR(bundle.price_inr) : "Price set in the shop admin"}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-12">
        <h2 className="font-display text-3xl">Where it goes</h2>
        <div className="mt-4 flex gap-3 overflow-x-auto pb-2">
          {config.home.occasions.map((item) => (
            <Link key={item.id} to={item.href} className="min-w-[200px] rounded-full border border-pine-900 px-4 py-3 text-sm">
              <span className="font-semibold">{item.title}.</span> {item.copy}
            </Link>
          ))}
        </div>
      </section>

      <Finder />

      <section className="bg-lime py-12">
        <form className="mx-auto flex max-w-3xl flex-col gap-3 px-4 md:flex-row md:items-center" onSubmit={async (event: FormEvent) => {
          event.preventDefault();
          await api("/newsletter", { method: "POST", body: JSON.stringify({ email }) });
          track("newsletter_signup");
          setEmail("");
          notify("You're on the list. We'll write when a flavour drops.");
        }}>
          <h2 className="flex-1 font-display text-3xl sm:text-4xl">New flavours, first.</h2>
          <input aria-label="Email" required type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Email address" className="rounded-full px-4 py-3 text-sm" />
          <button className="rounded-full bg-pine-950 px-5 py-3 text-sm font-semibold text-cream-50">Join the list</button>
        </form>
      </section>
    </>
  );
}

function HeroStage({ products }: { products: Product[] }) {
  const reduced = useReducedMotion();
  const [index, setIndex] = useState(0);
  useEffect(() => {
    if (reduced || products.length < 2) return;
    const timer = window.setInterval(() => setIndex((value) => (value + 1) % products.length), 3200);
    return () => window.clearInterval(timer);
  }, [products.length, reduced]);
  const product = products[index];
  return (
    <div className="relative">
      <div className="relative overflow-hidden rounded-[28px] bg-pine-950 p-3 text-cream-50 shadow-card sm:p-4">
        <div className="flex items-center justify-between">
          <p className="spec text-lime">Now showing</p>
          <p className="text-xs text-cream-50/60">{products.length ? `${index + 1} / ${products.length}` : "—"}</p>
        </div>
        {product && (
          <motion.div key={product.slug} initial={reduced ? false : { opacity: 0.4, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
            <Link to={`/products/${product.slug}`} className="mt-3 block">
              <div className="rounded-[22px] bg-cream-50 p-2">
                <ProductArt family={product.flavor_family} className={`mx-auto w-40 rounded-2xl sm:w-48 ${reduced ? "" : "float-y"}`} />
              </div>
              <div className="mt-3 flex items-end justify-between gap-3">
                <div>
                  <p className={`inline-flex rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-widest ${stageColor[product.flavor_family] || "bg-pine-800 text-cream-50"}`}>{product.category_name}</p>
                  <p className="mt-2 font-display text-3xl leading-none">{product.flavor}</p>
                  <p className="mt-1 text-sm text-cream-50/75">{formatINR(product.price_inr)}</p>
                </div>
                <span className="shrink-0 rounded-full bg-lime px-4 py-2 text-xs font-semibold text-pine-950">View</span>
              </div>
            </Link>
          </motion.div>
        )}
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {products.map((item, itemIndex) => (
          <button key={item.id} aria-label={`Show ${item.flavor}`} onClick={() => setIndex(itemIndex)} className={`h-3 w-3 rounded-full ${itemIndex === index ? "bg-pine-900" : "bg-cream-200"}`} />
        ))}
      </div>
    </div>
  );
}

function ProductMarquee({ products }: { products: Product[] }) {
  const row = products.length ? [...products, ...products] : [];
  if (!row.length) return null;
  return (
    <div className="overflow-hidden border-y border-pine-900/10 bg-pine-900 py-3 text-cream-50">
      <div className="ticker-track">
        {row.map((product, index) => (
          <Link key={`${product.slug}-${index}`} to={`/products/${product.slug}`} className="mx-6 font-display text-lg">
            {product.flavor} <span className="text-lime">/</span> {product.category_name}
          </Link>
        ))}
      </div>
    </div>
  );
}

function AdCard({ href, kicker, title, copy, family, className, cta, flip = false }: { href: string; kicker: string; title: string; copy: string; family: string; className: string; cta: string; flip?: boolean }) {
  return (
    <Link to={href} className={`group grid items-center gap-6 overflow-hidden p-6 sm:grid-cols-2 sm:p-10 ${className}`}>
      <div className={flip ? "sm:order-2" : ""}>
        <p className="spec opacity-70">{kicker}</p>
        <h2 className="mt-3 max-w-md font-display text-4xl leading-[0.92] sm:text-5xl">{title}</h2>
        <p className="mt-4 max-w-sm text-sm opacity-80">{copy}</p>
        <span className="mt-6 inline-flex w-fit rounded-full bg-lime px-5 py-3 text-sm font-semibold text-pine-950">{cta}</span>
      </div>
      <div className={`mx-auto w-36 sm:w-48 ${flip ? "float-y-delay" : "float-y"}`}>
        <ProductArt family={family} className="rounded-[28px] transition-transform duration-500 group-hover:scale-105" />
      </div>
    </Link>
  );
}

function Finder() {
  const reduced = useReducedMotion();
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState({ occasion: "work", taste: "any", protein: "any", budget: "any" });
  const [products, setProducts] = useState<Product[]>([]);
  const [notes, setNotes] = useState<string[]>([]);
  const steps = [
    { key: "occasion", label: "When are you eating?", options: ["morning", "work", "pre-workout", "post-workout", "travel", "evening"] },
    { key: "taste", label: "Which flavour lane?", options: ["any", "cocoa", "nut", "fruit", "grain", "seed"] },
  ] as const;
  async function finish(next: typeof answers) {
    const result = await api<{ products: Product[]; notes: string[] }>("/recommendations", { method: "POST", body: JSON.stringify(next) });
    setProducts(result.products);
    setNotes(result.notes);
    setStep(2);
  }
  const current = steps[step];
  return (
    <section className="mx-auto max-w-6xl px-4 py-16">
      <p className="spec">Help me pick</p>
      <h2 className="mt-2 font-display text-4xl">Two questions. Then the shelf.</h2>
      {current && (
        <div className="mt-6">
          <p className="font-display text-2xl">{current.label}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {current.options.map((option) => (
              <button key={option} className="rounded-full border border-pine-900 px-4 py-2 text-sm capitalize" onClick={() => {
                const next = { ...answers, [current.key]: option };
                setAnswers(next);
                if (step === 1) finish(next);
                else setStep(1);
              }}>{option}</button>
            ))}
          </div>
        </div>
      )}
      {step === 2 && (
        <motion.div className="mt-8" initial={reduced ? false : { opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          {notes.map((note) => <p key={note} className="mb-3 text-sm text-ink/70">{note}</p>)}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {products.slice(0, 3).map((product) => (
              <Link key={product.id} to={`/products/${product.slug}`} onClick={() => track("recommendation_click", { slug: product.slug })} className={`rounded-[28px] p-4 ${stageColor[product.flavor_family] || "bg-cream-100"}`}>
                <ProductArt family={product.flavor_family} className="rounded-2xl" />
                <h3 className="mt-3 font-display text-2xl">{product.flavor}</h3>
              </Link>
            ))}
          </div>
          <button className="mt-4 text-sm underline" onClick={() => setStep(0)}>Start again</button>
        </motion.div>
      )}
    </section>
  );
}
