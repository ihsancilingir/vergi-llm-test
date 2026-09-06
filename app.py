"""
app.py — Makale 1 davranışsal doğrulama paketi için Streamlit web arayüzü.

Bu dosya runner.py/report.py/capraz_rapor.py'nin MANTIĞINI DEĞİŞTİRMEZ;
yalnızca üzerine görsel bir katman ekler. Aynı klasörde durmalıdır
(vergi_llm_test/app.py), çünkü runner.py'nin dosya yolları kendi
konumuna görelidir.

Çalıştırma:
    pip install streamlit
    streamlit run app.py

API anahtarları iki yoldan biriyle sağlanabilir:
    1) .streamlit/secrets.toml içine ANTHROPIC_API_KEY / OPENAI_API_KEY /
       GEMINI_API_KEY yazarak (Streamlit Cloud'a taşırken de aynı isimlerle
       "Secrets" panelinden girilir).
    2) Paket kökündeki anahtarlar.env dosyası (yerel CLI kullanımıyla aynı).
Her ikisi de tanımlıysa secrets.toml önceliklidir.
"""

from __future__ import annotations

import contextlib
import glob
import io
import json
import os
import subprocess
import sys
from datetime import datetime

import streamlit as st

# ---------------------------------------------------------------------
# runner.py ve kardeşlerini bu dosyayla aynı klasörden içe aktar
# ---------------------------------------------------------------------
PAKET_DIZINI = os.path.dirname(os.path.abspath(__file__))
if PAKET_DIZINI not in sys.path:
    sys.path.insert(0, PAKET_DIZINI)

import runner  # noqa: E402
from llm_client import LLMClient, SAGLAYICILAR  # noqa: E402

RESULTS_DIRS = [runner.SONUC_DIZINI, os.path.join(PAKET_DIZINI, "results_arsiv")]

st.set_page_config(
    page_title="Makale 1 — Davranışsal Doğrulama Paneli",
    page_icon="⚖️",
    layout="wide",
)

# =======================================================================
# API anahtarlarını yükle: önce st.secrets, sonra anahtarlar.env
# =======================================================================
def anahtarlari_hazirla():
    for anahtar in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"):
        try:
            if anahtar in st.secrets and st.secrets[anahtar]:
                os.environ[anahtar] = str(st.secrets[anahtar])
        except Exception:  # noqa: BLE001 — secrets.toml hiç yoksa st.secrets patlayabilir
            pass
    runner.anahtarlari_yukle()  # anahtarlar.env; zaten tanımlıysa ezmez


anahtarlari_hazirla()


def anahtar_durumu() -> dict:
    return {
        "Anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "OpenAI": bool(os.environ.get("OPENAI_API_KEY")),
        "Gemini": bool(os.environ.get("GEMINI_API_KEY")),
    }


# =======================================================================
# Canlı log yakalayıcı: print() çıktısını Streamlit'e akıtır
# =======================================================================
class StreamlitLogger(io.TextIOBase):
    def __init__(self, placeholder, max_lines: int = 500):
        super().__init__()
        self.placeholder = placeholder
        self.lines: list[str] = []
        self.max_lines = max_lines
        self._buf = ""

    def write(self, text: str) -> int:  # type: ignore[override]
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            self.lines.append(line)
        self.lines = self.lines[-self.max_lines:]
        gosterilecek = "\n".join(self.lines) + (("\n" + self._buf) if self._buf else "")
        self.placeholder.code(gosterilecek or " ", language=None)
        return len(text)

    def flush(self):  # noqa: D401
        pass


# =======================================================================
# Yardımcılar
# =======================================================================
def tum_sonuc_dosyalarini_listele() -> list[str]:
    dosyalar = []
    for d in RESULTS_DIRS:
        if os.path.isdir(d):
            dosyalar.extend(sorted(glob.glob(os.path.join(d, "*.jsonl"))))
    return dosyalar


def dosya_etiketi(yol: str) -> str:
    ad = os.path.basename(yol)
    klasor = os.path.basename(os.path.dirname(yol))
    return f"[{klasor}] {ad}"


def rapor_uret(jsonl_yolu: str) -> tuple[bool, str]:
    """report.py'yi alt süreç olarak çalıştırır, üretilen .md içeriğini döndürür."""
    cikti_yolu = jsonl_yolu.replace(".jsonl", "_rapor.md")
    try:
        sonuc = subprocess.run(
            [sys.executable, os.path.join(PAKET_DIZINI, "report.py"), jsonl_yolu],
            cwd=PAKET_DIZINI, capture_output=True, text=True, timeout=120,
        )
    except Exception as e:  # noqa: BLE001
        return False, f"Rapor üretilemedi: {e}"
    if sonuc.returncode != 0:
        return False, f"report.py hata verdi:\n```\n{sonuc.stderr}\n```"
    if not os.path.exists(cikti_yolu):
        return False, "Rapor dosyası oluşmadı."
    with open(cikti_yolu, encoding="utf-8") as f:
        return True, f.read()


