"""Depo Robotu Simulatoru - tum kurallar burada. (Arayuz kodu YOK!)

Bolumler:
  1) Sabitler
  2) Dosya okuma  : harita_oku, ayarlari_oku, komutlari_oku
  3) Durum        : yeni_durum
  4) Kurallar     : batarya, hareket, donus, AL/BIRAK/SARJ, GIT
  5) Simulasyon   : komut_uygula, simulasyonu_calistir
  6) Cikti        : sonuc_yaz, log_yaz, harita_metni
"""
import csv
import json

from yol_bulma import en_kisa_yol

# ---------------------------------------------------------------- 1) Sabitler
YONLER = ["K", "D", "G", "B"]  # saat yonunde: yukari, sag, asagi, sol
FARK = {"K": (0, -1), "D": (1, 0), "G": (0, 1), "B": (-1, 0)}
GECERLI_HUCRELER = set("#.RKTS")
TEK_KELIMELI = ("SAG", "SOL", "AL", "BIRAK", "SARJ")

VARSAYILAN_AYARLAR = {
    "batarya_kapasitesi": 60,
    "baslangic_yonu": "D",
    "adim_maliyeti": 2,
    "yuk_carpani": 2,
    "donus_maliyeti": 1,
    "carpisma_cezasi": 5,
}


# ------------------------------------------------------------- 2) Dosya okuma
def harita_oku(dosya_yolu):
    """-> (izgara, (x, y)). Bozuk haritada ValueError verir.

    izgara: karakter listelerinden olusan 2B liste. 'R' hucresi '.' yapilir
    (robotun yeri ayrica (x, y) olarak doner).
    """
    with open(dosya_yolu, "r", encoding="utf-8-sig") as f:
        satirlar = [s.rstrip() for s in f]  # satir sonu / sondaki bosluklar atilir
    while satirlar and satirlar[-1] == "":  # dosya sonundaki bos satirlar
        satirlar.pop()
    if not satirlar:
        raise ValueError("Harita dosyası boş.")

    genislik = len(satirlar[0])
    for no, s in enumerate(satirlar, start=1):
        if len(s) != genislik:
            raise ValueError(f"Harita satır uzunlukları farklı (satır {no}).")
        for c in s:
            if c not in GECERLI_HUCRELER:
                raise ValueError(f"Haritada geçersiz karakter '{c}' (satır {no}).")

    robotlar = [(x, y) for y, s in enumerate(satirlar)
                for x, c in enumerate(s) if c == "R"]
    if len(robotlar) == 0:
        raise ValueError("Haritada robot (R) yok.")
    if len(robotlar) > 1:
        raise ValueError("Haritada birden fazla robot (R) var.")

    izgara = [["." if c == "R" else c for c in s] for s in satirlar]
    return izgara, robotlar[0]


def ayarlari_oku(dosya_yolu):
    """-> ayarlar sozlugu. Eksik anahtarlar varsayilanla doldurulur.

    Sadece bilinen kural anahtarlari kontrol edilir; fazladan anahtarlar
    (ornegin aciklama) sorun cikarmaz.
    """
    with open(dosya_yolu, "r", encoding="utf-8-sig") as f:
        veri = json.load(f)  # bozuk JSON -> JSONDecodeError (ValueError alt sinifi)
    if not isinstance(veri, dict):
        raise ValueError("ayarlar.json bir JSON nesnesi olmalı.")

    ayarlar = dict(VARSAYILAN_AYARLAR)
    ayarlar.update(veri)
    for anahtar in VARSAYILAN_AYARLAR:
        deger = ayarlar[anahtar]
        if anahtar == "baslangic_yonu":
            if deger not in YONLER:
                raise ValueError("baslangic_yonu K, D, G veya B olmalı.")
        elif isinstance(deger, bool) or not isinstance(deger, (int, float)) or deger < 0:
            raise ValueError(f"'{anahtar}' negatif olmayan bir sayı olmalı.")
    return ayarlar


