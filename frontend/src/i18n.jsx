import { createContext, useContext, useEffect, useState } from "react";

/* ── Diller ───────────────────────────────────────────────────────
   tr: Türkçe (varsayılan) · en: English · ar: العربية (RTL)
   Kullanım:  const t = useT();  →  t("nav.sim")
   Eksik anahtar bulunursa Türkçe'ye, o da yoksa anahtarın kendisine düşer. */

export const DILLER = [
  { kod: "tr", ad: "Türkçe", bayrak: "🇹🇷" },
  { kod: "en", ad: "English", bayrak: "🇬🇧" },
  { kod: "ar", ad: "العربية", bayrak: "🇸🇦" },
];

const S = {
  // ── Menü / genel ──
  "nav.sim":      { tr: "Bina Simülasyonu", en: "Building Simulation", ar: "محاكاة المبنى" },
  "nav.epias":    { tr: "Canlı EPİAŞ",      en: "Live Prices",         ar: "الأسعار المباشرة" },
  "nav.invest":   { tr: "Yatırım & Çevre",  en: "Investment & Impact", ar: "الاستثمار والبيئة" },
  "nav.expert":   { tr: "Uzman Modu",       en: "Expert Mode",         ar: "الوضع المتقدم" },
  "nav.howitworks": { tr: "Nasıl Çalışır",  en: "How It Works",        ar: "كيف يعمل" },
  "nav.results":  { tr: "Sonuçlar",         en: "Results",             ar: "النتائج" },
  "nav.whofor":   { tr: "Kimler İçin",      en: "Who It's For",        ar: "لمن" },
  "nav.faq":      { tr: "SSS",              en: "FAQ",                 ar: "الأسئلة الشائعة" },
  "nav.signup":   { tr: "Kayıt Ol",         en: "Sign Up",             ar: "إنشاء حساب" },
  "nav.logout":   { tr: "Çıkış",            en: "Log Out",             ar: "تسجيل الخروج" },
  "nav.profile":  { tr: "Profil",           en: "Profile",             ar: "الملف الشخصي" },
  "nav.tryfree":  { tr: "Ücretsiz Dene",    en: "Try for Free",        ar: "جرّب مجانًا" },

  "common.loading":   { tr: "Yükleniyor…", en: "Loading…", ar: "جارٍ التحميل…" },
  "common.saved":     { tr: "Kaydedildi",  en: "Saved",    ar: "تم الحفظ" },
  "common.apidown":   { tr: "API'ye ulaşılamadı", en: "Cannot reach the server", ar: "تعذّر الوصول إلى الخادم" },

  // ── Kayıt / Giriş ──
  "auth.register.title": { tr: "Hesap oluşturun", en: "Create your account", ar: "أنشئ حسابك" },
  "auth.login.title":    { tr: "Tekrar hoş geldiniz", en: "Welcome back", ar: "مرحبًا بعودتك" },
  "auth.register.sub":   { tr: "Binanızı tarif edin, tasarrufu hemen görün — ücretsiz.", en: "Describe your building and see savings instantly — free.", ar: "صِف مبناك وشاهد التوفير فورًا — مجانًا." },
  "auth.login.sub":      { tr: "Devam etmek için giriş yapın.", en: "Sign in to continue.", ar: "سجّل الدخول للمتابعة." },
  "auth.name":     { tr: "Ad Soyad", en: "Full Name", ar: "الاسم الكامل" },
  "auth.name.ph":  { tr: "Adınız", en: "Your name", ar: "اسمك" },
  "auth.email":    { tr: "E-posta", en: "Email", ar: "البريد الإلكتروني" },
  "auth.password": { tr: "Şifre", en: "Password", ar: "كلمة المرور" },
  "auth.wait":     { tr: "Lütfen bekleyin…", en: "Please wait…", ar: "يرجى الانتظار…" },
  "auth.register.btn": { tr: "Kayıt Ol", en: "Sign Up", ar: "إنشاء حساب" },
  "auth.login.btn":    { tr: "Giriş Yap", en: "Log In", ar: "تسجيل الدخول" },
  "auth.haveAccount":  { tr: "Zaten hesabınız var mı?", en: "Already have an account?", ar: "لديك حساب بالفعل؟" },
  "auth.noAccount":    { tr: "Hesabınız yok mu?", en: "Don't have an account?", ar: "ليس لديك حساب؟" },
  "auth.goLogin":  { tr: "Giriş yapın", en: "Log in", ar: "سجّل الدخول" },
  "auth.goRegister": { tr: "Kayıt olun", en: "Sign up", ar: "أنشئ حسابًا" },

  // ── Profil ──
  "profile.title": { tr: "Profil", en: "Profile", ar: "الملف الشخصي" },
  "profile.sub":   { tr: "Hesabın, kayıtlı binan ve simülasyon geçmişin. Yaptığın her değişiklik otomatik kaydedilir.", en: "Your account, saved building and simulation history. Every change is saved automatically.", ar: "حسابك، المبنى المحفوظ وسجل المحاكاة. يتم حفظ كل تغيير تلقائيًا." },
  "profile.member": { tr: "Üyelik", en: "Member since", ar: "عضو منذ" },
  "profile.changePw": { tr: "Şifre değiştir", en: "Change password", ar: "تغيير كلمة المرور" },
  "profile.currentPw": { tr: "Mevcut şifre", en: "Current password", ar: "كلمة المرور الحالية" },
  "profile.newPw": { tr: "Yeni şifre", en: "New password", ar: "كلمة المرور الجديدة" },
  "profile.updatePw": { tr: "Şifreyi güncelle", en: "Update password", ar: "تحديث كلمة المرور" },
  "profile.pwUpdated": { tr: "Şifre güncellendi.", en: "Password updated.", ar: "تم تحديث كلمة المرور." },
  "profile.savedBuilding": { tr: "Kayıtlı binam", en: "My saved building", ar: "مبناي المحفوظ" },
  "profile.savedBuilding.alt": { tr: "Bina Simülasyonu'nda yaptığın ayarlar otomatik olarak hesabına kaydedilir; her girişte hazır gelir.", en: "Settings you make in Building Simulation are saved automatically; ready on every login.", ar: "تُحفظ إعداداتك في محاكاة المبنى تلقائيًا وتكون جاهزة عند كل تسجيل دخول." },
  "profile.noBuilding": { tr: "Henüz bina ayarı yok — Bina Simülasyonu'na gidip ayarla, otomatik kaydedilir.", en: "No building yet — set one up in Building Simulation; it saves automatically.", ar: "لا يوجد مبنى بعد — أنشئ واحدًا في محاكاة المبنى؛ يُحفظ تلقائيًا." },
  "profile.savingsSummary": { tr: "Tasarruf özeti (kayıtlı binana göre)", en: "Savings summary (for your saved building)", ar: "ملخص التوفير (لمبناك المحفوظ)" },
  "profile.history": { tr: "Simülasyon geçmişi", en: "Simulation history", ar: "سجل المحاكاة" },
  "profile.noHistory": { tr: "Henüz kayıt yok.", en: "No records yet.", ar: "لا توجد سجلات بعد." },
  "profile.floors": { tr: "kat", en: "floors", ar: "طوابق" },
  "profile.activeFlats": { tr: "aktif daire", en: "active flats", ar: "شقق مأهولة" },
  "profile.roof": { tr: "m² çatı", en: "m² roof", ar: "م² سطح" },

  // ── Ortak metrik/etiketler ──
  "m.dailySaving":  { tr: "Bugünkü tasarruf", en: "Today's saving", ar: "توفير اليوم" },
  "m.yearlySaving": { tr: "Yıllık tasarruf", en: "Annual saving", ar: "التوفير السنوي" },
  "m.payback":      { tr: "Amorti süresi", en: "Payback period", ar: "فترة الاسترداد" },
  "m.co2":          { tr: "Yıllık CO₂", en: "Annual CO₂", ar: "ثاني أكسيد الكربون سنويًا" },
  "m.battery":      { tr: "Batarya seviyesi", en: "Battery level", ar: "مستوى البطارية" },
  "m.solar":        { tr: "Güneş üretimi", en: "Solar output", ar: "إنتاج الطاقة الشمسية" },
  "m.consumption":  { tr: "Toplam tüketim", en: "Total consumption", ar: "إجمالي الاستهلاك" },
  "unit.year":      { tr: "yıl", en: "yr", ar: "سنة" },
  "unit.ton":       { tr: "ton", en: "t", ar: "طن" },

  // ── Bina Simülasyonu ──
  "sim.title": { tr: "Bina Simülasyonu", en: "Building Simulation", ar: "محاكاة المبنى" },
  "sim.step1": { tr: "Soldan binanızı tarif edin", en: "Describe your building on the left", ar: "صِف مبناك من اليسار" },
  "sim.step2": { tr: "Binanın altındaki saat çubuğuyla günü gezin", en: "Use the hour slider below the building", ar: "استخدم شريط الساعة أسفل المبنى" },
  "sim.step3": { tr: "Sonuçlar anında güncellenir", en: "Results update instantly", ar: "تتحدث النتائج فورًا" },
  "sim.auto":  { tr: "Otomatik hesaplanıyor — başlat butonuna gerek yok", en: "Calculated automatically — no start button needed", ar: "يُحسب تلقائيًا — لا حاجة لزر البدء" },
  "sim.hour":  { tr: "Günün saati", en: "Hour of day", ar: "ساعة اليوم" },
  "sim.now":   { tr: "ajan şu an", en: "the agent is now", ar: "الوكيل الآن" },
  "sim.store": { tr: "DEPOLUYOR", en: "STORING", ar: "يُخزّن" },
  "sim.use":   { tr: "KULLANIYOR", en: "USING", ar: "يستخدم" },
  "sim.wait":  { tr: "BEKLEMEDE", en: "WAITING", ar: "في الانتظار" },
  "sim.chart": { tr: "24 saatlik plan — fiyat, batarya ve ajan kararları", en: "24-hour plan — price, battery and agent decisions", ar: "خطة 24 ساعة — السعر والبطارية وقرارات الوكيل" },
  "sim.recos": { tr: "Şu anki öneriler", en: "Current recommendations", ar: "التوصيات الحالية" },
  "sim.billCompare": { tr: "Bugünkü fatura karşılaştırması", en: "Today's bill comparison", ar: "مقارنة فاتورة اليوم" },
  "sim.without": { tr: "Sistem olmadan", en: "Without the system", ar: "بدون النظام" },
  "sim.with":   { tr: "Akıllı sistemle", en: "With the smart system", ar: "مع النظام الذكي" },
  "sim.batteryEff": { tr: "Batarya verimi", en: "Battery efficiency", ar: "كفاءة البطارية" },

  // ── Konfigüratör ──
  "cfg.title": { tr: "Bina Konfigüratörü", en: "Building Configurator", ar: "مُهيّئ المبنى" },
  "cfg.type":  { tr: "Bina tipi", en: "Building type", ar: "نوع المبنى" },
  "cfg.floors": { tr: "Kat sayısı", en: "Number of floors", ar: "عدد الطوابق" },
  "cfg.flatsPer": { tr: "Kat başına daire", en: "Flats per floor", ar: "شقق لكل طابق" },
  "cfg.activeFlats": { tr: "Aktif daire", en: "Active flats", ar: "الشقق المأهولة" },
  "cfg.rooms": { tr: "Oda sayısı (daire başına)", en: "Rooms (per flat)", ar: "الغرف (لكل شقة)" },
  "cfg.roof": { tr: "Çatı alanı (m²)", en: "Roof area (m²)", ar: "مساحة السطح (م²)" },
  "cfg.systems": { tr: "Sistemler", en: "Systems", ar: "الأنظمة" },
  "cfg.month": { tr: "Ay (mevsim)", en: "Month (season)", ar: "الشهر (الموسم)" },
  "cfg.hour": { tr: "Saat", en: "Hour", ar: "الساعة" },
  "sys.elevator": { tr: "Asansör", en: "Elevator", ar: "مصعد" },
  "sys.hvac": { tr: "HVAC (klima)", en: "HVAC (A/C)", ar: "تكييف" },
  "sys.pump": { tr: "Su Pompası", en: "Water Pump", ar: "مضخة مياه" },
  "sys.ev": { tr: "EV Şarj", en: "EV Charger", ar: "شحن السيارات" },
  "sys.camera": { tr: "Kamera", en: "Camera", ar: "كاميرا" },
  "sys.solarheat": { tr: "Güneş Isıtıcı", en: "Solar Heater", ar: "سخان شمسي" },
  "sys.generator": { tr: "Jeneratör", en: "Generator", ar: "مولّد" },
  "btype.Müstakil Ev": { tr: "Müstakil Ev", en: "Detached House", ar: "منزل مستقل" },
  "btype.Villa": { tr: "Villa", en: "Villa", ar: "فيلا" },
  "btype.Apartman": { tr: "Apartman", en: "Apartment", ar: "شقة سكنية" },
  "btype.Ofis Binası": { tr: "Ofis Binası", en: "Office Building", ar: "مبنى مكاتب" },

  // ── EPİAŞ ──
  "epias.title": { tr: "Canlı EPİAŞ — Gün Öncesi Piyasası", en: "Live Market — Day-Ahead Prices", ar: "السوق المباشر — أسعار اليوم التالي" },
  "epias.sub": { tr: "Elektriğin saatlik fiyatı ve akıllı sistemin bugün her saat ne yaptığı.", en: "Hourly electricity price and what the smart system does each hour today.", ar: "سعر الكهرباء بالساعة وما يفعله النظام الذكي كل ساعة اليوم." },
  "epias.nowPrice": { tr: "Şu anki fiyat", en: "Current price", ar: "السعر الحالي" },
  "epias.cheapest": { tr: "Günün en ucuz saati", en: "Cheapest hour", ar: "أرخص ساعة" },
  "epias.priciest": { tr: "Günün en pahalı saati", en: "Priciest hour", ar: "أغلى ساعة" },
  "epias.todaySaving": { tr: "Bugünkü tasarruf", en: "Today's saving", ar: "توفير اليوم" },
  "epias.hourlyTitle": { tr: "Bugünün saatlik elektrik fiyatları", en: "Today's hourly electricity prices", ar: "أسعار الكهرباء بالساعة اليوم" },
  "epias.hourlyAlt": { tr: "Yeşil çubuk: en ucuz saatler (depolama). Kırmızı: en pahalı (kullanım). Sarı: şu an.", en: "Green: cheapest hours (store). Red: priciest (use). Yellow: now.", ar: "الأخضر: الأرخص (تخزين). الأحمر: الأغلى (استخدام). الأصفر: الآن." },
  "epias.outage": { tr: "Kesinti senaryosu", en: "Outage scenario", ar: "سيناريو انقطاع" },
  "epias.outageAlt": { tr: "Elektrik kesildiğinde batarya ve güneşin sizi kaç saat idare edeceğini test edin.", en: "Test how long battery + solar keep you running during a blackout.", ar: "اختبر كم ساعة تكفيك البطارية والطاقة الشمسية أثناء الانقطاع." },
  "epias.outageToggle": { tr: "Elektrik kesintisi simülasyonu", en: "Power outage simulation", ar: "محاكاة انقطاع الكهرباء" },
  "epias.tariffTitle": { tr: "Hangi tarife size uygun?", en: "Which tariff suits you?", ar: "أي تعرفة تناسبك؟" },
  "epias.table": { tr: "Saat saat karar tablosu", en: "Hour-by-hour decision table", ar: "جدول القرارات ساعة بساعة" },
  "epias.data": { tr: "Veri", en: "Data", ar: "البيانات" },

  // ── Yatırım ──
  "invest.title": { tr: "Yatırım & Çevre Analizi", en: "Investment & Impact Analysis", ar: "تحليل الاستثمار والأثر" },
  "invest.pdf": { tr: "Raporu indir (PDF)", en: "Download report (PDF)", ar: "تنزيل التقرير (PDF)" },
  "invest.costs": { tr: "Yatırım Maliyetleri", en: "Investment Costs", ar: "تكاليف الاستثمار" },
  "invest.battCost": { tr: "Batarya maliyeti (TL)", en: "Battery cost (TL)", ar: "تكلفة البطارية (ليرة)" },
  "invest.panelCost": { tr: "Panel maliyeti (TL)", en: "Panel cost (TL)", ar: "تكلفة الألواح (ليرة)" },
  "invest.total": { tr: "Toplam yatırım", en: "Total investment", ar: "إجمالي الاستثمار" },
  "invest.monthly": { tr: "Ay ay tasarruf — hangi ay ne kadar kazandırıyor?", en: "Month-by-month savings", ar: "التوفير شهرًا بشهر" },
  "invest.payChart": { tr: "Amorti süresi — kümülatif tasarruf vs yatırım", en: "Payback — cumulative savings vs investment", ar: "الاسترداد — التوفير التراكمي مقابل الاستثمار" },
  "invest.sensitivity": { tr: "Fiyat duyarlılık analizi", en: "Price sensitivity analysis", ar: "تحليل حساسية السعر" },

  // ── Uzman ──
  "expert.title": { tr: "Uzman Modu", en: "Expert Mode", ar: "الوضع المتقدم" },
  "expert.sub": { tr: "İşin tekniğini merak edenler için: yapay zekâ yöntemlerinin karşılaştırması, tahmin kalitesinin etkisi ve mevsimsel analizler.", en: "For the technically curious: comparison of AI methods, effect of forecast quality, and seasonal analysis.", ar: "للمهتمين بالتقنية: مقارنة طرق الذكاء الاصطناعي وأثر جودة التنبؤ والتحليل الموسمي." },
  "expert.toggle": { tr: "Teknik detaylar", en: "Technical details", ar: "تفاصيل تقنية" },
  "expert.gateTitle": { tr: "Bu bölüm teknik detaylar içerir", en: "This section contains technical details", ar: "يحتوي هذا القسم على تفاصيل تقنية" },
  "expert.gateSub": { tr: "Algoritma karşılaştırmaları ve model analizleri burada. Görmek için teknik detayları açın.", en: "Algorithm comparisons and model analysis live here. Turn on technical details to view.", ar: "مقارنات الخوارزميات وتحليل النماذج هنا. فعّل التفاصيل التقنية للعرض." },
  "expert.gateBtn": { tr: "Teknik detayları aç", en: "Show technical details", ar: "عرض التفاصيل التقنية" },
  "expert.tab.algo": { tr: "Algoritma Karşılaştırması", en: "Algorithm Comparison", ar: "مقارنة الخوارزميات" },
  "expert.tab.mode": { tr: "Fiyat Bilgisi Etkisi", en: "Price Info Effect", ar: "أثر معلومات السعر" },
  "expert.tab.season": { tr: "Mevsimsel Analiz", en: "Seasonal Analysis", ar: "التحليل الموسمي" },
};

function detectDefault() {
  const kayit = localStorage.getItem("she_dil");
  if (kayit && DILLER.some((d) => d.kod === kayit)) return kayit;
  return "tr";
}

const Ctx = createContext(null);

export function LangProvider({ children }) {
  const [dil, setDilState] = useState(detectDefault);

  useEffect(() => {
    const el = document.documentElement;
    el.setAttribute("lang", dil);
    el.setAttribute("dir", dil === "ar" ? "rtl" : "ltr");
  }, [dil]);

  const setDil = (k) => {
    setDilState(k);
    localStorage.setItem("she_dil", k);
  };

  const t = (key) => {
    const e = S[key];
    if (!e) return key;
    return e[dil] ?? e.tr ?? key;
  };

  return <Ctx.Provider value={{ dil, setDil, t }}>{children}</Ctx.Provider>;
}

export function useI18n() {
  return useContext(Ctx) || { dil: "tr", setDil: () => {}, t: (k) => (S[k]?.tr ?? k) };
}

export function useT() {
  return useI18n().t;
}
