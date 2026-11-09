import math
import random
import pygame
import desenho
from fisica import mover_corpo
from projeteis import projetil
from configuracoes import gravidade

TEMPO_MORTE = 26


class inimigo(pygame.sprite.Sprite):
    """Base de todos os inimigos."""

    ancora = "base"      # 'base' = pés no chão | 'centro' = voadores

    def __init__(self, tipo, largura, altura):
        super().__init__()
        self.enemy_type = tipo
        self.rect = pygame.Rect(0, 0, largura, altura)
        self.fx = 0.0
        self.fy = 0.0
        self.vy = 0.0
        self.kb = 0.0
        self.no_chao = False
        self.bateu_parede = False
        self.hp = self.hp_max = 6
        self.invuln = 0
        self.flash = 0
        self.morrendo = 0
        self.recompensado = False
        self.face = 1
        self.tempo = 0.0
        self.pontos = 100
        self.image = pygame.Surface((largura, altura), pygame.SRCALPHA)

    # ---- posicionamento
    def posicionar_base(self, x_centro, y_base):
        self.rect.midbottom = (int(x_centro), int(y_base))
        self.fx, self.fy = float(self.rect.x), float(self.rect.y)

    def posicionar_centro(self, x, y):
        self.rect.center = (int(x), int(y))
        self.fx, self.fy = float(self.rect.x), float(self.rect.y)

    # ---- vida
    def receber_dano(self, dano=1, empurrao=0):
        if self.invuln > 0 or self.morrendo > 0:
            return False
        self.hp -= dano
        self.invuln = 10
        self.flash = 10
        self.empurrar(empurrao)
        if self.hp <= 0:
            self.morrendo = TEMPO_MORTE
        return True

    def empurrar(self, vx):
        self.kb = vx

    def area_dano(self):
        """Região que machuca a jogadora ao encostar."""
        return self.rect

    def ao_ferir_jogador(self):
        pass

    def passo_comum(self, escala):
        """Timers. Devolve True se o inimigo está morrendo (pula o resto)."""
        if self.invuln > 0:
            self.invuln -= 1
        if self.flash > 0:
            self.flash -= 1
        if self.morrendo > 0:
            self.morrendo -= 1
            if self.morrendo <= 0:
                self.kill()
            return True
        return False

    # ---- desenho
    def desenhar(self, tela, cam_x):
        img = self.image
        if self.ancora == "centro":
            pos = img.get_rect(center=(self.rect.centerx - cam_x, self.rect.centery))
        else:
            pos = img.get_rect(midbottom=(self.rect.centerx - cam_x, self.rect.bottom + 2))
        if self.flash > 0 and (self.flash // 2) % 2 == 0:
            img = img.copy()
            img.fill((150, 150, 150, 0), special_flags=pygame.BLEND_RGB_ADD)
        if self.morrendo > 0:
            img = img.copy()
            img.set_alpha(int(255 * self.morrendo / TEMPO_MORTE))
        tela.blit(img, pos)

    def desenhar_barra_vida(self, tela, cam_x):
        if self.hp >= self.hp_max or self.morrendo > 0 or self.enemy_type == "Boss":
            return
        largura = 40
        x = self.rect.centerx - cam_x - largura // 2
        y = self.rect.top - 12
        pygame.draw.rect(tela, (40, 10, 20), (x - 1, y - 1, largura + 2, 7))
        pygame.draw.rect(tela, (230, 60, 80), (x, y, int(largura * max(0, self.hp) / self.hp_max), 5))


# ====================================================================== PLANTA
class Planta(inimigo):
    """Obstáculo estático. Fica de olho na jogadora e dá uma mordida
    (com alcance maior) quando ela chega perto."""

    def __init__(self, x, y_base, **_):
        super().__init__("Planta", 44, 56)
        self.hp = self.hp_max = 6
        self.pontos = 100
        self.quadros = desenho.quadros_planta()    # (fechada, aberta) -> (dir, esq)
        self.posicionar_base(x, y_base)
        self.mordendo = 0
        self.recarga = random.randint(50, 110)
        self.image = self.quadros[0][0]

    def area_dano(self):
        return self.rect.inflate(46, 6) if self.mordendo > 0 else self.rect

    def update(self, jogador, escala, mundo):
        if self.passo_comum(escala):
            return
        self.tempo += escala
        self.face = 1 if jogador.rect.centerx >= self.rect.centerx else -1
        dist = abs(jogador.rect.centerx - self.rect.centerx)
        alt = abs(jogador.rect.centery - self.rect.centery)

        if self.mordendo > 0:
            self.mordendo -= escala
        else:
            self.recarga -= escala
            if self.recarga <= 0 and dist < 150 and alt < 120:
                self.mordendo = 30
                self.recarga = 100
                mundo.audio.tocar("planta_morde")

        par = self.quadros[1] if self.mordendo > 0 else self.quadros[0]
        self.image = par[0] if self.face > 0 else par[1]
        # balançadinha de leve
        self.rect.y = int(self.fy)


# ====================================================================== BRUXA
class Bruxa(inimigo):
    """Anda pelo cenário (aproxima / recua / patrulha) e arremessa poções
    em arco que transformam a princesa em sapinho."""

    def __init__(self, x, y_base, x_min=None, x_max=None, **_):
        super().__init__("Bruxa", 34, 66)
        self.hp = self.hp_max = 6
        self.pontos = 150
        self.quadros = desenho.quadros_bruxa()
        self.posicionar_base(x, y_base)
        self.x_min = x_min if x_min is not None else x - 220
        self.x_max = x_max if x_max is not None else x + 220
        self.dir_patrulha = random.choice((-1, 1))
        self.recarga = random.uniform(60, 130)
        self.lancando = 0
        self.arremessou = True
        self.direcao = 0
        self.image = self.quadros["parada"][0]

    def _arremessar(self, jogador, mundo):
        ox = self.rect.centerx + self.face * 16
        oy = self.rect.top + 24
        alvo_x = jogador.rect.centerx + random.randint(-35, 35)
        mundo.proj_inimigos.add(projetil(ox, oy, alvo_x, jogador.rect.centery,
                                         eh_inimigo=True, tipo="pocao_bruxa"))
        mundo.audio.tocar("pocao_lancada")

    def update(self, jogador, escala, mundo):
        if self.passo_comum(escala):
            return
        self.tempo += escala
        dx = jogador.rect.centerx - self.rect.centerx
        adx = abs(dx)
        self.face = 1 if dx >= 0 else -1

        # ---- movimento: aproxima se longe, recua se perto, senão patrulha
        if adx > 430:
            direcao = self.face
        elif adx < 230:
            direcao = -self.face
        else:
            if self.rect.left <= self.x_min:
                self.dir_patrulha = 1
            elif self.rect.right >= self.x_max:
                self.dir_patrulha = -1
            direcao = self.dir_patrulha
        if direcao > 0 and self.rect.right >= self.x_max:
            direcao = 0
        if direcao < 0 and self.rect.left <= self.x_min:
            direcao = 0
        if self.lancando > 0:
            direcao = 0          # para um instante para lançar
        self.direcao = direcao

        self.vy = min(12.0, self.vy + gravidade * escala)
        dx_mov = direcao * 1.5 * escala + self.kb
        self.kb *= 0.85
        if abs(self.kb) < 0.3:
            self.kb = 0.0
        mover_corpo(self, dx_mov, self.vy * escala, mundo.plataformas)

        # ---- ataque
        if self.lancando > 0:
            self.lancando -= escala
            if not self.arremessou and self.lancando <= 12:
                self._arremessar(jogador, mundo)
                self.arremessou = True
        else:
            self.recarga -= escala
            if self.recarga <= 0 and adx < 640 and self.no_chao:
                self.lancando = 26
                self.arremessou = False
                self.recarga = random.uniform(110, 170)
                if random.random() < 0.4:
                    mundo.audio.tocar("bruxa_ri")

        # ---- imagem
        if self.lancando > 0:
            par = self.quadros["lancando"]
        elif self.direcao != 0:
            andar = self.quadros["andar"]
            par = andar[int(self.tempo // 10) % len(andar)]
        else:
            par = self.quadros["parada"]
        self.image = par[0] if self.face > 0 else par[1]


# ====================================================================== VESPA
class Vespa(inimigo):
    """Voadora. Fica zunindo no lugar até a princesa chegar perto; então
    persegue. Depois de ferir, recua um pouco para dar um respiro."""

    ancora = "centro"

    def __init__(self, x, y, **_):
        super().__init__("Vespa", 46, 34)
        self.hp = self.hp_max = 6
        self.pontos = 120
        self.voo, self.hit = desenho.quadros_vespa()
        self.posicionar_centro(x, y)
        self.ox, self.oy = float(x), float(y)
        self.fase_voo = random.uniform(0, 6.28)
        self.ativada = False
        self.recuo = 0
        self.image = self.voo[0][0]

    def ao_ferir_jogador(self):
        self.recuo = 55

    def update(self, jogador, escala, mundo):
        if self.passo_comum(escala):
            return
        self.tempo += escala
        self.fase_voo += 0.13 * escala

        dx = jogador.rect.centerx - self.rect.centerx
        dy = jogador.rect.centery - self.rect.centery
        dist = max(1.0, math.hypot(dx, dy))
        self.face = 1 if dx >= 0 else -1

        if self.recuo > 0:
            self.recuo -= escala
            self.fx += (-dx / dist) * 3.2 * escala
            self.fy += (-dy / dist) * 2.0 * escala - 0.8 * escala
        elif self.ativada or dist < 430:
            if not self.ativada:
                self.ativada = True
                mundo.audio.tocar("vespa")
            if dist > 750:                       # perdeu a presa: volta ao posto
                self.ativada = False
            vel = 2.5 + (0.6 if dist > 260 else 0.0)
            self.fx += dx / dist * vel * escala
            self.fy += (dy / dist * vel + math.sin(self.fase_voo * 1.3) * 1.1) * escala
        else:
            alvo_y = self.oy + math.sin(self.fase_voo) * 12
            alvo_x = self.ox + math.cos(self.fase_voo * 0.5) * 18
            self.fx += (alvo_x - self.rect.width / 2 - self.fx) * 0.03 * escala
            self.fy += (alvo_y - self.rect.height / 2 - self.fy) * 0.03 * escala

        # empurrão de golpes
        self.fx += self.kb * escala
        self.kb *= 0.85
        if abs(self.kb) < 0.3:
            self.kb = 0.0

        # limites do mundo
        self.fx = max(0.0, min(self.fx, mundo.largura - self.rect.width))
        self.fy = max(30.0, min(self.fy, mundo.chao_y - self.rect.height - 6))
        self.rect.x, self.rect.y = int(round(self.fx)), int(round(self.fy))

        if self.invuln > 0:
            par = self.hit[int(self.tempo // 3) % len(self.hit)]
        else:
            par = self.voo[int(self.tempo // 3) % len(self.voo)]
        # as imagens originais olham p/ a esquerda: par = (esq, dir)
        self.image = par[1] if self.face > 0 else par[0]


# ====================================================================== BOSS
class Boss(inimigo):
    """Rei das Fadas Corrompido. 3 fases conforme perde vida:
       1) tiros em leque
       2) + invoca vespas e dispara anéis de energia
       3) mais rápido, + investidas contra a princesa"""

    ancora = "centro"

    def __init__(self, x, y, **_):
        super().__init__("Boss", 84, 112)
        self.hp = self.hp_max = 80
        self.pontos = 2000
        self.quadros = desenho.quadros_boss()
        self.posicionar_centro(x, y)
        self.y_base = float(y)
        self.fase_boss = 1
        self.estado = "flutuando"
        self.t_estado = 0.0
        self.t_tiro = 100.0
        self.t_radial = 260.0
        self.t_invoca = 300.0
        self.t_investida = 420.0
        self.vx_investida = 0.0
        self.vy_investida = 0.0
        self.image = self.quadros[0][0]

    def empurrar(self, vx):      # o chefe não se deixa empurrar
        pass

    def area_dano(self):
        return self.rect.inflate(-18, -18)

    def fase_atual(self):
        r = self.hp / float(self.hp_max)
        return 1 if r > 0.66 else (2 if r > 0.33 else 3)

    def _tiro_em_leque(self, jogador, mundo, fase):
        cx, cy = self.rect.center
        base = math.atan2(jogador.rect.centery - cy, jogador.rect.centerx - cx)
        desvios = (-0.22, 0.0, 0.22) if fase == 1 else (-0.44, -0.22, 0.0, 0.22, 0.44)
        for d in desvios:
            a = base + d
            mundo.proj_inimigos.add(projetil(cx, cy, cx + math.cos(a) * 300, cy + math.sin(a) * 300,
                                             eh_inimigo=True, tipo="orbe"))
        mundo.audio.tocar("boss_tiro")

    def _anel(self, mundo, quantidade):
        cx, cy = self.rect.center
        giro = random.uniform(0, math.pi)
        for i in range(quantidade):
            a = giro + i * 2 * math.pi / quantidade
            mundo.proj_inimigos.add(projetil(cx, cy, cx + math.cos(a) * 300, cy + math.sin(a) * 300,
                                             eh_inimigo=True, tipo="orbe"))
        mundo.audio.tocar("boss_tiro")

    def _invocar(self, mundo):
        vivas = sum(1 for e in mundo.inimigos if e.enemy_type == "Vespa" and e.morrendo == 0)
        if vivas >= 3:
            return
        for lado in (-1, 1):
            v = Vespa(self.rect.centerx + lado * 90, self.rect.centery)
            v.ativada = True
            mundo.inimigos.add(v)
        mundo.emitir(self.rect.centerx, self.rect.centery, (200, 120, 255), n=18, vel=4)
        mundo.audio.tocar("vespa")

    def update(self, jogador, escala, mundo):
        if self.passo_comum(escala):
            return
        self.tempo += escala
        fase = self.fase_atual()
        if fase != self.fase_boss:
            self.fase_boss = fase
            mundo.boss_mudou_de_fase(self, fase)

        mult = {1: 1.0, 2: 1.25, 3: 1.6}[fase]
        self.face = 1 if jogador.rect.centerx >= self.rect.centerx else -1

        esq = 60.0
        dir_ = mundo.largura - 60.0 - self.rect.width
        centro = (esq + dir_) / 2
        amp = (dir_ - esq) / 2 * 0.9
        pos_x = centro + math.sin(self.tempo * 0.014 * mult) * amp
        pos_y = self.y_base + math.sin(self.tempo * 0.045) * 30

        if self.estado == "flutuando":
            self.fx, self.fy = pos_x, pos_y
        elif self.estado == "carregando":
            self.t_estado -= escala
            self.fx += random.uniform(-2.5, 2.5)
            self.flash = 4 if int(self.t_estado) % 6 < 3 else 0
            if self.t_estado <= 0:
                dx = jogador.rect.centerx - self.rect.centerx
                dy = jogador.rect.centery - self.rect.centery
                d = max(1.0, math.hypot(dx, dy))
                self.vx_investida = dx / d * 11
                self.vy_investida = dy / d * 11
                self.estado = "investindo"
                self.t_estado = 32
                mundo.audio.tocar("boss_investida")
        elif self.estado == "investindo":
            self.t_estado -= escala
            self.fx += self.vx_investida * escala
            self.fy += self.vy_investida * escala
            self.fx = max(esq, min(self.fx, dir_))
            self.fy = max(60.0, min(self.fy, mundo.chao_y - self.rect.height - 6))
            if self.t_estado <= 0:
                self.estado = "voltando"
                self.t_estado = 50
        elif self.estado == "voltando":
            self.t_estado -= escala
            self.fx += (pos_x - self.fx) * 0.09 * escala
            self.fy += (pos_y - self.fy) * 0.09 * escala
            if self.t_estado <= 0:
                self.estado = "flutuando"

        self.rect.x, self.rect.y = int(round(self.fx)), int(round(self.fy))

        # ---- ataques (não ataca enquanto carrega/investe)
        if self.estado in ("flutuando", "voltando"):
            self.t_tiro -= escala
            if self.t_tiro <= 0:
                self._tiro_em_leque(jogador, mundo, fase)
                self.t_tiro = {1: 95, 2: 80, 3: 62}[fase]
            if fase >= 2:
                self.t_radial -= escala
                if self.t_radial <= 0:
                    self._anel(mundo, 10 if fase == 2 else 14)
                    self.t_radial = 260 if fase == 2 else 200
                self.t_invoca -= escala
                if self.t_invoca <= 0:
                    self._invocar(mundo)
                    self.t_invoca = 420 if fase == 2 else 330
            if fase >= 3 and self.estado == "flutuando":
                self.t_investida -= escala
                if self.t_investida <= 0:
                    self.estado = "carregando"
                    self.t_estado = 45
                    self.t_investida = 380
                    mundo.audio.tocar("boss_rugido")

        par = self.quadros[int(self.tempo // 12) % len(self.quadros)]
        self.image = par[0] if self.face > 0 else par[1]


# ====================================================================== fábrica
def criar_inimigo(tipo, x, y, **extras):
    classes = {"Planta": Planta, "Bruxa": Bruxa, "Vespa": Vespa, "Boss": Boss}
    return classes[tipo](x, y, **extras)
