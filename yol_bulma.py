"""En kisa yol bulma (bonus: GIT x y komutu icin).

BFS (genislik oncelikli arama) kullanilir: her adimin maliyeti esit oldugu
icin ilk bulunan yol en kisa yoldur.
"""
from collections import deque

YON_FARKLARI = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # yukari, sag, asagi, sol


def hucre_bos_mu(izgara, x, y):
    """Harita icinde ve duvar degilse True."""
    return 0 <= y < len(izgara) and 0 <= x < len(izgara[0]) and izgara[y][x] != "#"


def en_kisa_yol(izgara, baslangic, hedef):
    """baslangic'tan hedef'e [(x, y), ...] listesi doner (baslangic dahil).

    Yol yoksa None doner.
    """
    if not hucre_bos_mu(izgara, *hedef) or not hucre_bos_mu(izgara, *baslangic):
        return None

    onceki = {baslangic: None}
    kuyruk = deque([baslangic])
    while kuyruk:
        x, y = kuyruk.popleft()
        if (x, y) == hedef:
            break
        for dx, dy in YON_FARKLARI:
            komsu = (x + dx, y + dy)
            if komsu not in onceki and hucre_bos_mu(izgara, *komsu):
                onceki[komsu] = (x, y)
                kuyruk.append(komsu)

    if hedef not in onceki:
        return None

    yol = []
    h = hedef
    while h is not None:
        yol.append(h)
        h = onceki[h]
    yol.reverse()
    return yol
