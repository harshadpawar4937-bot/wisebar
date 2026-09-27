export function formatINR(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") return "Price pending";
  const amount = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(amount)) return "Price pending";
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(amount);
}

export function nutritionText(value: number | null | undefined, suffix: string): string {
  if (value === null || value === undefined) return "Pending";
  return `${value}${suffix}`;
}

export function discountLabel(price: string | null, mrp: string | null): string | null {
  if (!price || !mrp) return null;
  const p = Number(price);
  const m = Number(mrp);
  if (!m || p >= m) return null;
  return `${Math.round(((m - p) / m) * 100)}% off`;
}