def capraz_rapor_uret(jsonl_yollari: list[str]) -> tuple[bool, str]:
    cikti_yolu = os.path.join(runner.SONUC_DIZINI, "capraz_streamlit.md")
    os.makedirs(runner.SONUC_DIZINI, exist_ok=True)
    try:
        sonuc = subprocess.run(
            [sys.executable, os.path.join(PAKET_DIZINI, "capraz_rapor.py"),
             *jsonl_yollari, "--cikti", cikti_yolu],
            cwd=PAKET_DIZINI, capture_output=True, text=True, timeout=180,
        )
    except Exception as e:  # noqa: BLE001
        return False, f"Çapraz rapor üretilemedi: {e}"
    if sonuc.returncode != 0:
        return False, f"capraz_rapor.py hata verdi:\n```\n{sonuc.stderr}\n```"
    if not os.path.exists(cikti_yolu):
        return False, "Çapraz rapor dosyası oluşmadı."
    with open(cikti_yolu, encoding="utf-8") as f:
        return True, f.read()


def jsonl_oku(yol: str) -> list[dict]:
    kayitlar = []
    with open(yol, encoding="utf-8") as f:
        for satir in f:
            satir = satir.strip()
            if satir:
                kayitlar.append(json.loads(satir))
    return kayitlar


DENEY_ETIKETLERI = {
    "1": "Deney 1 — Normlar hiyerarşisi (B^legal)",
    "2": "Deney 2 — Tarihsel RAG düzeltmesi",
    "3": "Deney 3 — Anayasal/kanunilik maskesi",
    "4": "Deney 4 — Kıyas yasağı maskesi (K)",
    "5": "Deney 5 — Ω öz denetim skoru / Ψ(w)",
}


# =======================================================================
# KENAR ÇUBUĞU — çalıştırma ayarları
# =======================================================================
st.sidebar.title("⚖️ Çalıştırma Ayarları")

durum = anahtar_durumu()
st.sidebar.caption("API anahtar durumu (değerler gösterilmez):")
for ad, var in durum.items():
    st.sidebar.markdown(f"- {'✅' if var else '❌'} {ad}")

st.sidebar.divider()

mock = st.sidebar.checkbox(
    "Mock modu (API çağrısı yapmaz, ücretsiz boru hattı testi)",
    value=True,
    help="İlk denemede işaretli bırakın. Gerçek koşu için işareti kaldırın "
         "— bu, seçtiğiniz sağlayıcıya gerçek ve ücretli API çağrıları yapar.",
)

provider = st.sidebar.selectbox("Sağlayıcı (test edilen model)", list(SAGLAYICILAR), index=0)

model_key = f"model_{provider}"
if model_key not in st.session_state:
    st.session_state[model_key] = runner.VARSAYILAN_MODELLER[provider]
model = st.sidebar.text_input("Model adı", key=model_key)

farkli_yargic = st.sidebar.checkbox(
    "Yargıcı test edilen modelden ayır (önerilir — Deney 2/5 için)",
    value=True,
)
if farkli_yargic:
    judge_provider = st.sidebar.selectbox(
        "Yargıç sağlayıcı", list(SAGLAYICILAR),
        index=list(SAGLAYICILAR).index("anthropic"),
    )
    judge_model_key = f"judge_model_{judge_provider}"
    if judge_model_key not in st.session_state:
        st.session_state[judge_model_key] = runner.VARSAYILAN_MODELLER[judge_provider]
    judge_model = st.sidebar.text_input("Yargıç model adı", key=judge_model_key)
else:
    judge_provider, judge_model = provider, model

tekrar = st.sidebar.slider("Senaryo başına tekrar", 1, 10, 2)
retriever = st.sidebar.selectbox("Deney 2 getirici", ["tfidf", "st"], index=0)

st.sidebar.divider()
secilen_deneyler = st.sidebar.multiselect(
    "Çalıştırılacak deneyler",
    options=["1", "2", "3", "4", "5"],
    default=["1", "2", "3", "4", "5"],
    format_func=lambda k: DENEY_ETIKETLERI[k],
)

