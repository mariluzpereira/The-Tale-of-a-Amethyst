import math
import pygame
import recursos as rec
from configuracoes import largura_tela, altura_tela, estrelas_maximas, custo_poder, total_fases, total_flores_easter_egg

_fontes = {}


def fonte(tamanho):
    if tamanho not in _fontes:
        _fontes[tamanho] = pygame.font.Font(None, tamanho)
    return _fontes[tamanho]


def texto(tela, s, tamanho, cor, pos, centro=False, sombra=True, direita=False):
    f = fonte(tamanho)
    img = f.render(s, True, cor)
    r = img.get_rect()
    if centro:
        r.center = pos
    elif direita:
        r.topright = pos
    else:
        r.topleft = pos
    if sombra:
        sh = f.render(s, True, (15, 8, 25))
        tela.blit(sh, r.move(2, 2))
    tela.blit(img, r)
    return r


def quebrar_texto(s, tamanho, largura_max):
    f = fonte(tamanho)
    linhas, atual = [], ""
    for palavra in s.split():
        teste = (atual + " " + palavra).strip()
        if f.size(teste)[0] <= largura_max:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def cobrir(img, largura, altura):
    """Escala a imagem para cobrir a área (estilo 'cover') e recorta o centro."""
    escala = max(largura / img.get_width(), altura / img.get_height())
    novo = pygame.transform.smoothscale(
        img, (int(img.get_width() * escala) + 1, int(img.get_height() * escala) + 1))
    x = (novo.get_width() - largura) // 2
    y = (novo.get_height() - altura) // 2
    return novo.subsurface((x, y, largura, altura)).copy()


_cache_escurecer = {}


def escurecer(tela, alfa):
    if alfa not in _cache_escurecer:
        v = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
        v.fill((10, 5, 20, alfa))
        _cache_escurecer[alfa] = v
    tela.blit(_cache_escurecer[alfa], (0, 0))