def _pozitif_tam_sayi(metin):
    """'12' -> 12, ama '0', '-3', '2.5', 'abc' -> None."""
    if metin.isascii() and metin.isdigit() and int(metin) > 0:
        return int(metin)
    return None


def _negatif_olmayan_tam_sayi(metin):
    if metin.isascii() and metin.isdigit():
        return int(metin)
    return None


def _satir_coz(satir):
    """Tek satiri cozer -> (komut, None) veya (None, neden)."""
    p = satir.split()
    ad = p[0]

    if ad == "ILERI":
        if len(p) < 2:
            return None, "ILERI için adım sayısı eksik"
        if len(p) > 2:
            return None, "ILERI için fazla parametre"
        n = _pozitif_tam_sayi(p[1])
        if n is None:
            return None, f"geçersiz sayı: '{p[1]}'"
        return ("ILERI", n), None

    if ad in TEK_KELIMELI:
        if len(p) > 1:
            return None, f"{ad} parametre almaz"
        return (ad, None), None

    if ad == "GIT":  # bonus
        if len(p) != 3:
            return None, "GIT x y biçiminde olmalı"
        x, y = _negatif_olmayan_tam_sayi(p[1]), _negatif_olmayan_tam_sayi(p[2])
        if x is None or y is None:
            return None, "GIT için geçersiz koordinat"
        return ("GIT", (x, y)), None

    return None, f"bilinmeyen komut: '{ad}'"


def komutlari_oku(dosya_yolu):
    """-> (komutlar, hatalar). Hatali satirlar atlanir, program cokmez.

    Satir numaralari 1'den baslar ve bos satirlar da sayilir.
    """
    komutlar, hatalar = [], []
    with open(dosya_yolu, "r", encoding="utf-8-sig") as f:
        for no, ham in enumerate(f, start=1):
            satir = ham.strip()
            if satir == "":
                continue
            komut, neden = _satir_coz(satir)
            if neden is not None:
                hatalar.append({"satir": no, "icerik": satir, "neden": neden})
            else:
                komutlar.append(komut)
    return komutlar, hatalar


# ------------------------------------------------------------------- 3) Durum
def yeni_durum(izgara, baslangic, ayarlar):
    """Simulasyonun baslangic durumunu (sozluk) olusturur."""
    ayarlar = {**VARSAYILAN_AYARLAR, **ayarlar}
    x, y = baslangic
    return {
        "izgara": [satir[:] for satir in izgara],  # kopya: orijinal bozulmaz
        "x": x,
        "y": y,
        "yon": ayarlar["baslangic_yonu"],
        "batarya": ayarlar["batarya_kapasitesi"],
        "yuk": False,
        "teslim": 0,
        "carpisma": 0,
        "adim": 0,          # calistirilan komut sayisi
        "bitti": False,     # batarya yuzunden simulasyon durdu mu
        "ziyaret": {(x, y): 1},
        "ayarlar": ayarlar,
    }


# ------------------------------------------------------------------ 4) Kurallar
def _hucre(durum):
    return durum["izgara"][durum["y"]][durum["x"]]


def _bos_mu(izgara, x, y):
    return 0 <= y < len(izgara) and 0 <= x < len(izgara[0]) and izgara[y][x] != "#"


def _batarya_harca(durum, maliyet):
    """Maliyet bataryadan buyukse islem yapilmaz ve simulasyon durur.
    Esitse islem yapilir, batarya 0 olur."""
    if maliyet > durum["batarya"]:
        durum["bitti"] = True
        return False
    durum["batarya"] -= maliyet
    return True


