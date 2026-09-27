export type Nutrition = {
  protein_g: number | null;
  calories_kcal: number | null;
  carbs_g: number | null;
  sugar_g: number | null;
  fat_g: number | null;
  fibre_g: number | null;
  status: "verified" | "pending_verification";
};

export type Product = {
  id: number;
  sku: string;
  slug: string;
  name: string;
  flavor: string;
  flavor_family: string;
  category_slug: string;
  category_name: string;
  description: string;
  status: string;
  purchasable: boolean;
  is_featured: boolean;
  price_inr: string | null;
  mrp_inr: string | null;
  pack_size: number | null;
  net_quantity: string | null;
  serving_size: string | null;
  ingredients: string | null;
  allergens: string | null;
  storage: string | null;
  fssai_license: string | null;
  manufacturer: string | null;
  customer_care: string | null;
  nutrition: Nutrition;
  occasions: string[];
  dietary_labels: string[];
  image_url: string | null;
  lab_report_url: string | null;
  seo_title: string | null;
  seo_description: string | null;
  spec_status: string;
  sort_order: number;
  rating_avg: number | null;
  review_count: number;
  inventory: { available: number; reserved: number; low_stock_threshold: number };
  ingredient_rows?: { name: string; note: string | null }[];
  batches?: { batch_number: string; manufacturing_date: string | null; expiry_date: string | null }[];
  reviews?: Review[];
};

export type Review = {
  id: number;
  author_name: string;
  rating: number;
  body: string;
  verified_purchase: boolean;
  created_at?: string;
};

export type CartLine = {
  id: number;
  product_id: number;
  slug: string;
  name: string;
  flavor: string;
  flavor_family: string;
  quantity: number;
  saved_for_later: boolean;
  purchasable?: boolean;
  unit_price_inr?: string | null;
  line_total_inr?: string | null;
};

export type Cart = {
  items: CartLine[];
  saved: CartLine[];
  coupon_code: string | null;
  coupon_note: string | null;
  priced: boolean;
  subtotal_inr: string | null;
  discount_inr: string | null;
  shipping_inr: string | null;
  total_inr: string | null;
  shipping_message: string;
  shipping_progress: number | null;
  selling_enabled: boolean;
  suggestions?: Product[];
};

export type User = {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  role: string;
  referral_code: string;
  points_balance: number;
};

export type HomeContent = {
  eyebrow: string;
  hero_line_1: string;
  hero_line_2: string;
  hero_support: string;
  announcement: string;
  primary_cta: string;
  secondary_cta: string;
  tertiary_cta: string;
  category_heading: string;
  featured_heading: string;
  transparency_heading: string;
  box_heading: string;
  corporate_line: string;
  newsletter_heading: string;
  newsletter_cta: string;
  occasions: { id: string; title: string; copy: string; href: string }[];
};

export type Config = {
  home: HomeContent;
  story: { heading: string; chapters: { id: string; title: string; body: string }[] };
  merchandising: {
    box_sizes: number[];
    subscription_cadence_days: number[];
    ticker_live: string[];
    ticker_when_verified: string[];
    claims_verified: boolean;
  };
  commerce: {
    selling_enabled: boolean;
    free_shipping_threshold_inr: number | null;
    shipping_fee_inr: number | null;
    max_qty_per_line: number;
  };
  company: {
    legal_name: string | null;
    support_email: string | null;
    phone: string | null;
    instagram: string | null;
    facebook: string | null;
    youtube: string | null;
    linkedin: string | null;
  };
  payments_configured: boolean;
  ga_measurement_id: string | null;
};

export type Session = { csrf: string; user: User | null; cart: Cart; config: Config };

export type Bundle = {
  slug: string;
  name: string;
  description: string;
  price_inr: string | null;
  items: { product_id: number; slug: string; name: string; flavor: string; quantity: number; flavor_family: string }[];
};

export type Post = {
  slug: string;
  title: string;
  excerpt: string;
  category: string;
  published_at: string | null;
  seo_title: string | null;
  seo_description: string | null;
  author: string;
  body?: string;
};

export type PageDoc = { slug: string; title: string; body: string; notice: string | null; seo_title: string | null; seo_description: string | null };
