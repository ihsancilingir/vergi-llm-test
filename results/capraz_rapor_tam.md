# Çapraz Model Raporu (ham kayıtlardan yeniden üretilmiş sürüm)

Bu rapor `tables/tablolar.py` tarafından `results/` klasöründeki ham kayıtlardan üretilir. Oranların paydası çözümlenebilen ölçüm sayısıdır; modelin çözümlenebilir bir karar üretmediği ölçümler (`karar`/`secim` = None) köşeli parantez içinde ayrıca gösterilir ve hiçbir orana dâhil edilmez.

Modeller: anthropic/claude-sonnet-4-6, openai/gpt-4o, gemini/gemini-3.6-flash, deepseek/deepseek-v4-flash, grok/grok-4.6, kumru/vngrs-ai/Kumru-2B

## Deney 1 — Normlar hiyerarşisi (B^legal): kanun-dışı şart senaryolarında doğruluk

Beklenen desen: ana senaryolarda V_hiyerarsi ↑; kontrol senaryolarında (kanuni dayanağı olan şart) düşüş YOK (aşırı düzeltme denetimi).

| Model | V_baseline | V_hiyerarsi | Kontrol/baseline | Kontrol/hiyerarşi |
|---|---|---|---|---|
| Claude Sonnet 4.6 | 100% (120/120) | 100% (120/120) | 75% (30/40) | 50% (20/40) |
| GPT-4o | 9% (11/120) | 100% (120/120) | 100% (40/40) | 50% (20/40) |
| Gemini 3.6 Flash | 100% (120/120) | 100% (120/120) | 50% (20/40) | 50% (20/40) |
| DeepSeek v4-flash | 87% (104/119) [1 çözümlenemeyen] | 100% (120/120) | 98% (39/40) | 50% (20/40) |
| Grok 4.6 | 100% (120/120) | 100% (120/120) | 50% (20/40) | 42% (17/40) |
| Kumru-2B | 28% (34/120) | 74% (89/120) | 50% (20/40) | 35% (14/40) |

## Deney 2 — RAG: gerekçe örtüşmesi / halüsinasyon (yargıç modelce puanlanmıştır)

