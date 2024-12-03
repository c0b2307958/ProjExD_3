import os
import random
import sys
import time
import math
import pygame as pg

WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
NUM_OF_BOMBS = 5  # 爆弾の個数
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)  # 初期向きは右向き

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)  # 移動方向を更新
            self.img = __class__.imgs[self.dire]
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird: "Bird"):
        self.vx, self.vy = bird.dire  # こうかとんの向きに応じて速度を設定
        self.img = pg.image.load("fig/beam.png")
        angle = math.degrees(math.atan2(-self.vy, self.vx))  # 角度を計算
        self.img = pg.transform.rotozoom(self.img, angle, 0.9)  # 回転
        self.rct = self.img.get_rect()
        self.rct.centerx = bird.rct.centerx + bird.rct.width * self.vx // 5
        self.rct.centery = bird.rct.centery + bird.rct.height * self.vy // 5

    def update(self, screen: pg.Surface):
        self.rct.move_ip(self.vx, self.vy)
        if check_bound(self.rct) == (True, True):
            screen.blit(self.img, self.rct)


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Explosion:
    """
    爆発エフェクトに関するクラス
    """
    def __init__(self, center: tuple[int, int]):
        self.images = [pg.image.load(f"fig/explosion{i}.png") for i in range(5)]
        self.index = 0
        self.rct = self.images[0].get_rect(center=center)
        self.life = len(self.images) * 5  # フレーム数

    def update(self, screen: pg.Surface):
        if self.life > 0:
            screen.blit(self.images[self.index // 5], self.rct)
            self.index += 1
            self.life -= 1


class Score:
    """
    スコア表示クラス
    """
    def __init__(self):
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)
        self.value = 0
        self.img = self.font.render(f"Score: {self.value}", True, self.color)
        self.rct = self.img.get_rect()
        self.rct.bottomright = (WIDTH - 10, HEIGHT - 10)  # 右下に表示

    def update(self, screen: pg.Surface):
        self.img = self.font.render(f"Score: {self.value}", True, self.color)
        screen.blit(self.img, self.rct)


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    beams = []
    explosions = []
    score = Score()
    clock = pg.time.Clock()

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.append(Beam(bird))

        screen.blit(bg_img, [0, 0])

        for bomb in bombs[:]:
            if bird.rct.colliderect(bomb.rct):
                bird.change_img(8, screen)
                pg.display.update()
                time.sleep(1)
                return

        for beam in beams[:]:
            for bomb in bombs[:]:
                if beam.rct.colliderect(bomb.rct):
                    beams.remove(beam)
                    bombs.remove(bomb)
                    explosions.append(Explosion(bomb.rct.center))
                    score.value += 1

        beams = [beam for beam in beams if check_bound(beam.rct) == (True, True)]
        explosions = [exp for exp in explosions if exp.life > 0]

        for beam in beams:
            beam.update(screen)
        for bomb in bombs:
            bomb.update(screen)
        for explosion in explosions:
            explosion.update(screen)

        score.update(screen)
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)

        pg.display.update()
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