def _bir_adim_ilerle(durum):
    """Tek adim ileri. -> 'HAREKET' | 'CARPISMA' | 'BATARYA_BITTI'"""
    a = durum["ayarlar"]
    dx, dy = FARK[durum["yon"]]
    nx, ny = durum["x"] + dx, durum["y"] + dy

    if not _bos_mu(durum["izgara"], nx, ny):  # duvar veya harita disi
        durum["carpisma"] += 1
        ceza = a["carpisma_cezasi"]
        if ceza > durum["batarya"]:  # eksiye dusecekse 0 ve dur
            durum["batarya"] = 0
            durum["bitti"] = True
        else:
            durum["batarya"] -= ceza
        return "CARPISMA"

    maliyet = a["adim_maliyeti"] * (a["yuk_carpani"] if durum["yuk"] else 1)
    if not _batarya_harca(durum, maliyet):
        return "BATARYA_BITTI"

    durum["x"], durum["y"] = nx, ny
    konum = (nx, ny)
    durum["ziyaret"][konum] = durum["ziyaret"].get(konum, 0) + 1
    return "HAREKET"


def _don(durum, sag_mi):
    """90 derece doner. -> 'DONUS' | 'BATARYA_BITTI'"""
    if not _batarya_harca(durum, durum["ayarlar"]["donus_maliyeti"]):
        return "BATARYA_BITTI"
    i = YONLER.index(durum["yon"])
    durum["yon"] = YONLER[(i + (1 if sag_mi else -1)) % 4]
    return "DONUS"


def _donus_listesi(durum, hedef_yon):
    """Hedef yone en az donusle donmek icin gereken donusler (True=SAG, False=SOL)."""
    fark = (YONLER.index(hedef_yon) - YONLER.index(durum["yon"])) % 4
    return {0: [], 1: [True], 2: [True, True], 3: [False]}[fark]


def _git_parcalari(durum, hedef):
    """Bonus: duvarlardan kacarak en kisa yoldan hedefe git.

    Uretec (generator): her donus / adimdan sonra yield eder, sonunda olayi doner.
    """
    hx, hy = hedef
    if not _bos_mu(durum["izgara"], hx, hy):
        return "GECERSIZ"
    yol = en_kisa_yol(durum["izgara"], (durum["x"], durum["y"]), (hx, hy))
    if yol is None:
        return "GECERSIZ"

    for (nx, ny) in yol[1:]:
        fark = (nx - durum["x"], ny - durum["y"])
        hedef_yon = next(y for y, f in FARK.items() if f == fark)
        for sag in _donus_listesi(durum, hedef_yon):
            if _don(durum, sag) != "DONUS":
                return "BATARYA_BITTI"
            yield
        sonuc = _bir_adim_ilerle(durum)
        if sonuc != "HAREKET":
            return sonuc
        yield
    return "GIT"


def _al(durum):
    if durum["yuk"] or _hucre(durum) != "K":
        return "GECERSIZ"
    durum["yuk"] = True
    durum["izgara"][durum["y"]][durum["x"]] = "."  # kutu haritadan kalkar
    return "AL"


def _birak(durum):
    if not durum["yuk"]:
        return "GECERSIZ"
    hucre = _hucre(durum)
    if hucre == "T":
        durum["yuk"] = False
        durum["teslim"] += 1
        return "TESLIM"
    if hucre == ".":
        durum["yuk"] = False
        durum["izgara"][durum["y"]][durum["x"]] = "K"  # kutu orada kalir
        return "BIRAK"
    return "GECERSIZ"  # K veya S ustune birakilamaz


def _sarj(durum):
    if _hucre(durum) != "S":
        return "GECERSIZ"
    durum["batarya"] = durum["ayarlar"]["batarya_kapasitesi"]
    return "SARJ"


