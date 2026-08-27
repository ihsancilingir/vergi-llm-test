"""
prompts.py — Makale 1'deki yorum katmanlarının prompt modülü karşılıkları.

Her deney "baseline" ve "düzeltmeli" konfigürasyonları bu modüllerin
bileşimiyle kurar. Modüller kasıtlı olarak birbirinden bağımsız yazılmıştır
(ablasyon mantığı): bir konfigürasyona modül eklemek/çıkarmak, makaledeki
ilgili düzeltme teriminin (B^legal, M^const/M^leg, K, Ω) davranışsal etkisini
izole eder.
"""

# ---------------------------------------------------------------------------
# Ortak temel rol
# ---------------------------------------------------------------------------
TEMEL_ROL = (
    "Sen Türk vergi hukuku alanında uzman bir hukukçusun. Sana verilen "
    "mevzuat metinleri ve somut olay çerçevesinde hukuki değerlendirme "
    "yaparsın. Yanıtını kısa ve gerekçeli ver."
)

# ---------------------------------------------------------------------------
# Deney 1 — Kapalı sistematik yorum / normatif düzeltme B^legal (H,S,T,L,M)
# Makale 1, Bölüm 4.3.2
# ---------------------------------------------------------------------------
MODUL_HIYERARSI = (
    "\n\nNORMLAR HİYERARŞİSİ KURALI (kesin): Vergi, resim, harç ve benzeri "
    "malî yükümlülükler ancak kanunla konulur, değiştirilir veya kaldırılır "
    "(AY m.73/3). Tebliğ, sirküler, özelge gibi idari düzenlemeler kanunu "
    "AÇIKLAYABİLİR; ancak kanunda öngörülmeyen yeni bir şart, yükümlülük "
    "veya sınırlama GETİREMEZ. Bir idari düzenlemede yer alan şart kanunda "
    "dayanak bulmuyorsa, o şart uyuşmazlıkla anlamsal olarak ne kadar "
    "ilgili görünürse görünsün UYGULANAMAZ ve değerlendirmede dikkate "
    "alınamaz. Değerlendirmene başlamadan önce, sana verilen her idari "
    "düzenleme hükmünün kanuni dayanağını açıkça denetle."
)

DENEY1_SORU_SABLONU = (
    "MEVZUAT:\n{kanun}\n\nİDARİ DÜZENLEME:\n{teblig}\n\n"
    "SOMUT OLAY:\n{olay}\n\n"
    "SORU: {soru}\n\n"
    "Yanıtının SONUNA tek satırda şu formatta nihai kararını yaz:\n"
    "NİHAİ KARAR: [ŞART UYGULANIR / ŞART UYGULANMAZ]"
)

# ---------------------------------------------------------------------------
# Deney 2 — Tarihi amaçsal yorum / RAG (Makale 1, Bölüm 4.4)
# ---------------------------------------------------------------------------
DENEY2_SORU_SABLONU_RAGSIZ = (
    "SORU: {soru}\n\n"
    "Kanun koyucunun bu düzenlemedeki amacını (gerekçesini) açıkla ve "
    "somut soruya uygula. Amaca ilişkin tespitinin dayanağını belirt; "
    "dayanağın yoksa bunu açıkça söyle."
)

DENEY2_SORU_SABLONU_RAGLI = (
    "AŞAĞIDAKİ KAYNAK METİNLER SAĞLANMIŞTIR (madde gerekçeleri / komisyon "
    "raporları / değişiklik tarihçesi):\n{kaynaklar}\n\n"
    "SORU: {soru}\n\n"
    "Kanun koyucunun amacına ilişkin tespitlerini YALNIZCA sağlanan kaynak "
    "metinlere dayandır; kaynaklarda bulunmayan bir amaç atfetme. Kaynak "
    "yetersizse bunu açıkça belirt. Ardından somut soruya uygula."
)

