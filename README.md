# Depo Robotu Simülatörü

Kocaeli Sağlık ve Teknoloji Üniversitesi - Programlama Lab-I - Proje 1

Python 3 (sadece standart kütüphane) + Tkinter. Varsayılan batarya kapasitesi: 60.

## Dosyalar
| Dosya | Görevi |
|---|---|
| `simulasyon.py` | Tüm kurallar: dosya okuma, hareket, batarya, çıktı yazma (arayüz kodu yok) |
| `yol_bulma.py` | BFS ile en kısa yol (bonus: `GIT x y`) |
| `arayuz.py` | Tkinter arayüzü |
| `kendi_test.py` | Kendi birim testlerimiz |
| `birlestir.py` | Teslim için tüm kodu tek txt'ye birleştirir |
| `deneme_verileri/` | Arayüzü denemek için örnek veri setleri |

## Çalıştırma
```
python arayuz.py                        # arayüz
python test_calistir.py paket_ornek     # resmi testler
python kendi_test.py                    # kendi testlerimiz
python birlestir.py <no1> <no2>         # teslim txt dosyası
```
Arayüzde **Dosyaları Yükle** ile `harita.txt`, `komutlar.txt`, `ayarlar.json`
içeren klasörü seçin. Simülasyon bitince `sonuc.json` ve `log.csv` aynı klasöre yazılır.

## Komutlar
`ILERI n`, `SAG`, `SOL`, `AL`, `BIRAK`, `SARJ`, `GIT x y` (bonus).
Hatalı satırlar atlanır ve satır numarasıyla raporlanır.

## Olaylar (log.csv)
`HAREKET, CARPISMA, DONUS, AL, BIRAK, TESLIM, SARJ, GIT, GECERSIZ, BATARYA_BITTI`
