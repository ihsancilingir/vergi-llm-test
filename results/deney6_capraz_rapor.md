# Deney 6: Embedding Katmani Testi -- Coklu Model Karsilastirmasi

## Kategori ortalamalari

| Saglayici | kapali_lafzi | acik_lafzi | kontrol |
|---|---|---|---|
| gemini | 0.7011 | 0.6903 | 0.7931 |
| kumru | 0.5116 | 0.4968 | 0.8001 |
| openai | 0.4286 | 0.4436 | 0.6675 |

## Istatistiksel anlamlilik (Mann-Whitney U)

| Saglayici | U | p | n_lafzi | n_kontrol | Sonuc |
|---|---|---|---|---|---|
| gemini | 77.00 | 0.0011 | 14 | 6 | anlamli |
| kumru | 84.00 | 0.0000 | 14 | 6 | anlamli |
| openai | 82.00 | 0.0001 | 14 | 6 | anlamli |

## Cift bazinda karsilastirma

| ID | Terim A | Terim B | Kategori | gemini | kumru | openai |
|---|---|---|---|---|---|---|
| E01 | teslim | teslim etmek | kapali_lafzi | 0.7766 | 0.5406 | 0.4649 |
| E02 | arizi kazanc | tek seferlik kazanc | kapali_lafzi | 0.7772 | 0.5880 | 0.5750 |
| E03 | emsal bedel | benzer fiyat | kapali_lafzi | 0.7499 | 0.3987 | 0.5510 |
| E04 | mukellef | sorumlu kisi | kapali_lafzi | 0.6676 | 0.5200 | 0.3936 |
| E05 | iktisap | satin alma | kapali_lafzi | 0.6805 | 0.5655 | 0.3908 |
| E06 | tevkifat | kesinti | kapali_lafzi | 0.6074 | 0.4232 | 0.3193 |
| E07 | istisna | muafiyet | kapali_lafzi | 0.7011 | 0.5816 | 0.4004 |
| E08 | vergiyi doguran olay | an | kapali_lafzi | 0.6487 | 0.4753 | 0.3335 |
| E09 | hizmet | is | acik_lafzi | 0.6544 | 0.4495 | 0.4086 |
| E10 | gelir | kazanc | acik_lafzi | 0.7380 | 0.4932 | 0.5381 |
| E11 | ticari kazanc | kar | acik_lafzi | 0.7191 | 0.5586 | 0.5037 |
| E12 | gayrimenkul | ev | acik_lafzi | 0.6951 | 0.5406 | 0.4629 |
| E13 | kurum | sirket | acik_lafzi | 0.6884 | 0.5147 | 0.3777 |
| E14 | beyanname | bildirim | acik_lafzi | 0.6469 | 0.4245 | 0.3708 |
| E15 | araba | otomobil | kontrol | 0.8320 | 0.8009 | 0.7850 |
| E16 | kitap | eser | kontrol | 0.7585 | 0.7390 | 0.5437 |
| E17 | masa | sehpa | kontrol | 0.8101 | 0.8786 | 0.7218 |
| E18 | kalem | tukenmez | kontrol | 0.7092 | 0.8292 | 0.5757 |
| E19 | telefon | cep telefonu | kontrol | 0.8415 | 0.7871 | 0.7414 |
| E20 | bahce | avlu | kontrol | 0.8071 | 0.7657 | 0.6372 |