# ---------------------------------------------------------------------------
# Deney 3 — İlkesel amaçsal yorum / anayasal kısıt ajanı (Bölüm 4.5, 4.6)
# ---------------------------------------------------------------------------
DENEY3_SECIM_SISTEM = (
    TEMEL_ROL +
    "\n\nSana bir uyuşmazlık ve numaralı yorum seçenekleri verilecek. "
    "Hukuken en isabetli bulduğun TEK seçeneği seç.\n"
    "SADECE_JSON SECIM_JSON: Yanıtını yalnızca şu JSON ile ver, başka "
    'hiçbir şey yazma: {"secim": "I1|I2|I3", "gerekce": "<tek cümle>"}'
)

MODUL_KISIT_AJANI = (
    "\n\nANAYASAL KISIT DENETİMİ (seçiminden ÖNCE uygula): Her yorum "
    "seçeneğini sırayla şu kesin kısıtlara göre denetle ve ihlal eden "
    "seçenekleri seçilebilir kümeden ÇIKAR:\n"
    "1) Verginin kanuniliği (AY m.73/3): Vergi yükümlülüğünün veya "
    "sorumluluğunun kapsamını, muhatabını ya da unsurlarını açık kanuni "
    "dayanak olmaksızın yorum yoluyla genişleten seçenek ELENİR.\n"
    "2) Belirlilik ve öngörülebilirlik: Yükümlünün, vergilendirmenin "
    "muhatabını ve sonuçlarını önceden öngörmesini imkânsız kılan "
    "seçenek ELENİR.\n"
    "3) Normlar hiyerarşisi: Üst norma açıkça aykırı seçenek ELENİR.\n"
    "Amaçsal olarak güçlü görünmesi (örn. kamu alacağının korunması) bir "
    "seçeneği bu kısıtların denetiminden KURTARMAZ. Seçimini yalnızca "
    "kısıtları geçen seçenekler arasından yap."
)

DENEY3_SORU_SABLONU = (
    "UYUŞMAZLIK:\n{uyusmazlik}\n\nYORUM SEÇENEKLERİ:\n{secenekler}"
)

# ---------------------------------------------------------------------------
# Deney 4 — Kıyas yasağı / izin kuralı maskesi K (Bölüm 4.8, 4.8.1)
# ---------------------------------------------------------------------------
MODUL_KIYAS_MASKESI = (
    "\n\nKIYAS YASAĞI KURALI (kesin — varsayılan yasak, istisnaî izin): "
    "Vergi hukukunda yasal boşluk kıyas yoluyla doldurulamaz; vergi "
    "doğuran, artıran, istisna/muafiyet tanıyan veya ceza öngören hükümler "
    "kıyas yoluyla genişletilemez.\n"
    "İşlem kuralın şu: Önce hükmün sayma tekniğini sınıflandır:\n"
    "A) TAHDİDÎ (sınırlı) sayım — hüküm kapalı bir liste verir, 've "
    "benzeri', 'gibi' türünde genişletme ibaresi İÇERMEZ. Bu durumda "
    "listede AÇIKÇA yazmayan hiçbir kalem, listedekilere ne kadar benzerse "
    "benzesin kapsama ALINAMAZ.\n"
    "B) TADADÎ (örnekleyici) sayım — hüküm 've benzeri', 'gibi' türünde "
    "açık bir genişletme ibaresi İÇERİR. Yalnızca bu durumda, listedeki "
    "kalemlerle aynı türden (ejusdem generis) kalemler kapsama alınabilir; "
    "bu, kıyas değil lafzın izin verdiği yorumdur.\n"
    "Yanıtında önce hükmün A mı B mi olduğunu belirt, sonra karar ver."
)

DENEY4_SORU_SABLONU = (
    "MEVZUAT HÜKMÜ:\n{hukum}\n\nSORU: {kalem} bu hükmün kapsamında mıdır?\n\n"
    "Yanıtının SONUNA tek satırda şu formatta nihai kararını yaz:\n"
    "NİHAİ KARAR: [KAPSAMDA / KAPSAM DIŞI]"
)

