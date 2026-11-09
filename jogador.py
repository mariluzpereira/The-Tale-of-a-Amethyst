import math
import pygame
import recursos as rec
from fisica import mover_corpo
from projeteis import projetil
from configuracoes import (
    gravidade, cores_princesa, vida_maxima, estrelas_maximas, custo_poder
)

TAM_HUMANO = (36, 80)     # hitbox em pé
TAM_SAPO = (36, 28)       # hitbox de sapinho


class jogador(pygame.sprite.Sprite):
    def __init__(self, x, y_base, tipo_personagem):
        super().__init__()
        self.tipo_personagem = tipo_personagem
        self.color = cores_princesa.get(tipo_personagem, (255, 255, 255))
        self.sprites = rec.sprites_princesa(tipo_personagem)

        self.rect = pygame.Rect(0, 0, *TAM_HUMANO)
        self.rect.midbottom = (int(x), int(y_base))
        self.fx = float(self.rect.x)
        self.fy = float(self.rect.y)
        self.vx = 0.0
        self.vy = 0.0
        self.empurrao = 0.0
        self.velocidade = 5.0
        self.forca_pulo = -13.5
        self.no_chao = False
        self.bateu_parede = False
        self.atravessar = False
        self.face = 1
        self.coyote = 0
        self.buffer_pulo = 0
        self.tempo_anim = 0
        self.movendo = False

        # status
        self.coracoes_maximos = vida_maxima
        self.hearts = vida_maxima
        self.stars = estrelas_maximas
        self.score = 0
        self.flowers_collected = 0

        # poderes
        self.special_active = False
        self.tempo_especial = 0
        self.cooldown_timer = 0
        self.tempo_recarga_maximo = 180
        self.tempo_invulnerabilidade = 0
        self.recarga_tiro = 0
        self.timer_giro = 0

        # sapinho
        self.eh_sapinho = False
        self.tempo_sapinho = 0

        self._escudo = None

    # ------------------------------------------------------------------ vida
    @property
    def morta(self):
        return self.hearts <= 0

    def reposicionar(self, x, y_base):
        """Usada ao começar uma fase nova (mantém coração, estrelas e pontos)."""
        self.rect.midbottom = (int(x), int(y_base))
        self.fx, self.fy = float(self.rect.x), float(self.rect.y)
        self.vx = self.vy = self.empurrao = 0.0
        self.special_active = False
        self.tempo_especial = 0
        self.cooldown_timer = 0
        self.tempo_invulnerabilidade = 60

    def restaurar_para_nova_tentativa(self):
        self.hearts = self.coracoes_maximos
        self.stars = estrelas_maximas
        self.eh_sapinho = False
        self._trocar_hitbox(TAM_HUMANO)

    # ------------------------------------------------------------------ sapinho
    def _trocar_hitbox(self, tamanho):
        base = self.rect.midbottom
        self.rect = pygame.Rect(0, 0, *tamanho)
        self.rect.midbottom = base
        self.fx, self.fy = float(self.rect.x), float(self.rect.y)

    def transformar_em_sapinho(self):
        if self.eh_sapinho:
            return False
        self.eh_sapinho = True
        self.tempo_sapinho = 600           # 10 segundos
        self.special_active = False
        self.tempo_especial = 0
        self._trocar_hitbox(TAM_SAPO)
        return True

    def restaurar_forma_humana(self, plataformas):
        # só volta ao normal se houver espaço em cima (não nascer dentro de uma parede)
        teste = pygame.Rect(0, 0, *TAM_HUMANO)
        teste.midbottom = self.rect.midbottom
        for p in plataformas:
            if not p.unidirecional and teste.colliderect(p.rect):
                self.tempo_sapinho = 15
                return False
        self.eh_sapinho = False
        self._trocar_hitbox(TAM_HUMANO)
        return True

    # ------------------------------------------------------------------ update
    def update(self, teclas, mundo):
        self.tempo_anim += 1
        if self.tempo_invulnerabilidade > 0:
            self.tempo_invulnerabilidade -= 1
        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1
        if self.recarga_tiro > 0:
            self.recarga_tiro -= 1

        if self.eh_sapinho:
            self.tempo_sapinho -= 1
            if self.tempo_sapinho <= 0:
                if self.restaurar_forma_humana(mundo.plataformas):
                    mundo.audio.tocar("destransforma")
                    mundo.emitir(self.rect.centerx, self.rect.centery, (255, 255, 255), n=14, vel=3)

        esquerda = teclas[pygame.K_a] or teclas[pygame.K_LEFT]
        direita = teclas[pygame.K_d] or teclas[pygame.K_RIGHT]
        pular = teclas[pygame.K_w] or teclas[pygame.K_SPACE] or teclas[pygame.K_UP]
        descer = teclas[pygame.K_s] or teclas[pygame.K_DOWN]
        self.atravessar = bool(descer)

        vel = 4.2 if self.eh_sapinho else self.velocidade
        self.vx = 0.0
        if esquerda and not direita:
            self.vx = -vel
            self.face = -1
        elif direita and not esquerda:
            self.vx = vel
            self.face = 1
        self.movendo = self.vx != 0

        flutuando = (self.tipo_personagem == "Safira" and self.special_active
                     and not self.eh_sapinho)
        if flutuando:
            # paira no ar: W/Espaço sobe, S desce
            alvo = -3.2 if pular else (3.2 if descer else 0.0)
            self.vy += (alvo - self.vy) * 0.18
            if self.tempo_anim % 4 == 0:
                mundo.emitir(self.rect.centerx + self.face * -8, self.rect.bottom - 4,
                             (255, 190, 225), n=1, vel=0.8, vida=22, raio=2)
        else:
            self.vy = min(15.0, self.vy + gravidade)

        # pulo com "coyote time" e buffer (mais perdoador)
        if self.no_chao:
            self.coyote = 7
        elif self.coyote > 0:
            self.coyote -= 1
        self.buffer_pulo = 7 if pular else max(0, self.buffer_pulo - 1)
        if not flutuando and self.buffer_pulo > 0 and self.coyote > 0:
            self.vy = -10.5 if self.eh_sapinho else self.forca_pulo
            self.coyote = 0
            self.buffer_pulo = 0
            self.no_chao = False
            mundo.audio.tocar("pulo")
        # soltou o botão cedo = pulo mais baixo
        if not pular and self.vy < -4.5 and not flutuando:
            self.vy = -4.5

        # duração dos poderes
        if self.special_active:
            self.tempo_especial -= 1
            if self.tempo_especial <= 0:
                self.special_active = False
                self.cooldown_timer = self.tempo_recarga_maximo

        dx = self.vx + self.empurrao
        self.empurrao *= 0.8
        if abs(self.empurrao) < 0.3:
            self.empurrao = 0.0
        mover_corpo(self, dx, self.vy, mundo.plataformas)

        if self.rect.left < 0:
            self.rect.left = 0
            self.fx = float(self.rect.x)
        if self.rect.right > mundo.limite_direito:
            self.rect.right = mundo.limite_direito
            self.fx = float(self.rect.x)
        if self.rect.top < -60:
            self.rect.top = -60
            self.fy = float(self.rect.y)
            self.vy = max(self.vy, 0)

    # ------------------------------------------------------------------ ações
    def atirar(self, alvo, grupo, mundo):
        """Ataque básico em direção ao cursor (alvo = posição no mundo)."""
        if self.eh_sapinho or self.recarga_tiro > 0 or self.morta:
            return False
        self.recarga_tiro = 18
        ox = self.rect.centerx + (20 if alvo[0] >= self.rect.centerx else -20)
        oy = self.rect.top + 30
        grupo.add(projetil(ox, oy, alvo[0], alvo[1], eh_inimigo=False, tipo="basico",
                           tipo_personagem=self.tipo_personagem))
        self.face = 1 if alvo[0] >= self.rect.centerx else -1
        mundo.audio.tocar("tiro")
        return True

    def use_special(self, mundo):
        """Devolve: 'ok', 'sapinho', 'recarga' ou 'sem_energia'."""
        if self.eh_sapinho:
            return "sapinho"
        if self.special_active or self.cooldown_timer > 0:
            return "recarga"
        if self.stars < custo_poder:
            return "sem_energia"
        self.stars -= custo_poder
        self.special_active = True
        duracoes = {"Safira": 180, "Louise": 70, "Anika": 150, "Meliah": 180}
        self.tempo_especial = duracoes.get(self.tipo_personagem, 120)
        self.timer_giro = 0
        mundo.audio.tocar("poder_" + self.tipo_personagem.lower())
        return "ok"

    def receber_dano(self, origem_x=None, forca=1):
        """True se o dano foi aplicado (fora do tempo de invulnerabilidade)."""
        if self.tempo_invulnerabilidade > 0 or self.morta:
            return False
        self.hearts -= forca
        self.tempo_invulnerabilidade = 90
        if origem_x is not None:
            self.empurrao = 9.0 if self.rect.centerx >= origem_x else -9.0
        self.vy = -6.0
        self.no_chao = False
        return True

    def bloqueia(self, x_origem):
        """Escudo da Anika: bloqueia ataques vindos da frente."""
        if self.tipo_personagem != "Anika" or not self.special_active or self.eh_sapinho:
            return False
        return (x_origem - self.rect.centerx) * self.face > -10

    def atacar_inimigos(self, grupo_inimigos, proj_inimigos, mundo):
        """Pirueta Furacão da Louise: dano em área contínuo + repele."""
        if (self.tipo_personagem != "Louise" or not self.special_active or self.eh_sapinho):
            return
        self.timer_giro += 1
        area = self.rect.inflate(150, 50)
        if self.timer_giro % 8 == 1:
            for e in grupo_inimigos:
                if e.morrendo == 0 and area.colliderect(e.rect):
                    sentido = 1 if e.rect.centerx >= self.rect.centerx else -1
                    if e.receber_dano(1, empurrao=9 * sentido):
                        mundo.audio.tocar("acerto")
                        mundo.emitir(e.rect.centerx, e.rect.centery, (255, 110, 110), n=6)
        for p in proj_inimigos:
            if area.colliderect(p.rect):
                p.estourar(mundo)

    # ------------------------------------------------------------------ desenho
    def _imagem_atual(self):
        if not self.sprites:
            return None
        lado = "dir" if self.face > 0 else "esq"
        if self.eh_sapinho:
            quadros = self.sprites.get("sapo_" + lado)
            if not quadros:
                return None
            if not self.no_chao:
                return self.sprites.get("sapo_pulo_" + lado, quadros[0])
            return quadros[(self.tempo_anim // 8) % len(quadros)] if self.movendo else quadros[0]
        quadros = self.sprites["andar_" + lado]
        if not self.no_chao:
            return quadros[1 % len(quadros)]
        if self.movendo:
            sequencia = [0, 1, 2, 1]
            return quadros[sequencia[(self.tempo_anim // 7) % 4] % len(quadros)]
        return quadros[0]

    def desenhar(self, tela, cam_x):
        # pisca quando está invulnerável
        if self.tempo_invulnerabilidade > 0 and (self.tempo_invulnerabilidade // 4) % 2 == 0:
            visivel = False
        else:
            visivel = True

        img = self._imagem_atual()
        r = self.rect.move(-cam_x, 0)
        if visivel:
            if img is not None:
                pos = img.get_rect(midbottom=(r.centerx, r.bottom + 2))
                tela.blit(img, pos)
            else:
                pygame.draw.rect(tela, self.color, r)

        self._desenhar_efeitos(tela, cam_x)

    def _desenhar_efeitos(self, tela, cam_x):
        if not self.special_active or self.eh_sapinho:
            return
        cx = self.rect.centerx - cam_x
        cy = self.rect.centery
        t = self.tempo_anim

        if self.tipo_personagem == "Anika":
            if self._escudo is None:
                base = rec.imagem("Escudo (2).png")
                if base is not None:
                    self._escudo = rec.escalar_largura(rec.recortar(base), 120, suave=True)
                else:
                    s = pygame.Surface((110, 110), pygame.SRCALPHA)
                    pygame.draw.circle(s, (120, 200, 255, 120), (55, 55), 54)
                    pygame.draw.circle(s, (200, 235, 255), (55, 55), 54, 3)
                    self._escudo = s
            img = self._escudo
            alfa = 170 + int(60 * math.sin(t * 0.2))
            copia = img.copy()
            copia.set_alpha(alfa)
            tela.blit(copia, copia.get_rect(center=(cx + self.face * 30, cy)))

        elif self.tipo_personagem == "Louise":
            sup = pygame.Surface((220, 130), pygame.SRCALPHA)
            for k in range(4):
                larg = 200 - k * 34 + int(10 * math.sin(t * 0.5 + k))
                alt = 40 + k * 16
                deslocamento = int(math.sin(t * 0.7 + k * 1.7) * 14)
                retangulo = pygame.Rect(0, 0, larg, alt)
                retangulo.center = (110 + deslocamento, 65 + (k - 2) * 12)
                pygame.draw.ellipse(sup, (255, 120 + k * 25, 120, 190), retangulo, 3)
            tela.blit(sup, sup.get_rect(center=(cx, cy)))

        elif self.tipo_personagem == "Meliah":
            raio = 40 + int(8 * math.sin(t * 0.15))
            sup = pygame.Surface((raio * 2 + 4, raio * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(sup, (190, 150, 255, 45), (raio + 2, raio + 2), raio)
            pygame.draw.circle(sup, (220, 190, 255, 160), (raio + 2, raio + 2), raio, 2)
            tela.blit(sup, sup.get_rect(center=(cx, cy)))

        elif self.tipo_personagem == "Safira":
            sup = pygame.Surface((90, 90), pygame.SRCALPHA)
            pygame.draw.circle(sup, (255, 190, 225, 45), (45, 45), 42)
            tela.blit(sup, sup.get_rect(center=(cx, cy)))
