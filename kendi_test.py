"""Kendi küçük testlerimiz (resmi test_calistir.py'den bağımsız).
Çalıştırma: python kendi_test.py
"""
import os
import tempfile
import unittest

import simulasyon as sim


def yaz(klasor, ad, icerik):
    yol = os.path.join(klasor, ad)
    with open(yol, "w", encoding="utf-8") as f:
        f.write(icerik)
    return yol


class Testler(unittest.TestCase):
    def setUp(self):
        self.k = tempfile.mkdtemp()

    def _kos(self, harita, bat, komutlar, **ek):
        izgara, bas = sim.harita_oku(yaz(self.k, "h.txt", harita))
        ayar = dict(sim.VARSAYILAN_AYARLAR, batarya_kapasitesi=bat, adim_maliyeti=2,
                    yuk_carpani=2, donus_maliyeti=1, carpisma_cezasi=5)
        ayar.update(ek)
        return sim.simulasyonu_calistir(izgara, bas, komutlar, ayar)

    # ---------------------------------------------------------- PDF örneği
    def test_pdf_ornegi(self):
        """PDF'teki örnek: #R.K.T#, batarya 20 -> son batarya 11."""
        izgara, bas = sim.harita_oku(yaz(self.k, "harita.txt", "#R.K.T#\n"))
        ayarlar = {"batarya_kapasitesi": 20, "baslangic_yonu": "D", "adim_maliyeti": 1,
                   "yuk_carpani": 2, "donus_maliyeti": 1, "carpisma_cezasi": 3}
        komutlar = [("ILERI", 2), ("AL", None), ("ILERI", 5), ("BIRAK", None)]
        sonuc, log = sim.simulasyonu_calistir(izgara, bas, komutlar, ayarlar)
        self.assertEqual([l["batarya"] for l in log], [18, 18, 11, 11])
        self.assertEqual(sonuc["konum"], [5, 0])  # harita tek satır: y=0
        self.assertEqual(sonuc["teslim"], 1)
        self.assertEqual(sonuc["carpisma"], 1)
        self.assertEqual(log[3]["olay"], "TESLIM")

    # ---------------------------------------------------------- dosya okuma
    def test_varsayilan_batarya_60(self):
        self.assertEqual(sim.VARSAYILAN_AYARLAR["batarya_kapasitesi"], 60)
        yol = yaz(self.k, "a.json", "{}")
        self.assertEqual(sim.ayarlari_oku(yol)["batarya_kapasitesi"], 60)

    def test_ayarlar_fazladan_anahtar(self):
        yol = yaz(self.k, "a.json", '{"batarya_kapasitesi": 60, "aciklama": "deneme"}')
        self.assertEqual(sim.ayarlari_oku(yol)["batarya_kapasitesi"], 60)

    def test_ayarlar_bozuk(self):
        for icerik in ["{bozuk", '{"adim_maliyeti": -1}', '{"baslangic_yonu": "X"}', "[1]"]:
            with self.assertRaises(ValueError):
                sim.ayarlari_oku(yaz(self.k, "a.json", icerik))

    def test_hatali_satirlar(self):
        yol = yaz(self.k, "komutlar.txt",
                  "ILERI 3\n\nILER 3\nILERI\nILERI 2 5\nILERI -1\nILERI abc\nSAG 1\nSOL\n")
        komutlar, hatalar = sim.komutlari_oku(yol)
        self.assertEqual(komutlar, [("ILERI", 3), ("SOL", None)])
        self.assertEqual([h["satir"] for h in hatalar], [3, 4, 5, 6, 7, 8])

    def test_bozuk_harita(self):
        for icerik in ["#...#\n", "#RR#\n", "#R.#\n#R#\n", "#R?#\n", ""]:
            with self.assertRaises(ValueError):
                sim.harita_oku(yaz(self.k, "h.txt", icerik))

    def test_harita_sondaki_bosluk(self):
        izgara, bas = sim.harita_oku(yaz(self.k, "h.txt", "#R.#  \n#..#\n\n"))
        self.assertEqual(bas, (1, 0))
        self.assertEqual(len(izgara), 2)

    def test_dosya_bulunamadi(self):
        with self.assertRaises(FileNotFoundError):
            sim.harita_oku(os.path.join(self.k, "yok.txt"))

    # ---------------------------------------------------------- batarya
    def test_batarya_biter(self):
        sonuc, log = self._kos("R....\n", 3, [("ILERI", 3), ("SAG", None)])
        self.assertTrue(sonuc["batarya_bitti"])
        self.assertEqual(len(log), 1)           # sonraki komut çalışmadı
        self.assertEqual(sonuc["konum"], [1, 0])
        self.assertEqual(sonuc["batarya"], 1)

    def test_batarya_esit_islem_yapilir(self):
        """Maliyet == batarya: işlem yapılır, batarya 0 olur."""
        sonuc, log = self._kos("R...#\n", 2, [("ILERI", 1), ("SAG", None)])
        self.assertEqual(log[0]["batarya"], 0)
        self.assertEqual(log[0]["olay"], "HAREKET")
        self.assertEqual(log[1]["olay"], "BATARYA_BITTI")
        self.assertTrue(sonuc["batarya_bitti"])

    def test_carpisma_cezasi_eksiye_dusurur(self):
        sonuc, log = self._kos("R#\n", 3, [("ILERI", 1), ("SAG", None)])
        self.assertEqual(sonuc["batarya"], 0)
        self.assertEqual(sonuc["carpisma"], 1)
        self.assertTrue(sonuc["batarya_bitti"])
        self.assertEqual(len(log), 1)

    def test_batarya_0_iken_sarj_calisir(self):
        sonuc, log = self._kos("RS.\n", 2, [("ILERI", 1), ("SARJ", None)])
        self.assertEqual(log[0]["batarya"], 0)
        self.assertEqual(log[1]["olay"], "SARJ")
        self.assertEqual(sonuc["batarya"], 2)
        self.assertFalse(sonuc["batarya_bitti"])

    def test_yuklu_adim_carpan(self):
        sonuc, log = self._kos("RK..\n", 6, [("ILERI", 1), ("AL", None), ("ILERI", 2)])
        self.assertEqual(sonuc["konum"], [2, 0])
        self.assertTrue(sonuc["batarya_bitti"])
        self.assertEqual(sonuc["batarya"], 0)

    # ---------------------------------------------------------- yük / geçersiz
    def test_gecersiz_islemler(self):
        _, log = self._kos("R..\n", 60, [("AL", None), ("BIRAK", None), ("SARJ", None)])
        self.assertEqual([l["olay"] for l in log], ["GECERSIZ"] * 3)

    def test_en_fazla_bir_kutu(self):
        _, log = self._kos("RK.\n", 60, [("ILERI", 1), ("AL", None), ("AL", None)])
        self.assertEqual([l["olay"] for l in log][1:], ["AL", "GECERSIZ"])

    def test_kutu_birakma(self):
        sonuc, log = self._kos("RK.\n", 60, [("ILERI", 1), ("AL", None), ("ILERI", 1),
                                           ("BIRAK", None), ("AL", None)])
        # boş hücreye bırakılan kutu orada kalır; AL onu tekrar alabilir
        self.assertEqual([l["olay"] for l in log][3:], ["BIRAK", "AL"])
        self.assertTrue(sonuc["yuk"])

    # ---------------------------------------------------------- ziyaret
    def test_en_cok_ziyaret_esitlik(self):
        """Tüm hücreler 1 kez ziyaret -> y'si, sonra x'i küçük olan: (1, 0)."""
        sonuc, _ = self._kos("R..\n", 60, [("ILERI", 2)])
        self.assertEqual(sonuc["en_cok_ziyaret_edilen"], [0, 0])

    # ---------------------------------------------------------- bonus
    def test_git(self):
        harita = "#######\n#R.#..#\n#.##.T#\n#.....#\n#######\n"
        sonuc, log = self._kos(harita, 200, [("GIT", (5, 2))])
        self.assertEqual(sonuc["konum"], [5, 2])
        self.assertEqual(log[0]["olay"], "GIT")

    def test_git_ulasilamaz(self):
        sonuc, log = self._kos("R#.\n", 60, [("GIT", (2, 0))])
        self.assertEqual(log[0]["olay"], "GECERSIZ")
        self.assertEqual(sonuc["konum"], [0, 0])

    # ---------------------------------------------------------- çıktılar
    def test_dosyalar_yazilir(self):
        izgara, bas = sim.harita_oku(yaz(self.k, "h.txt", "#R.#\n"))
        sonuc, log = sim.simulasyonu_calistir(izgara, bas, [("ILERI", 1)],
                                              sim.VARSAYILAN_AYARLAR)
        sim.sonuc_yaz(sonuc, os.path.join(self.k, "sonuc.json"))
        sim.log_yaz(log, os.path.join(self.k, "log.csv"))
        with open(os.path.join(self.k, "log.csv"), encoding="utf-8") as f:
            self.assertEqual(f.readline().strip(), "adim,komut,x,y,yon,batarya,olay")

    def test_harita_metni(self):
        izgara, bas = sim.harita_oku(yaz(self.k, "h.txt", "#R.#\n"))
        durum = sim.yeni_durum(izgara, bas, sim.VARSAYILAN_AYARLAR)
        self.assertEqual(sim.harita_metni(durum), "#R.#")

    # ---------------------------------------------------------- parça parça uygulama
    def _parcalari_topla(self, durum, komut):
        """komut_parcalari'ni sonuna kadar çalıştırır -> (ara konumlar, olay)."""
        g = sim.komut_parcalari(durum, komut)
        konumlar = []
        while True:
            try:
                next(g)
                konumlar.append((durum["x"], durum["y"]))
            except StopIteration as son:
                return konumlar, son.value

    def test_ileri_hucre_hucre(self):
        izgara, bas = sim.harita_oku(yaz(self.k, "h.txt", "R....\n"))
        durum = sim.yeni_durum(izgara, bas, sim.VARSAYILAN_AYARLAR)
        konumlar, olay = self._parcalari_topla(durum, ("ILERI", 3))
        self.assertEqual(konumlar, [(1, 0), (2, 0), (3, 0)])
        self.assertEqual(olay, "HAREKET")

    def test_ileri_carpisma_parca(self):
        izgara, bas = sim.harita_oku(yaz(self.k, "h.txt", "R.#\n"))
        durum = sim.yeni_durum(izgara, bas, sim.VARSAYILAN_AYARLAR)
        konumlar, olay = self._parcalari_topla(durum, ("ILERI", 5))
        self.assertEqual(konumlar, [(1, 0)])   # sadece 1 adım, sonra duvar
        self.assertEqual(olay, "CARPISMA")

    def test_git_yolu_k_hucresinden_gecer(self):
        """GIT, kutu (K) hücresinden geçebilir; AL yazılmadıkça kutu alınmaz."""
        harita = "#####\nR.K.#\n#####\n"
        izgara, bas = sim.harita_oku(yaz(self.k, "h.txt", harita))
        durum = sim.yeni_durum(izgara, bas, sim.VARSAYILAN_AYARLAR)
        konumlar, olay = self._parcalari_topla(durum, ("GIT", (3, 1)))
        self.assertIn((2, 1), konumlar)
        self.assertEqual(olay, "GIT")
        self.assertFalse(durum["yuk"])

    def test_parca_ile_toplu_ayni_sonuc(self):
        """Parça parça çalıştırmak komut_uygula ile birebir aynı durumu verir."""
        harita = "#######\n#R.#..#\n#.##.T#\n#.....#\n#######\n"
        izgara, bas = sim.harita_oku(yaz(self.k, "h.txt", harita))
        a = sim.yeni_durum(izgara, bas, sim.VARSAYILAN_AYARLAR)
        b = sim.yeni_durum(izgara, bas, sim.VARSAYILAN_AYARLAR)
        _, olay_a = self._parcalari_topla(a, ("GIT", (5, 2)))
        olay_b = sim.komut_uygula(b, ("GIT", (5, 2)))
        self.assertEqual(olay_a, olay_b)
        for anahtar in ("x", "y", "yon", "batarya", "adim", "carpisma"):
            self.assertEqual(a[anahtar], b[anahtar])
        self.assertEqual(a["ziyaret"], b["ziyaret"])


if __name__ == "__main__":
    unittest.main()
