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

// Ay isimleri (tam ve kısa) — dil bazlı
export const AYLAR_FULL = {
  tr: ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"],
  en: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
  ar: ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"],
};
export const AYLAR_KISA = {
  tr: ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"],
  en: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  ar: ["ينا", "فبر", "مار", "أبر", "ماي", "يون", "يول", "أغس", "سبت", "أكت", "نوف", "ديس"],
};

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
  // ── Öneriler (backend kod + parametre) — {..} yer tutucular biçimlendirilir ──
  "rec.charge": { tr: "Şu an şarj edin — fiyat düşük ({p} TL/MWh, ortalama {ort})", en: "Charge now — price is low ({p} TL/MWh, avg {ort})", ar: "اشحن الآن — السعر منخفض ({p} ليرة/م.و.س، المتوسط {ort})" },
  "rec.discharge": { tr: "Batarya %{soc} — deşarj ile pahalı saatten kaçınılıyor ({p} TL/MWh)", en: "Battery {soc}% — discharging to avoid the expensive hour ({p} TL/MWh)", ar: "البطارية {soc}% — يفرّغ لتفادي ساعة الذروة ({p} ليرة/م.و.س)" },
  "rec.idle": { tr: "Beklemede — fiyat nötr bölgede ({p} TL/MWh)", en: "On standby — price is neutral ({p} TL/MWh)", ar: "في وضع الانتظار — السعر متعادل ({p} ليرة/م.و.س)" },
  "rec.defer": { tr: "Çamaşır/bulaşık makinesini saat {saat}:00'te çalıştırın (günün en uygun saati)", en: "Run the washer/dishwasher at {saat}:00 (the day's best hour)", ar: "شغّل الغسالة/غسالة الصحون الساعة {saat}:00 (أفضل ساعة في اليوم)" },
  "rec.solar": { tr: "Güneş {kw} kW üretiyor — yüksek tüketimli işleri şimdi yapın", en: "Solar is producing {kw} kW — run high-consumption tasks now", ar: "الطاقة الشمسية تنتج {kw} كيلوواط — نفّذ المهام عالية الاستهلاك الآن" },
  "rec.outageGen": { tr: "Elektrik kesintisi! Jeneratör devrede.", en: "Power outage! Generator is active.", ar: "انقطاع الكهرباء! المولّد يعمل." },
  "rec.outageUnmet": { tr: "Elektrik kesintisi! {kwh} kWh karşılanamıyor!", en: "Power outage! {kwh} kWh cannot be supplied!", ar: "انقطاع الكهرباء! لا يمكن تزويد {kwh} كيلوواط·ساعة!" },
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
  "expert.best": { tr: "en iyi", en: "best", ar: "الأفضل" },
  "expert.dailyAvg": { tr: "günlük ort. ±", en: "daily avg ±", ar: "متوسط يومي ±" },
  "expert.perfTitle": { tr: "Günlük performans (Oracle fiyat bilgisiyle)", en: "Daily performance (with Oracle price info)", ar: "الأداء اليومي (بمعلومات أوراكل)" },
  "expert.perfAlt": { tr: "Her algoritmanın bir günde sağladığı ortalama net kazanç.", en: "Average net gain each algorithm delivers per day.", ar: "متوسط الربح الصافي لكل خوارزمية يوميًا." },
  "expert.forecastTitle": { tr: "Fiyat tahmin modelleri", en: "Price forecast models", ar: "نماذج التنبؤ بالأسعار" },
  "expert.forecastAlt": { tr: "Yarının elektrik fiyatını tahmin eden modellerin doğruluğu.", en: "Accuracy of models forecasting tomorrow's electricity price.", ar: "دقة نماذج التنبؤ بسعر كهرباء الغد." },
  "expert.modeTitle": { tr: "Tahmin kalitesi kararı ne kadar etkiliyor?", en: "How much does forecast quality affect decisions?", ar: "كم تؤثر جودة التنبؤ على القرارات؟" },
  "expert.modeAlt": { tr: "Ajan yarının fiyatını ne kadar iyi bildikçe günlük kazanç nasıl değişiyor (TL/gün).", en: "How daily gain changes with how well the agent knows tomorrow's price (TL/day).", ar: "كيف يتغير الربح اليومي حسب معرفة الوكيل بسعر الغد (ليرة/يوم)." },
  "expert.policy": { tr: "Algoritma", en: "Algorithm", ar: "الخوارزمية" },
  "expert.oracleDesc": { tr: "Yarının gerçek fiyatını bilir (ideal üst sınır)", en: "Knows tomorrow's real price (ideal upper bound)", ar: "يعرف سعر الغد الحقيقي (الحد الأعلى المثالي)" },
  "expert.forecastDesc": { tr: "LightGBM tahmini kullanır (gerçekçi senaryo)", en: "Uses LightGBM forecast (realistic scenario)", ar: "يستخدم تنبؤ LightGBM (سيناريو واقعي)" },
  "expert.naiveDesc": { tr: "Bugünün fiyatını yarın sayar (en basit)", en: "Assumes today's price for tomorrow (simplest)", ar: "يفترض سعر اليوم للغد (الأبسط)" },
  "expert.modeNote": { tr: "Ajan, yarının fiyatını tam bilmese bile (Naive) Oracle'a çok yakın kazanç sağlıyor — yani tahmine bağımlı değil, sağlam bir strateji öğrenmiş.", en: "Even without knowing tomorrow's price (Naive), the agent earns close to Oracle — it learned a robust strategy, not a forecast-dependent one.", ar: "حتى دون معرفة سعر الغد (Naive)، يحقق الوكيل ربحًا قريبًا من أوراكل — تعلّم استراتيجية متينة لا تعتمد على التنبؤ." },
  "expert.monthlyPrice": { tr: "Aylık ortalama elektrik fiyatı", en: "Monthly average electricity price", ar: "متوسط سعر الكهرباء الشهري" },
  "expert.monthlyPriceAlt": { tr: "Renkler mevsimi gösterir — kış mavi, ilkbahar yeşil, yaz sarı, sonbahar turuncu.", en: "Colors show the season — winter blue, spring green, summer yellow, autumn orange.", ar: "الألوان تدل على الموسم — الشتاء أزرق، الربيع أخضر، الصيف أصفر، الخريف برتقالي." },
  "expert.sumWinPrice": { tr: "Yaz — Kış günlük fiyat profili", en: "Summer — Winter daily price profile", ar: "ملف السعر اليومي صيفًا وشتاءً" },
  "expert.sumWinSolar": { tr: "Yaz — Kış güneş üretim profili", en: "Summer — Winter solar output profile", ar: "ملف إنتاج الطاقة الشمسية صيفًا وشتاءً" },
  "expert.summer": { tr: "Yaz", en: "Summer", ar: "الصيف" },
  "expert.winter": { tr: "Kış", en: "Winter", ar: "الشتاء" },
  "expert.dailyReward": { tr: "Günlük ödül", en: "Daily reward", ar: "المكافأة اليومية" },

  // ── Sim ek ──
  "sim.storeDesc": { tr: "Elektrik şu an ucuz — batarya dolduruluyor", en: "Electricity is cheap now — charging the battery", ar: "الكهرباء رخيصة الآن — يتم شحن البطارية" },
  "sim.useDesc": { tr: "Elektrik şu an pahalı — depodaki ucuz elektrik devrede", en: "Electricity is pricey now — using stored cheap power", ar: "الكهرباء غالية الآن — يُستخدم المخزون الرخيص" },
  "sim.waitDesc": { tr: "Fiyat nötr bölgede — batarya doluluğu korunuyor", en: "Price is neutral — holding battery level", ar: "السعر محايد — يتم الحفاظ على مستوى البطارية" },
  "sim.chargePct": { tr: "Batarya", en: "Battery", ar: "البطارية" },
  "sim.storeDecision": { tr: "Depolama kararı", en: "Store decision", ar: "قرار التخزين" },
  "sim.useDecision": { tr: "Kullanma kararı", en: "Use decision", ar: "قرار الاستخدام" },
  "sim.price": { tr: "Elektrik fiyatı (TL/MWh)", en: "Electricity price (TL/MWh)", ar: "سعر الكهرباء (ليرة/م.و.س)" },
  "sim.batteryLine": { tr: "Batarya doluluğu (%)", en: "Battery level (%)", ar: "مستوى البطارية (٪)" },
  "sim.solarLine": { tr: "Güneş (kW)", en: "Solar (kW)", ar: "شمسي (ك.و)" },
  "sim.billZeroed": { tr: "bugünkü fatura sıfırlandı, üstüne kazanç var", en: "today's bill is zeroed, with extra earnings", ar: "فاتورة اليوم صفر، مع أرباح إضافية" },
  "sim.billPct": { tr: "faturanın %{x}'i kadar tasarruf", en: "saving about {x}% of the bill", ar: "توفير نحو {x}٪ من الفاتورة" },
  "sim.gainToday": { tr: "kazanç", en: "earnings", ar: "أرباح" },

  // ── EPİAŞ ek ──
  "epias.avg": { tr: "ortalama", en: "average", ar: "المتوسط" },
  "epias.tariffSingle": { tr: "Tek zamanlı tarife", en: "Single-rate tariff", ar: "تعرفة موحّدة" },
  "epias.tariffThree": { tr: "Üç zamanlı tarife", en: "Three-period tariff", ar: "تعرفة ثلاثية" },
  "epias.smart": { tr: "Akıllı sistem", en: "Smart system", ar: "النظام الذكي" },
  "epias.tariffSingleNot": { tr: "sabit fiyat, sistem yok", en: "flat price, no system", ar: "سعر ثابت، بدون نظام" },
  "epias.tariffThreeNot": { tr: "gece ucuz / akşam pahalı, sistem yok", en: "cheap at night / pricey evening, no system", ar: "رخيص ليلًا / غالٍ مساءً، بدون نظام" },
  "epias.smartNot": { tr: "güneş + batarya + saatlik optimizasyon", en: "solar + battery + hourly optimization", ar: "شمسي + بطارية + تحسين بالساعة" },
  "epias.perDay": { tr: "TL/gün", en: "TL/day", ar: "ليرة/يوم" },
  "epias.gainDay": { tr: "TL kazanç", en: "TL earnings", ar: "ليرة أرباح" },
  "epias.tariffNote": { tr: "Akıllı sistem, en ucuz konut tarifesine göre bile günde {x} TL daha az — çünkü güneş üretimini ve saatlik fiyat farkını birlikte kullanıyor.", en: "The smart system costs {x} TL/day less than even the cheapest household tariff — because it combines solar output with hourly price gaps.", ar: "النظام الذكي أقل بـ {x} ليرة/يوم حتى من أرخص تعرفة منزلية — لأنه يجمع الإنتاج الشمسي مع فروق الأسعار بالساعة." },
  "epias.col.hour": { tr: "Saat", en: "Hour", ar: "الساعة" },
  "epias.col.price": { tr: "Fiyat (TL/MWh)", en: "Price (TL/MWh)", ar: "السعر (ليرة/م.و.س)" },
  "epias.col.decision": { tr: "Karar", en: "Decision", ar: "القرار" },
  "epias.col.battery": { tr: "Batarya", en: "Battery", ar: "البطارية" },
  "epias.col.solar": { tr: "Güneş (kW)", en: "Solar (kW)", ar: "شمسي (ك.و)" },
  "epias.col.demand": { tr: "Talep (kW)", en: "Demand (kW)", ar: "الطلب (ك.و)" },
  "epias.col.cost": { tr: "Maliyet (TL)", en: "Cost (TL)", ar: "التكلفة (ليرة)" },
  "epias.col.saving": { tr: "Tasarruf (TL)", en: "Saving (TL)", ar: "التوفير (ليرة)" },
  "kw.store": { tr: "depola", en: "store", ar: "تخزين" },
  "kw.use": { tr: "kullan", en: "use", ar: "استخدام" },

  // ── Yatırım ek ──
  "invest.costsNote": { tr: "Değerler senin binana özel; 12 ayın her biri ayrı simüle edilip toplandı.", en: "Values are specific to your building; each of the 12 months is simulated and summed.", ar: "القيم خاصة بمبناك؛ تُحاكى كل شهر من الـ12 وتُجمع." },
  "invest.solarProd": { tr: "Panel üretimi", en: "Panel output", ar: "إنتاج الألواح" },
  "invest.envNote": { tr: "Sisteminiz {y} yılda kendini amorti ediyor; yılda {a} ağacın tuttuğu kadar CO₂ tasarrufu sağlıyor — bu {c} arabanın yıllık emisyonuna eşit.", en: "Your system pays for itself in {y} years; it saves as much CO₂ as {a} trees absorb yearly — equal to {c} cars' annual emissions.", ar: "يسترد نظامك تكلفته خلال {y} سنوات؛ يوفّر من ثاني أكسيد الكربون ما يمتصه {a} شجرة سنويًا — أي ما يعادل انبعاثات {c} سيارة سنويًا." },
  "invest.monthlyNote": { tr: "Yazın güneş bol → tasarruf yüksek; kışın güneş az + batarya verimi düşük → tasarruf azalır.", en: "Summer has abundant sun → high savings; winter has less sun + lower battery efficiency → lower savings.", ar: "الصيف مشمس → توفير مرتفع؛ الشتاء أقل شمسًا وكفاءة بطارية أقل → توفير أقل." },
  "invest.cumSaving": { tr: "Kümülatif tasarruf", en: "Cumulative savings", ar: "التوفير التراكمي" },
  "invest.investLine": { tr: "Yatırım", en: "Investment", ar: "الاستثمار" },
  "invest.paybackLine": { tr: "Amorti", en: "Payback", ar: "الاسترداد" },
  "invest.priceRise": { tr: "Elektrik fiyat artışı (%)", en: "Electricity price rise (%)", ar: "ارتفاع سعر الكهرباء (٪)" },
  "invest.paybackYr": { tr: "Amorti (yıl)", en: "Payback (yr)", ar: "الاسترداد (سنة)" },
  "invest.sensNote": { tr: "Elektrik fiyatları %30 artarsa amorti süresi {x} yıl kısalarak {y} yıla iner.", en: "If electricity prices rise 30%, payback shortens by {x} years to {y} years.", ar: "إذا ارتفعت أسعار الكهرباء 30٪، تقصر فترة الاسترداد بمقدار {x} سنة لتصبح {y} سنة." },

  // ── Yükleniyor ──
  "load.sim": { tr: "Simülasyon çalışıyor…", en: "Running simulation…", ar: "جارٍ تشغيل المحاكاة…" },
  "load.prices": { tr: "Fiyatlar yükleniyor…", en: "Loading prices…", ar: "جارٍ تحميل الأسعار…" },
  "load.invest": { tr: "12 aylık simülasyon çalışıyor…", en: "Running 12-month simulation…", ar: "جارٍ محاكاة 12 شهرًا…" },
  "load.analysis": { tr: "Analizler yükleniyor…", en: "Loading analysis…", ar: "جارٍ تحميل التحليلات…" },
  "load.profile": { tr: "Profil yükleniyor…", en: "Loading profile…", ar: "جارٍ تحميل الملف…" },

  // ── Footer ──
  "foot.tagline": { tr: "Güneş panelli ve bataryalı binalar için akıllı enerji yönetimi — faturanızı kendiliğinden düşürür.", en: "Smart energy management for buildings with solar and batteries — lowers your bill automatically.", ar: "إدارة طاقة ذكية للمباني ذات الألواح الشمسية والبطاريات — تخفّض فاتورتك تلقائيًا." },
  "foot.online": { tr: "Sistem çevrimiçi · Canlı EPİAŞ verisi", en: "System online · Live market data", ar: "النظام متصل · بيانات السوق المباشرة" },
  "foot.dashboard": { tr: "Panel", en: "Dashboard", ar: "لوحة التحكم" },
  "foot.project": { tr: "Proje", en: "Project", ar: "المشروع" },
  "foot.links": { tr: "Bağlantılar", en: "Links", ar: "روابط" },
  "foot.features": { tr: "Özellikler", en: "Features", ar: "الميزات" },
  "foot.rights": { tr: "Akademik staj projesi", en: "Academic internship project", ar: "مشروع تدريب أكاديمي" },
  "foot.top": { tr: "Başa dön", en: "Back to top", ar: "العودة للأعلى" },

  // ── Landing ──
  "lp.hero.badge": { tr: "Güneş paneliniz ve bataryanız varsa, tanışın", en: "Have solar and a battery? Meet your assistant", ar: "لديك ألواح شمسية وبطارية؟ تعرّف على مساعدك" },
  "lp.hero.titleFull": { tr: "elektrik faturanızı düşürsün", en: "lowers your electricity bill", ar: "يخفّض فاتورة الكهرباء" },
  "lp.hero.sub": { tr: "Akıllı asistanınız elektriğin ucuz olduğu saatlerde bataryanızı doldurur, pahalı saatlerde depoladığı enerjiyi kullanır. Siz hiçbir şey yapmazsınız — fatura kendiliğinden düşer.", en: "Your smart assistant charges the battery when electricity is cheap and uses the stored energy when it's expensive. You do nothing — the bill drops by itself.", ar: "يشحن مساعدك الذكي البطارية عندما تكون الكهرباء رخيصة ويستخدم الطاقة المخزّنة عندما تكون غالية. لا تفعل شيئًا — تنخفض الفاتورة من تلقاء نفسها." },
  "lp.hero.cta": { tr: "Ücretsiz Dene", en: "Try for Free", ar: "جرّب مجانًا" },
  "lp.hero.how": { tr: "Nasıl Çalışır", en: "How It Works", ar: "كيف يعمل" },
  "lp.hero.chip1": { tr: "Günde ~14 TL cebinizde kalır", en: "Keep ~14 TL in your pocket daily", ar: "احتفظ بنحو 14 ليرة يوميًا" },
  "lp.hero.chip2": { tr: "Tamamen otomatik", en: "Fully automatic", ar: "تلقائي بالكامل" },
  "lp.hero.chip3": { tr: "Kesintide de sizi korur", en: "Protects you during outages", ar: "يحميك أثناء الانقطاع" },

  // ── Mockup (dashboard önizleme) ──
  "mock.running": { tr: "Asistan çalışıyor", en: "Assistant running", ar: "المساعد يعمل" },
  "mock.title": { tr: "Bina Simülasyonu", en: "Building Simulation", ar: "محاكاة المبنى" },
  "mock.sub": { tr: "5 katlı apartman · 12 daire · bugünün elektrik fiyatları", en: "5-storey apartment · 12 flats · today's electricity prices", ar: "شقة من 5 طوابق · 12 وحدة · أسعار كهرباء اليوم" },
  "mock.save": { tr: "Bugünkü tasarruf", en: "Today's savings", ar: "توفير اليوم" },
  "mock.soc": { tr: "Batarya doluluğu", en: "Battery level", ar: "مستوى البطارية" },
  "mock.solar": { tr: "Güneş üretimi", en: "Solar output", ar: "إنتاج شمسي" },
  "mock.now": { tr: "Şu an ne yapıyor?", en: "What is it doing now?", ar: "ماذا يفعل الآن؟" },
  "mock.discharging": { tr: "Bataryadan kullanıyor", en: "Using the battery", ar: "يستخدم البطارية" },
  "mock.panels": { tr: "Panel: 37 adet", en: "Panels: 37 units", ar: "الألواح: 37 وحدة" },
  "mock.installed": { tr: "8.0 kW kurulu", en: "8.0 kW installed", ar: "8.0 كيلوواط مُركّب" },
  "mock.batt": { tr: "Batarya", en: "Battery", ar: "بطارية" },
  "mock.chartTitle": { tr: "Elektrik fiyatı & batarya — bugün", en: "Electricity price & battery — today", ar: "سعر الكهرباء والبطارية — اليوم" },
  "mock.legPrice": { tr: "Elektrik fiyatı", en: "Electricity price", ar: "سعر الكهرباء" },
  "mock.legSoc": { tr: "Batarya doluluğu", en: "Battery level", ar: "مستوى البطارية" },
  "mock.legCharge": { tr: "depoluyor", en: "charging", ar: "يشحن" },
  "mock.legDischarge": { tr: "kullanıyor", en: "using", ar: "يستخدم" },
  "mock.config": { tr: "Bina Konfigürasyonu", en: "Building Configuration", ar: "إعدادات المبنى" },
  "mock.cfgType": { tr: "Bina tipi", en: "Building type", ar: "نوع المبنى" },
  "mock.cfgTypeVal": { tr: "Apartman", en: "Apartment", ar: "شقة" },
  "mock.cfgFloor": { tr: "Kat", en: "Floors", ar: "طوابق" },
  "mock.cfgFlats": { tr: "Aktif daire", en: "Active flats", ar: "وحدات نشطة" },
  "mock.cfgBatt": { tr: "Batarya", en: "Battery", ar: "بطارية" },

  // ── Showcase panelleri (ProductPanel) ──
  "show.solar.title": { tr: "Güneş Üretimi", en: "Solar Output", ar: "الإنتاج الشمسي" },
  "show.batt.title": { tr: "Batarya Yönetimi", en: "Battery Management", ar: "إدارة البطارية" },
  "show.price.title": { tr: "Elektrik Fiyatları", en: "Electricity Prices", ar: "أسعار الكهرباء" },
  "show.outage.title": { tr: "Kesinti Modu", en: "Outage Mode", ar: "وضع الانقطاع" },
  "show.agent.title": { tr: "Asistanın Kararları", en: "Assistant's Decisions", ar: "قرارات المساعد" },

  "show.solar.instant": { tr: "Anlık üretim", en: "Instant output", ar: "إنتاج لحظي" },
  "show.solar.dayTotal": { tr: "Gün toplamı", en: "Daily total", ar: "إجمالي اليوم" },
  "show.solar.selfUse": { tr: "Öz-tüketim", en: "Self-consumption", ar: "استهلاك ذاتي" },
  "show.solar.peak": { tr: "tepe", en: "peak", ar: "ذروة" },

  "show.batt.full": { tr: "dolu · şarj oluyor", en: "full · charging", ar: "ممتلئة · تشحن" },
  "show.batt.plan": { tr: "24 saatlik şarj planı", en: "24-hour charge plan", ar: "خطة شحن 24 ساعة" },
  "show.batt.charge": { tr: "şarj (ucuz saat)", en: "charge (cheap hours)", ar: "شحن (ساعات رخيصة)" },
  "show.batt.discharge": { tr: "deşarj (pahalı saat)", en: "discharge (peak hours)", ar: "تفريغ (ساعات الذروة)" },

  "show.price.now": { tr: "/MWh · şu an", en: "/MWh · now", ar: "/ميغاواط·س · الآن" },
  "show.price.live": { tr: "Canlı", en: "Live", ar: "مباشر" },
  "show.price.cheap": { tr: "ucuz → şarj", en: "cheap → charge", ar: "رخيص ← شحن" },
  "show.price.exp": { tr: "pahalı → deşarj", en: "expensive → discharge", ar: "غالٍ ← تفريغ" },

  "show.outage.alert": { tr: "Şebeke kesintisi algılandı — batarya + güneş devrede", en: "Grid outage detected — battery + solar active", ar: "تم رصد انقطاع الشبكة — البطارية والطاقة الشمسية تعملان" },
  "show.outage.critical": { tr: "Kritik yükler", en: "Critical loads", ar: "الأحمال الحرجة" },
  "show.outage.lighting": { tr: "Aydınlatma", en: "Lighting", ar: "الإضاءة" },
  "show.outage.outlets": { tr: "Priz devreleri", en: "Outlet circuits", ar: "دوائر المقابس" },
  "show.outage.ev": { tr: "EV şarj", en: "EV charging", ar: "شحن السيارة" },
  "show.outage.suspended": { tr: "askıda", en: "suspended", ar: "معلّق" },
  "show.outage.autonomy": { tr: "Tahmini otonomi", en: "Estimated autonomy", ar: "الاستقلالية المقدّرة" },
  "show.outage.autonomyVal": { tr: "4s 20dk", en: "4h 20m", ar: "4س 20د" },
  "show.outage.gen": { tr: "Jeneratör", en: "Generator", ar: "المولّد" },
  "show.outage.ready": { tr: "hazır", en: "ready", ar: "جاهز" },

  "show.agent.store": { tr: "DEPOLA", en: "STORE", ar: "تخزين" },
  "show.agent.wait": { tr: "BEKLE", en: "WAIT", ar: "انتظار" },
  "show.agent.use": { tr: "KULLAN", en: "USE", ar: "استخدام" },
  "show.agent.d1": { tr: "elektrik en ucuz — batarya doluyor", en: "electricity cheapest — battery charging", ar: "الكهرباء الأرخص — البطارية تشحن" },
  "show.agent.d2": { tr: "güneş zaten evi besliyor", en: "solar already powers the home", ar: "الطاقة الشمسية تغذّي المنزل بالفعل" },
  "show.agent.d3": { tr: "elektrik en pahalı — depodakini kullan", en: "electricity priciest — use stored energy", ar: "الكهرباء الأغلى — استخدم المخزون" },
  "show.agent.d4": { tr: "gece ucuz tarife başladı", en: "cheap night tariff started", ar: "بدأت تعرفة الليل الرخيصة" },
  "show.agent.net": { tr: "Bugünkü net kazanç", en: "Today's net gain", ar: "صافي ربح اليوم" },

  "lp.problem.title": { tr: "Akıllı kararlar, daha düşük fatura", en: "Smarter decisions, lower bills", ar: "قرارات أذكى، فواتير أقل" },
  "lp.problem.before": { tr: "Sisteme sahip olmadan", en: "Without the system", ar: "بدون النظام" },
  "lp.problem.after": { tr: "Akıllı asistanla", en: "With the smart assistant", ar: "مع المساعد الذكي" },
  "lp.problem.beforeTitle": { tr: "Enerji yönetimindeki zorluklar", en: "Challenges in energy management", ar: "تحديات إدارة الطاقة" },
  "lp.problem.b1": { tr: "Güneş üretimi en pahalı saatte değil, en ucuz saatte depoya giriyor", en: "Solar output is stored at the cheapest hour, not saved for the priciest", ar: "يُخزّن إنتاج الطاقة الشمسية في أرخص ساعة بدل أغلاها" },
  "lp.problem.b2": { tr: "Elektrik kesintisinde batarya yeterince hazır değil", en: "The battery isn't ready for a blackout", ar: "البطارية ليست جاهزة للانقطاع" },
  "lp.problem.b3": { tr: "Hangi saatte şarj, hangi saatte deşarj yapılacağı bilinmiyor", en: "It's unclear when to charge or discharge", ar: "غير واضح متى تشحن ومتى تفرّغ" },
  "lp.problem.b4": { tr: "EPİAŞ fiyat değişimlerini takip etmek zaman alıyor", en: "Tracking price changes takes time", ar: "متابعة تغيّرات الأسعار تستغرق وقتًا" },
  "lp.problem.afterTitle": { tr: "Akıllı asistanla her şey otomatik", en: "With the smart assistant, everything is automatic", ar: "مع المساعد الذكي، كل شيء تلقائي" },
  "lp.problem.a1": { tr: "Elektrik ucuzken depolar, pahalıyken depodakini kullanır — her gün, kendiliğinden", en: "Stores power when cheap, uses it when pricey — every day, automatically", ar: "يخزّن عند الرخص ويستخدم عند الغلاء — كل يوم تلقائيًا" },
  "lp.problem.a2": { tr: "Kesinti gelmeden bataryayı hazır tutar, ışıklarınız sönmez", en: "Keeps the battery ready before outages; your lights stay on", ar: "يبقي البطارية جاهزة قبل الانقطاع؛ تبقى الأضواء مضاءة" },
  "lp.problem.a3": { tr: "Testlerde günde ortalama 14 TL tasarruf sağladı — yılda 5.000 TL'den fazla", en: "Saved ~14 TL/day in tests — over 5,000 TL a year", ar: "وفّر نحو 14 ليرة يوميًا في الاختبارات — أكثر من 5000 ليرة سنويًا" },
  "lp.problem.a4": { tr: "Elektrik fiyatlarını sizin yerinize o takip eder", en: "It tracks electricity prices for you", ar: "يتابع أسعار الكهرباء بدلًا عنك" },
  "lp.problem.stat1": { tr: "Kaçan tasarruf fırsatı", en: "Missed savings", ar: "توفير ضائع" },
  "lp.problem.stat2": { tr: "Fiyat takip etme derdi", en: "Price-tracking hassle", ar: "عناء متابعة الأسعار" },
  "lp.problem.stat3": { tr: "Günde cebinizde kalan", en: "Kept in your pocket daily", ar: "يبقى في جيبك يوميًا" },
  "lp.problem.stat4": { tr: "Sizin yerinize düşünür", en: "Thinks for you", ar: "يفكّر بدلًا عنك" },
  "lp.problem.constant": { tr: "Sürekli", en: "Constant", ar: "مستمر" },

  "lp.feat.eyebrow": { tr: "Kaydırarak keşfedin", en: "Scroll to explore", ar: "مرّر للاستكشاف" },
  "lp.feat.title": { tr: "Sistem sizin için ne yapıyor?", en: "What does the system do for you?", ar: "ماذا يفعل النظام من أجلك؟" },
  "lp.feat.sub": { tr: "Güneşten kesinti korumasına — beş şey, hepsi kendiliğinden.", en: "From solar to outage protection — five things, all automatic.", ar: "من الطاقة الشمسية إلى الحماية من الانقطاع — خمسة أمور، كلها تلقائية." },
  "lp.feat.solar.t": { tr: "Güneş Paneli Optimizasyonu", en: "Solar Panel Optimization", ar: "تحسين الألواح الشمسية" },
  "lp.feat.solar.d": { tr: "Güneşten üretilen elektrik önce evinizde kullanılır. Artan kısım ya bataryaya depolanır ya da şebekeye satılıp size gelir yazar.", en: "Solar power is used at home first. The surplus is stored in the battery or sold to the grid as income.", ar: "تُستخدم الطاقة الشمسية في المنزل أولًا. يُخزّن الفائض في البطارية أو يُباع للشبكة كدخل." },
  "lp.feat.batt.t": { tr: "Akıllı Batarya Yönetimi", en: "Smart Battery Management", ar: "إدارة ذكية للبطارية" },
  "lp.feat.batt.d": { tr: "Elektrik gece yarısı ucuzken batarya dolar, akşam pahalıyken depodaki ucuz elektrik devreye girer. Aradaki fark cebinizde kalır.", en: "The battery charges when electricity is cheap at night and discharges the cheap stored power in the expensive evening. The gap stays in your pocket.", ar: "تُشحن البطارية ليلًا عند الرخص وتُفرّغ الطاقة المخزّنة الرخيصة مساءً عند الغلاء. يبقى الفرق في جيبك." },
  "lp.feat.price.t": { tr: "Güncel Elektrik Fiyatları", en: "Live Electricity Prices", ar: "أسعار الكهرباء المباشرة" },
  "lp.feat.price.d": { tr: "Elektriğin fiyatı her saat değişir — gece ucuz, akşam pahalıdır. Sistem resmi piyasa fiyatlarını her gün otomatik alır.", en: "Electricity price changes every hour — cheap at night, pricey in the evening. The system fetches official market prices daily.", ar: "يتغيّر سعر الكهرباء كل ساعة — رخيص ليلًا وغالٍ مساءً. يجلب النظام أسعار السوق الرسمية يوميًا." },
  "lp.feat.outage.t": { tr: "Kesinti Koruması", en: "Outage Protection", ar: "الحماية من الانقطاع" },
  "lp.feat.outage.d": { tr: "Elektrik kesildiğinde batarya ve güneş otomatik devreye girer. Opsiyonel jeneratörle kesintisiz güç sağlanır.", en: "When power fails, battery and solar kick in automatically. With an optional generator you get uninterrupted power.", ar: "عند انقطاع الكهرباء تعمل البطارية والطاقة الشمسية تلقائيًا. مع مولّد اختياري تحصل على طاقة دون انقطاع." },
  "lp.feat.agent.t": { tr: "Kendi Kendine Öğrenen Asistan", en: "Self-Learning Assistant", ar: "مساعد ذاتي التعلّم" },
  "lp.feat.agent.d": { tr: "Asistan, binlerce günlük fiyat verisiyle eğitildi: hangi saatte ne yapılacağını deneye deneye kendisi öğrendi.", en: "The assistant was trained on thousands of days of price data, learning what to do each hour by trial and error.", ar: "دُرّب المساعد على بيانات أسعار لآلاف الأيام، وتعلّم ماذا يفعل كل ساعة بالتجربة." },

  "lp.how.eyebrow": { tr: "Nasıl çalışır", en: "How it works", ar: "كيف يعمل" },
  "lp.how.title": { tr: "Dakikalar içinde başlayın", en: "Get started in minutes", ar: "ابدأ خلال دقائق" },
  "lp.how.s1t": { tr: "Binanızı tarif edin", en: "Describe your building", ar: "صِف مبناك" },
  "lp.how.s1d": { tr: "Bina tipi, kat ve daire sayısı, çatı alanı — panel ve batarya kapasitesi otomatik önerilir.", en: "Building type, floors, flats, roof area — panel and battery capacity are suggested automatically.", ar: "نوع المبنى والطوابق والشقق ومساحة السطح — تُقترح سعة الألواح والبطارية تلقائيًا." },
  "lp.how.s2t": { tr: "Asistan günü planlar", en: "The assistant plans the day", ar: "يخطّط المساعد لليوم" },
  "lp.how.s2d": { tr: "24 saatlik fiyat, güneş ve talep tahminine bakarak her saat için en kârlı kararı üretir.", en: "It produces the most profitable decision for each hour from 24-hour price, solar and demand forecasts.", ar: "ينتج القرار الأكثر ربحية لكل ساعة من توقعات السعر والطاقة الشمسية والطلب على مدار 24 ساعة." },
  "lp.how.s3t": { tr: "Tasarrufu görün", en: "See the savings", ar: "شاهد التوفير" },
  "lp.how.s3d": { tr: "Saat saat maliyet, tasarruf ve öneriler; yatırımınızın kaç yılda amorti olacağıyla birlikte.", en: "Hour-by-hour cost, savings and tips, along with how many years your investment takes to pay off.", ar: "التكلفة والتوفير والنصائح ساعة بساعة، مع عدد سنوات استرداد استثمارك." },

  "lp.stats.eyebrow": { tr: "Rakamlarla", en: "By the numbers", ar: "بالأرقام" },
  "lp.stats.title": { tr: "Peki size ne kazandırır?", en: "So what do you gain?", ar: "إذًا ماذا تكسب؟" },
  "lp.stats.sub": { tr: "74 günlük gerçek fiyat verisiyle yapılan testlerin sonuçları.", en: "Results from tests on 74 days of real price data.", ar: "نتائج اختبارات على بيانات أسعار حقيقية لـ74 يومًا." },
  "lp.stats.1l": { tr: "Günlük tasarruf", en: "Daily saving", ar: "التوفير اليومي" },
  "lp.stats.1d": { tr: "Elektriği ucuzken alıp pahalıyken kullanmanın günlük getirisi", en: "Daily gain from buying cheap and using it when pricey", ar: "العائد اليومي من الشراء رخيصًا والاستخدام عند الغلاء" },
  "lp.stats.2l": { tr: "Yıllık tasarruf", en: "Annual saving", ar: "التوفير السنوي" },
  "lp.stats.2d": { tr: "Ortalama bir apartman için yıllık tahmini kazanç", en: "Estimated annual gain for an average apartment", ar: "العائد السنوي التقديري لشقة متوسطة" },
  "lp.stats.3l": { tr: "Kurulum süresi", en: "Setup time", ar: "وقت الإعداد" },
  "lp.stats.3d": { tr: "Binanızı tarif edin, gerisini asistan halleder", en: "Describe your building, the assistant does the rest", ar: "صِف مبناك، والمساعد يتولى الباقي" },
  "lp.stats.4l": { tr: "Kesintide dayanma", en: "Outage endurance", ar: "الصمود أثناء الانقطاع" },
  "lp.stats.4d": { tr: "Batarya ve güneşle elektriksiz kalmadan geçen süre", en: "Time you stay powered with battery and solar", ar: "المدة التي تبقى فيها متصلًا بالبطارية والطاقة الشمسية" },
  "lp.stats.5l": { tr: "Sizin yapacağınız", en: "What you do", ar: "ما تفعله أنت" },
  "lp.stats.5d": { tr: "Sistem 7/24 kendi kendine çalışır", en: "The system runs itself 24/7", ar: "يعمل النظام من تلقاء نفسه على مدار الساعة" },
  "lp.stats.nothing": { tr: "Hiçbir şey", en: "Nothing", ar: "لا شيء" },
  "lp.stats.mins": { tr: "2 dakika", en: "2 minutes", ar: "دقيقتان" },
  "lp.stats.hrs": { tr: "4+ saat", en: "4+ hours", ar: "أكثر من 4 ساعات" },

  "lp.use.eyebrow": { tr: "Kullanım senaryoları", en: "Use cases", ar: "حالات الاستخدام" },
  "lp.use.title": { tr: "Kim için geliştirildi?", en: "Who is it for?", ar: "لمن صُمّم؟" },
  "lp.use.1t": { tr: "Müstakil ev & villa sahipleri", en: "Detached house & villa owners", ar: "أصحاب المنازل والفلل" },
  "lp.use.1d": { tr: "Güneş paneliniz ve bataryanız varsa asistan gece ucuz elektriği depolar, akşam pahalı saatte onu kullanır — fatura kendiliğinden düşer.", en: "With solar and a battery, the assistant stores cheap night power and uses it in the pricey evening — the bill drops by itself.", ar: "مع الألواح والبطارية، يخزّن المساعد كهرباء الليل الرخيصة ويستخدمها مساءً — تنخفض الفاتورة تلقائيًا." },
  "lp.use.1m": { tr: "Ortalama yıllık tasarruf tahmini", en: "Estimated average annual saving", ar: "متوسط التوفير السنوي التقديري" },
  "lp.use.2t": { tr: "Apartman yöneticileri", en: "Building managers", ar: "مديرو المباني" },
  "lp.use.2d": { tr: "Asansör, merdiven aydınlatması ve su pompası gibi ortak giderleri düşürün. Aidatlara yansıyan elektrik kalemi küçülür.", en: "Lower shared costs like elevators, stairwell lighting and water pumps. The electricity share of dues shrinks.", ar: "خفّض التكاليف المشتركة كالمصاعد وإنارة السلالم ومضخات المياه. يتقلّص بند الكهرباء في الرسوم." },
  "lp.use.2m": { tr: "Ortak gider tasarrufu", en: "Shared-cost savings", ar: "توفير التكاليف المشتركة" },
  "lp.use.3t": { tr: "Ofis binaları & ticari", en: "Offices & commercial", ar: "المكاتب والمنشآت التجارية" },
  "lp.use.3d": { tr: "HVAC, EV şarj istasyonu ve güvenlik kameralarını birlikte yönetin. Amorti süresi ve CO₂ tasarrufu anında görülür.", en: "Manage HVAC, EV charging and security cameras together. Payback time and CO₂ savings are shown instantly.", ar: "أدر التكييف وشحن السيارات وكاميرات المراقبة معًا. تظهر فترة الاسترداد وتوفير الكربون فورًا." },
  "lp.use.3m": { tr: "Ortalama amorti süresi", en: "Average payback time", ar: "متوسط فترة الاسترداد" },
  "lp.use.4t": { tr: "Meraklısına: uzman modu", en: "For the curious: expert mode", ar: "للمهتمين: الوضع المتقدم" },
  "lp.use.4d": { tr: "İşin tekniğini merak edenler için ayrı bir bölüm var: farklı yapay zekâ yöntemlerinin karşılaştırması, mevsimsel analizler ve tüm detaylar orada.", en: "A separate section for the technically curious: comparison of AI methods, seasonal analysis and all the details.", ar: "قسم منفصل للمهتمين بالتقنية: مقارنة طرق الذكاء الاصطناعي والتحليل الموسمي وكل التفاصيل." },
  "lp.use.4m": { tr: "Ana ekranda teknik detay yok", en: "No jargon on the main screen", ar: "لا مصطلحات تقنية في الشاشة الرئيسية" },

  "lp.quote.text": { tr: "\"Elektriğin ne zaman ucuz, ne zaman pahalı olduğunu sistem kendisi öğreniyor. Siz sadece ay sonunda düşen faturayı görüyorsunuz.\"", en: "\"The system learns when electricity is cheap or expensive on its own. You just see a lower bill at month's end.\"", ar: "\"يتعلّم النظام بنفسه متى تكون الكهرباء رخيصة أو غالية. أنت فقط ترى فاتورة أقل في نهاية الشهر.\"" },
  "lp.quote.by": { tr: "SmartHome Energy — Proje Ekibi", en: "SmartHome Energy — Project Team", ar: "SmartHome Energy — فريق المشروع" },
  "lp.quote.c1": { tr: "Gerçek fiyat verisi", en: "Real price data", ar: "بيانات أسعار حقيقية" },
  "lp.quote.c2": { tr: "7/24 otomatik", en: "24/7 automatic", ar: "تلقائي على مدار الساعة" },
  "lp.quote.c3": { tr: "Kesinti koruması", en: "Outage protection", ar: "حماية من الانقطاع" },
  "lp.quote.c4": { tr: "Kurulum 2 dakika", en: "2-minute setup", ar: "إعداد بدقيقتين" },

  "lp.faq.title": { tr: "Sıkça sorulan sorular", en: "Frequently asked questions", ar: "الأسئلة الشائعة" },
  "lp.faq.q1": { tr: "Kullanmak için teknik bilgi gerekiyor mu?", en: "Do I need technical knowledge to use it?", ar: "هل أحتاج معرفة تقنية لاستخدامه؟" },
  "lp.faq.a1": { tr: "Hayır. Binanızı tarif edersiniz (kaç kat, kaç daire, çatı ne kadar) — gerisini sistem halleder. Ekranda gördüğünüz her şey günlük dille yazılmıştır.", en: "No. You describe your building (floors, flats, roof) — the system does the rest. Everything on screen is written in plain language.", ar: "لا. تصف مبناك (الطوابق، الشقق، السطح) — والنظام يتولى الباقي. كل ما على الشاشة مكتوب بلغة بسيطة." },
  "lp.faq.q2": { tr: "Bu gerçekten faturamı düşürür mü?", en: "Will it really lower my bill?", ar: "هل سيخفّض فاتورتي فعلًا؟" },
  "lp.faq.a2": { tr: "Elektriğin fiyatı gün içinde 2-3 kata kadar değişir. Sistem ucuz saatte elektriği bataryaya depolar, pahalı saatte onu kullanır. Testlerde günde ortalama 14 TL, yılda 5.000 TL'nin üzerinde tasarruf sağladı.", en: "Electricity price varies 2-3x during the day. The system stores power when cheap and uses it when pricey. In tests it saved ~14 TL/day, over 5,000 TL a year.", ar: "يتغيّر سعر الكهرباء 2-3 أضعاف خلال اليوم. يخزّن النظام عند الرخص ويستخدم عند الغلاء. وفّر في الاختبارات نحو 14 ليرة يوميًا وأكثر من 5000 ليرة سنويًا." },
  "lp.faq.q3": { tr: "Benim bir şey yapmam gerekiyor mu?", en: "Do I have to do anything?", ar: "هل عليّ فعل أي شيء؟" },
  "lp.faq.a3": { tr: "Hayır. Kurulumdan sonra sistem 7/24 kendi kendine çalışır. İsterseniz ekrandan ne yaptığını izlersiniz, istemezseniz hiç açmazsınız — tasarruf her iki durumda da devam eder.", en: "No. After setup the system runs itself 24/7. You can watch what it does or never open it — savings continue either way.", ar: "لا. بعد الإعداد يعمل النظام وحده على مدار الساعة. يمكنك متابعته أو عدم فتحه أبدًا — يستمر التوفير في الحالتين." },
  "lp.faq.q4": { tr: "Elektrik kesilirse ne olur?", en: "What happens during a blackout?", ar: "ماذا يحدث أثناء انقطاع الكهرباء؟" },
  "lp.faq.a4": { tr: "Sistem bataryayı kesintilere karşı hazır tutar. Kesinti anında batarya ve güneş otomatik devreye girer; jeneratörünüz varsa onu da yönetir.", en: "The system keeps the battery ready for outages. When one hits, battery and solar engage automatically; it also manages your generator if you have one.", ar: "يبقي النظام البطارية جاهزة للانقطاع. عند حدوثه تعمل البطارية والطاقة الشمسية تلقائيًا؛ ويدير مولّدك إن وُجد." },
  "lp.faq.q5": { tr: "Gerçek bir binaya bağlanabilir mi?", en: "Can it connect to a real building?", ar: "هل يمكن ربطه بمبنى حقيقي؟" },
  "lp.faq.a5": { tr: "Şu an bu bir simülasyon ve karar destek uygulamasıdır: binanızın birebir modelini kurar, gerçek fiyatlarla ne kadar tasarruf edeceğinizi gösterir. Gerçek binaya fiziksel bağlantı gelecek sürümde planlanıyor.", en: "For now it's a simulation and decision-support app: it builds a model of your building and shows savings with real prices. Physical connection to a real building is planned for a future release.", ar: "حاليًا هو تطبيق محاكاة ودعم قرار: يبني نموذجًا لمبناك ويعرض التوفير بأسعار حقيقية. الربط الفعلي بمبنى حقيقي مخطّط لإصدار قادم." },

  "lp.cta.title": { tr: "Daha akıllı enerji yönetimine hazır mısınız?", en: "Ready for smarter energy management?", ar: "هل أنت مستعد لإدارة طاقة أذكى؟" },
  "lp.cta.sub": { tr: "Binanızı 2 dakikada tarif edin — ne kadar tasarruf edeceğinizi hemen görün.", en: "Describe your building in 2 minutes — see your savings instantly.", ar: "صِف مبناك خلال دقيقتين — شاهد توفيرك فورًا." },
  "lp.cta.btn": { tr: "Ücretsiz Dene", en: "Try for Free", ar: "جرّب مجانًا" },

  // ── Bina tipleri bölümü ──
  "lp.bt.eyebrow": { tr: "Desteklenen bina tipleri", en: "Supported building types", ar: "أنواع المباني المدعومة" },
  "lp.bt.title": { tr: "Her bina tipi, kendi profiliyle", en: "Each building type, its own profile", ar: "لكل نوع مبنى ملفه الخاص" },
  "lp.bt.sub": { tr: "Kat sayısı, oda sayısı, çatı alanı — hepsi kaydırıcıyla ayarlanır. Batarya kapasitesi otomatik hesaplanır.", en: "Floors, rooms, roof area — all adjustable with sliders. Battery capacity is computed automatically.", ar: "الطوابق والغرف ومساحة السطح — كلها قابلة للضبط بالمنزلقات. تُحسب سعة البطارية تلقائيًا." },
  "lp.bt.mustak.d": { tr: "Bahçeli müstakil evler için yüksek güneş potansiyeli.", en: "High solar potential for detached homes with gardens.", ar: "إمكانات شمسية عالية للمنازل المستقلة ذات الحدائق." },
  "lp.bt.villa.d": { tr: "Geniş çatılı villalar için yüksek panel kapasitesi.", en: "High panel capacity for villas with large roofs.", ar: "سعة ألواح عالية للفلل ذات الأسطح الواسعة." },
  "lp.bt.apt.d": { tr: "Ortak alan tüketimi + daire bazlı optimizasyon.", en: "Shared-area consumption + per-flat optimization.", ar: "استهلاك المناطق المشتركة + تحسين لكل شقة." },
  "lp.bt.ofis.d": { tr: "Gündüz yoğun tüketim + EV şarj istasyonu desteği.", en: "Daytime-heavy load + EV charging support.", ar: "استهلاك نهاري مرتفع + دعم شحن السيارات." },
  "lp.bt.floor": { tr: "Kat", en: "Floors", ar: "طوابق" },
  "lp.bt.room": { tr: "Oda", en: "Rooms", ar: "غرف" },
  "lp.bt.roof": { tr: "Çatı", en: "Roof", ar: "السطح" },
  "lp.bt.battery": { tr: "Batarya", en: "Battery", ar: "بطارية" },
  "lp.bt.flatPer": { tr: "Daire/kat", en: "Flats/floor", ar: "شقق/طابق" },
  "lp.bt.elevator": { tr: "Asansör", en: "Elevator", ar: "مصعد" },
  "lp.bt.unit": { tr: "Birim", en: "Units", ar: "وحدات" },
  "lp.bt.hvac": { tr: "HVAC", en: "HVAC", ar: "تكييف" },
  "lp.bt.optional": { tr: "opsiyonel", en: "optional", ar: "اختياري" },
  "lp.bt.central": { tr: "merkezi sistem", en: "central system", ar: "نظام مركزي" },
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
