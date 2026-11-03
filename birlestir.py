"""Teslim dosyasını üretir: tüm .py dosyalarını, başına dosya adı yazarak
tek bir txt dosyasında art arda ekler.

Kullanım:  python birlestir.py 230101001 230101002
Çıktı   :  230101001_230101002.txt
"""
import glob
import os
import sys


def main():
    if len(sys.argv) != 3:
        print("Kullanım: python birlestir.py <ogrenci_no1> <ogrenci_no2>")
        return
    cikti = f"{sys.argv[1]}_{sys.argv[2]}.txt"
    dosyalar = sorted(glob.glob("*.py"))
    with open(cikti, "w", encoding="utf-8") as c:
        for d in dosyalar:
            c.write(f"{d}\n")
            with open(d, "r", encoding="utf-8") as f:
                c.write(f.read())
            c.write("\n\n")
    print(f"{len(dosyalar)} dosya birleştirildi -> {cikti}")


if __name__ == "__main__":
    main()
