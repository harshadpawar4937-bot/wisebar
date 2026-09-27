import { useEffect } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import Lenis from "lenis";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Announcement, CartDrawer, Footer, Header, MobileBar, SearchDialog } from "./components/Chrome";
import { ShopProvider, useShop } from "./shop";
import { HomePage } from "./pages/Home";
import { CatalogPage, SearchPage } from "./pages/Catalog";
import { ProductPage } from "./pages/ProductPage";
import { BuildBoxPage, BundlesPage, CheckoutPage } from "./pages/Commerce";
import { AboutPage, AccountPage, ContactPage, CorporatePage, FaqPage, JournalPage, JournalPostPage, LegalPage, NotFoundPage } from "./pages/Content";
import { AdminPage } from "./pages/Admin";

export function App() {
  const reduced = useReducedMotion();
  useEffect(() => {
    if (reduced) return;
    const lenis = new Lenis();
    let frame = 0;
    const loop = (time: number) => {
      lenis.raf(time);
      frame = requestAnimationFrame(loop);
    };
    frame = requestAnimationFrame(loop);
    return () => {
      cancelAnimationFrame(frame);
      lenis.destroy();
    };
  }, [reduced]);
  return (
    <ShopProvider>
      <a className="skip-link" href="#main">Skip to content</a>
      <Announcement />
      <Status />
      <Header />
      <main id="main" className="min-h-[70vh] pb-20 md:pb-0">
        <AnimatedRoutes />
      </main>
      <Footer />
      <MobileBar />
      <CartDrawer />
      <SearchDialog />
    </ShopProvider>
  );
}

function Status() {
  const { error } = useShop();
  if (!error) return null;
  return <p role="alert" className="bg-berry px-4 py-2 text-center text-sm text-white">{error}</p>;
}

function AnimatedRoutes() {
  const location = useLocation();
  const reduced = useReducedMotion();
  return (
    <AnimatePresence mode="wait">
      <motion.div key={location.pathname} initial={reduced ? false : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
        <Routes location={location}>
          <Route index element={<HomePage />} />
          <Route path="protein-bars" element={<CatalogPage category="protein-bars" />} />
          <Route path="protein-muesli" element={<CatalogPage category="protein-muesli" />} />
          <Route path="products/:slug" element={<ProductPage />} />
          <Route path="bundles" element={<BundlesPage />} />
          <Route path="build-your-box" element={<BuildBoxPage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="journal" element={<JournalPage />} />
          <Route path="journal/:slug" element={<JournalPostPage />} />
          <Route path="corporate" element={<CorporatePage />} />
          <Route path="contact" element={<ContactPage />} />
          <Route path="faq" element={<FaqPage />} />
          <Route path="shipping" element={<LegalPage slug="shipping" />} />
          <Route path="returns" element={<LegalPage slug="returns" />} />
          <Route path="privacy" element={<LegalPage slug="privacy" />} />
          <Route path="terms" element={<LegalPage slug="terms" />} />
          <Route path="cookies" element={<LegalPage slug="cookies" />} />
          <Route path="account" element={<AccountPage />} />
          <Route path="checkout" element={<CheckoutPage />} />
          <Route path="search" element={<SearchPage />} />
          <Route path="admin" element={<AdminPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
}
