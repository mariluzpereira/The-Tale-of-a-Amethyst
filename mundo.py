import math
import random
import pygame
from objetos import item


class Mundo:
    """Tudo que existe na fase atual (plataformas, inimigos, tiros, itens...).
    É passado para inimigos/projéteis para eles poderem agir no cenário."""

    def __init__(self, audio):
        self.audio = audio
        self.plataformas = pygame.sprite.Group()
        self.inimigos = pygame.sprite.Group()
        self.proj_inimigos = pygame.sprite.Group()
        self.proj_jogador = pygame.sprite.Group()
        self.itens = pygame.sprite.Group()
        self.particulas = []
        self.largura = 1024
        self.chao_y = 424
        self.limite_direito = 1024
        self.tempo = 0
        self.fase_limpa = False
        self.eventos = []            # recados para o motor: ("boss_fase", n)

    # ------------------------------------------------------------ partículas
    def emitir(self, x, y, cor, n=8, vel=3.0, vida=26, raio=3, grav=0.12):
        for _ in range(n):
            ang = random.uniform(0, 2 * math.pi)
            v = random.uniform(0.3, 1.0) * vel
            self.particulas.append([x, y, math.cos(ang) * v, math.sin(ang) * v - 0.5,
                                    vida * random.uniform(0.6, 1.0), vida, cor, raio, grav])

    def atualizar_particulas(self):
        vivas = []
        for p in self.particulas:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += p[8]
            p[4] -= 1
            if p[4] > 0:
                vivas.append(p)
        self.particulas = vivas[-400:]

    def desenhar_particulas(self, tela, cam_x):
        for p in self.particulas:
            r = max(1, int(p[7] * p[4] / p[5]))
            pygame.draw.circle(tela, p[6], (int(p[0] - cam_x), int(p[1])), r)

    # ------------------------------------------------------------ itens
    def soltar_item(self, tipo, x, y):
        self.itens.add(item(int(x), int(y), tipo))

    # ------------------------------------------------------------ boss
    def boss_mudou_de_fase(self, boss, fase):
        self.audio.tocar("boss_rugido")
        self.emitir(boss.rect.centerx, boss.rect.centery, (210, 120, 255), n=40, vel=6, vida=40, raio=5)
        # presentinhos para a jogadora respirar entre as fases do chefe
        self.soltar_item("Maca", self.largura // 2, 215)
        self.soltar_item("Estrela", 235, 300)
        self.soltar_item("Estrela", self.largura - 235, 300)
        self.eventos.append(("boss_fase", fase))
