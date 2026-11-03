"""Depo Robotu Simülatörü - Tkinter arayüzü.

Kurallar burada YOK; hepsi simulasyon.py içinde. Bu dosya sadece
simulasyon fonksiyonlarını çağırıp sonucu çizer.
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox

import simulasyon as sim

RENKLER = {"#": "#555555", ".": "#ffffff", "K": "#c8874a", "T": "#6aa84f", "S": "#ffd966"}
GECIKME_MS = 250   # "Tümünü Çalıştır": komutlar arası bekleme
PARCA_MS = 120     # bir komutun hücre hücre çizim hızı


class Arayuz:
    def __init__(self, kok):
        self.kok = kok
        kok.title("Depo Robotu Simülatörü")

        # yüklenen veriler
        self.klasor = None
        self.izgara = self.baslangic = self.ayarlar = None
        self.komutlar, self.hatalar = [], []
        self.durum = None
        self.idx = 0            # sıradaki komutun indeksi
        self.log = []
        self.is_id = None       # bekleyen after() işi
        self.parcalar = None    # çizilmekte olan komutun üreteci
        self.aktif_komut = None
        self.otomatik = False   # "Tümünü Çalıştır" sürüyor mu
        self.yazildi = False    # sonuç dosyaları yazıldı mı

        self._arayuzu_kur()
        self._ciz()

    # ------------------------------------------------------------ arayüz kurulumu
    def _arayuzu_kur(self):
        butonlar = tk.Frame(self.kok)
        butonlar.pack(fill="x", padx=10, pady=8)
        for metin, komut in [("Dosyaları Yükle", self.dosyalari_yukle),
                             ("Adım", self.adim),
                             ("Tümünü Çalıştır", self.tumunu_calistir),
                             ("Sıfırla", self.sifirla)]:
            tk.Button(butonlar, text=metin, width=16, command=komut).pack(side="left", padx=4)

        orta = tk.Frame(self.kok)
        orta.pack(padx=10)
        self.tuval = tk.Canvas(orta, width=480, height=360, bg="#f0f0f0", highlightthickness=0)
        self.tuval.pack(side="left")
        sag = tk.Frame(orta)
        sag.pack(side="left", fill="y", padx=(10, 0))
        self.bilgi = tk.Label(sag, text="", font=("Courier", 11), justify="left",
                              anchor="nw", relief="solid", bd=1, width=30, height=8,
                              padx=8, pady=8)
        self.bilgi.pack(fill="x")

        # Hatalı komut satırları: pencere açmadan burada listelenir
        self.hata_cerceve = tk.LabelFrame(sag, text="Hatalı satırlar", padx=4, pady=4)
        self.hata_cerceve.pack(fill="both", expand=True, pady=(8, 0))
        self.hata_kutusu = tk.Text(self.hata_cerceve, width=30, height=8, wrap="word",
                                   font=("Courier", 9), bg="#fafafa", state="disabled")
        kaydirma = tk.Scrollbar(self.hata_cerceve, command=self.hata_kutusu.yview)
        self.hata_kutusu.config(yscrollcommand=kaydirma.set)
        kaydirma.pack(side="right", fill="y")
        self.hata_kutusu.pack(side="left", fill="both", expand=True)

        self.log_etiket = tk.Label(self.kok, text="Dosyaları yükleyin.", font=("Courier", 10),
                                   anchor="w", relief="solid", bd=1, padx=8, pady=6)
        self.log_etiket.pack(fill="x", padx=10, pady=10)

    # ------------------------------------------------------------ dosya yükleme
    def dosyalari_yukle(self):
        klasor = filedialog.askdirectory(
            title="harita.txt, komutlar.txt ve ayarlar.json'un bulunduğu klasörü seçin")
        if not klasor:
            return
        try:
            izgara, baslangic = sim.harita_oku(os.path.join(klasor, "harita.txt"))
            ayarlar = sim.ayarlari_oku(os.path.join(klasor, "ayarlar.json"))
            komutlar, hatalar = sim.komutlari_oku(os.path.join(klasor, "komutlar.txt"))
        except FileNotFoundError as e:
            messagebox.showerror("Dosya bulunamadı", f"Bulunamayan dosya: {e.filename}")
            return
        except (ValueError, OSError) as e:  # bozuk harita, bozuk JSON, okuma hatası
            messagebox.showerror("Hata", str(e))
            return

        self._isi_durdur()
        self.klasor, self.izgara, self.baslangic = klasor, izgara, baslangic
        self.ayarlar, self.komutlar, self.hatalar = ayarlar, komutlar, hatalar
        self.sifirla()

        self._hatalari_goster()
        if hatalar:
            self.log_etiket.config(
                text=f"Hazır. {len(hatalar)} hatalı satır atlandı (sağ panelde listelendi).")

    def _hatalari_goster(self):
        """Hatalı satırları (satır no, içerik, neden) sağ paneldeki kutuya yazar."""
        satirlar = [f"Satır {h['satir']}: '{h['icerik']}' -> {h['neden']}"
                    for h in self.hatalar] or ["Hatalı satır yok."]
        self.hata_cerceve.config(text=f"Hatalı satırlar ({len(self.hatalar)})")
        self.hata_kutusu.config(state="normal")
        self.hata_kutusu.delete("1.0", "end")
        self.hata_kutusu.insert("end", "\n".join(satirlar))
        self.hata_kutusu.config(state="disabled")

    # ------------------------------------------------------------ kontrol butonları
    def sifirla(self):
        self._isi_durdur()
        self.otomatik = False
        self.parcalar = None
        if self.izgara is None:
            return
        self.durum = sim.yeni_durum(self.izgara, self.baslangic, self.ayarlar)
        self.idx = 0
        self.log = []
        self.yazildi = False
        self.log_etiket.config(text="Hazır. 'Adım' veya 'Tümünü Çalıştır'a basın.")
        self._ciz()

    def adim(self):
        if not self._hazir_mi():
            return
        self.otomatik = False
        self._isi_durdur()
        if self.parcalar is not None:  # hareket çizimi sürüyor: komutu hemen tamamla
            self._komutu_hizla_bitir()
            return
        if self._bitti_mi():
            self._bitir()
            self.log_etiket.config(
                text="Simülasyon bitti. Yeniden başlatmak için 'Sıfırla'ya basın.")
            return
        self._komut_baslat()

    def tumunu_calistir(self):
        if not self._hazir_mi():
            return
        if self.parcalar is not None:  # bir komut çiziliyor: bitince devam edilir
            self.otomatik = True
            return
        self._isi_durdur()
        if self._bitti_mi():  # zaten bitmiş: kullanıcıya haber ver
            self._bitir()
            self.log_etiket.config(
                text="Simülasyon bitti. Yeniden başlatmak için 'Sıfırla'ya basın.")
            return
        self.otomatik = True
        self._komut_baslat()

    # ------------------------------------------------------------ komut çalıştırma
    def _komut_baslat(self):
        """Sıradaki komutu başlatır; hareketler hücre hücre / dönüş dönüş çizilir.

        Böylece ILERI n ve GIT x y robotun "zıplaması" olarak değil, yürümesi
        olarak görünür. Sonuçlar (log, sonuc.json) hiç değişmez.
        """
        self.aktif_komut = self.komutlar[self.idx]
        self.idx += 1
        self.parcalar = sim.komut_parcalari(self.durum, self.aktif_komut)
        self._parca_ilerlet()

    def _parca_ilerlet(self):
        self.is_id = None
        try:
            next(self.parcalar)
        except StopIteration as son:   # komut bitti, son.value = olay
            self._komut_bitti(son.value)
            return
        self._ciz()
        self.is_id = self.kok.after(PARCA_MS, self._parca_ilerlet)

    def _komutu_hizla_bitir(self):
        while self.parcalar is not None:
            try:
                next(self.parcalar)
            except StopIteration as son:
                self._komut_bitti(son.value)

    def _komut_bitti(self, olay):
        komut = self.aktif_komut
        self.parcalar = None
        satir = sim.log_satiri(self.durum, komut, olay)
        self.log.append(satir)
        self.log_etiket.config(
            text=f"Adım {satir['adim']}: {satir['komut']} -> "
                 f"({satir['x']},{satir['y']}) {olay}")
        self._ciz()
        if self._bitti_mi():
            self.otomatik = False
            self._bitir()
        elif self.otomatik:
            self.is_id = self.kok.after(GECIKME_MS, self._otomatik_sonraki)

    def _otomatik_sonraki(self):
        self.is_id = None
        if self.otomatik and self.parcalar is None and not self._bitti_mi():
            self._komut_baslat()

    def _isi_durdur(self):
        if self.is_id is not None:
            self.kok.after_cancel(self.is_id)
            self.is_id = None

    def _hazir_mi(self):
        if self.durum is None:
            messagebox.showinfo("Bilgi", "Önce dosyaları yükleyin.")
            return False
        return True

    def _bitti_mi(self):
        return self.durum["bitti"] or self.idx >= len(self.komutlar)

    def _bitir(self):
        """Simülasyon bitince sonuc.json ve log.csv yazılır (bir kez)."""
        if self.yazildi:
            return
        self.yazildi = True
        try:
            sonuc = sim.sonuc_olustur(self.durum, self.hatalar)
            sim.sonuc_yaz(sonuc, os.path.join(self.klasor, "sonuc.json"))
            sim.log_yaz(self.log, os.path.join(self.klasor, "log.csv"))
            self.log_etiket.config(
                text=self.log_etiket.cget("text") + "  | BİTTİ (sonuc.json, log.csv yazıldı)")
        except OSError as e:
            messagebox.showerror("Yazma hatası", str(e))
        if self.durum["bitti"]:
            kalan = len(self.komutlar) - self.idx
            messagebox.showwarning(
                "Batarya bitti",
                f"Batarya yetersiz, simülasyon durdu.\n\n"
                f"Konum: ({self.durum['x']}, {self.durum['y']})   "
                f"Batarya: {self.durum['batarya']}\n"
                f"Çalıştırılan komut: {self.idx}/{len(self.komutlar)}\n"
                f"Çalıştırılmayan komut: {kalan}")

    # ------------------------------------------------------------ çizim
    def _ciz(self):
        self.tuval.delete("all")
        if self.durum is None:
            self.bilgi.config(text="")
            return
        izgara = self.durum["izgara"]
        satir_say, sutun_say = len(izgara), len(izgara[0])
        hs = max(16, min(48, 640 // sutun_say, 480 // satir_say))  # hücre boyutu
        self.tuval.config(width=sutun_say * hs, height=satir_say * hs)

        for y, satir in enumerate(izgara):
            for x, h in enumerate(satir):
                x0, y0 = x * hs, y * hs
                self.tuval.create_rectangle(x0, y0, x0 + hs, y0 + hs,
                                            fill=RENKLER[h], outline="#999999")
                if h in "KTS":
                    self.tuval.create_text(x0 + hs / 2, y0 + hs / 2, text=h,
                                           font=("Helvetica", max(8, hs // 3), "bold"))
        self._robot_ciz(hs)
        self._bilgi_guncelle()

    def _robot_ciz(self, hs):
        px, py = self.durum["x"] * hs, self.durum["y"] * hs
        m, s = hs * 0.2, hs
        cx = cy = hs / 2
        ucgenler = {
            "K": [px + cx, py + m, px + m, py + s - m, px + s - m, py + s - m],
            "D": [px + m, py + m, px + m, py + s - m, px + s - m, py + cy],
            "G": [px + m, py + m, px + s - m, py + m, px + cx, py + s - m],
            "B": [px + s - m, py + m, px + s - m, py + s - m, px + m, py + cy],
        }
        renk = "#e07b00" if self.durum["yuk"] else "#1f77b4"  # yüklüyse turuncu
        self.tuval.create_polygon(ucgenler[self.durum["yon"]], fill=renk, outline="black")

    def _bilgi_guncelle(self):
        d = self.durum
        bitmedi = self.idx < len(self.komutlar) and not d["bitti"]
        siradaki = sim.komut_metni(self.komutlar[self.idx]) if bitmedi else "-"
        self.bilgi.config(text=(
            f"Batarya : {d['batarya']}/{d['ayarlar']['batarya_kapasitesi']}\n"
            f"Yön     : {d['yon']}\n"
            f"Yük     : {'Var' if d['yuk'] else 'Yok'}\n"
            f"Teslim  : {d['teslim']}\n"
            f"Çarpışma: {d['carpisma']}\n"
            f"Sıradaki: {siradaki}"
            + ("\n\nBATARYA BİTTİ!" if d["bitti"] else "")))


def main():
    kok = tk.Tk()
    Arayuz(kok)
    kok.mainloop()


if __name__ == "__main__":
    main()
