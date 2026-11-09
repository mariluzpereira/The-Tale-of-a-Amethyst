"""Desenhos de reserva (pixel art feita por código) para os personagens que
ainda não têm sprite: Bruxa, Planta Carnívora, Rei das Fadas e itens.

Quando você criar os PNGs, é só colocar na pasta com estes nomes e o jogo
passa a usá-los automaticamente (ver README_FASES.md):
  bruxa_parada.png  bruxa_andando(1..2).png  bruxa_lancando.png   (viradas p/ a DIREITA)
  planta_fechada.png  planta_mordendo.png
  boss_voando(1..2).png                                            (virado p/ a DIREITA)
"""
import math
import pygame
import recursos as rec


def _ampliar(surf, fator):
    return pygame.transform.scale(surf, (surf.get_width() * fator, surf.get_height() * fator))


def _par(surf):
    """(virado p/ direita, virado p/ esquerda)"""
    return surf, rec.espelhar(surf)


# ------------------------------------------------------------------ Bruxa
def _bruxa_base(passo, braco_erguido):
    s = pygame.Surface((16, 24), pygame.SRCALPHA)
    roxo = (125, 45, 165)
    roxo_esc = (80, 25, 115)
    verde = (135, 205, 95)
    verde_esc = (90, 150, 60)
    preto = (25, 10, 35)
    dourado = (250, 215, 70)
    marrom = (110, 70, 40)
    # chapéu
    pygame.draw.polygon(s, roxo_esc, [(8, 0), (12, 7), (4, 7)])
    pygame.draw.rect(s, dourado, (4, 6, 9, 1))
    pygame.draw.rect(s, roxo, (2, 7, 13, 2))
    # rosto
    pygame.draw.rect(s, verde, (5, 9, 7, 5))
    s.set_at((6, 11), preto)
    s.set_at((10, 11), preto)
    s.set_at((8, 12), verde_esc)
    pygame.draw.rect(s, preto, (7, 13, 3, 1))
    # corpo / vestido
    pygame.draw.polygon(s, roxo, [(5, 14), (12, 14), (14, 22), (2, 22)])
    pygame.draw.rect(s, roxo_esc, (7, 15, 3, 7))
    # braço (frente = direita)
    if braco_erguido:
        pygame.draw.rect(s, verde, (12, 10, 2, 5))
        pygame.draw.rect(s, (60, 220, 60), (12, 7, 3, 3))    # poção na mão
    else:
        pygame.draw.rect(s, verde, (12, 15, 2, 4))
    # pés
    if passo == 0:
        pygame.draw.rect(s, marrom, (4, 22, 3, 2))
        pygame.draw.rect(s, marrom, (9, 22, 3, 2))
    elif passo == 1:
        pygame.draw.rect(s, marrom, (3, 22, 3, 2))
        pygame.draw.rect(s, marrom, (10, 22, 3, 2))
    else:
        pygame.draw.rect(s, marrom, (5, 22, 3, 2))
        pygame.draw.rect(s, marrom, (8, 22, 3, 2))
    return _ampliar(s, 3)


def quadros_bruxa():
    """dict: parada, andar (lista de 2), lancando -> cada um (dir, esq)"""
    parada = rec.imagem("bruxa_parada.png")
    if parada is not None:
        andar = rec.carregar_quadros("bruxa_andando({})", 2) or [parada]
        lanc = rec.imagem("bruxa_lancando.png") or parada
        f = lambda im: _par(rec.escalar_altura(rec.recortar(im), 72))
        return {"parada": f(parada), "andar": [f(a) for a in andar], "lancando": f(lanc)}
    return {
        "parada": _par(_bruxa_base(0, False)),
        "andar": [_par(_bruxa_base(1, False)), _par(_bruxa_base(2, False))],
        "lancando": _par(_bruxa_base(0, True)),
    }


# ------------------------------------------------------------------ Planta carnívora
def _planta_base(boca_aberta):
    s = pygame.Surface((16, 20), pygame.SRCALPHA)
    verde = (60, 160, 70)
    verde_esc = (35, 110, 50)
    vermelho = (205, 45, 60)
    vermelho_esc = (140, 20, 40)
    branco = (245, 245, 235)
    # caule e folhas
    pygame.draw.rect(s, verde, (7, 10, 2, 10))
    pygame.draw.polygon(s, verde_esc, [(7, 18), (1, 15), (4, 19)])
    pygame.draw.polygon(s, verde_esc, [(9, 18), (15, 15), (12, 19)])
    # cabeça
    if boca_aberta:
        pygame.draw.polygon(s, vermelho, [(8, 8), (1, 1), (15, 1)])     # mandíbula de cima
        pygame.draw.polygon(s, vermelho_esc, [(8, 9), (2, 11), (14, 11)])  # de baixo
        pygame.draw.rect(s, (60, 10, 20), (4, 3, 8, 6))
        for x in (4, 6, 8, 10):
            s.set_at((x, 3), branco)
            s.set_at((x, 8), branco)
    else:
        pygame.draw.ellipse(s, vermelho, (1, 3, 14, 8))
        pygame.draw.line(s, vermelho_esc, (2, 7), (14, 7))
        for x in (3, 5, 7, 9, 11, 13):
            s.set_at((x, 6), branco)
        pygame.draw.rect(s, (255, 230, 80), (6, 4, 2, 1))   # olhinho
    return _ampliar(s, 3)


