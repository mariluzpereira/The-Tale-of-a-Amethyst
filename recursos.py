"""Carregamento de imagens com cache + utilitários de recorte/escala.

Tudo aqui é tolerante: se um arquivo não existir, a função devolve None
(ou lista vazia) e o resto do jogo usa um desenho de reserva.
"""
import os
import re
import unicodedata
import pygame
from configuracoes import pasta_base, nomes_arquivo, arquivo_poder

_cache = {}
_indice = None
erros_carga = []          # (arquivo, mensagem) das imagens que existem mas não abriram


def _normalizar(nome):
    return unicodedata.normalize("NFC", nome).casefold()


def _montar_indice():
    """Mapeia nome-do-arquivo -> caminho para tudo dentro da pasta do jogo
    (inclui subpastas, até 4 níveis). Assim as sprites são achadas mesmo que
    estejam numa subpasta (assets/, imagens/...) ou com maiúscula diferente."""
    global _indice
    _indice = {}
    for pasta, subpastas, arquivos in os.walk(pasta_base):
        rel = os.path.relpath(pasta, pasta_base)
        nivel = 0 if rel == "." else rel.count(os.sep) + 1
        subpastas[:] = [d for d in subpastas if not d.startswith(".") and d != "__pycache__" and nivel < 4]
        for a in arquivos:
            caminho = os.path.join(pasta, a)
            _indice.setdefault(_normalizar(a), caminho)
            # nomes que o zip trocou: 'po#U00e7#U00e3o.png' -> 'poção.png'
            destrocado = re.sub(r"#U([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), a)
            _indice.setdefault(_normalizar(destrocado), caminho)


def achar(nome):
    """Procura o arquivo na pasta do jogo (e subpastas).

    Tenta o caminho exato e variações de acentuação; se não achar, procura o
    mesmo nome de arquivo em qualquer subpasta."""
    candidatos = [nome]
    candidatos.append("".join(c if ord(c) < 128 else "#U%04x" % ord(c) for c in nome))
    for forma in ("NFC", "NFD"):
        candidatos.append(unicodedata.normalize(forma, nome))
    for c in candidatos:
        caminho = os.path.join(pasta_base, c)
        if os.path.exists(caminho):
            return caminho
    if _indice is None:
        _montar_indice()
    return _indice.get(_normalizar(os.path.basename(nome)))


def imagem(nome):
    """Carrega uma imagem (com alpha) ou devolve None."""
    if nome in _cache:
        return _cache[nome]
    surf = None
    caminho = achar(nome)
    if caminho:
        try:
            surf = pygame.image.load(caminho).convert_alpha()
        except (pygame.error, MemoryError) as e:
            erros_carga.append((nome, str(e)))
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
        except (pygame.error, MemoryError) as e:
            erros_carga.append((nome, str(e)))
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


def recortar_visivel(surf, min_alpha=100):
    """Como recortar(), mas ignora pixels quase transparentes ('poeira')."""
    r = surf.get_bounding_rect(min_alpha)
    if r.width == 0 or r.height == 0:
        return surf
    return surf.subsurface(r).copy()


def _centro_de_massa_x(img):
    """x do centro do corpo (a nuvem de poeira do pulo puxaria o centro da caixa)."""
    try:
        return float(pygame.mask.from_surface(img, 100).centroid()[0])
    except Exception:
        return img.get_width() / 2.0


correcoes_orientacao = []        # sprites que estavam viradas para o lado errado e foram espelhadas


def _olha_para_direita(surf):
    """Para onde a sprite olha? Usa os OLHOS (pixels brancos): se estão à direita do centro do
    corpo, olha para a direita. Devolve None se não der para saber."""
    try:
        brancos = pygame.mask.from_threshold(surf, (255, 255, 255, 255), (30, 30, 30, 100))
        if brancos.count() == 0:
            return None
        caixa = surf.get_bounding_rect(100)
        return brancos.centroid()[0] > caixa.x + caixa.width / 2.0
    except Exception:
        return None


def _orientar(surf, deve_olhar_direita, nome):
    """Espelha a sprite se ela olhar para o lado contrário ao que o nome do arquivo diz."""
    atual = _olha_para_direita(surf)
    if atual is not None and atual != deve_olhar_direita:
        correcoes_orientacao.append(nome)
        return espelhar(surf)
    return surf


def imagem_alternativas(*nomes):
    """Primeira imagem que existir (ex.: 'fadinha (2).png' e depois 'fadinha.png')."""
    for n in nomes:
        im = imagem(n)
        if im is not None:
            return im
    return None


def _quadros_de_caminhada(quadros, altura_alvo=88):
    """Devolve (quadros prontos, fator de escala usado)."""
    alturas = [max(1, q.get_bounding_rect(100).height) for q in quadros]
    mediana = sorted(alturas)[len(alturas) // 2]
    fora_de_escala = any(abs(h / float(mediana) - 1.0) > 0.3 for h in alturas)
    if not fora_de_escala:
        recortados = uniao_recorte(quadros)
        fator = altura_alvo / float(recortados[0].get_height())
        return [escalar_altura(q, altura_alvo) for q in recortados], fator
    fator = altura_alvo / float(mediana)
    prontos = []
    for q, h in zip(quadros, alturas):
        c = recortar_visivel(q)
        f = fator if abs(h / float(mediana) - 1.0) <= 0.3 else altura_alvo / float(h)
        prontos.append(pygame.transform.scale(c, (max(1, int(c.get_width() * f)), max(1, int(c.get_height() * f)))))
    return prontos, fator


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

    # caminhada. Se algum quadro foi desenhado numa escala bem diferente dos outros
    # (acontece quando o PNG é exportado maior), cada quadro é recortado e ajustado
    # sozinho; senão usa-se o recorte comum, que mantém o balanço natural da animação.
    pacote["andar_dir"], fator = _quadros_de_caminhada(andar_dir)
    pacote["andar_esq"], _ = _quadros_de_caminhada(andar_esq)

    # pulo (um quadro por princesa; o desenho olha para a DIREITA)
    pulo = imagem(nome + "_pulo.png")
    if pulo is not None:
        recorte = recortar_visivel(pulo)
        img = pygame.transform.scale(recorte, (max(1, int(recorte.get_width() * fator)),
                                               max(1, int(recorte.get_height() * fator))))
        limite = int(88 * 1.25)           # alguns desenhos de pulo vêm bem mais altos (braços/cabelo/poeira)
        if img.get_height() > limite:
            img = pygame.transform.scale(img, (max(1, int(img.get_width() * limite / img.get_height())), limite))
        ax = _centro_de_massa_x(img)
        pacote["pulo_dir"] = (img, ax)
        pacote["pulo_esq"] = (espelhar(img), img.get_width() - ax)

    # sapinho (transformação da poção). Cada sprite é conferida: se estiver virada para o lado
    # contrário ao do nome do arquivo (acontece quando a arte sai espelhada), o jogo espelha sozinho.
    for lado in ("direita", "esquerda"):
        sufixo = "dir" if lado == "direita" else "esq"
        olha_dir = lado == "direita"
        quadros = []
        for i in (1, 2, 3):
            nome_arq = "%s_sapo_%s(%d).png" % (nome, lado, i)
            im = imagem(nome_arq)
            if im is not None:
                quadros.append(_orientar(im, olha_dir, nome_arq))
        nome_pulo = "%s_sapo_pulo_%s.png" % (nome, lado)
        pulo_img = imagem(nome_pulo)
        pulo = _orientar(pulo_img, olha_dir, nome_pulo) if pulo_img is not None else None
        todos = quadros + ([pulo] if pulo is not None else [])
        if todos:
            todos = [escalar_altura(q, 40) for q in uniao_recorte(todos)]
            pacote["sapo_" + sufixo] = todos[:len(quadros)] or todos
            pacote["sapo_pulo_" + sufixo] = todos[-1]
        morto = imagem(nome + "_sapo_morto_" + lado + ".png")
        if morto is not None:
            pacote["sapo_morto_" + sufixo] = escalar_altura(recortar(morto), 110)

    # princesa atingida (um quadro por lado, com as exclamações): todas ajustadas para a mesma altura
    for lado in ("direita", "esquerda"):
        sufixo = "dir" if lado == "direita" else "esq"
        im = imagem("%s_atingida_%s(1).png" % (nome, lado))
        if im is not None:
            c = recortar_visivel(im)
            img = pygame.transform.scale(c, (max(1, int(c.get_width() * 92.0 / c.get_height())), 92))
            pacote["atingida_" + sufixo] = (img, _centro_de_massa_x(img))

    # princesa derrotada (deitada): versão pequena para o jogo e grande para a tela de Game Over
    der = imagem(nome + "_derrotada(1).png")
    if der is not None:
        c = recortar_visivel(der)
        pacote["derrotada"] = escalar_largura(c, 150)
        pacote["derrotada_grande"] = escalar_largura(c, 420)

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
        # reserva: arquivo original (muito grande: 7000x7000). Gera uma versão
        # leve e guarda em extras/ para as próximas vezes serem instantâneas.
        grande = imagem("%s_sprite_dialogo(1).png" % nome) or imagem("%s_sprite_diálogo(1).png" % nome)
        if grande is not None:
            im = escalar_altura(recortar(grande), 300, suave=True)
            _salvar_extra("extras/rosto_%s.png" % nome, im)
            _cache.pop(("img", grande), None)
    _cache[chave] = im
    return im


def _salvar_extra(nome, surf):
    try:
        caminho = os.path.join(pasta_base, nome)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        pygame.image.save(surf, caminho)
    except (pygame.error, OSError):
        pass


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


# ------------------------------------------------------------------ quadros ancorados
class Quadro:
    """Imagem + ponto de ancoragem (ax, ay) dentro dela.

    ancora='pes'    -> (ax, ay) é o ponto dos pés: vai para o meio-base da hitbox
    ancora='centro' -> (ax, ay) é o centro do corpo: vai para o centro da hitbox

    Assim cada quadro de uma animação fica no lugar certo mesmo quando as
    imagens têm tamanhos de tela diferentes (braço esticado, golpe, etc.)."""

    __slots__ = ("img", "ax", "ay", "ancora")

    def __init__(self, img, ax, ay, ancora="pes"):
        self.img = img
        self.ax = ax
        self.ay = ay
        self.ancora = ancora

    def espelhado(self):
        return Quadro(pygame.transform.flip(self.img, True, False),
                      self.img.get_width() - self.ax, self.ay, self.ancora)

    def posicao(self, rect, cam_x=0):
        """Canto superior esquerdo para desenhar este quadro sobre a hitbox."""
        y_mundo = rect.bottom if self.ancora == "pes" else rect.centery
        return (int(rect.centerx - cam_x - self.ax), int(y_mundo - self.ay))


def _caixa_visivel(surf, min_alpha=100):
    """Retângulo do conteúdo visível, ignorando 'poeira' quase transparente."""
    caixa = surf.get_bounding_rect(min_alpha)
    if caixa.width == 0 or caixa.height == 0:
        caixa = surf.get_rect()
    return caixa


def quadros_alinhados(superficies, fator, ancora="pes", suave=True, k_x=None, min_alpha=100):
    """Cria Quadros que compartilham o MESMO ponto de ancoragem (união dos
    conteúdos), para a animação não tremer. Se k_x for dado, o x da âncora é
    'borda esquerda do conteúdo + k_x' em cada quadro (corpo fixo, braço livre)."""
    caixas = [_caixa_visivel(s, min_alpha) for s in superficies]
    uniao = caixas[0].copy()
    for c in caixas[1:]:
        uniao = uniao.union(c)
    f = pygame.transform.smoothscale if suave else pygame.transform.scale
    resultado = []
    for surf, caixa in zip(superficies, caixas):
        w = max(1, int(round(surf.get_width() * fator)))
        h = max(1, int(round(surf.get_height() * fator)))
        img = f(surf, (w, h))
        if k_x is not None:
            ax = caixa.x * fator + k_x
        else:
            ax = (uniao.x + uniao.width / 2.0) * fator
        if ancora == "centro":
            ay = (uniao.y + uniao.height / 2.0) * fator
        else:
            ay = (uniao.y + uniao.height) * fator
        resultado.append(Quadro(img, min(ax, w), min(ay, h), ancora))
    return resultado


def quadro_de_superficie(surf, ancora="pes"):
    """Quadro simples para desenhos prontos (sem escala)."""
    if ancora == "centro":
        return Quadro(surf, surf.get_width() / 2.0, surf.get_height() / 2.0, "centro")
    return Quadro(surf, surf.get_width() / 2.0, surf.get_height() - 2, "pes")


# ------------------------------------------------------------------ diagnóstico
def _lista_essencial():
    imagens = ["menu.png", "jogar.png", "opcoes.png", "creditos.png",
               "maca.png", "Flor.png", "poção.png", "plataforma(1).png", "Plataforma (2).png",
               "Escudo (2).png", "dialogo.png",
               "flor_rosa_selecao.png", "flor_vermelha_selecao.png",
               "flor_azul_selecao.png", "flor_roxa_selecao.png", "sair.png",
               "bruxa_sprite_voando(1).png", "bruxa_sprite_atingida(1).png", "bruxa_sprite_morta(1).png",
               "planta_derrotada.png", "parado.png", "atacando_04_sem_fogo.png"]
    imagens += ["coracoes_sprites(%d).png" % i for i in range(1, 11)]
    imagens += ["estrelas_sprites(%d).png" % i for i in range(1, 11)]
    imagens += ["vespa_sprite_voando(%d).png" % i for i in range(1, 6)]
    imagens += ["vespa_sprite_atingida(%d).png" % i for i in range(1, 5)]
    imagens += ["planta_mordida_%02d.png" % i for i in range(1, 5)]
    imagens += ["andando(%d).png" % i for i in range(5)]
    imagens += ["%s_%02d.png" % (p, i) for p, n in (("apontando", 3), ("atacando", 4), ("dano", 4), ("derrotado", 4))
                for i in range(1, n + 1)]
    for tipo, nome in nomes_arquivo.items():
        imagens += ["%s_movimentacao_%s(%d).png" % (nome, lado, i) for lado in ("direita", "esquerda") for i in (1, 2, 3)]
        imagens += ["%s_sapo_%s(%d).png" % (nome, lado, i) for lado in ("direita", "esquerda") for i in (1, 2, 3)]
        imagens += ["%s_sapo_pulo_%s.png" % (nome, lado) for lado in ("direita", "esquerda")]
        imagens.append("%s_pulo.png" % nome)
        imagens += ["%s_atingida_%s(1).png" % (nome, lado) for lado in ("direita", "esquerda")]
        imagens.append("%s_derrotada(1).png" % nome)
        imagens += ["%s_sapo_morto_%s.png" % (nome, lado) for lado in ("direita", "esquerda")]
        imagens += ["%s(%d).png" % (arquivo_poder[tipo], i) for i in range(1, 7)]
    opacas = ["casa_fada.jpg", "cenário_caminho_floresta.jpg", "cenario_boss.jpg"]
    audio = ["menu.mp3", "selecao_personagem.mp3", "prologo.ogg", "combate.mp3", "boss.mp3",
             "vitoria.wav", "derrota.mp3", "creditos.mp3", "easter_egg_musica.mp3"]
    return imagens, opacas, audio


def verificar_recursos():
    """Confere (e já carrega) tudo que o jogo usa. Devolve um dicionário com o
    que faltou e grava o relatório 'diagnostico_recursos.txt'."""
    imagens, opacas, audio = _lista_essencial()
    faltam_img = [n for n in imagens if imagem(n) is None]
    faltam_img += [n for n in opacas if imagem_opaca(n) is None]
    faltam_audio = [n for n in audio if achar(n) is None]
    if imagem_alternativas("fadinha (2).png", "fadinha.png") is None:
        faltam_img.append("fadinha (2).png")
    if imagem_opaca("cenario_prologo.jpg") is None:
        # opcional: sem ele o prólogo usa o cenário da casa da fada
        print("[recursos] aviso: cenario_prologo.jpg não encontrado - o prólogo usará a casa da fada como fundo")
    # retratos dos diálogos: serve a versão leve (extras/) ou a original grande
    faltam_rostos = []
    for nome in list(nomes_arquivo.values()) + ["bruxa", "fadinha"]:
        if not (achar("extras/rosto_%s.png" % nome) or achar("%s_sprite_dialogo(1).png" % nome)
                or achar("%s_sprite_diálogo(1).png" % nome)):
            faltam_rostos.append(nome)
    resultado = {"imagens": faltam_img, "audio": faltam_audio, "rostos": faltam_rostos,
                 "erros": list(erros_carga)}
    try:
        extendido = pygame.image.get_extended()
    except Exception:
        extendido = "?"
    linhas = ["RELATÓRIO DE RECURSOS DO JOGO", "",
              "Pasta onde o jogo procura os arquivos:", "  " + pasta_base, "",
              "pygame: %s | suporte a PNG/JPG (SDL_image): %s" % (getattr(pygame, "version", None) and pygame.version.ver, extendido),
              ""]
    for titulo, lista in (("IMAGENS NÃO ENCONTRADAS", faltam_img), ("RETRATOS (diálogos) SEM ARQUIVO", faltam_rostos),
                          ("MÚSICAS NÃO ENCONTRADAS", faltam_audio)):
        linhas.append("%s: %d" % (titulo, len(lista)))
        linhas += ["  - " + n for n in lista]
        linhas.append("")
    linhas.append("SPRITES ESPELHADAS AUTOMATICAMENTE (olhavam para o lado errado): %d" % len(correcoes_orientacao))
    linhas += ["  - " + n for n in correcoes_orientacao]
    linhas.append("")
    linhas.append("IMAGENS QUE EXISTEM MAS NÃO ABRIRAM: %d" % len(erros_carga))
    linhas += ["  - %s -> %s" % (n, e) for n, e in erros_carga]
    texto = "\n".join(linhas) + "\n"
    try:
        with open(os.path.join(pasta_base, "diagnostico_recursos.txt"), "w", encoding="utf-8") as f:
            f.write(texto)
    except OSError:
        pass
    problemas = len(set(faltam_img) | set(n for n, _ in erros_carga)) + len(faltam_rostos)
    if problemas or faltam_audio:
        print(texto)
    else:
        print("[recursos] tudo certo: todas as imagens e músicas foram encontradas em", pasta_base)
    resultado["problemas"] = problemas
    return resultado


_cache_escala = {}


def escalado(surf, altura, suave=True, largura_max=None):
    """Versão da imagem com a altura pedida, guardada em cache (use em telas
    que redesenham todo frame: escalar a cada frame deixa o jogo pesado)."""
    chave = (id(surf), int(altura), suave, largura_max)
    if chave not in _cache_escala:
        img = escalar_altura(surf, altura, suave)
        if largura_max and img.get_width() > largura_max:
            img = escalar_largura(img, largura_max, suave)
        _cache_escala[chave] = (surf, img)       # guarda surf para o id() não ser reaproveitado
    return _cache_escala[chave][1]


def preparar_retratos(progresso=None):
    """Carrega (ou gera e salva em extras/) todos os retratos de diálogo.
    Chamado ao abrir o jogo, para a espera acontecer na tela de carregamento
    e não no meio da partida."""
    nomes = list(nomes_arquivo.values()) + ["bruxa", "fadinha"]
    for i, n in enumerate(nomes):
        rosto(next((k for k, v in nomes_arquivo.items() if v == n), n))
        if progresso:
            progresso((i + 1) / float(len(nomes)))
