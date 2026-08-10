import { lazy, Suspense } from "react";
import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import TopNav from "./components/TopNav.jsx";
import Footer from "./components/Footer.jsx";
import { AppState, useApp } from "./state.jsx";

// Lazy loading — her sayfa ihtiyaç olunca yüklenir
const Auth = lazy(() => import("./pages/Auth.jsx"));
const Epias = lazy(() => import("./pages/Epias.jsx"));
const Landing = lazy(() => import("./pages/Landing.jsx"));
const Profil = lazy(() => import("./pages/Profil.jsx"));
const Simulasyon = lazy(() => import("./pages/Simulasyon.jsx"));
const Uzman = lazy(() => import("./pages/Uzman.jsx"));
const Yatirim = lazy(() => import("./pages/Yatirim.jsx"));

function PageLoading() {
  return <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "60vh", color: "#64748b" }}>Yükleniyor…</div>;
}

/* Uygulama sayfaları — landing ile AYNI üst bar, aynı zemin.
   Giriş yapılmadıysa kayıt sayfasına yönlendirir. */
function AppLayout() {
  const { user } = useApp();
  const loc = useLocation();
  if (!user) return <Navigate to="/kayit" replace />;
  const footerGizle = loc.pathname === "/profil";

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", display: "flex", flexDirection: "column" }}>
      <TopNav />
      <main className="main" style={{ paddingTop: 96, maxWidth: 1440, margin: "0 auto", width: "100%", flex: 1 }}>
        <Outlet />
      </main>
      {!footerGizle && <Footer />}
    </div>
  );
}

export default function App() {
  return (
    <AppState>
      <Suspense fallback={<PageLoading />}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/kayit" element={<Auth mode="kayit" />} />
          <Route path="/giris" element={<Auth mode="giris" />} />
          <Route element={<AppLayout />}>
            <Route path="/simulasyon" element={<Simulasyon />} />
            <Route path="/epias" element={<Epias />} />
            <Route path="/yatirim" element={<Yatirim />} />
            <Route path="/uzman" element={<Uzman />} />
            <Route path="/profil" element={<Profil />} />
          </Route>
        </Routes>
      </Suspense>
    </AppState>
  );
}