def quadros_planta():
    """(fechada, aberta) -> cada um (dir, esq)"""
    fechada = rec.imagem("planta_fechada.png")
    if fechada is not None:
        aberta = rec.imagem("planta_mordendo.png") or fechada
        f = lambda im: _par(rec.escalar_altura(rec.recortar(im), 60))
        return f(fechada), f(aberta)
    return _par(_planta_base(False)), _par(_planta_base(True))


# ------------------------------------------------------------------ Rei das Fadas Corrompido
def _boss_base(asa_cima):
    s = pygame.Surface((32, 38), pygame.SRCALPHA)
    asa = (190, 120, 235, 190)
    asa_esc = (130, 60, 190, 200)
    manto = (55, 20, 85)
    manto_cl = (95, 45, 135)
    pele = (225, 200, 215)
    ouro = (250, 210, 70)
    gema = (170, 60, 255)
    olho = (255, 40, 70)
    # asas
    if asa_cima:
        pygame.draw.polygon(s, asa, [(12, 14), (0, 0), (3, 14)])
        pygame.draw.polygon(s, asa, [(20, 14), (32, 0), (29, 14)])
        pygame.draw.polygon(s, asa_esc, [(12, 18), (1, 12), (6, 22)])
        pygame.draw.polygon(s, asa_esc, [(20, 18), (31, 12), (26, 22)])
    else:
        pygame.draw.polygon(s, asa, [(12, 14), (0, 10), (4, 24)])
        pygame.draw.polygon(s, asa, [(20, 14), (32, 10), (28, 24)])
        pygame.draw.polygon(s, asa_esc, [(12, 20), (2, 22), (7, 30)])
        pygame.draw.polygon(s, asa_esc, [(20, 20), (30, 22), (25, 30)])
    # manto
    pygame.draw.polygon(s, manto, [(11, 14), (21, 14), (25, 37), (7, 37)])
    pygame.draw.polygon(s, manto_cl, [(14, 15), (18, 15), (19, 36), (13, 36)])
    # cabeça
    pygame.draw.rect(s, pele, (12, 5, 8, 8))
    s.set_at((14, 8), olho)
    s.set_at((17, 8), olho)
    pygame.draw.rect(s, (60, 20, 40), (14, 11, 4, 1))
    # coroa
    pygame.draw.rect(s, ouro, (11, 3, 10, 2))
    for x in (11, 15, 19):
        pygame.draw.polygon(s, ouro, [(x, 3), (x + 1, 0), (x + 2, 3)])
    s.set_at((16, 1), gema)
    # cajado com a Ametista
    pygame.draw.rect(s, (110, 75, 45), (26, 14, 1, 22))
    pygame.draw.polygon(s, gema, [(26, 8), (29, 12), (26, 15), (23, 12)])
    s.set_at((26, 10), (240, 200, 255))
    return _ampliar(s, 3)


def quadros_boss():
    """lista de 2 quadros (asa pra cima / pra baixo) -> cada um (dir, esq)"""
    q = rec.carregar_quadros("boss_voando({})", 2)
    if q:
        return [_par(rec.escalar_altura(rec.recortar(im), 120)) for im in q]
    return [_par(_boss_base(True)), _par(_boss_base(False))]


# ------------------------------------------------------------------ vespa (usa os PNGs existentes)
def quadros_vespa():
    """(voando[5], atingida[4]) -> cada quadro (olhando p/ esquerda, p/ direita)"""
    voo = rec.carregar_quadros("vespa_sprite_voando({})", 5)
    hit = rec.carregar_quadros("vespa_sprite_atingida({})", 4)
    todos = rec.uniao_recorte(voo + hit) if (voo or hit) else []
    if not todos:
        s = pygame.Surface((60, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (240, 190, 20), (14, 10, 36, 20))
        for x in (24, 32, 40):
            pygame.draw.rect(s, (30, 20, 10), (x, 11, 4, 18))
        pygame.draw.ellipse(s, (255, 255, 255, 170), (22, 0, 20, 12))
        todos = [s] * (len(voo) + len(hit) or 9)
        voo, hit = todos[:5], todos[5:9]
    else:
        todos = [rec.escalar_largura(q, 76, suave=True) for q in todos]
        voo, hit = todos[:len(voo)], todos[len(voo):]
    # as imagens originais olham para a ESQUERDA
    def par(im):
        return im, rec.espelhar(im)
    return [par(q) for q in voo], [par(q) for q in (hit or voo)]


# ------------------------------------------------------------------ itens
def desenhar_estrela(tamanho, cor=(70, 170, 255)):
    s = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)
    c = tamanho / 2.0
    pontos = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        r = c - 1 if i % 2 == 0 else (c - 1) * 0.45
        pontos.append((c + math.cos(ang) * r, c + math.sin(ang) * r))
    pygame.draw.polygon(s, (20, 40, 120), pontos)
    interno = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        r = (c - 3) if i % 2 == 0 else (c - 3) * 0.45
        interno.append((c + math.cos(ang) * r, c + math.sin(ang) * r))
    pygame.draw.polygon(s, cor, interno)
    pygame.draw.circle(s, (220, 245, 255), (int(c - 2), int(c - 3)), max(1, tamanho // 10))
    return s
