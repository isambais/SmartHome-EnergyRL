import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import TopNav from "./components/TopNav.jsx";
import Auth from "./pages/Auth.jsx";
import Epias from "./pages/Epias.jsx";
import Landing from "./pages/Landing.jsx";
import Profil from "./pages/Profil.jsx";
import Simulasyon from "./pages/Simulasyon.jsx";
import Uzman from "./pages/Uzman.jsx";
import Yatirim from "./pages/Yatirim.jsx";
import { AppState, useApp } from "./state.jsx";

/* Uygulama sayfaları — landing ile AYNI üst bar, aynı zemin.
   Giriş yapılmadıysa kayıt sayfasına yönlendirir. */
function AppLayout() {
  const { user } = useApp();
  if (!user) return <Navigate to="/kayit" replace />;

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      <TopNav />
      <main className="main" style={{ paddingTop: 96, maxWidth: 1440, margin: "0 auto" }}>
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AppState>
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
    </AppState>
  );
}
