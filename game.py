import pgzrun
import random
from math import hypot
from pygame import Rect
from pgzero.actor import Actor
from pgzero.keyboard import keyboard, keys
from pgzero.clock import clock
from pgzero.builtins import music, sounds

GENISLIK = 800
YUKSEKLIK = 600
OYUN_ADI = "Zindan Oyunu"

durum_menu = "menu"
durum_oyun = "oyun"
durum_bitti = "bitti"
durum_kazandi = "kazandi"

def mesafe(a, b):
    # İki nokta arasındaki mesafe 
    return hypot(a[0] - b[0], a[1] - b[1])

def sinirla(deger, mn, mx):
    # sınırlamayı kutu içine alma
    return max(mn, min(deger, mx))

class Karakter:
    def __init__(self, x, y, idle, yurume, hiz=2, cap=18):
        self.x = x
        self.y = y
        self.bekle = idle[:]
        self.yuru = yurume[:]
        self.kare = 0
        self.zaman = 0.0
        self.aralik = 0.18
        self.yon = "sag"
        self.hareket = False
        self.hiz = hiz
        self.cap = cap
        self.actor = Actor(self.bekle[0], (self.x, self.y))
    def animasyon(self, dt):
        self.zaman += dt
        frameler = self.yuru if self.hareket else self.bekle
        if not frameler:
            return
        if self.zaman >= self.aralik:
            self.zaman = 0.0
            self.kare = (self.kare + 1) % len(frameler)
            self.actor.image = frameler[self.kare]
    def ciz(self):
        self.actor.pos = (self.x, self.y)
        self.actor.draw()
    def carpisti(self, diger):
        return mesafe((self.x, self.y), (diger.x, diger.y)) <= (self.cap + diger.cap)

class Oyuncu(Karakter):
    def __init__(self, x, y):
        super().__init__(x, y, ["player_idle_0", "player_idle_1"], ["player_walk_0", "player_walk_1"], 3.2, 16)
        self.can = 3
        self.puan = 0
    def tus_kontrol(self):
        dx = 0
        dy = 0
        if keyboard.left:
            dx -= 1
        if keyboard.right:
            dx += 1
        if keyboard.up:
            dy -= 1
        if keyboard.down:
            dy += 1
        self.hareket = (dx != 0 or dy != 0)
        if dx != 0:
            self.yon = "sol" if dx < 0 else "sag"
        if self.hareket:
            norm = hypot(dx, dy) or 1
            self.x += (dx / norm) * self.hiz
            self.y += (dy / norm) * self.hiz
            self.x = sinirla(self.x, 16, GENISLIK - 16)
            self.y = sinirla(self.y, 16, YUKSEKLIK - 16)
    def guncelle(self, dt):
        self.tus_kontrol()
        self.animasyon(dt)

class DusmanPatrol(Karakter):
    def __init__(self, x1, x2, y):
        super().__init__(x1, y, ["enemy_patrol_idle_0"], ["enemy_patrol_walk_0"], 2, 16)
        self.minx = min(x1, x2)
        self.maxx = max(x1, x2)
        self.yon = 1
    def guncelle(self, dt):
        self.hareket = True
        self.x += self.yon * self.hiz
        if self.x > self.maxx:
            self.x = self.maxx
            self.yon = -1
        if self.x < self.minx:
            self.x = self.minx
            self.yon = 1
        self.animasyon(dt)

class DusmanGezgin(Karakter):
    def __init__(self, alan):
        cx = (alan.left + alan.right) // 2
        cy = (alan.top + alan.bottom) // 2
        super().__init__(cx, cy, ["enemy_wander_idle_0"], ["enemy_wander_walk_0"], 1.5, 16)
        self.alan = alan
        self.hedef = (self.x, self.y)
        self.zaman2 = 0.0
        self.sure = random.uniform(1.0, 3.0)
    def yeni_hedef(self):
        tx = random.uniform(self.alan.left + 10, self.alan.right - 10)
        ty = random.uniform(self.alan.top + 10, self.alan.bottom - 10)
        self.hedef = (tx, ty)
    def guncelle(self, dt):
        self.zaman2 += dt
        if self.zaman2 >= self.sure:
            self.yeni_hedef()
            self.zaman2 = 0.0
            self.sure = random.uniform(1.0, 3.0)
        dx = self.hedef[0] - self.x
        dy = self.hedef[1] - self.y
        uzak = hypot(dx, dy)
        if uzak > 4:
            self.hareket = True
            self.x += (dx / uzak) * self.hiz
            self.y += (dy / uzak) * self.hiz
        else:
            self.hareket = False
        self.x = sinirla(self.x, self.alan.left + 5, self.alan.right - 5)
        self.y = sinirla(self.y, self.alan.top + 5, self.alan.bottom - 5)
        self.animasyon(dt)

class Altin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.actor = Actor("coin", (self.x, self.y))
        self.alindi = False
        self.cap = 12
    def ciz(self):
        if not self.alindi:
            self.actor.pos = (self.x, self.y)
            self.actor.draw()

oyun_durum = durum_menu
oyuncu = None
dusmanlar = []
altinlar = []
muzik_acik = True

menu_buton = {
    "basla": Rect(300, 230, 200, 48),
    "muzik": Rect(300, 300, 200, 48),
    "cikis": Rect(300, 370, 200, 48),
}

