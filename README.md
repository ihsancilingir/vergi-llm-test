# Makale 1 Davranışsal Doğrulama Test Ajanı (v2 — çok sağlayıcılı)

Çilingir — *Vergi Hukukunda Klasik Yorum Yöntemleri ile Büyük Dil Modellerinin
Hesaplama Mimarisi Arasında Kavramsal Bir Eşleştirme* (Makale 1) içindeki
mimari iddiaların **davranışsal (kara kutu, ablasyon)** testleri.

**v2 yenilikleri:** Google **Gemini** üçüncü sağlayıcı olarak eklendi;
API anahtarları tek dosyadan (`anahtarlar.env`) okunuyor; üç model
ailesinde arka arkaya koşu betiği (`tum_modeller.sh`) ve modeller arası
çapraz karşılaştırma raporu (`capraz_rapor.py`) eklendi.

**v2.1 — makale hizalaması (revize docx denetimi sonrası):**
- **Ψ(w) düzeltmesi (esaslı):** Makale 4.9.3 DÖRT çıktı tanımlar; F=0 ve
  Ω>θ₂ hâli OLGU_ALANI değil **YOGUN_INCELEME** yönlendirmesidir ("yüksek
  Ω hiçbir zaman tek başına kaçakçılık isnadını desteklemez"). Önceki
  sürüm bu hâli yanlışlıkla olgu alanına atıyordu; düzeltildi ve bu kolu
  sınayan yeni senaryo (O05) eklendi. Aralık sınırları da makaledeki
  kapalı biçime (Ω≤θ₁, θ₁<Ω≤θ₂) çekildi.
- **Terim hizalaması:** "γ·H" → makaledeki B^legal = H+S+T+L+M (denk. 3;
  γ makalede 4.2.2'nin pragmatik eksen katsayısıdır, farklı kavram);
  "M^kıyas" → K maskesi (4.8.1); Deney 3 maskesi → M^const (4.6.2) +
  M^leg (4.6.6).
- **Bölüm numaraları:** Deney 2 → 4.4 (yürürlük tuzağı 4.4.2); Deney 3 →
  4.5–4.6. (Önceki etiketler makalenin bölünme öncesi numaralandırmasını
  taşıyordu.)
- K01 senaryosundaki AYM karar tarihi makaleyle eşitlendi (29.6.2022).

> Lâfzî yorum ↔ embedding eşleştirmesi (Bölüm 4.2) bu pakete dahil
> DEĞİLDİR; ilgili ampirik kanıt yazarın önceki yayınında (Çilingir, 2025)
> mevcuttur ve atıfla karşılanmaktadır.

## Deney–makale eşlemesi

| Deney | Makale bölümü | Test edilen terim | Konfigürasyon çifti | Ana ölçüt |
|---|---|---|---|---|
| 1 | 4.3.2 | Normatif düzeltme B^legal = H+S+T+L+M (özellikle H, L, M bileşenleri) | V_baseline / V_hiyerarsi | Kanun-dışı tebliğ şartını uygulama oranı |
| 2 | 4.4 (4.4.2) | Tarihsel-normatif RAG düzeltmesi (β₁s+β₂T+β₃H+β₄A+M) | V_ragsiz / V_ragli | Gerekçe örtüşmesi; halüsinasyon; yürürlük tuzağı (T_i/M_i) |
| 3 | 4.5–4.6 (4.6.2, 4.6.6) | Anayasal maske M^const + kanunilik maskesi M^leg | V_kisitsiz / V_kisitli | Yasak (kanuniliğe aykırı) seçeneğin seçilme oranı |
| 4 | 4.8 (4.8.1) | Kıyas maskesi K (izin kuralı, numerus clausus) | V_maskesiz / V_maskeli | Tahdidî/tadadî ayrışması; analojik aşırı genelleme |
| 5 | 4.9 (4.9.2–4.9.3) | Ω öz denetim skoru, Ψ(w) DÖRT çıktılı nitelendirme, F kuralı | (yargıç boru hattı) | Nitelendirme doğruluğu; F bağımsızlığı; YOGUN_INCELEME kolu |

## Kurulum

```bash
pip install -r requirements.txt
# İsteğe bağlı (Deney 2'de yoğun embedding getiricisi için):
pip install sentence-transformers
```

## API anahtarları

```bash
cp anahtarlar.env.example anahtarlar.env
# anahtarlar.env dosyasını açıp kendi anahtarlarınızı yazın:
#   ANTHROPIC_API_KEY=...
#   OPENAI_API_KEY=...
#   GEMINI_API_KEY=...
```

`runner.py` bu dosyayı her koşuda otomatik okur. Ortam değişkeni zaten
tanımlıysa dosyadaki değer onu ezmez. Dosya `.gitignore`'a dahildir;
paylaşmayın.

## Çalıştırma

```bash
# 1) Boru hattını API'siz doğrula (sonuçlar anlamsızdır, sadece teknik test):
python runner.py --deney hepsi --mock --tekrar 2

# 2) Tek model, gerçek koşu:
python runner.py --deney hepsi --provider anthropic \
    --model claude-sonnet-4-6 --tekrar 10
python runner.py --deney hepsi --provider gemini \
    --model gemini-2.5-pro --tekrar 10

# 3) Yargıcı test edilen modelden ayırma (önerilir — öz-puanlama
#    yanlılığını azaltır):
python runner.py --deney 2,5 --provider openai --model gpt-4o \
    --judge-provider anthropic --judge-model claude-sonnet-4-6

# 4) ÜÇ MODEL AİLESİNDE tam koşu (metodolojik not 6'nın gereği):
bash tum_modeller.sh              # tüm deneyler, tekrar=5
bash tum_modeller.sh "1,4" 10     # sadece 1 ve 4, tekrar=10

# 5) Raporlar:
python report.py results/<dosya>.jsonl        # tek model raporu
python capraz_rapor.py results/*.jsonl        # modeller arası çapraz tablo
```

Model adları için varsayılanlar `runner.py` içindeki
`VARSAYILAN_MODELLER` sözlüğündedir (anthropic: claude-sonnet-4-6,
openai: gpt-4o, gemini: gemini-2.5-pro); yeni sürümler çıktıkça
`--model` bayrağıyla veya sözlükten güncelleyin.

## Metodolojik notlar (makaleye/hakem yanıtlarına taşınabilir)

1. **Davranışsal ≠ mekanistik.** API üzerinden yapılan bu testler
   modelin içine bakmaz; girdi manipülasyonunun çıktı üzerindeki etkisini
   ölçer (ablasyon). Attention/embedding düzeyindeki mekanizma iddiaları
   için açık ağırlıklı modellerle (`transformers`) ayrı bir mekanistik
   çalışma gerekir.
2. **Sentetik mevzuat.** Gerçek kanun/tebliğ metinleri modellerin eğitim
   verisinde bulunabilir; ezber ile muhakemeyi ayırmak için sentetik
   hükümler kullanılmıştır (krş. Blair-Stanek vd. 2023'ün sentetik kanun
   yaklaşımı).
3. **Eşleştirilmiş tasarım.** Aynı senaryo-tekrar çifti her iki
   konfigürasyonda koşulur; karşılaştırma tam (exact) McNemar ile yapılır.
   Tekrarlar tam bağımsız gözlem olmadığından (senaryo kümeleme etkisi)
   asıl istatistiksel güç senaryo sayısını artırmaktan gelir — buradaki
   3-4 senaryo/deney bir ŞABLONDUR; yayın için deney başına 20-30 senaryo
   hedeflenmelidir.
4. **Yargıç ayrımı.** Deney 2 ve 5'te LLM-as-judge kullanılır; yargıç
   modelinin test edilen modelden farklı seçilmesi ve yargıç
   temperature=0 koşulması önerilir. Yargıcın kendisinin güvenilirliği
   için küçük bir alt kümede insan-yargıç uyumu (Cohen's κ) raporlanmalıdır.
   `tum_modeller.sh` yargıcı SABİT tutar; böylece üç test modeli aynı
   yargıçla puanlanır ve karşılaştırma yargıç farkından etkilenmez.
5. **Kontrol senaryoları.** Deney 1'deki H04 (kanuni dayanaklı şart) ve
   Deney 4'teki tadadî sürümler, düzeltme modüllerinin AŞIRI düzeltme
   yapıp yapmadığını denetler. Bir güvenlik katmanının değeri yalnızca
   yanlışı engellemesinde değil, doğruyu engellemMEmesindedir — makaledeki
   "izin kuralı" tasarımının test karşılığı budur.
6. **Çoklu model.** Mimari iddia tek modelde doğrulanamaz; aynı deseni en
   az 2-3 model ailesinde göstermek gerekir. Bu sürümde üç aile
   (Anthropic, OpenAI, Google) desteklenir; `tum_modeller.sh` +
   `capraz_rapor.py` bu karşılaştırmayı otomatikleştirir.
7. **Kapsam notu.** Makalenin 4.5 (amacın olasılıksal çıkarımı) ve
   4.4.4 (niyet kısıtı) modelleri için ayrı bir deney yoktur; Deney 2
   amaç tespitine yalnızca dolaylı dokunur. Ayrıca 4.8.1'deki izin
   kuralının ÜÇÜNCÜ koşulu (yön denetimi: genişletme mükellef aleyhine
   sonuç doğuramaz) mevcut senaryolarda sınanmaz — tadadî bir CEZA
   hükmü çifti eklenerek test edilebilir. Bunlar senaryo genişletme
   aşamasının doğal adaylarıdır.
8. **Deterministik oracle.** Sayısal sonuç gerektiren senaryolar
   eklendiğinde altın standart, yazarın JavaScript vergi hesaplama
   kütüphanesinden üretilmelidir (elle etiketleme hatasını sıfırlar).

## Dosya yapısı

```
vergi_llm_test/
├── runner.py               # ana koşucu (CLI, anahtarlar.env'i okur)
├── tum_modeller.sh         # üç model ailesinde arka arkaya koşu
├── report.py               # JSONL → Markdown rapor (tek model)
├── capraz_rapor.py         # çoklu JSONL → çapraz model tablosu
├── prompts.py              # yorum katmanlarının prompt modülü karşılıkları
├── llm_client.py           # Anthropic/OpenAI/Gemini istemcisi + mock modu
├── judge.py                # ayrıştırıcılar ve LLM-as-judge
├── rag.py                  # TF-IDF / sentence-transformers getirici
├── stats.py                # tam McNemar, Wilson GA
├── anahtarlar.env.example  # API anahtar şablonu (kopyalayıp doldurun)
├── scenarios/              # deney senaryoları (JSON) — genişletilecek şablonlar
└── results/                # JSONL sonuçlar ve raporlar
```

## Senaryo ekleme

Her deneyin JSON şeması kendi dosyasındaki mevcut kayıtlarla örneklenmiştir;
yeni senaryo eklemek için ilgili listeye aynı alanlarla kayıt eklemeniz
yeterlidir. Deney 4'te senaryolar **çift** hâlinde eklenmelidir (aynı
`cift_id` ile tahdidî + tadadî sürüm); ayrışma analizi bu çiftler üzerinden
çalışır.
