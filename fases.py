"""As 5 fases do jogo.

Como editar: cada fase é um dicionário.
  plataformas: (x, y, largura)            -> plataformas suspensas (y = topo)
  inimigos:    ("Tipo", x, y, {extras})
                  Planta / Boss: y = onde ficam os pés (None = em cima do chão)
                  Bruxa: y = chão de referência (ela paira ~80 px acima, de vassoura)
                  Vespa: y = altura do centro
                  Bruxa aceita {"x_min":..,"x_max":..} (limites por onde ela voa)
  itens:       ("Maca"|"Estrela"|"Flor", x, y)   (x,y = centro do item)
  npcs:        ("Fada", x, y)   -> a Fadinha: aperte a tecla de interagir perto dela
Para passar de fase: matar TODOS os inimigos e sair pela direita.

TORRES: para deixar os itens difíceis, eles ficam no alto de "torres" de 3
plataformas em degraus (o pulo alcança ~150 px, então cada degrau sobe ~95 px).
A função _torre(x) cria as 3 plataformas e devolve pontos prontos:
   t1/t2/t3 = onde colocar um item em cada degrau
   p1/p2/p3 = onde colocar os pés de um inimigo em cada degrau
"""
import pygame
from objetos import plataforma, item, fada
from inimigos import criar_inimigo

CHAO_FLORESTA = 424
CHAO_BOSS = 458