def yeni_oyun():
    global oyuncu, dusmanlar, altinlar, oyun_durum
    oyuncu = Oyuncu(GENISLIK // 2, YUKSEKLIK - 80)
    dusmanlar = []
    dusmanlar.append(DusmanPatrol(160, 360, 180))
    dusmanlar.append(DusmanPatrol(420, 680, 260))
    dusmanlar.append(DusmanGezgin(Rect(80, 340, 240, 160)))
    dusmanlar.append(DusmanGezgin(Rect(520, 120, 240, 160)))
    altinlar.clear()
    for _ in range(8):
        x = random.randint(40, GENISLIK - 40)
        y = random.randint(40, YUKSEKLIK - 120)
        altinlar.append(Altin(x, y))
    oyuncu.can = 3
    oyuncu.puan = 0
    oyun_durum = durum_oyun
    if muzik_acik:
        try:
            music.play("bg_music")
        except Exception as e:
            print("Müzik hatası:", e)

def menu_ciz():
    screen.clear()
    screen.fill((20, 20, 30))
    screen.draw.text(OYUN_ADI, center=(GENISLIK // 2, 120), fontsize=56, owidth=1.0, scolor="white")
    for isim, rect in menu_buton.items():
        screen.draw.filled_rect(rect, (40, 40, 70))
        etiket = {"basla": "Başla", "muzik": f"Müzik: {'Açık' if muzik_acik else 'Kapalı'}", "cikis": "Çıkış"}[isim]
        screen.draw.text(etiket, center=rect.center, fontsize=28, color="white")
    screen.draw.text("Yön tuşlarıyla hareket et. Altınları topla. Düşmanlardan kaç.", (40, YUKSEKLIK - 40), fontsize=20, color="white")

def oyun_ciz():
    screen.clear()
    screen.fill((12, 16, 30))
    for d in dusmanlar:
        if isinstance(d, DusmanGezgin):
            rect = d.alan
            screen.draw.rect(rect, "darkslateblue")
    for a in altinlar:
        a.ciz()
    for d in dusmanlar:
        d.ciz()
    oyuncu.ciz()
    screen.draw.text(f"Can: {oyuncu.can}", (10, 10), fontsize=26, color="white")
    screen.draw.text(f"Puan: {oyuncu.puan}", (GENISLIK - 140, 10), fontsize=26, color="white")

def bitti_ciz():
    screen.clear()
    screen.fill((10, 10, 10))
    screen.draw.text("Oyun Bitti", center=(GENISLIK // 2, YUKSEKLIK // 2 - 30), fontsize=64, color="red")
    screen.draw.text("R'ye bas, menüye dön", center=(GENISLIK // 2, YUKSEKLIK // 2 + 30), fontsize=28, color="white")

def kazandi_ciz():
    screen.clear()
    screen.fill((6, 30, 10))
    screen.draw.text("Kazandın!", center=(GENISLIK // 2, YUKSEKLIK // 2 - 30), fontsize=64, color="gold")
    screen.draw.text("R'ye bas, menüye dön", center=(GENISLIK // 2, YUKSEKLIK // 2 + 30), fontsize=28, color="white")

def draw():
    if oyun_durum == durum_menu:
        menu_ciz()
    elif oyun_durum == durum_oyun:
        oyun_ciz()
    elif oyun_durum == durum_bitti:
        bitti_ciz()
    elif oyun_durum == durum_kazandi:
        kazandi_ciz()

def update(dt):
    global oyun_durum
    if oyun_durum == durum_oyun:
        oyuncu.guncelle(dt)
        for d in dusmanlar:
            d.guncelle(dt)
            if d.carpisti(oyuncu):
                oyuncuya_vur()
        for a in altinlar:
            if not a.alindi and mesafe((oyuncu.x, oyuncu.y), (a.x, a.y)) <= (oyuncu.cap + a.cap):
                a.alindi = True
                oyuncu.puan += 1
                try:
                    sounds.coin.play()
                except Exception:
                    pass
        if all(a.alindi for a in altinlar):
            oyun_durum = durum_kazandi
            try:
                music.stop()
            except Exception:
                pass

def oyuncuya_vur():
    # Can azalınca kısa süre dokunulmazlık
    if not hasattr(oyuncu, "vur_cooldown") or oyuncu.vur_cooldown <= 0:
        oyuncu.can -= 1
        oyuncu.vur_cooldown = 1.2
        try:
            sounds.hit_sound.play()
        except Exception:
            pass
        if oyuncu.can <= 0:
            oyun_bitti()

def oyun_bitti():
    global oyun_durum
    oyun_durum = durum_bitti
    try:
        music.stop()
        sounds.death_sound.play()
    except Exception:
        pass

def on_key_down(key):
    global oyun_durum
    if oyun_durum in (durum_bitti, durum_kazandi) and key == keys.R:
        menuye_git()

def menuye_git():
    global oyun_durum
    oyun_durum = durum_menu
    try:
        music.stop()
    except Exception:
        pass

def on_mouse_down(pos):
    global muzik_acik, oyun_durum
    if oyun_durum == durum_menu:
        if menu_buton["basla"].collidepoint(pos):
            yeni_oyun()
        elif menu_buton["muzik"].collidepoint(pos):
            muzik_acik = not muzik_acik
            if muzik_acik:
                try:
                    music.play("bg_music")
                except Exception as e:
                    print("Müzik hatası:", e)
            else:
                try:
                    music.stop()
                except Exception:
                    pass
        elif menu_buton["cikis"].collidepoint(pos):
            quit()
    elif oyun_durum in (durum_bitti, durum_kazandi):
        menuye_git()

def _cooldown_tick():
    if oyun_durum == durum_oyun and hasattr(oyuncu, "vur_cooldown"):
        oyuncu.vur_cooldown -= 0.1
        if oyuncu.vur_cooldown < 0:
            oyuncu.vur_cooldown = 0

clock.schedule_interval(_cooldown_tick, 0.1)
oyun_durum = durum_menu