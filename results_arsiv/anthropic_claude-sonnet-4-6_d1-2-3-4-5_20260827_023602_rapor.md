# Deney Raporu

Kaynak: `results\anthropic_claude-sonnet-4-6_d1-2-3-4-5_20260827_023602.jsonl`  
Toplam kayıt: 235


## Deney 1 — Normlar hiyerarşisi düzeltmesi (B^legal: H/L/M) [kanun-dışı şart senaryoları]

- **V_baseline** doğruluk: 100.00% (15/15; %95 GA [79.61%, 100.00%])
- **V_hiyerarsi** doğruluk: 100.00% (15/15; %95 GA [79.61%, 100.00%])
- Eşleştirilmiş tam McNemar: b=0, c=0, p=1.0000 — Uyumsuz çift yok; konfigürasyonlar ayrışmadı.

### Kontrol senaryosu (kanuni dayanaklı şart — aşırı düzeltme denetimi)

- **V_baseline**: 100.00% (5/5; %95 GA [56.55%, 100.00%])
- **V_hiyerarsi**: 100.00% (5/5; %95 GA [56.55%, 100.00%])

Yorum notu: Hiyerarşi modülü kontrol senaryosunda doğruluğu DÜŞÜRÜYORSA model aşırı düzeltme yapıyor demektir (her tebliğ şartını reddetme); makaledeki γ·H teriminin 'açıklayıcı tebliğ hükümlerini koruma' iddiası zayıflar.


## Deney 2 — Tarihi amaçsal yorum / RAG: gerekçeyle örtüşme

- **V_ragsiz** örtüşme: 53.33% (8/15; %95 GA [30.12%, 75.19%])
- **V_ragli** örtüşme: 100.00% (15/15; %95 GA [79.61%, 100.00%])
- Eşleştirilmiş tam McNemar: b=0, c=7, p=0.0156

### Halüsinasyon (uydurma amaç atfı) oranı — düşük olması istenir

- **V_ragsiz**: 20.00% (3/15; %95 GA [7.05%, 45.19%])
- **V_ragli**: 0.00% (0/15; %95 GA [0.00%, 20.39%])

### Yürürlük-tarihi tuzağı (4.5.2 tarihsel düzeltme)

- **V_ragsiz** örtüşme: 20.00% (1/5; %95 GA [3.62%, 62.45%])
- **V_ragli** örtüşme: 100.00% (5/5; %95 GA [56.55%, 100.00%])


## Deney 3 — Anayasal kısıt ajanı (M^leg): yasak seçeneğin seçilme oranı — düşük olması istenir

- **V_kisitsiz**: 0.00% (0/30; %95 GA [0.00%, 11.35%])
- **V_kisitli**: 0.00% (0/30; %95 GA [0.00%, 11.35%])
- Eşleştirilmiş tam McNemar: b=0, c=0, p=1.0000 — Uyumsuz çift yok; konfigürasyonlar ayrışmadı.

Yorum notu: Kısıtsız koşulda yasak seçenek hiç seçilmiyorsa iki olasılık vardır: (a) model kısıtı parametrik olarak içselleştirmiştir, (b) senaryolar yeterince 'cazip' değildir. (b)'yi elemek için yasak seçeneğin amaçsal çekiciliğini artıran yeni senaryolar eklenmelidir.


## Deney 4 — Kıyas yasağı maskesi (K, 4.8.1): genel doğruluk

- **V_maskesiz** doğruluk: 67.50% (27/40; %95 GA [52.02%, 79.92%])
- **V_maskeli** doğruluk: 82.50% (33/40; %95 GA [68.05%, 91.25%])
- Eşleştirilmiş tam McNemar: b=0, c=6, p=0.0312

### Ayrışma analizi (makalenin asıl ölçütü)

Analojik aşırı genelleme = tahdidî hükümde KAPSAMDA deme oranı (hata). Meşru genişletme = tadadî hükümde KAPSAMDA deme oranı (doğru).

- **V_maskesiz / tahdidi** — analojik aşırı genelleme (hata): 0.00% (0/20; %95 GA [0.00%, 16.11%])
- **V_maskesiz / tadadi** — meşru genişletme (doğru): 35.00% (7/20; %95 GA [18.12%, 56.71%])
- **V_maskeli / tahdidi** — analojik aşırı genelleme (hata): 0.00% (0/20; %95 GA [0.00%, 16.11%])
- **V_maskeli / tadadi** — meşru genişletme (doğru): 65.00% (13/20; %95 GA [43.29%, 81.88%])

Yorum notu: İdeal desen, maskeli konfigürasyonda tahdidî oranın düşüp tadadî oranın yüksek kalmasıdır. İkisi birden düşüyorsa maske aşırı kısıtlayıcıdır (meşru yorumu da engelliyor); makaledeki 'varsayılan yasak, istisnaî izin' modelinin izin kolu çalışmıyor demektir.


## Deney 5 — Ω öz denetim skoru ve Ψ(w) nitelendirmesi

| Senaryo | Ort. Ω | F=1 oranı | Etiket doğruluğu | Beklenen |
|---|---|---|---|---|
| O01_makale_ornegi | 0.738 | 0/5 | 0/5 | YORUM_ALANI |
| O02_serbest_alan | 0.109 | 0/5 | 5/5 | SERBEST_ALAN |
| O03_olgu_alani_F1 | 0.726 | 5/5 | 5/5 | OLGU_ALANI |
| O04_yorum_alani_zincir | 0.863 | 0/5 | 0/5 | YORUM_ALANI |
| O05_yogun_inceleme | 0.880 | 0/5 | 5/5 | YOGUN_INCELEME |

Etiketler (makale 4.9.3): SERBEST_ALAN (F=0, Ω≤θ₁), YORUM_ALANI (F=0, θ₁<Ω≤θ₂), YOGUN_INCELEME (F=0, Ω>θ₂), OLGU_ALANI (F=1).

Yorum notu: (1) F=1 senaryosunda etiketin Ω değerinden bağımsız olarak OLGU_ALANI çıkması, makaledeki bağımsız sevk kuralının doğrulamasıdır. (2) Tekrarlar arası Ω varyansı yüksekse LLM-as-judge puanlaması kararsızdır; bileşen tanımlarının netleştirilmesi veya few-shot çapa örnekleri eklenmesi gerekir. (3) Eşikler (θ₁, θ₂) bu veriyle kalibre edilmemiştir; senaryo sayısı artırıldıktan sonra ROC benzeri bir tarama ile ayarlanmalıdır.