def _torre(x, w1=170, y1=325):
    p1 = (x, y1, w1)
    p2 = (x + w1 - 30, y1 - 95, 120)
    p3 = (x + w1 + 110, y1 - 185, 100)
    pontos = {
        "t1": (x + w1 // 2, y1 - 30), "t2": (p2[0] + 60, p2[1] - 30), "t3": (p3[0] + 50, p3[1] - 30),
        "p1": (x + w1 // 2, y1), "p2": (p2[0] + 60, p2[1]), "p3": (p3[0] + 50, p3[1]),
    }
    return [p1, p2, p3], pontos


def _torres(xs):
    plataformas, pontos = [], []
    for x in xs:
        p, pt = _torre(x)
        plataformas += p
        pontos.append(pt)
    return plataformas, pontos


# ------------------------------------------------------------------ fase 1: plantas
_pl1, _t1 = _torres([420, 880, 1340, 1800, 2260, 2720])
# ------------------------------------------------------------------ fase 2: bruxas
_pl2, _t2 = _torres([450, 900, 1400, 1900, 2400, 2900])
# ------------------------------------------------------------------ fase 3: vespas
_pl3, _t3 = _torres([450, 950, 1450, 1950, 2450, 2950])
# ------------------------------------------------------------------ fase 4: os três juntos
_pl4, _t4 = _torres([380, 860, 1340, 1820, 2300, 2780])

FASES = {
    1: dict(
        npcs=[("Fada", 300, 330)],
        largura=3200, chao_y=CHAO_FLORESTA, fundo="floresta", tinta=None,
        musica="combate.mp3", estilo_plataforma=1,
        plataformas=_pl1,
        inimigos=[("Planta", x, None, {}) for x in (650, 1000, 1250, 1560, 1980, 2200, 2550, 2950)]
                 + [("Planta",) + _t1[2]["p2"] + ({},), ("Planta",) + _t1[4]["p2"] + ({},)],
        itens=[("Flor",) + _t1[i]["t3"] for i in range(5)]
              + [("Estrela",) + _t1[1]["t2"], ("Estrela",) + _t1[5]["t2"], ("Maca",) + _t1[5]["t3"]],
    ),
    2: dict(
        largura=3400, chao_y=CHAO_FLORESTA, fundo="floresta", tinta=(255, 140, 60, 38),
        musica="combate.mp3", estilo_plataforma=1,
        plataformas=_pl2,
        inimigos=[("Bruxa", 900, None, {"x_min": 700, "x_max": 1250}),
                  ("Bruxa", 1100, None, {"x_min": 800, "x_max": 1500}),
                  ("Bruxa", 1500, None, {"x_min": 1250, "x_max": 1800}),
                  ("Bruxa", 2000, None, {"x_min": 1750, "x_max": 2300}),
                  ("Bruxa", 2500, None, {"x_min": 2250, "x_max": 2800}),
                  ("Bruxa", 2950, None, {"x_min": 2650, "x_max": 3350})],
        itens=[("Flor",) + _t2[i]["t3"] for i in range(5)]
              + [("Estrela",) + _t2[2]["t2"], ("Estrela",) + _t2[4]["t2"], ("Maca",) + _t2[5]["t3"]],
    ),
    3: dict(
        largura=3400, chao_y=CHAO_FLORESTA, fundo="floresta", tinta=(70, 200, 100, 34),
        musica="combate.mp3", estilo_plataforma=1,
        plataformas=_pl3,
        inimigos=[("Vespa", x, y, {}) for (x, y) in
                  ((800, 260), (1050, 330), (1300, 220), (1550, 300), (1800, 240), (2050, 330),
                   (2300, 230), (2550, 300), (2800, 250), (3050, 330), (3250, 260))],
        itens=[("Flor",) + _t3[i]["t3"] for i in range(5)]
              + [("Estrela",) + _t3[1]["t2"], ("Estrela",) + _t3[3]["t2"], ("Estrela",) + _t3[5]["t2"],
                 ("Maca",) + _t3[5]["t3"]],
    ),
    4: dict(
        largura=3600, chao_y=CHAO_FLORESTA, fundo="floresta", tinta=(80, 30, 120, 75),
        musica="combate.mp3", estilo_plataforma=1,
        plataformas=_pl4,
        inimigos=[("Planta", x, None, {}) for x in (800, 1500, 1950, 2250, 3000, 3350)]
                 + [("Bruxa", 1200, None, {"x_min": 1000, "x_max": 1550}),
                    ("Bruxa", 1600, None, {"x_min": 1400, "x_max": 2000}),
                    ("Bruxa", 2000, None, {"x_min": 1800, "x_max": 2400}),
                    ("Bruxa", 2800, None, {"x_min": 2600, "x_max": 3300})]
                 + [("Vespa", x, y, {}) for (x, y) in
                    ((1000, 300), (1400, 260), (2200, 240), (2600, 320), (2900, 260), (3350, 300))],
        itens=[("Flor",) + _t4[i]["t3"] for i in range(5)]
              + [("Estrela",) + _t4[1]["t2"], ("Estrela",) + _t4[3]["t2"], ("Estrela",) + _t4[5]["t2"],
                 ("Maca",) + _t4[2]["t2"], ("Maca",) + _t4[5]["t3"]],
    ),
    5: dict(
        largura=1024, chao_y=CHAO_BOSS, fundo="boss", tinta=None,
        musica="boss.mp3", estilo_plataforma=2,
        plataformas=[(150, 345, 170), (704, 345, 170), (432, 265, 160)],
        inimigos=[("Boss", 760, None, {})],
        itens=[],
    ),
}


def construir_fase(mundo, numero):
    """Preenche o 'mundo' com a fase e devolve o dicionário de dados."""
    d = FASES[numero]
    mundo.largura = d["largura"]
    mundo.chao_y = d["chao_y"]
    mundo.limite_direito = d["largura"]
    mundo.fase_limpa = False

    # chão sólido (invisível: o cenário já desenha o chão); se estende além
    # da borda direita para a princesa poder sair andando
    mundo.plataformas.add(plataforma(-200, d["chao_y"], d["largura"] + 700, 400, eh_chao=True))
    for (x, y, w) in d["plataformas"]:
        mundo.plataformas.add(plataforma(x, y, w, 14, estilo=d["estilo_plataforma"]))

    for (tipo, x, y, extras) in d["inimigos"]:
        if y is None:
            y = d["chao_y"]
        mundo.inimigos.add(criar_inimigo(tipo, x, y, **extras))

    for (tipo, x, y) in d["itens"]:
        mundo.itens.add(item(x, y, tipo))

    for (tipo, x, y) in d.get("npcs", []):
        mundo.npcs.add(fada(x, y))
    return d