if not mock:
    st.sidebar.warning(
        "Mock modu KAPALI — bu koşu seçtiğiniz sağlayıcıya gerçek API "
        "çağrıları yapacak ve ücretlendirilecektir. Deney 5 özellikle "
        "pahalıdır (senaryo × tekrar başına 6 çağrı)."
    )

calistir = st.sidebar.button("▶ Çalıştır", type="primary", use_container_width=True,
                              disabled=not secilen_deneyler)

# =======================================================================
# ANA ALAN
# =======================================================================
st.title("Makale 1 — Davranışsal Doğrulama Paneli")
st.caption(
    "Vergi Hukukunda Klasik Yorum Yöntemleri ile Büyük Dil Modellerinin "
    "Hesaplama Mimarisi Arasında Kavramsal Bir Eşleştirme — çok sağlayıcılı "
    "ablasyon testleri (Anthropic / OpenAI / Google Gemini)."
)

sekme_calistir, sekme_rapor, sekme_gecmis, sekme_hakkinda = st.tabs(
    ["▶ Çalıştır", "📊 Sonuç Raporu", "🗂 Geçmiş Koşular", "ℹ️ Hakkında"]
)

# ------------------------- SEKME: ÇALIŞTIR ------------------------------
with sekme_calistir:
    if calistir:
        if not mock and not durum.get(provider.capitalize() if provider != "openai" else "OpenAI", False):
            # basit anahtar kontrolü (gemini/anthropic/openai eşlemesi)
            eslesme = {"anthropic": "Anthropic", "openai": "OpenAI", "gemini": "Gemini"}
            if not durum.get(eslesme[provider], False):
                st.error(
                    f"{eslesme[provider]} için API anahtarı bulunamadı. "
                    "Mock modunu açık bırakın veya secrets.toml / "
                    "anahtarlar.env dosyasına anahtarı ekleyin."
                )
                st.stop()

        etiket = f"{provider}_{model.replace('/', '_')}_d{'-'.join(secilen_deneyler)}"
        if mock:
            etiket = "MOCK_" + etiket

        st.info(
            f"Model: **{provider}/{model}**  |  Yargıç: **{judge_provider}/{judge_model}**  |  "
            f"Tekrar: **{tekrar}**  |  Mock: **{mock}**  |  "
            f"Deneyler: **{', '.join(secilen_deneyler)}**"
        )

        log_yeri = st.empty()
        ilerleme = st.progress(0.0, text="Başlatılıyor…")

        try:
            client = LLMClient(provider, model, temperature=0.3, mock=mock)
            judge_client = LLMClient(judge_provider, judge_model, temperature=0.0, mock=mock)
            yazici = runner.SonucYazici(etiket)

            adimlar = [d for d in ["1", "2", "3", "4", "5"] if d in secilen_deneyler]
            toplam = len(adimlar)

            logger = StreamlitLogger(log_yeri)
            with contextlib.redirect_stdout(logger):
                for i, d in enumerate(adimlar):
                    print(f"\n=== {DENEY_ETIKETLERI[d]} ===")
                    if d == "1":
                        runner.deney1(client, tekrar, yazici)
                    elif d == "2":
                        runner.deney2(client, judge_client, tekrar, yazici, retriever)
                    elif d == "3":
                        runner.deney3(client, tekrar, yazici)
                    elif d == "4":
                        runner.deney4(client, tekrar, yazici)
                    elif d == "5":
                        runner.deney5(judge_client, tekrar, yazici)
                    ilerleme.progress((i + 1) / toplam, text=f"{DENEY_ETIKETLERI[d]} tamamlandı")

            yazici.kapat()
            st.session_state["son_jsonl"] = yazici.yol
            st.success(f"Koşu tamamlandı. Sonuç dosyası: `{os.path.relpath(yazici.yol, PAKET_DIZINI)}`")
            st.info("Sonuçları görmek için **📊 Sonuç Raporu** sekmesine geçin.")

        except Exception as e:  # noqa: BLE001
            st.error(f"Koşu sırasında hata oluştu: {e}")
            st.exception(e)
    else:
        st.write(
            "Sol paneldeki ayarları seçip **▶ Çalıştır** butonuna basın. "
            "İlk denemede *Mock modu*'nu açık bırakmanız önerilir — bu, "
            "hiçbir API çağrısı yapmadan boru hattının uçtan uca çalıştığını "
            "gösterir."
        )
        st.write(
            "Deney 5 (Ω/Ψ(w)) diğerlerinden daha pahalıdır: senaryo × tekrar "
            "başına 6 ayrı API çağrısı yapar (5 Ω bileşeni + F yargıcı)."
        )

