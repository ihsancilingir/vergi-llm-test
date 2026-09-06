# Çapraz Model Raporu

Modeller: anthropic/claude-sonnet-4-6, deepseek/deepseek-v4-flash, gemini/gemini-3.6-flash, grok/grok-4.6, kumru/vngrs-ai/Kumru-2B, openai/gpt-4o


## Deney 1 — Normlar hiyerarşisi (B^legal: H/L/M): doğruluk (kanun-dışı şart senaryoları)

Beklenen desen: ana senaryolarda V_hiyerarsi ↑, kontrolde düşüş YOK (aşırı düzeltme denetimi).

| Model | V_baseline | V_hiyerarsi | Kontrol/baseline | Kontrol/hiyerarşi |
|---|---|---|---|---|
| anthropic/claude-sonnet-4-6 | 100% (120/120) | 100% (120/120) | 75% (30/40) | 50% (20/40) |
| deepseek/deepseek-v4-flash | 87% (104/119) | 100% (120/120) | 98% (39/40) | 50% (20/40) |
| gemini/gemini-3.6-flash | 100% (120/120) | 100% (120/120) | 50% (20/40) | 50% (20/40) |
| grok/grok-4.6 | 100% (120/120) | 100% (120/120) | 50% (20/40) | 42% (17/40) |
| kumru/vngrs-ai/Kumru-2B | 28% (34/120) | 74% (89/120) | 50% (20/40) | 35% (14/40) |
| openai/gpt-4o | 9% (11/120) | 100% (120/120) | 100% (40/40) | 50% (20/40) |

## Deney 2 — RAG: gerekçe örtüşmesi / halüsinasyon

Beklenen desen: örtüşme ↑, halüsinasyon ↓ (RAG'lı sütunlarda).

| Model | Örtüşme RAG'sız | Örtüşme RAG'lı | Halüsinasyon RAG'sız | Halüsinasyon RAG'lı |
|---|---|---|---|---|
| anthropic/claude-sonnet-4-6 | 72% (101/140) | 93% (130/140) | 5% (7/140) | 9% (12/140) |
| deepseek/deepseek-v4-flash | 59% (83/140) | 92% (129/140) | 16% (23/140) | 8% (11/140) |
| gemini/gemini-3.6-flash | 76% (106/140) | 93% (130/140) | 23% (32/140) | 7% (10/140) |
| grok/grok-4.6 | 9% (13/140) | 93% (130/140) | 0% (0/140) | 7% (10/140) |
| kumru/vngrs-ai/Kumru-2B | 8% (11/140) | 68% (95/140) | 95% (133/140) | 64% (90/140) |
| openai/gpt-4o | 67% (94/140) | 93% (130/140) | 34% (47/140) | 7% (10/140) |

## Deney 3 — Anayasal kısıt (M^const/M^leg): yasak seçeneğin seçilme oranı (düşük iyi)

Beklenen desen: kısıtlı konfigürasyonda oran ↓ (veya her ikisinde 0 ise parametrik içselleştirme tartışılır).

| Model | V_kisitsiz | V_kisitli |
|---|---|---|
| anthropic/claude-sonnet-4-6 | 0% (0/160) | 0% (0/160) |
| deepseek/deepseek-v4-flash | 0% (0/160) | 0% (0/160) |
| gemini/gemini-3.6-flash | 0% (0/160) | 0% (0/160) |
| grok/grok-4.6 | 0% (0/160) | 0% (0/160) |
| kumru/vngrs-ai/Kumru-2B | 0% (0/160) | 0% (0/160) |
| openai/gpt-4o | 0% (0/160) | 0% (0/160) |

## Deney 4 — Kıyas maskesi (K): KAPSAMDA deme oranı

Beklenen desen: maskeli sütunda tahdidî ↓, tadadî yüksek kalır (ayrışma). İkisi birden düşerse maske aşırı kısıtlayıcıdır.

| Model | Tahdidî/maskesiz (hata) | Tahdidî/maskeli (hata) | Tadadî/maskesiz (doğru) | Tadadî/maskeli (doğru) |
|---|---|---|---|---|
| anthropic/claude-sonnet-4-6 | 10% (10/100) | 8% (8/100) | 58% (58/100) | 76% (76/100) |
| deepseek/deepseek-v4-flash | 24% (24/99) | 6% (6/100) | 67% (67/100) | 75% (73/97) |
| gemini/gemini-3.6-flash | 17% (17/100) | 10% (10/100) | 83% (83/100) | 92% (92/100) |
| grok/grok-4.6 | 13% (13/100) | 10% (10/100) | 56% (56/100) | 68% (68/100) |
| kumru/vngrs-ai/Kumru-2B | 76% (75/99) | 51% (47/93) | 96% (95/99) | 72% (68/95) |
| openai/gpt-4o | 27% (27/100) | 6% (6/100) | 80% (80/100) | 91% (91/100) |

## Deney 5 — Ω / Ψ(w): üçlü nitelendirme

F sütunu: F=1 saptanan tüm koşularda etiketin Ω'dan bağımsız olarak OLGU_ALANI çıkması beklenir (bağımsız sevk kuralı).

| Model | Etiket doğruluğu | F=1 → OLGU_ALANI sevki |
|---|---|---|
| anthropic/claude-sonnet-4-6 | 73% (110/150) | 30/30 |
| deepseek/deepseek-v4-flash | 73% (110/150) | 30/30 |
| gemini/gemini-3.6-flash | 73% (110/150) | 30/30 |
| grok/grok-4.6 | 73% (110/150) | 30/30 |
| kumru/vngrs-ai/Kumru-2B | 73% (110/150) | 30/30 |
| openai/gpt-4o | 73% (110/150) | 30/30 |

**Metodolojik not:** Deney 5, `--provider` ile secilen test modelini kullanmaz; F/Omega hesaplamasi tamamen `--judge-provider` ile secilen yargic tarafindan yapilir. Bu nedenle yukaridaki tabloda 'Model' sutunu aslinda yargici degil, o kosuda kullanilan --provider degerini gosterir ve farkli --provider degerleriyle alinan Deney 5 sonuclari AYNI YARGICLA uretilmisse birebir ozdes cikar (bu bir hata degildir). Deney 5, coklu-model karsilastirmasi degil, Omega/Psi(w) cercevesinin yargic-tutarliligini test eder.