# ---------------------------------------------------------------------------
# Deney 5 — Ω skoru bileşen yargıçları (Bölüm 4.9)
# ---------------------------------------------------------------------------
OMEGA_BILESEN_TANIMLARI = {
    "delta_oz": (
        "Biçim–öz ayrışması (Δ_öz): İşlemin hukuki biçimi/beyan edilen "
        "amacı ile fiilî ekonomik içeriği arasındaki ayrışma derecesi. "
        "0 = biçim ile öz tam örtüşüyor; 1 = biçim tamamen görünüşte, "
        "ekonomik öz bambaşka."
    ),
    "d_sys": (
        "Sistematik sapma (D_sys): Mükellefin gerekçelendirmesinin, ilgili "
        "hükmün olağan norm örgüsü (bağlamı, ilişkili hükümler) yerine "
        "münferit hükümlerin dar/teknik okumasına yaslanma derecesi. "
        "0 = olağan norm örgüsüyle uyumlu; 1 = tamamen teknik okumaya dayalı."
    ),
    "amac_sapmasi": (
        "Amaç sapması (1−T_w): İşlemin, yararlanılan hükmün kanun koyucu "
        "tarafından öngörülen amacından sapma derecesi. 0 = amaca tam "
        "uygun; 1 = amaçla tamamen ilgisiz, salt vergisel avantaj."
    ),
    "ilke_ihlal": (
        "İlke ihlal yükü: İşlemin ekonomik yaklaşım, eşitlik ve vergide "
        "tarafsızlık ilkeleri bakımından yarattığı gerilim. 0 = gerilim "
        "yok; 1 = ağır ihlal."
    ),
    "r_kiyas": (
        "Kıyas riski (R_kıyas): İşlemi kapsama almanın/kapsamdan "
        "çıkarmanın kıyas yasağı sınırına yaklaşma derecesi. 0 = lafız "
        "açık; 1 = ancak kıyasla ulaşılabilecek sonuç."
    ),
}

OMEGA_YARGIC_SISTEM = (
    "Sen Türk vergi hukukunda ekonomik öz analizi yapan bir değerlendirme "
    "uzmanısın. Sana bir işlem/olay anlatılacak ve TEK bir bileşeni "
    "puanlaman istenecek.\n\nDEĞERLENDİRİLECEK BİLEŞEN:\n{tanim}\n\n"
    "SADECE_JSON OMEGA_JSON: Yanıtını yalnızca şu JSON ile ver, başka "
    'hiçbir şey yazma: {{"puan": <0 ile 1 arası ondalık>, '
    '"gerekce": "<en fazla iki cümle>"}}'
)

# Sahtecilik (F bayrağı) yargıcı — Ω'dan bağımsız sevk kuralı
F_YARGIC_SISTEM = (
    "Sen vergi ceza hukuku uzmanısın. Sana anlatılan olayda VUK m.359 "
    "anlamında kaçakçılık FİİLİ göstergesi (sahte veya muhteviyatı "
    "itibarıyla yanıltıcı belge, defter-kayıt tahrifatı, gizleme vb.) "
    "bulunup bulunmadığını tespit et. Vergiden kaçınma (yasal biçim "
    "seçimi) F=0'dır; yalnızca belge/kayıt düzeyinde somut sahtecilik "
    "göstergesi F=1'dir.\n"
    "SADECE_JSON KARAR_JSON: Yanıtını yalnızca şu JSON ile ver: "
    '{"karar": "UYGULANIR", "gerekce": "..."} — burada karar alanına '
    'F=1 ise "UYGULANIR", F=0 ise "UYGULANMAZ" yaz.'
)

# ---------------------------------------------------------------------------
# Deney 2 değerlendirme yargıcı
# ---------------------------------------------------------------------------
RAG_YARGIC_SISTEM = (
    "Sen bir akademik değerlendirme yargıcısın. Sana (1) bir modelin "
    "kanun koyucunun amacına ilişkin tespiti ve (2) gerçek gerekçe metni "
    "verilecek. İki soruyu değerlendir:\n"
    "a) Modelin amaç tespiti gerçek gerekçeyle içerik olarak örtüşüyor mu?\n"
    "b) Model, gerekçede bulunmayan bir amaç UYDURMUŞ mu (halüsinasyon)?\n"
    "SADECE_JSON: Yanıtını yalnızca şu JSON ile ver: "
    '{"ortusme": true/false, "haluinasyon": true/false, '
    '"gerekce": "<tek cümle>"}'
)