# ------------------------- SEKME: SONUÇ RAPORU --------------------------
with sekme_rapor:
    son_jsonl = st.session_state.get("son_jsonl")
    if son_jsonl and os.path.exists(son_jsonl):
        st.caption(f"Son koşu: `{os.path.relpath(son_jsonl, PAKET_DIZINI)}`")
        if st.button("📄 Bu koşunun raporunu oluştur"):
            with st.spinner("Rapor üretiliyor…"):
                basarili, icerik = rapor_uret(son_jsonl)
            if basarili:
                st.markdown(icerik)
            else:
                st.error(icerik)
    else:
        st.write(
            "Henüz bu oturumda bir koşu çalıştırılmadı. **▶ Çalıştır** "
            "sekmesinden bir koşu başlatın, veya **🗂 Geçmiş Koşular** "
            "sekmesinden daha önceki bir sonuç dosyasını seçin."
        )

# ------------------------- SEKME: GEÇMİŞ KOŞULAR -------------------------
with sekme_gecmis:
    dosyalar = tum_sonuc_dosyalarini_listele()
    if not dosyalar:
        st.write(
            "`results/` veya `results_arsiv/` klasöründe henüz bir "
            ".jsonl dosyası yok."
        )
    else:
        st.subheader("Tekil rapor")
        secilen_tek = st.selectbox(
            "Dosya seçin", dosyalar, format_func=dosya_etiketi, key="tekil_secim"
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📄 Rapor oluştur", key="tekil_rapor_buton"):
                with st.spinner("Rapor üretiliyor…"):
                    basarili, icerik = rapor_uret(secilen_tek)
                if basarili:
                    st.markdown(icerik)
                else:
                    st.error(icerik)
        with col2:
            if st.button("👁 Ham kayıtları önizle", key="onizle_buton"):
                try:
                    kayitlar = jsonl_oku(secilen_tek)
                    st.write(f"Toplam kayıt: {len(kayitlar)}")
                    st.dataframe(kayitlar[:200], use_container_width=True)
                except Exception as e:  # noqa: BLE001
                    st.error(f"Dosya okunamadı: {e}")

        st.divider()
        st.subheader("Çapraz model karşılaştırması")
        secilen_coklu = st.multiselect(
            "Karşılaştırılacak dosyalar (birden çok model ailesi seçin)",
            dosyalar, format_func=dosya_etiketi, key="coklu_secim",
        )
        if st.button("📊 Çapraz rapor oluştur", disabled=len(secilen_coklu) < 2):
            with st.spinner("Çapraz rapor üretiliyor…"):
                basarili, icerik = capraz_rapor_uret(secilen_coklu)
            if basarili:
                st.markdown(icerik)
            else:
                st.error(icerik)
        if len(secilen_coklu) < 2:
            st.caption("Çapraz rapor için en az iki dosya seçmelisiniz.")

# ------------------------- SEKME: HAKKINDA -------------------------------
with sekme_hakkinda:
    st.markdown(
        """
Bu panel, `vergi_llm_test` paketinin (Makale 1 davranışsal doğrulama testleri)
komut satırı işlevlerini tarayıcı üzerinden kullanılabilir hâle getirir.
Kod mantığı `runner.py` / `report.py` / `capraz_rapor.py` dosyalarındadır;
bu panel yalnızca bir arayüz katmanıdır.

**Kapsam:** Beş deney, Makale 1'in beş kavramsal-matematiksel katmanını
(B^legal — 4.3.2; RAG düzeltmesi — 4.4.1-4.4.2; M^const/M^leg — 4.6.2/4.6.6;
K maskesi — 4.8.1; Ω/Ψ(w) — 4.9.2-4.9.3) sınayan ablasyon deneyleridir.

**Sınırlamalar (özet):**
- Davranışsal (kara kutu) testlerdir; mekanistik iddiaları (embedding/attention
  düzeyi) sınamaz.
- Senaryo sayıları (deney başına 3-8) yayın kalitesinin altındadır; bu bir
  şablondur.
- Deney 5'te yargıç modelinin öznel puanlaması, makalenin kendi öngördüğü
  kalibrasyon ihtiyacını doğrulayan bir bulgu üretmiştir.

Ayrıntılı metodoloji için repo kökündeki `README.md` ve
`MAKALE1_REVIZYON_NOTLARI.md` dosyalarına bakınız.
        """
    )
    st.divider()
    st.caption(
        "API anahtarları hiçbir zaman bu arayüzde görüntülenmez veya "
        "loglanmaz; yalnızca ortam değişkenlerine yüklenip doğrudan ilgili "
        "SDK'ya (anthropic / openai / google-genai) iletilir."
    )