Beklenen desen: örtüşme ↑, halüsinasyon ↓ (RAG'lı sütunlarda). Halüsinasyon = gerekçede bulunmayan bir amacın uydurulması.

| Model | Örtüşme RAG'sız | Örtüşme RAG'lı | Halüsinasyon RAG'sız | Halüsinasyon RAG'lı |
|---|---|---|---|---|
| Claude Sonnet 4.6 | 72% (101/140) | 93% (130/140) | 5% (7/140) | 9% (12/140) |
| GPT-4o | 67% (94/140) | 93% (130/140) | 34% (47/140) | 7% (10/140) |
| Gemini 3.6 Flash | 76% (106/140) | 93% (130/140) | 23% (32/140) | 7% (10/140) |
| DeepSeek v4-flash | 59% (83/140) | 92% (129/140) | 16% (23/140) | 8% (11/140) |
| Grok 4.6 | 9% (13/140) | 93% (130/140) | 0% (0/140) | 7% (10/140) |
| Kumru-2B | 8% (11/140) | 68% (95/140) | 95% (133/140) | 64% (90/140) |

## Deney 3 — Anayasal kısıt (M^const): üç seçenek arasında seçim dağılımı

I₂ kanunilik ilkesini ihlal eden yasak seçenektir; I₁ ve I₃ kabul edilebilir seçeneklerdir. "Belirsiz" = birden çok seçenek işaretlendi; "çözümlenemeyen" = cevaptan seçim çıkarılamadı. Yasak seçim oranının paydası çözümlenen ölçüm sayısıdır; çözümlenen sayısı düşük olan satırlar (özellikle Kumru-2B) yorumlanamaz.

| Model | Koşul | I₂ yasak / çözümlenen | I₁ | I₃ | Belirsiz | Çözümlenemeyen |
|---|---|---|---|---|---|---|
| Claude Sonnet 4.6 | V_kisitsiz | 0% (0/160) | 142 | 18 | 0 | 0 |
| Claude Sonnet 4.6 | V_kisitli | 0% (0/160) | 134 | 10 | 16 | 0 |
| GPT-4o | V_kisitsiz | 0% (0/160) | 160 | 0 | 0 | 0 |
| GPT-4o | V_kisitli | 0% (0/160) | 160 | 0 | 0 | 0 |
| Gemini 3.6 Flash | V_kisitsiz | 0% (0/160) | 158 | 2 | 0 | 0 |
| Gemini 3.6 Flash | V_kisitli | 0% (0/160) | 159 | 1 | 0 | 0 |
| DeepSeek v4-flash | V_kisitsiz | 0% (0/155) | 136 | 19 | 0 | 5 |
| DeepSeek v4-flash | V_kisitli | 0% (0/127) | 97 | 30 | 0 | 33 |
| Grok 4.6 | V_kisitsiz | 0% (0/160) | 152 | 8 | 0 | 0 |
| Grok 4.6 | V_kisitli | 0% (0/160) | 154 | 6 | 0 | 0 |
| Kumru-2B | V_kisitsiz | 0% (0/31) | 23 | 7 | 1 | 129 |
| Kumru-2B | V_kisitli | 0% (0/6) | 4 | 1 | 1 | 154 |

## Deney 4 — Kıyas maskesi (K): tahdidî hükümde KAPSAMDA deme (hata) / tadadî hükümde KAPSAMDA deme (doğru)

Beklenen desen: maskeli sütunda tahdidî hata ↓, tadadî doğruluk yüksek kalır (ayrışma). İkisi birden düşerse maske aşırı kısıtlayıcıdır.

| Model | Tahdidî/maskesiz (hata) | Tahdidî/maskeli (hata) | Tadadî/maskesiz (doğru) | Tadadî/maskeli (doğru) |
|---|---|---|---|---|
| Claude Sonnet 4.6 | 10% (10/100) | 8% (8/100) | 58% (58/100) | 76% (76/100) |
| GPT-4o | 27% (27/100) | 6% (6/100) | 80% (80/100) | 91% (91/100) |
| Gemini 3.6 Flash | 17% (17/100) | 10% (10/100) | 83% (83/100) | 92% (92/100) |
| DeepSeek v4-flash | 24% (24/99) [1 çözümlenemeyen] | 6% (6/100) | 67% (67/100) | 75% (73/97) [3 çözümlenemeyen] |
| Grok 4.6 | 13% (13/100) | 10% (10/100) | 56% (56/100) | 68% (68/100) |
| Kumru-2B | 76% (75/99) [1 çözümlenemeyen] | 51% (47/93) [7 çözümlenemeyen] | 96% (95/99) [1 çözümlenemeyen] | 72% (68/95) [5 çözümlenemeyen] |

## Deney 5 — Ω / Ψ(w): dört çıktılı nitelendirme (yalnızca yargıç model çalışır)

Bu deneyde test modeli çağrılmaz; bileşen puanları, F ve Ω tamamen yargıç model tarafından üretilir. Aşağıdaki satırlar bu nedenle yargıç bazında verilmiştir. Yargıç sıcaklık 0 ile koşulmuş, tekrarlar neredeyse özdeş çıkmıştır (Ω senaryo içi std. sapması sütunda).

| Yargıç | Etiket doğruluğu | F=1 → OLGU_ALANI | Ortalama Ω | Senaryo içi Ω sd | Uyumsuzluk dağılımı |
|---|---|---|---|---|---|
| claude-sonnet-4-6 | 73% (110/150) | 30/30 | 0.622 | 0.007 | YORUM_ALANI→YOGUN_INCELEME: 40 |
| gpt-4o | 72% (108/150) | 30/30 | 0.690 | 0.014 | YORUM_ALANI→YOGUN_INCELEME: 40; SERBEST_ALAN→YORUM_ALANI: 2 |

Not: Altı sağlayıcı dosyasındaki Deney 5 kayıtlarının tamamı aynı yargıçla (claude-sonnet-4-6) üretildiğinden birbirinin tekrarıdır (110/150, 30/30, Ω ≈ 0,62); ikinci yargıç koşusu ayrı dosyadadır (`*_d5_*.jsonl`).

## Deney 6 — Temsil düzeyi: kanuni-teknik terim çiftleri ile kontrol çiftlerinin kosinüs benzerliği

| Sağlayıcı | Kapalı lâfzî (n=8) | Açık lâfzî (n=6) | Kontrol (n=6) | U | p (tek yönlü, kesin) | Lâfzî maks / kontrol min |
|---|---|---|---|---|---|---|
| gemini | 0.701 | 0.690 | 0.793 | 77.0 | 0.001135 | 0.777 / 0.709 |
| kumru | 0.512 | 0.497 | 0.800 | 84.0 | 2.58e-05 | 0.588 / 0.739 |
| openai | 0.429 | 0.444 | 0.667 | 82.0 | 0.0001032 | 0.575 / 0.544 |