# ====================================================================== HUD
class HUD:
    def __init__(self):
        self.coracoes = rec.quadros_barra("coracoes_sprites", 10, 6)
        self.estrelas = rec.quadros_barra("estrelas_sprites", 10, 4)
        flor = rec.imagem("Flor.png")
        self.icone_flor = rec.escalar_altura(rec.recortar(flor), 26) if flor is not None else None
        self.painel = pygame.Surface((300, 132), pygame.SRCALPHA)
        self.painel.fill((20, 12, 35, 150))
        retrato = rec.imagem("dialogo.png")        # retrato do Rei das Fadas Corrompido
        self.retrato_chefe = rec.escalar_altura(rec.recortar(retrato), 64, suave=True) if retrato is not None else None

    @staticmethod
    def _indice(fracao):
        fracao = max(0.0, min(1.0, fracao))
        return int(round((1.0 - fracao) * 9))

    def desenhar(self, tela, j, info):
        tela.blit(self.painel, (8, 8))

        # corações
        if self.coracoes:
            tela.blit(self.coracoes[self._indice(j.hearts / float(j.coracoes_maximos))], (18, 16))
        else:
            for i in range(j.coracoes_maximos):
                cor = (230, 50, 90) if i < j.hearts else (80, 40, 90)
                pygame.draw.circle(tela, cor, (30 + i * 28, 30), 11)
        texto(tela, "%d/%d" % (max(0, j.hearts), j.coracoes_maximos), 26, (255, 200, 220), (200, 22))

        # estrelas (energia)
        if self.estrelas:
            tela.blit(self.estrelas[self._indice(j.stars / float(estrelas_maximas))], (18, 56))
        else:
            pygame.draw.rect(tela, (60, 140, 255), (18, 60, int(150 * j.stars / estrelas_maximas), 14))
        texto(tela, "%d" % j.stars, 26, (170, 220, 255), (200, 62))

        # estado do poder
        y = 108
        if j.eh_sapinho:
            texto(tela, "Sapinho! volta em %ds" % (j.tempo_sapinho // 60 + 1), 24, (140, 255, 140), (18, y))
        elif j.special_active:
            pygame.draw.rect(tela, (30, 20, 50), (18, y, 160, 10))
            duracoes = {"Safira": 180, "Louise": 70, "Anika": 150, "Meliah": 180}
            frac = j.tempo_especial / float(duracoes.get(j.tipo_personagem, 100))
            pygame.draw.rect(tela, (255, 220, 90), (18, y, int(160 * max(0, frac)), 10))
            texto(tela, "poder ativo", 22, (255, 230, 150), (186, y - 3))
        elif j.cooldown_timer > 0:
            pygame.draw.rect(tela, (30, 20, 50), (18, y, 160, 10))
            frac = 1 - j.cooldown_timer / float(j.tempo_recarga_maximo)
            pygame.draw.rect(tela, (140, 140, 170), (18, y, int(160 * frac), 10))
            texto(tela, "recarregando", 22, (190, 190, 210), (186, y - 3))
        elif j.stars >= custo_poder:
            texto(tela, "Poder pronto: " + info.get("tecla_poder", "botão direito"), 22, (255, 240, 170), (18, y - 3))
        else:
            texto(tela, "Sem energia: pegue estrelas!", 22, (255, 150, 150), (18, y - 3))

        # canto direito: fase, pontos, flores, inimigos
        nome = info["nome_fase"]
        texto(tela, "%s - %s" % nome, 28, (255, 255, 255), (largura_tela - 16, 14), direita=True)
        texto(tela, "Pontos: %d" % j.score, 26, (255, 240, 170), (largura_tela - 16, 42), direita=True)
        if self.icone_flor is not None:
            tela.blit(self.icone_flor, (largura_tela - 92, 66))
        texto(tela, "%d/%d" % (j.flowers_collected, total_flores_easter_egg), 26,
              (255, 190, 230), (largura_tela - 16, 70), direita=True)
        if info["numero"] < total_fases:
            if info["limpa"]:
                if (info["tempo"] // 25) % 2 == 0:
                    texto(tela, "Caminho livre! Siga para a direita >>", 28, (170, 255, 170),
                          (largura_tela - 16, 98), direita=True)
            else:
                texto(tela, "Inimigos restantes: %d" % info["inimigos"], 26, (255, 170, 170),
                      (largura_tela - 16, 98), direita=True)

        # barra do chefe
        boss = info.get("boss")
        if boss is not None:
            w = 520
            x = (largura_tela - w) // 2
            y = altura_tela - 38
            pygame.draw.rect(tela, (20, 8, 30), (x - 3, y - 3, w + 6, 22))
            frac = max(0.0, boss.hp / float(boss.hp_max))
            pygame.draw.rect(tela, (170, 40, 90), (x, y, int(w * frac), 16))
            for marca in (0.33, 0.66):
                pygame.draw.line(tela, (255, 255, 255), (x + int(w * marca), y), (x + int(w * marca), y + 15), 1)
            texto(tela, "Rei das Fadas Corrompido", 24, (255, 220, 240), (largura_tela // 2, y - 14), centro=True)
            if self.retrato_chefe is not None:
                tela.blit(self.retrato_chefe, self.retrato_chefe.get_rect(midright=(x - 10, y + 8)))

        # setas apontando inimigos que sobraram fora da tela
        for lado in info.get("setas", []):
            y = altura_tela // 2
            if lado < 0:
                pygame.draw.polygon(tela, (255, 120, 120), [(14, y), (40, y - 18), (40, y + 18)])
            else:
                pygame.draw.polygon(tela, (255, 120, 120),
                                    [(largura_tela - 14, y), (largura_tela - 40, y - 18), (largura_tela - 40, y + 18)])


# ====================================================================== diálogos
_cache_linhas = {}


def _linhas(frase, tamanho, largura):
    chave = (frase, tamanho, largura)
    if chave not in _cache_linhas:
        _cache_linhas[chave] = quebrar_texto(frase, tamanho, largura)
    return _cache_linhas[chave]


VELOCIDADE_DIGITACAO = 1.3          # letras por frame


def desenhar_caixa_dialogo(tela, nome, frase, rosto, t, bloqueia, duracao=None, topo=None, dica=None):
    """Caixa de fala com retrato e efeito de digitação (usada nas fases e na casa da Fada)."""
    if bloqueia or duracao is None:
        fade = min(1.0, t / 8.0)
    else:
        fade = max(0.0, min(1.0, t / 10.0, (duracao - t) / 10.0))
    caixa = pygame.Rect(24, altura_tela - 156 if topo is None else topo, largura_tela - 48, 132)
    sup = pygame.Surface(caixa.size, pygame.SRCALPHA)
    sup.fill((28, 14, 48, int(225 * fade)))
    pygame.draw.rect(sup, (255, 225, 130, int(255 * fade)) if bloqueia else (200, 150, 255, int(255 * fade)),
                     sup.get_rect(), 3)
    tela.blit(sup, caixa.topleft)

    x_texto = caixa.x + 20
    if rosto is not None:
        img = rec.escalado(rosto, 140, True, 150)
        if fade < 1.0:
            img = img.copy()
            img.set_alpha(int(255 * fade))
        tela.blit(img, img.get_rect(midbottom=(caixa.x + 85, caixa.bottom - 4)))
        x_texto = caixa.x + 175
    if fade > 0.3:
        texto(tela, nome, 32, (255, 225, 120), (x_texto, caixa.y + 14))
        restante = int(t * VELOCIDADE_DIGITACAO)
        y = caixa.y + 48
        for linha in _linhas(frase, 30, caixa.right - x_texto - 24):
            if restante <= 0:
                break
            texto(tela, linha[:restante], 30, (255, 255, 255), (x_texto, y))
            restante -= len(linha) + 1
            y += 30
        if dica is None:
            dica = "[E] continuar" if bloqueia else "[E] fechar"
        texto(tela, dica, 22, (255, 235, 170) if bloqueia else (180, 170, 210),
              (caixa.right - 16, caixa.bottom - 26), direita=True)


class CaixaDialogo:
    """Legendas com retrato. Dois tipos:
       - comum: some sozinha depois de alguns segundos (o jogo continua)
       - bloqueante: congela o jogo; avança com a tecla de interagir / Enter / clique"""

    def __init__(self):
        self.fila = []
        self.atual = None
        self.t = 0
        self.ultimo = {}
        self.ao_digitar = None          # função chamada a cada poucas letras (som)
        self.ao_avancar = None          # função chamada quando passa para a próxima fala
        self.dica = None                # texto do canto da caixa (ex.: "[E] continuar")

    @property
    def bloqueando(self):
        return self.atual is not None and self.atual[4]

    def mostrar(self, chave, nome, frase, rosto, agora, intervalo=600, bloqueia=False):
        """Mostra legenda (com retrato). 'intervalo' evita repetir cedo demais."""
        if agora - self.ultimo.get(chave, -10 ** 9) < intervalo:
            return False
        self.ultimo[chave] = agora
        duracao = 120 + int(len(frase) * 2.5)
        item = (nome, frase, rosto, duracao, bloqueia)
        if self.atual is None:
            self.atual, self.t = item, 0
        else:
            self.fila.append(item)
            if not bloqueia:
                # falas comuns acumuladas demais são descartadas (as bloqueantes, nunca)
                comuns = [i for i in self.fila if not i[4]]
                while len(comuns) > 2:
                    self.fila.remove(comuns.pop(0))
        return True

    def limpar(self):
        self.fila, self.atual, self.t = [], None, 0

    def fechar(self):
        if self.atual is None:
            return
        if self.fila:
            self.atual, self.t = self.fila.pop(0), 0
            if self.ao_avancar:
                self.ao_avancar()
        else:
            self.atual, self.t = None, 0

    def avancar(self):
        """1º aperto: mostra o texto inteiro; 2º aperto: vai para a próxima fala."""
        if self.atual is None:
            return
        if self.t * VELOCIDADE_DIGITACAO < len(self.atual[1]):
            self.t = int(len(self.atual[1]) / VELOCIDADE_DIGITACAO) + 1
        else:
            self.fechar()

    def atualizar(self):
        if self.atual is None:
            return
        self.t += 1
        n = len(self.atual[1])
        antes, agora = int((self.t - 1) * VELOCIDADE_DIGITACAO), int(self.t * VELOCIDADE_DIGITACAO)
        if self.ao_digitar and agora < n and agora // 3 != antes // 3:
            self.ao_digitar()
        if not self.atual[4] and self.t >= self.atual[3]:
            self.fechar()

    def desenhar(self, tela):
        if self.atual is None:
            return
        nome, frase, rosto, duracao, bloqueia = self.atual
        desenhar_caixa_dialogo(tela, nome, frase, rosto, self.t, bloqueia, duracao,
                               dica=(self.dica if self.dica and bloqueia else None))


# ====================================================================== botão de menu
def desenhar_botao(tela, imagem_botao, rotulo, centro, selecionado):
    if imagem_botao is not None:
        r = imagem_botao.get_rect(center=centro)
        tela.blit(imagem_botao, r)
    else:
        r = pygame.Rect(0, 0, 172, 44)
        r.center = centro
        pygame.draw.rect(tela, (255, 150, 255), r, border_radius=6)
        pygame.draw.rect(tela, (60, 20, 90), r, 3, border_radius=6)
        texto(tela, rotulo, 28, (50, 15, 70), r.center, centro=True, sombra=False)
    if selecionado:
        pygame.draw.rect(tela, (255, 255, 255), r.inflate(10, 8), 3, border_radius=8)
        base = int(4 * math.sin(pygame.time.get_ticks() * 0.01))
        pygame.draw.polygon(tela, (255, 255, 255),
                            [(r.left - 18 + base, r.centery), (r.left - 30 + base, r.centery - 8),
                             (r.left - 30 + base, r.centery + 8)])
    return r
