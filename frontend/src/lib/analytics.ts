import { api } from "./api";

export function track(name: string, payload: Record<string, unknown> = {}) {
  const ga = (window as Window & { gtag?: (...args: unknown[]) => void }).gtag;
  ga?.("event", name, payload);
  api("/analytics/events", { method: "POST", body: JSON.stringify({ name, payload }) }).catch(() => undefined);
}

export function loadAnalytics(measurementId: string | null) {
  if (!measurementId || document.getElementById("ga4")) return;
  const script = document.createElement("script");
  script.id = "ga4";
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(measurementId)}`;
  document.head.appendChild(script);
  const inline = document.createElement("script");
  inline.text = `window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','${measurementId}');`;
  document.head.appendChild(inline);
}
