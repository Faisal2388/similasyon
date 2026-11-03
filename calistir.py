"""Arayüzsüz çalıştırma (Şekil 3'teki akış): oku -> simüle et -> yaz.

Kullanım:  python calistir.py deneme_verileri/veri_1
Klasörde harita.txt, komutlar.txt, ayarlar.json bulunmalı;
sonuc.json ve log.csv aynı klasöre yazılır.
"""
import os
import sys

import simulasyon as sim


def main():
    if len(sys.argv) != 2:
        print("Kullanım: python calistir.py <klasör>")
        return
    k = sys.argv[1]
    try:
        izgara, baslangic = sim.harita_oku(os.path.join(k, "harita.txt"))
        ayarlar = sim.ayarlari_oku(os.path.join(k, "ayarlar.json"))
        komutlar, hatalar = sim.komutlari_oku(os.path.join(k, "komutlar.txt"))
    except FileNotFoundError as e:
        print(f"Hata: dosya bulunamadı: {e.filename}")
        return
    except (ValueError, OSError) as e:
        print(f"Hata: {e}")
        return

    for h in hatalar:
        print(f"Hatalı satır {h['satir']}: '{h['icerik']}' -> {h['neden']}")

    sonuc, log = sim.simulasyonu_calistir(izgara, baslangic, komutlar, ayarlar, hatalar)
    sim.sonuc_yaz(sonuc, os.path.join(k, "sonuc.json"))
    sim.log_yaz(log, os.path.join(k, "log.csv"))
    print(f"Bitti: konum={sonuc['konum']} batarya={sonuc['batarya']} "
          f"teslim={sonuc['teslim']} çarpışma={sonuc['carpisma']} "
          f"batarya_bitti={sonuc['batarya_bitti']}")


if __name__ == "__main__":
    main()
