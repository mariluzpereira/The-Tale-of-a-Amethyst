"""Sprites dos inimigos.

Usa os PNGs do projeto quando existem (senão entra um desenho feito por código):
  Bruxa:  bruxa_sprite_voando(1).png / bruxa_sprite_atingida(1).png / bruxa_sprite_morta(1).png
  Planta: planta_mordida_01..04.png / planta_derrotada.png
  Boss:   parado.png, andando(0..4).png, apontando_01..03.png, atacando_01..04.png,
          atacando_04_sem_fogo.png, dano_01..04.png, derrotado_01..04.png
  Vespa:  vespa_sprite_voando(1..5).png / vespa_sprite_atingida(1..4).png

Cada quadro é um 'Quadro' (imagem + ponto de ancoragem) e vem em PAR:
(virado p/ direita, virado p/ esquerda).
"""
import math
import pygame
import recursos as rec

_memo = {}


def _memoizar(nome, fabrica):
    if nome not in _memo:
        _memo[nome] = fabrica()
    return _memo[nome]


def _par_de(quadro, olha_para="direita"):
    """Devolve (virado p/ direita, virado p/ esquerda) a partir do original."""
    if olha_para == "direita":
        return quadro, quadro.espelhado()
    return quadro.espelhado(), quadro


def _ampliar(surf, fator):
    return pygame.transform.scale(surf, (surf.get_width() * fator, surf.get_height() * fator))


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
    """dict: voando [..], atingida [..], morta -> cada quadro é um par (dir, esq).
    As sprites da bruxa (na vassoura) olham para a ESQUERDA nos arquivos."""
    return _memoizar("bruxa", _fabricar_bruxa)


def _fabricar_bruxa():
    voo = rec.carregar_quadros("bruxa_sprite_voando({})", 5)
    hit = rec.carregar_quadros("bruxa_sprite_atingida({})", 3)
    morta = rec.imagem("bruxa_sprite_morta(1).png")
    if voo:
        base = rec._caixa_visivel(voo[0]).width
        fator = 100.0 / max(1, base)                  # ~100 px de largura na tela
        qs = rec.quadros_alinhados(voo + hit, fator, "centro")
        voo_q, hit_q = qs[:len(voo)], (qs[len(voo):] or qs[:len(voo)])
        if morta is not None:
            morta_q = rec.quadros_alinhados([morta], fator, "pes")[0]
        else:
            morta_q = hit_q[0]
        return {"voando": [_par_de(q, "esquerda") for q in voo_q],
                "atingida": [_par_de(q, "esquerda") for q in hit_q],
                "morta": _par_de(morta_q, "esquerda")}
    # reserva: bruxa desenhada por código
    normal = _par_de(rec.quadro_de_superficie(_bruxa_base(0, False), "centro"), "direita")
    lancando = _par_de(rec.quadro_de_superficie(_bruxa_base(0, True), "centro"), "direita")
    return {"voando": [normal], "atingida": [lancando], "morta": normal}


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
    """dict: idle, preparando, mordendo, voltando, derrotada -> par (dir, esq).
    Nos arquivos a planta olha para a DIREITA."""
    return _memoizar("planta", _fabricar_planta)


def _fabricar_planta():
    nomes = ["planta_mordida_01.png", "planta_mordida_02.png", "planta_mordida_03.png",
             "planta_mordida_04.png", "planta_derrotada.png"]
    imgs = [rec.imagem(n) for n in nomes]
    if all(im is not None for im in imgs):
        fator = 100.0 / 242.0                          # o quadro mais alto fica com ~100 px
        pares = [_par_de(rec.quadros_alinhados([im], fator, "pes")[0], "direita") for im in imgs]
        return {"idle": pares[0], "preparando": pares[1], "mordendo": pares[2],
                "voltando": pares[3], "derrotada": pares[4]}
    # reserva: planta desenhada por código
    fechada = _par_de(rec.quadro_de_superficie(_planta_base(False), "pes"), "direita")
    aberta = _par_de(rec.quadro_de_superficie(_planta_base(True), "pes"), "direita")
    return {"idle": fechada, "preparando": aberta, "mordendo": aberta,
            "voltando": fechada, "derrotada": fechada}


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
    """dict de animações do Rei das Fadas Corrompido (olha para a DIREITA):
    parado, andando[5], apontando[3], atacando[4], sem_fogo, dano[4], derrotado[4]."""
    return _memoizar("boss", _fabricar_boss)


