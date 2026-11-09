"""As 5 fases do jogo.

Como editar: cada fase é um dicionário.
  plataformas: (x, y, largura)            -> plataformas suspensas
  inimigos:    ("Tipo", x, y, {extras})   -> y=None = em cima do chão
                  Planta/Bruxa: y = onde ficam os pés | Vespa/Boss: y = altura do centro
                  Bruxa aceita {"x_min":..,"x_max":..} (limites da caminhada)
  itens:       ("Maca"|"Estrela"|"Flor", x, y)   (x,y = centro do item)
Para passar de fase: matar TODOS os inimigos e sair pela direita.
"""
import pygame
from objetos import plataforma, item
from inimigos import criar_inimigo

CHAO_FLORESTA = 424
CHAO_BOSS = 458

FASES = {
    # ---------------------------------------------------------------- 1: plantas
    1: dict(
        largura=3200, chao_y=CHAO_FLORESTA, fundo="floresta", tinta=None,
        musica="combate.mp3", estilo_plataforma=1,
        plataformas=[(500, 330, 160), (900, 300, 200), (1350, 340, 150),
                     (1700, 290, 220), (2150, 330, 180), (2600, 300, 200)],
        inimigos=[("Planta", 700, None, {}), ("Planta", 1100, None, {}),
                  ("Planta", 1550, None, {}), ("Planta", 1810, 290, {}),
                  ("Planta", 1980, None, {}), ("Planta", 2400, None, {}),
                  ("Planta", 2850, None, {})],
        itens=[("Estrela", 580, 300), ("Maca", 1000, 270), ("Estrela", 1425, 310),
               ("Estrela", 2240, 300), ("Maca", 2700, 270), ("Estrela", 1300, 395),
               ("Flor", 380, 400), ("Flor", 950, 268), ("Flor", 1650, 400),
               ("Flor", 2250, 298), ("Flor", 3000, 400)],
    ),
    # ---------------------------------------------------------------- 2: bruxas
    2: dict(
        largura=3400, chao_y=CHAO_FLORESTA, fundo="floresta", tinta=(255, 140, 60, 38),
        musica="combate.mp3", estilo_plataforma=1,
        plataformas=[(600, 320, 160), (1200, 300, 180), (1800, 320, 160),
                     (2400, 290, 200), (3000, 320, 160)],
        inimigos=[("Bruxa", 1000, None, {"x_min": 800, "x_max": 1250}),
                  ("Bruxa", 1550, None, {"x_min": 1350, "x_max": 1900}),
                  ("Bruxa", 2050, None, {"x_min": 1850, "x_max": 2350}),
                  ("Bruxa", 2650, None, {"x_min": 2450, "x_max": 3000}),
                  ("Bruxa", 3100, None, {"x_min": 2900, "x_max": 3350})],
        itens=[("Estrela", 680, 290), ("Maca", 1290, 270), ("Estrela", 1880, 290),
               ("Maca", 2520, 260), ("Estrela", 3080, 290), ("Maca", 1580, 395),
               ("Flor", 420, 400), ("Flor", 1220, 268), ("Flor", 1900, 400),
               ("Flor", 2450, 258), ("Flor", 3300, 400)],
    ),
    # ---------------------------------------------------------------- 3: vespas
    3: dict(
        largura=3400, chao_y=CHAO_FLORESTA, fundo="floresta", tinta=(70, 200, 100, 34),
        musica="combate.mp3", estilo_plataforma=1,
        plataformas=[(400, 330, 160), (1000, 320, 160), (1600, 330, 160),
                     (2200, 320, 160), (2800, 330, 160)],
        inimigos=[("Vespa", 900, 250, {}), ("Vespa", 1250, 330, {}),
                  ("Vespa", 1600, 230, {}), ("Vespa", 1950, 300, {}),
                  ("Vespa", 2250, 240, {}), ("Vespa", 2550, 320, {}),
                  ("Vespa", 2850, 230, {}), ("Vespa", 3150, 300, {})],
        itens=[("Maca", 480, 300), ("Estrela", 1080, 290), ("Maca", 1680, 300),
               ("Estrela", 2280, 290), ("Maca", 2880, 300), ("Estrela", 700, 395),
               ("Estrela", 1400, 395), ("Estrela", 2500, 395),
               ("Flor", 300, 400), ("Flor", 1500, 400), ("Flor", 2000, 400),
               ("Flor", 2650, 400), ("Flor", 3250, 400)],
    ),
    # ---------------------------------------------------------------- 4: os três juntos
    4: dict(
        largura=3600, chao_y=CHAO_FLORESTA, fundo="floresta", tinta=(80, 30, 120, 75),
        musica="combate.mp3", estilo_plataforma=1,
        plataformas=[(450, 330, 160), (950, 300, 180), (1500, 330, 160),
                     (2000, 300, 200), (2600, 330, 160), (3100, 300, 180)],
        inimigos=[("Planta", 800, None, {}), ("Planta", 1700, None, {}),
                  ("Planta", 2400, None, {}), ("Planta", 3250, None, {}),
                  ("Bruxa", 1200, None, {"x_min": 1000, "x_max": 1500}),
                  ("Bruxa", 2100, None, {"x_min": 1900, "x_max": 2350}),
                  ("Bruxa", 2900, None, {"x_min": 2700, "x_max": 3300}),
                  ("Vespa", 1400, 260, {}), ("Vespa", 2200, 240, {}),
                  ("Vespa", 2900, 260, {}), ("Vespa", 3350, 300, {})],
        itens=[("Maca", 530, 300), ("Estrela", 1040, 270), ("Maca", 1580, 300),
               ("Estrela", 2100, 270), ("Maca", 2680, 300), ("Estrela", 3190, 270),
               ("Estrela", 700, 395), ("Estrela", 1900, 395), ("Estrela", 2800, 395),
               ("Flor", 350, 400), ("Flor", 990, 270), ("Flor", 1850, 400),
               ("Flor", 2650, 300), ("Flor", 3450, 400)],
    ),
    # ---------------------------------------------------------------- 5: boss
    5: dict(
        largura=1024, chao_y=CHAO_BOSS, fundo="boss", tinta=None,
        musica="boss.mp3", estilo_plataforma=2,
        plataformas=[(150, 345, 170), (704, 345, 170), (432, 265, 160)],
        inimigos=[("Boss", 700, 255, {})],
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
    return d
