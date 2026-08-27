# Çapraz Model Raporu

Modeller: anthropic/claude-sonnet-4-6, gemini/gemini-3.1-pro-preview, openai/gpt-4o


## Deney 1 — Normlar hiyerarşisi (B^legal: H/L/M): doğruluk (kanun-dışı şart senaryoları)

Beklenen desen: ana senaryolarda V_hiyerarsi ↑, kontrolde düşüş YOK (aşırı düzeltme denetimi).

| Model | V_baseline | V_hiyerarsi | Kontrol/baseline | Kontrol/hiyerarşi |
|---|---|---|---|---|
| anthropic/claude-sonnet-4-6 | 100% (15/15) | 100% (15/15) | 100% (5/5) | 100% (5/5) |
| gemini/gemini-3.1-pro-preview | 100% (15/15) | 100% (15/15) | 100% (5/5) | 100% (5/5) |
| openai/gpt-4o | 20% (3/15) | 100% (15/15) | 100% (5/5) | 100% (5/5) |

## Deney 2 — RAG: gerekçe örtüşmesi / halüsinasyon

Beklenen desen: örtüşme ↑, halüsinasyon ↓ (RAG'lı sütunlarda).

| Model | Örtüşme RAG'sız | Örtüşme RAG'lı | Halüsinasyon RAG'sız | Halüsinasyon RAG'lı |
|---|---|---|---|---|
| anthropic/claude-sonnet-4-6 | 53% (8/15) | 100% (15/15) | 20% (3/15) | 0% (0/15) |
| gemini/gemini-3.1-pro-preview | 33% (5/15) | 100% (15/15) | 67% (10/15) | 0% (0/15) |
| openai/gpt-4o | 67% (10/15) | 100% (15/15) | 53% (8/15) | 0% (0/15) |

## Deney 3 — Anayasal kısıt (M^const/M^leg): yasak seçeneğin seçilme oranı (düşük iyi)

Beklenen desen: kısıtlı konfigürasyonda oran ↓ (veya her ikisinde 0 ise parametrik içselleştirme tartışılır).

| Model | V_kisitsiz | V_kisitli |
|---|---|---|
| anthropic/claude-sonnet-4-6 | 0% (0/30) | 0% (0/30) |
| gemini/gemini-3.1-pro-preview | 0% (0/30) | 0% (0/30) |
| openai/gpt-4o | 0% (0/30) | 0% (0/30) |

## Deney 4 — Kıyas maskesi (K): KAPSAMDA deme oranı

Beklenen desen: maskeli sütunda tahdidî ↓, tadadî yüksek kalır (ayrışma). İkisi birden düşerse maske aşırı kısıtlayıcıdır.

| Model | Tahdidî/maskesiz (hata) | Tahdidî/maskeli (hata) | Tadadî/maskesiz (doğru) | Tadadî/maskeli (doğru) |
|---|---|---|---|---|
| anthropic/claude-sonnet-4-6 | 0% (0/20) | 0% (0/20) | 35% (7/20) | 65% (13/20) |
| gemini/gemini-3.1-pro-preview | 0% (0/18) | 0% (0/15) | 47% (7/15) | 73% (11/15) |
| openai/gpt-4o | 20% (4/20) | 0% (0/20) | 75% (15/20) | 85% (17/20) |

## Deney 5 — Ω / Ψ(w): üçlü nitelendirme

F sütunu: F=1 saptanan tüm koşularda etiketin Ω'dan bağımsız olarak OLGU_ALANI çıkması beklenir (bağımsız sevk kuralı).

| Model | Etiket doğruluğu | F=1 → OLGU_ALANI sevki |
|---|---|---|
| anthropic/claude-sonnet-4-6 | 60% (30/50) | 10/10 |
| gemini/gemini-3.1-pro-preview | — | — |
| openai/gpt-4o | 60% (15/25) | 5/5 |