def _fabricar_boss():
    parado = rec.imagem("parado.png")
    andando = rec.carregar_quadros("andando({})", 5, inicio=0)
    apontando = [rec.imagem("apontando_%02d.png" % i) for i in (1, 2, 3)]
    atacando = [rec.imagem("atacando_%02d.png" % i) for i in (1, 2, 3, 4)]
    sem_fogo = rec.imagem("atacando_04_sem_fogo.png")
    dano = [rec.imagem("dano_%02d.png" % i) for i in (1, 2, 3, 4)]
    derrotado = [rec.imagem("derrotado_%02d.png" % i) for i in (1, 2, 3, 4)]
    completo = (parado is not None and len(andando) == 5
                and all(i is not None for i in apontando + atacando + dano + derrotado))
    if completo:
        ref = rec._caixa_visivel(parado)
        fator = 150.0 / ref.height                    # corpo com ~150 px de altura
        k_base = ref.width * fator * 0.5              # centro do corpo a partir da borda esquerda

        def q(im, f=fator):
            return _par_de(rec.quadros_alinhados([im], f, "pes", True, k_base)[0], "direita")

        # o quadro 'sem fogo' vem em resolução maior: iguala a altura do corpo
        if sem_fogo is not None:
            f_sf = fator * ref.height / float(rec._caixa_visivel(sem_fogo).height)
            q_sf = q(sem_fogo, f_sf)
        else:
            q_sf = q(atacando[3])
        return {"parado": q(parado), "andando": [q(i) for i in andando],
                "apontando": [q(i) for i in apontando], "atacando": [q(i) for i in atacando],
                "sem_fogo": q_sf, "dano": [q(i) for i in dano], "derrotado": [q(i) for i in derrotado]}
    # reserva: rei desenhado por código (usa o mesmo quadro em tudo)
    frames = [_par_de(rec.quadro_de_superficie(_boss_base(a), "pes"), "direita") for a in (True, False)]
    return {"parado": frames[0], "andando": frames, "apontando": frames[:1] * 3, "atacando": frames[:1] * 4,
            "sem_fogo": frames[0], "dano": frames[:1] * 4, "derrotado": frames[1:] * 4}


# ------------------------------------------------------------------ vespa (usa os PNGs existentes)
def quadros_vespa():
    """(voando[..], atingida[..]) -> cada quadro um par (dir, esq).
    As imagens originais da vespa olham para a ESQUERDA."""
    return _memoizar("vespa", _fabricar_vespa)


def _fabricar_vespa():
    voo = rec.carregar_quadros("vespa_sprite_voando({})", 5)
    hit = rec.carregar_quadros("vespa_sprite_atingida({})", 4)
    todos = voo + hit
    if todos:
        caixas = [rec._caixa_visivel(t) for t in todos]
        uniao = caixas[0].copy()
        for c in caixas[1:]:
            uniao = uniao.union(c)
        fator = 76.0 / max(1, uniao.width)
        qs = rec.quadros_alinhados(todos, fator, "centro")
        voo_q, hit_q = qs[:len(voo)], qs[len(voo):]
        if not voo_q:
            voo_q = hit_q
        if not hit_q:
            hit_q = voo_q
    else:
        s = pygame.Surface((60, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (240, 190, 20), (14, 10, 36, 20))
        for x in (24, 32, 40):
            pygame.draw.rect(s, (30, 20, 10), (x, 11, 4, 18))
        pygame.draw.ellipse(s, (255, 255, 255, 170), (22, 0, 20, 12))
        voo_q = hit_q = [rec.quadro_de_superficie(s, "centro")]
    return [_par_de(q, "esquerda") for q in voo_q], [_par_de(q, "esquerda") for q in hit_q]


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
