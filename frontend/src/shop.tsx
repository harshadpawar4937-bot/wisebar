import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, setCsrf } from "./lib/api";
import { loadAnalytics, track } from "./lib/analytics";
import type { Cart, Config, Session, User } from "./types";

type ShopValue = {
  ready: boolean;
  error: string;
  user: User | null;
  cart: Cart | null;
  config: Config | null;
  cartOpen: boolean;
  searchOpen: boolean;
  setCartOpen: (open: boolean) => void;
  setSearchOpen: (open: boolean) => void;
  refresh: () => Promise<void>;
  toast: string;
  notify: (message: string) => void;
};

const ShopContext = createContext<ShopValue | null>(null);

export function ShopProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const [cartOpen, setCartOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [toast, setToast] = useState("");

  async function refresh() {
    const next = await api<Session>("/session");
    setCsrf(next.csrf);
    setSession(next);
    loadAnalytics(next.config.ga_measurement_id);
  }

  useEffect(() => {
    refresh()
      .catch(() => setError("The shop API is not reachable. Start the backend, then refresh."))
      .finally(() => setReady(true));
  }, []);

  function notify(message: string) {
    setToast(message);
    window.setTimeout(() => setToast(""), 3200);
  }

  const value = useMemo<ShopValue>(() => ({
    ready,
    error,
    user: session?.user ?? null,
    cart: session?.cart ?? null,
    config: session?.config ?? null,
    cartOpen,
    searchOpen,
    setCartOpen,
    setSearchOpen,
    refresh,
    toast,
    notify,
  }), [ready, error, session, cartOpen, searchOpen, toast]);

  return (
    <ShopContext.Provider value={value}>
      {children}
      {toast && <div role="status" className="fixed bottom-24 left-1/2 z-50 -translate-x-1/2 rounded-full bg-pine-900 px-4 py-2 text-sm text-cream-50 shadow-card md:bottom-6">{toast}</div>}
    </ShopContext.Provider>
  );
}

export function useShop() {
  const value = useContext(ShopContext);
  if (!value) throw new Error("ShopProvider missing");
  return value;
}

export function usePageView(path: string) {
  useEffect(() => { track("page_view", { path }); }, [path]);
}
