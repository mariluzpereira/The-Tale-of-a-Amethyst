import math
import random
import pygame
import desenho
from fisica import mover_corpo
from projeteis import projetil
from configuracoes import (
    gravidade, hp_planta, hp_bruxa, hp_vespa, hp_boss, vel_vespa, vel_bruxa, recarga_bruxa,
    recarga_planta, recuo_vespa, dano_contato_boss,
)


class inimigo(pygame.sprite.Sprite):
    """Base de todos os inimigos.

    Cada inimigo tem uma hitbox (rect) e um 'quadro' (imagem + ponto de
    ancoragem) que é escolhido a cada update de acordo com a animação."""

    tempo_morte = 26       # quantos frames dura a animação de morte

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
        self.dano_contato = 1       # corações que tira ao encostar
        self.quadro = None

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
            self.morrendo = self.tempo_morte
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

    def alfa_morte(self):
        """Opacidade durante a morte: inteira na 1ª metade, some na 2ª."""
        return int(255 * min(1.0, self.morrendo / max(1.0, self.tempo_morte * 0.5)))

    # ---- desenho
    def desenhar(self, tela, cam_x):
        q = self.quadro
        if q is None:
            return
        img = q.img
        pos = q.posicao(self.rect, cam_x)
        if self.flash > 0 and (self.flash // 2) % 2 == 0:
            img = img.copy()
            img.fill((150, 150, 150, 0), special_flags=pygame.BLEND_RGB_ADD)
        if self.morrendo > 0:
            alfa = self.alfa_morte()
            if alfa < 255:
                img = img.copy()
                img.set_alpha(alfa)
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
    """Obstáculo estático. Quando a princesa chega perto ela se prepara,
    dá o bote (alcance maior só nesse instante) e recolhe."""

    tempo_morte = 40
    DURACAO_MORDIDA = 40

    def __init__(self, x, y_base, **_):
        super().__init__("Planta", 64, 62)
        self.hp = self.hp_max = hp_planta
        self.pontos = 100
        self.q = desenho.quadros_planta()
        self.posicionar_base(x, y_base)
        self.mordendo = 0.0
        self.mordeu_som = False
        self.recarga = random.randint(40, recarga_planta)
        self.quadro = self.q["idle"][0]

    def _decorrido(self):
        return self.DURACAO_MORDIDA - self.mordendo

    def area_dano(self):
        # só no instante do bote o alcance aumenta
        if self.mordendo > 0 and 10 <= self._decorrido() < 27:
            return self.rect.inflate(120, 36)
        return self.rect

    def update(self, jogador, escala, mundo):
        if self.passo_comum(escala):
            self.quadro = self.q["derrotada"][0 if self.face > 0 else 1]
            return
        self.tempo += escala
        self.face = 1 if jogador.rect.centerx >= self.rect.centerx else -1
        dist = abs(jogador.rect.centerx - self.rect.centerx)
        alt = abs(jogador.rect.centery - self.rect.centery)

        if self.mordendo > 0:
            self.mordendo -= escala
            if not self.mordeu_som and self._decorrido() >= 10:
                self.mordeu_som = True
                mundo.audio.tocar("planta_morde")
        else:
            self.recarga -= escala
            if self.recarga <= 0 and dist < 200 and alt < 140:
                self.mordendo = float(self.DURACAO_MORDIDA)
                self.mordeu_som = False
                self.recarga = recarga_planta

        if self.mordendo > 0:
            d = self._decorrido()
            estado = "preparando" if d < 10 else ("mordendo" if d < 27 else "voltando")
        else:
            estado = "idle"
        par = self.q[estado]
        self.quadro = par[0] if self.face > 0 else par[1]


# ====================================================================== BRUXA
class Bruxa(inimigo):
    """Voa de vassoura pela região (aproxima / recua / patrulha) e arremessa
    poções em arco que transformam a princesa em sapinho. Ao morrer, cai."""

    tempo_morte = 50

    def __init__(self, x, y_base, x_min=None, x_max=None, **_):
        super().__init__("Bruxa", 56, 52)
        self.hp = self.hp_max = hp_bruxa
        self.pontos = 150
        self.q = desenho.quadros_bruxa()
        self.posicionar_centro(x, y_base - 80)
        self.x_min = x_min if x_min is not None else x - 220
        self.x_max = x_max if x_max is not None else x + 220
        self.dir_patrulha = random.choice((-1, 1))
        self.fase_voo = random.uniform(0, 6.28)
        self.recarga = random.uniform(50, 100)
        self.lancando = 0.0
        self.arremessou = True
        self.direcao = 0
        self.quadro = self.q["voando"][0][1]

    def _arremessar(self, jogador, mundo):
        ox = self.rect.centerx + self.face * 30
        oy = self.rect.centery - 6
        alvo_x = jogador.rect.centerx + random.randint(-35, 35)
        mundo.proj_inimigos.add(projetil(ox, oy, alvo_x, jogador.rect.centery,
                                         eh_inimigo=True, tipo="pocao_bruxa"))
        mundo.emitir(ox, oy, (90, 230, 90), n=5, vel=2)
        mundo.audio.tocar("pocao_lancada")

    def update(self, jogador, escala, mundo):
        if self.passo_comum(escala):
            # cai da vassoura até o chão
            self.vy = min(12.0, self.vy + gravidade * escala)
            self.fy = min(self.fy + self.vy * escala, float(mundo.chao_y - self.rect.height))
            self.rect.y = int(round(self.fy))
            self.quadro = self.q["morta"][0 if self.face > 0 else 1]
            return
        self.tempo += escala
        self.fase_voo += 0.07 * escala
        dx = jogador.rect.centerx - self.rect.centerx
        adx = abs(dx)
        self.face = 1 if dx >= 0 else -1

        # ---- movimento horizontal: aproxima se longe, recua se perto, senão patrulha
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
            direcao = 0                      # para um instante para lançar
        self.direcao = direcao

        self.fx += direcao * vel_bruxa * escala + self.kb * escala
        self.kb *= 0.85
        if abs(self.kb) < 0.3:
            self.kb = 0.0
        self.fx = max(float(self.x_min), min(self.fx, float(self.x_max - self.rect.width)))

        # ---- altura: paira perto do chão e sobe se a princesa estiver numa plataforma alta
        alvo_cy = max(mundo.chao_y - 230, min(mundo.chao_y - 80, jogador.rect.centery - 15))
        alvo_cy += math.sin(self.fase_voo) * 7
        cy = self.fy + self.rect.height / 2.0
        self.fy += (alvo_cy - cy) * 0.04 * escala
        self.fy = max(30.0, min(self.fy, float(mundo.chao_y - self.rect.height - 10)))
        self.rect.x, self.rect.y = int(round(self.fx)), int(round(self.fy))

        # ---- ataque
        if self.lancando > 0:
            self.lancando -= escala
            if not self.arremessou and self.lancando <= 12:
                self._arremessar(jogador, mundo)
                self.arremessou = True
        else:
            self.recarga -= escala
            if self.recarga <= 0 and adx < 640:
                self.lancando = 22
                self.arremessou = False
                self.recarga = random.uniform(*recarga_bruxa)
                if random.random() < 0.4:
                    mundo.audio.tocar("bruxa_ri")

        # ---- imagem
        lista = self.q["atingida"] if self.invuln > 0 else self.q["voando"]
        par = lista[int(self.tempo // 8) % len(lista)]
        self.quadro = par[0] if self.face > 0 else par[1]


# ====================================================================== VESPA
class Vespa(inimigo):
    """Voadora. Fica zunindo no lugar até a princesa chegar perto; então
    persegue. Depois de ferir, recua um pouco para dar um respiro."""

    def __init__(self, x, y, **_):
        super().__init__("Vespa", 46, 34)
        self.hp = self.hp_max = hp_vespa
        self.pontos = 120
        self.voo, self.hit = desenho.quadros_vespa()
        self.posicionar_centro(x, y)
        self.ox, self.oy = float(x), float(y)
        self.fase_voo = random.uniform(0, 6.28)
        self.ativada = False
        self.recuo = 0
        self.quadro = self.voo[0][0]

    def ao_ferir_jogador(self):
        self.recuo = recuo_vespa

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
            vel = vel_vespa + (0.6 if dist > 260 else 0.0)
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

        lista = self.hit if self.invuln > 0 else self.voo
        par = lista[int(self.tempo // 3) % len(lista)]
        self.quadro = par[0] if self.face > 0 else par[1]


# ====================================================================== BOSS
class Boss(inimigo):
    """Rei das Fadas Corrompido: um mago que caminha pela arena.
    3 fases conforme perde vida (a cada mudança ele cambaleia e solta itens):
       1) aponta e dispara um leque de orbes
       2) + bolas de fogo e invoca vespas
       3) mais rápido, + investidas contra a princesa
    Animações: parado, andando, apontando, atacando (fogo), dano, derrotado."""

    tempo_morte = 110

    VEL = {1: 1.7, 2: 2.2, 3: 2.8}
    PAUSA = {1: 75, 2: 55, 3: 38}

    def __init__(self, x, y_base, **_):
        super().__init__("Boss", 56, 142)
        self.hp = self.hp_max = hp_boss
        self.pontos = 2000
        self.dano_contato = dano_contato_boss
        self.q = desenho.quadros_boss()
        self.posicionar_base(x, y_base)
        self.fase_boss = 1
        self.estado = "andando"
        self.t = 0.0
        self.t_acao = 90.0
        self.acao = None
        self.disparou = False
        self.dir_investida = 1
        self.passo_anim = 0.0
        self.caminhando = False
        self.quadro = self.q["parado"][0]

    # ---- utilidades
    def empurrar(self, vx):      # o chefe não se deixa empurrar
        pass

    def area_dano(self):
        return self.rect.inflate(-6, -6)

    def fase_atual(self):
        r = self.hp / float(self.hp_max)
        return 1 if r > 0.66 else (2 if r > 0.33 else 3)

    def _mao(self):
        return (self.rect.centerx + self.face * 48, self.rect.top + 52)

    # ---- ataques
    def _leque(self, jogador, mundo, fase):
        ox, oy = self._mao()
        base = math.atan2(jogador.rect.centery - oy, jogador.rect.centerx - ox)
        desvios = (-0.22, 0.0, 0.22) if fase == 1 else (-0.44, -0.22, 0.0, 0.22, 0.44)
        for d in desvios:
            a = base + d
            mundo.proj_inimigos.add(projetil(ox, oy, ox + math.cos(a) * 300, oy + math.sin(a) * 300,
                                             eh_inimigo=True, tipo="orbe"))
        mundo.audio.tocar("boss_tiro")

    def _bola_de_fogo(self, jogador, mundo):
        ox, oy = self._mao()
        mundo.proj_inimigos.add(projetil(ox, oy, jogador.rect.centerx, jogador.rect.centery,
                                         eh_inimigo=True, tipo="bola_fogo"))
        mundo.emitir(ox, oy, (255, 170, 60), n=10, vel=3)
        mundo.audio.tocar("boss_fogo")

    def _vivas(self, mundo):
        return sum(1 for e in mundo.inimigos if e.enemy_type == "Vespa" and e.morrendo == 0)

    def _invocar(self, mundo):
        if self._vivas(mundo) >= 2:
            return
        for x in (130, mundo.largura - 130):
            v = Vespa(x, 140)
            v.ativada = True
            mundo.inimigos.add(v)
            mundo.emitir(x, 140, (200, 120, 255), n=14, vel=4)
        mundo.audio.tocar("vespa")

    def _escolher_acao(self, jogador, mundo, fase):
        r = random.random()
        if fase == 1:
            acao = "leque"
        elif fase == 2:
            acao = "leque" if r < 0.35 else ("fogo" if r < 0.70 else ("investida" if r < 0.85 else "invocar"))
        else:
            acao = "leque" if r < 0.20 else ("fogo" if r < 0.50 else ("investida" if r < 0.80 else "invocar"))
        if acao == "invocar" and self._vivas(mundo) >= 2:
            acao = "fogo"
        self.acao = acao
        self.t = 0.0
        self.disparou = False
        if acao in ("leque", "invocar"):
            self.estado = "apontando"
        elif acao == "fogo":
            self.estado = "conjurando"
        else:
            self.estado = "carregando"
            self.dir_investida = 1 if jogador.rect.centerx >= self.rect.centerx else -1
            self.face = self.dir_investida
            mundo.audio.tocar("boss_rugido")

    def _terminar_acao(self, fase, pausa=None):
        self.estado = "andando"
        self.t = 0.0
        self.t_acao = float(pausa if pausa is not None else self.PAUSA[fase])

    # ---- atualização
    def update(self, jogador, escala, mundo):
        if self.passo_comum(escala):
            prog = 1.0 - self.morrendo / float(self.tempo_morte)
            par = self.q["derrotado"][min(3, int(prog * 4))]
            self.quadro = par[0] if self.face > 0 else par[1]
            return
        self.tempo += escala
        fase = self.fase_atual()
        if fase != self.fase_boss:
            self.fase_boss = fase
            self.estado = "dano"
            self.t = 0.0
            mundo.boss_mudou_de_fase(self, fase)

        esq = 40.0
        dir_ = mundo.largura - 40.0 - self.rect.width
        dx = jogador.rect.centerx - self.rect.centerx
        if self.estado != "investindo":
            self.face = 1 if dx >= 0 else -1
        mover = 0.0
        e = self.estado

        if e == "andando":
            dist = abs(dx)
            if dist > 380:
                mover = self.face * self.VEL[fase]
            elif dist < 190:
                recuo = -self.face
                encurralado = (recuo < 0 and self.fx <= esq + 2) or (recuo > 0 and self.fx >= dir_ - 2)
                if encurralado:
                    self.t_acao = min(self.t_acao, 15.0)      # sem saída: ataca logo
                else:
                    mover = recuo * self.VEL[fase] * 0.9
            self.t_acao -= escala
            if self.t_acao <= 0:
                self._escolher_acao(jogador, mundo, fase)

        elif e == "apontando":
            self.t += escala
            if not self.disparou and self.t >= (26 if self.acao == "leque" else 20):
                self.disparou = True
                if self.acao == "leque":
                    self._leque(jogador, mundo, fase)
                else:
                    self._invocar(mundo)
            if self.t >= 40:
                self._terminar_acao(fase)

        elif e == "conjurando":
            self.t += escala
            if not self.disparou and self.t >= 34:
                self.disparou = True
                self._bola_de_fogo(jogador, mundo)
                if fase == 3:
                    self.t_acao = 25      # na fase 3 emenda outro ataque mais rápido
            if self.t >= 66:
                self._terminar_acao(fase, 25 if fase == 3 else None)

        elif e == "carregando":
            self.t += escala
            self.flash = 4 if (int(self.t) // 4) % 2 == 0 else 0
            if self.t >= 40:
                self.estado = "investindo"
                self.t = 0.0
                mundo.audio.tocar("boss_investida")

        elif e == "investindo":
            self.t += escala
            mover = self.dir_investida * 9.0
            bateu = (self.dir_investida < 0 and self.fx <= esq + 1) or \
                    (self.dir_investida > 0 and self.fx >= dir_ - 1)
            if bateu or self.t >= 45:
                self._terminar_acao(fase, 70)

        elif e == "dano":
            self.t += escala
            if self.t >= 72:
                self._terminar_acao(fase, 40)

        # ---- movimento (só no chão)
        self.caminhando = mover != 0
        if self.caminhando:
            self.passo_anim += (0.15 if e == "andando" else 0.45) * escala
        self.fx = max(esq, min(self.fx + mover * escala, dir_))
        self.rect.x = int(round(self.fx))

        # ---- quadro da animação
        if e == "andando":
            par = self.q["andando"][int(self.passo_anim) % 5] if self.caminhando else self.q["parado"]
        elif e == "apontando":
            par = self.q["apontando"][min(2, int(self.t / 13.4))]
        elif e == "conjurando":
            t = self.t
            if t < 18:
                par = self.q["atacando"][0]
            elif t < 34:
                par = self.q["atacando"][1]
            elif t < 46:
                par = self.q["atacando"][2]
            elif t < 56:
                par = self.q["atacando"][3]
            else:
                par = self.q["sem_fogo"]
        elif e == "carregando":
            par = self.q["apontando"][0]
        elif e == "investindo":
            par = self.q["andando"][int(self.passo_anim) % 5]
        else:  # dano
            par = self.q["dano"][min(3, int(self.t / 18))]
        self.quadro = par[0] if self.face > 0 else par[1]


# ====================================================================== fábrica
def criar_inimigo(tipo, x, y, **extras):
    classes = {"Planta": Planta, "Bruxa": Bruxa, "Vespa": Vespa, "Boss": Boss}
    return classes[tipo](x, y, **extras)
