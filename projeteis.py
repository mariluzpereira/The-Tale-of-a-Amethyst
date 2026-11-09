import math
import random
import pygame
import recursos as rec
from configuracoes import altura_tela, dano_tiro_jogador


class projetil(pygame.sprite.Sprite):
    """Tipos:
       'basico'       tiro da princesa (anima com os power_*.png)
       'pocao_bruxa'  poção arremessada em arco: transforma em sapinho
       'orbe'         bola de energia do Rei das Fadas
    """

    def __init__(self, x, y, alvo_x, alvo_y, eh_inimigo=False, tipo="normal",
                 tipo_personagem=None):
        super().__init__()
        self.eh_inimigo = eh_inimigo
        self.tipo = tipo
        self.transforma = False
        self.grav = 0.0
        self.vida = 240
        self.quadros = None
        self.indice = 0
        self.angulo_giro = 0
        self.dano = 1

        dx = alvo_x - x
        dy = alvo_y - y
        dist = max(1.0, math.hypot(dx, dy))

        if tipo == "pocao_bruxa":
            # arco: escolhe o tempo de voo e calcula a velocidade inicial
            tempo = max(38, min(85, dist / 6.5))
            self.grav = 0.32
            self.vx = dx / tempo
            self.vy = (dy - 0.5 * self.grav * tempo * tempo) / tempo
            self.transforma = True
            base = rec.imagem("poção.png")
            if base is not None:
                self.base = rec.escalar_altura(rec.recortar(base), 28)
            else:
                self.base = pygame.Surface((24, 24), pygame.SRCALPHA)
                pygame.draw.circle(self.base, (50, 220, 50), (12, 12), 11)
            self.image = self.base
            self.rect = pygame.Rect(0, 0, 22, 22)
        elif not eh_inimigo:
            velocidade = 13.0
            self.dano = dano_tiro_jogador
            self.vx = dx / dist * velocidade
            self.vy = dy / dist * velocidade
            sprites = rec.sprites_princesa(tipo_personagem) if tipo_personagem else None
            if sprites and sprites.get("poder"):
                # o desenho aponta para a ESQUERDA; gira para a direção do tiro
                ang = math.degrees(math.atan2(dy, -dx))
                self.quadros = [pygame.transform.rotate(q, ang) for q in sprites["poder"]]
                self.image = self.quadros[0]
            else:
                self.image = pygame.Surface((14, 14), pygame.SRCALPHA)
                pygame.draw.circle(self.image, (255, 255, 200), (7, 7), 7)
                pygame.draw.circle(self.image, (0, 255, 255), (7, 7), 4)
            self.rect = pygame.Rect(0, 0, 26, 18)
            self.vida = 70
        else:  # orbe do boss
            velocidade = 5.2
            self.vx = dx / dist * velocidade
            self.vy = dy / dist * velocidade
            self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (120, 20, 160, 120), (12, 12), 12)
            pygame.draw.circle(self.image, (230, 60, 120), (12, 12), 8)
            pygame.draw.circle(self.image, (255, 220, 240), (12, 12), 4)
            self.rect = pygame.Rect(0, 0, 18, 18)

        self.rect.center = (int(x), int(y))
        self.fx = float(x)
        self.fy = float(y)

    def update(self, escala_tempo, mundo):
        escala = escala_tempo if self.eh_inimigo else 1.0
        self.vy += self.grav * escala
        self.fx += self.vx * escala
        self.fy += self.vy * escala
        self.rect.center = (int(self.fx), int(self.fy))
        self.vida -= escala

        if self.quadros:
            self.indice += 0.4
            self.image = self.quadros[int(self.indice) % len(self.quadros)]
        elif self.tipo == "pocao_bruxa":
            self.angulo_giro += 9 * escala
            self.image = pygame.transform.rotate(self.base, self.angulo_giro)

        # bate em chão / paredes sólidas
        for p in mundo.plataformas:
            if not p.unidirecional and self.rect.colliderect(p.rect):
                self.estourar(mundo)
                return

        if (self.vida <= 0 or self.rect.right < -80 or self.rect.left > mundo.largura + 80
                or self.rect.top > altura_tela + 80 or self.rect.bottom < -300):
            self.kill()

    def estourar(self, mundo):
        if self.tipo == "pocao_bruxa":
            mundo.emitir(self.rect.centerx, self.rect.centery, (80, 230, 80), n=14, vel=3.5)
            mundo.audio.tocar("quebra")
        elif self.eh_inimigo:
            mundo.emitir(self.rect.centerx, self.rect.centery, (230, 80, 140), n=6, vel=2.5)
        else:
            mundo.emitir(self.rect.centerx, self.rect.centery, (255, 255, 220), n=5, vel=2.5)
        self.kill()
