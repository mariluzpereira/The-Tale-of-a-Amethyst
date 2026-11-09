"""Carregamento de imagens com cache + utilitários de recorte/escala.

Tudo aqui é tolerante: se um arquivo não existir, a função devolve None
(ou lista vazia) e o resto do jogo usa um desenho de reserva.
"""
import os
import unicodedata
import pygame
from configuracoes import pasta_base, nomes_arquivo, arquivo_poder

_cache = {}


def achar(nome):
    """Procura o arquivo na pasta do jogo.

    Tenta o nome normal e as variações de acentuação (alguns zips trocam
    'ç' por '#U00e7', por exemplo)."""
    candidatos = [nome]
    candidatos.append("".join(c if ord(c) < 128 else "#U%04x" % ord(c) for c in nome))
    for forma in ("NFC", "NFD"):
        candidatos.append(unicodedata.normalize(forma, nome))
    for c in candidatos:
        caminho = os.path.join(pasta_base, c)
        if os.path.exists(caminho):
            return caminho
    return None


def imagem(nome):
    """Carrega uma imagem (com alpha) ou devolve None."""
    if nome in _cache:
        return _cache[nome]
    surf = None
    caminho = achar(nome)
    if caminho:
        try:
            surf = pygame.image.load(caminho).convert_alpha()
        except pygame.error:
            surf = None
    _cache[nome] = surf
    return surf


def imagem_opaca(nome):
    """Carrega uma imagem sem transparência (cenários .jpg)."""
    chave = ("opaca", nome)
    if chave in _cache:
        return _cache[chave]
    surf = None
    caminho = achar(nome)
    if caminho:
        try:
            surf = pygame.image.load(caminho).convert()
        except pygame.error:
            surf = None
    _cache[chave] = surf
    return surf


def carregar_quadros(padrao, quantidade, inicio=1):
    """padrao: 'safira_movimentacao_direita({})' -> carrega (1), (2), (3)..."""
    quadros = []
    for i in range(inicio, inicio + quantidade):
        im = imagem(padrao.format(i) + ".png")
        if im is not None:
            quadros.append(im)
    return quadros


def recortar(surf):
    r = surf.get_bounding_rect()
    if r.width == 0 or r.height == 0:
        return surf
    return surf.subsurface(r).copy()


def uniao_recorte(quadros):
    """Recorta todos os quadros pelo MESMO retângulo (união dos conteúdos),
    assim a animação não 'treme' entre um quadro e outro."""
    uniao = None
    for q in quadros:
        b = q.get_bounding_rect()
        if b.width == 0 or b.height == 0:
            continue
        uniao = b.copy() if uniao is None else uniao.union(b)
    if uniao is None:
        return list(quadros)
    return [q.subsurface(uniao).copy() for q in quadros]


def escalar_altura(surf, altura, suave=False):
    altura = max(1, int(altura))
    largura = max(1, int(round(surf.get_width() * altura / surf.get_height())))
    f = pygame.transform.smoothscale if suave else pygame.transform.scale
    return f(surf, (largura, altura))


def escalar_largura(surf, largura, suave=False):
    largura = max(1, int(largura))
    altura = max(1, int(round(surf.get_height() * largura / surf.get_width())))
    f = pygame.transform.smoothscale if suave else pygame.transform.scale
    return f(surf, (largura, altura))


def espelhar(surf):
    return pygame.transform.flip(surf, True, False)


# ------------------------------------------------------------------ princesas
def sprites_princesa(tipo):
    """Devolve um dicionário com todas as sprites da princesa (ou None)."""
    chave = ("princesa", tipo)
    if chave in _cache:
        return _cache[chave]

    nome = nomes_arquivo[tipo]
    pacote = {}

    andar_dir = carregar_quadros(nome + "_movimentacao_direita({})", 3)
    andar_esq = carregar_quadros(nome + "_movimentacao_esquerda({})", 3)
    if not andar_dir or not andar_esq:
        _cache[chave] = None
        return None

    pacote["andar_dir"] = [escalar_altura(q, 88) for q in uniao_recorte(andar_dir)]
    pacote["andar_esq"] = [escalar_altura(q, 88) for q in uniao_recorte(andar_esq)]

    # sapinho (transformação da poção)
    for lado in ("direita", "esquerda"):
        sufixo = "dir" if lado == "direita" else "esq"
        quadros = carregar_quadros(nome + "_sapo_" + lado + "({})", 3)
        pulo = imagem(nome + "_sapo_pulo_" + lado + ".png")
        todos = quadros + ([pulo] if pulo is not None else [])
        if todos:
            todos = [escalar_altura(q, 40) for q in uniao_recorte(todos)]
            pacote["sapo_" + sufixo] = todos[:len(quadros)] or todos
            pacote["sapo_pulo_" + sufixo] = todos[-1]
        morto = imagem(nome + "_sapo_morto_" + lado + ".png")
        if morto is not None:
            pacote["sapo_morto_" + sufixo] = escalar_altura(recortar(morto), 110)

    # ataque básico (projétil animado, aponta para a ESQUERDA no arquivo)
    poder = carregar_quadros(arquivo_poder[tipo] + "({})", 6)
    if poder:
        pacote["poder"] = [escalar_largura(q, 72) for q in uniao_recorte(poder)]

    _cache[chave] = pacote
    return pacote


def rosto(nome_personagem):
    """Retrato usado nos diálogos. Usa a versão leve em extras/ se existir."""
    chave = ("rosto", nome_personagem)
    if chave in _cache:
        return _cache[chave]
    nome = nomes_arquivo.get(nome_personagem, nome_personagem)
    im = imagem("extras/rosto_%s.png" % nome)
    if im is None:
        # reserva: arquivo original (muito grande: 7000x7000)
        grande = imagem("%s_sprite_dialogo(1).png" % nome)
        if grande is not None:
            im = escalar_altura(recortar(grande), 300, suave=True)
    _cache[chave] = im
    return im


def quadros_barra(prefixo, quantidade, fator):
    """Barras de coração/estrela: 10 estados, todos recortados do mesmo jeito."""
    chave = ("barra", prefixo)
    if chave in _cache:
        return _cache[chave]
    quadros = carregar_quadros(prefixo + "({})", quantidade)
    if quadros:
        quadros = [pygame.transform.scale(q, (q.get_width() * fator, q.get_height() * fator))
                   for q in uniao_recorte(quadros)]
    _cache[chave] = quadros
    return quadros
