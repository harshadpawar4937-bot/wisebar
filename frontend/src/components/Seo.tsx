import { useEffect } from "react";

export function Seo({ title, description, path = "/", jsonLd }: { title: string; description: string; path?: string; jsonLd?: unknown }) {
  const encoded = jsonLd ? JSON.stringify(jsonLd) : "";
  useEffect(() => {
    document.title = title;
    setMeta("description", description);
    setMeta("og:title", title, true);
    setMeta("og:description", description, true);
    setMeta("twitter:title", title);
    setMeta("twitter:description", description);
    const canonical = document.querySelector<HTMLLinkElement>("link[rel=canonical]") || document.head.appendChild(document.createElement("link"));
    canonical.rel = "canonical";
    canonical.href = path;
    let script = document.getElementById("jsonld") as HTMLScriptElement | null;
    if (encoded) {
      if (!script) {
        script = document.createElement("script");
        script.id = "jsonld";
        script.type = "application/ld+json";
        document.head.appendChild(script);
      }
      script.text = encoded;
    } else if (script) script.remove();
  }, [title, description, path, encoded]);
  return null;
}

function setMeta(name: string, content: string, property = false) {
  const selector = property ? `meta[property="${name}"]` : `meta[name="${name}"]`;
  let tag = document.querySelector<HTMLMetaElement>(selector);
  if (!tag) {
    tag = document.createElement("meta");
    if (property) tag.setAttribute("property", name);
    else tag.setAttribute("name", name);
    document.head.appendChild(tag);
  }
  tag.content = content;
}