# -------------------------------------------------------------- 5) Simulasyon
def komut_parcalari(durum, komut):
    """Komutu parca parca uygular (arayuzde hareketi adim adim gostermek icin).

    Uretec (generator): her hucre adimindan / donusten sonra yield eder;
    sonunda olayi (str) doner (StopIteration.value).
    """
    if durum["bitti"]:
        return "DURDU"

    ad, deger = komut
    durum["adim"] += 1

    if ad == "ILERI":
        for _ in range(deger):
            sonuc = _bir_adim_ilerle(durum)
            if sonuc != "HAREKET":  # carpisma / batarya: kalan komut iptal
                return sonuc
            yield
        return "HAREKET"
    if ad == "SAG":
        return _don(durum, True)
    if ad == "SOL":
        return _don(durum, False)
    if ad == "AL":
        return _al(durum)
    if ad == "BIRAK":
        return _birak(durum)
    if ad == "SARJ":
        return _sarj(durum)
    if ad == "GIT":
        return (yield from _git_parcalari(durum, deger))
    return "GECERSIZ"


def komut_uygula(durum, komut):
    """Tek komutu uygular, durumu gunceller, olay (str) doner.

    Olaylar: HAREKET, CARPISMA, DONUS, AL, BIRAK, TESLIM, SARJ, GIT,
             GECERSIZ, BATARYA_BITTI, DURDU
    """
    parcalar = komut_parcalari(durum, komut)
    while True:
        try:
            next(parcalar)
        except StopIteration as son:
            return son.value


def komut_metni(komut):
    """('ILERI', 3) -> 'ILERI 3', ('GIT', (2, 4)) -> 'GIT 2 4', ('SAG', None) -> 'SAG'"""
    ad, deger = komut
    if deger is None:
        return ad
    if ad == "GIT":
        return f"GIT {deger[0]} {deger[1]}"
    return f"{ad} {deger}"


def log_satiri(durum, komut, olay):
    return {
        "adim": durum["adim"],
        "komut": komut_metni(komut),
        "x": durum["x"],
        "y": durum["y"],
        "yon": durum["yon"],
        "batarya": durum["batarya"],
        "olay": olay,
    }


def en_cok_ziyaret_edilen(durum):
    """Esitlikte y'si, sonra x'i kucuk olan secilir. -> [x, y]"""
    (x, y), _ = min(durum["ziyaret"].items(),
                    key=lambda kv: (-kv[1], kv[0][1], kv[0][0]))
    return [x, y]


def sonuc_olustur(durum, hatalar=None):
    return {
        "konum": [durum["x"], durum["y"]],
        "yon": durum["yon"],
        "batarya": durum["batarya"],
        "yuk": durum["yuk"],
        "teslim": durum["teslim"],
        "carpisma": durum["carpisma"],
        "toplam_adim": durum["adim"],
        "batarya_bitti": durum["bitti"],
        "en_cok_ziyaret_edilen": en_cok_ziyaret_edilen(durum),
        "hatali_satirlar": hatalar if hatalar is not None else [],
    }


def simulasyonu_calistir(izgara, baslangic, komutlar, ayarlar, hatalar=None):
    """Tum komutlari calistirir. -> (sonuc, log)

    Simulasyon durduktan sonraki komutlar calistirilmaz.
    """
    durum = yeni_durum(izgara, baslangic, ayarlar)
    log = []
    for komut in komutlar:
        if durum["bitti"]:
            break
        olay = komut_uygula(durum, komut)
        log.append(log_satiri(durum, komut, olay))
    return sonuc_olustur(durum, hatalar), log


# ----------------------------------------------------------------- 6) Cikti
def sonuc_yaz(sonuc, dosya_yolu):
    with open(dosya_yolu, "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=2)


def log_yaz(log, dosya_yolu):
    alanlar = ["adim", "komut", "x", "y", "yon", "batarya", "olay"]
    with open(dosya_yolu, "w", encoding="utf-8", newline="") as f:
        yazici = csv.DictWriter(f, fieldnames=alanlar)
        yazici.writeheader()
        yazici.writerows(log)


def harita_metni(durum):
    """Haritayi metin olarak verir; robot 'R' ile gosterilir."""
    satirlar = [satir[:] for satir in durum["izgara"]]
    satirlar[durum["y"]][durum["x"]] = "R"
    return "\n".join("".join(satir) for satir in satirlar)
