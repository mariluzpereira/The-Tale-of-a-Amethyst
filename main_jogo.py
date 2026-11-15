import math
import random
import pygame

import falas
import recursos as rec
from configuracoes import (
    largura_tela, altura_tela, fps, cor_fundo, nomes_arquivo, cor_particula,
    escala_tempo_congelado, custo_poder, total_fases, total_flores_easter_egg, estrelas_maximas,
    ganho_estrela, chance_drop_estrela, chance_drop_maca, tempo_item_dropado, estrelas_iniciais,
)
from controles import Controles, ACOES
from sons import Audio
from jogador import jogador
from mundo import Mundo
from objetos import item
from fases import construir_fase
from interface import (
    HUD, CaixaDialogo, texto, fonte, quebrar_texto, cobrir, escurecer, desenhar_botao,
    desenhar_caixa_dialogo, VELOCIDADE_DIGITACAO,
)

PERSONAGENS = ["Safira", "Louise", "Anika", "Meliah"]


class _SemTeclas:
    """Finge que nenhuma tecla está apertada (usado durante transições)."""

    def __getitem__(self, _):
        return False


SEM_TECLAS = _SemTeclas()


# ========================================================================== cenário
class Cenario:
    def __init__(self, dados):
        self.tipo = dados["fundo"]
        self.chao_y = dados["chao_y"]
        self.tile = None
        self.tile_inv = None
        if self.tipo == "floresta":
            img = rec.imagem_opaca("cenário_caminho_floresta.jpg")
            if img is not None:
                w = int(img.get_width() * altura_tela / img.get_height())
                self.tile = pygame.transform.smoothscale(img, (w, altura_tela))
                self.tile_inv = pygame.transform.flip(self.tile, True, False)
        else:
            img = rec.imagem_opaca("cenario_boss.jpg")
            if img is not None:
                self.tile = pygame.transform.smoothscale(img, (largura_tela, altura_tela))
        self.tinta = None
        if dados.get("tinta"):
            self.tinta = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
            self.tinta.fill(dados["tinta"])

    def desenhar(self, tela, cam_x):
        if self.tile is None:
            tela.fill((110, 170, 230))
            pygame.draw.rect(tela, (45, 130, 80), (0, self.chao_y, largura_tela, altura_tela))
        elif self.tipo == "boss":
            tela.blit(self.tile, (0, 0))
        else:
            # paralaxe: o fundo anda a metade da velocidade; azulejos alternados
            # espelhados para não aparecer emenda
            deslocamento = int(cam_x * 0.5)
            w = self.tile.get_width()
            indice = deslocamento // w
            x = -(deslocamento % w)
            while x < largura_tela:
                tela.blit(self.tile if indice % 2 == 0 else self.tile_inv, (x, 0))
                x += w
                indice += 1
        if self.tinta is not None:
            tela.blit(self.tinta, (0, 0))


# ========================================================================== motor
class motorjogo:

    def __init__(self):
        # buffer de áudio maior (2048): com 512 qualquer engasgo do computador vira chiado
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        pygame.init()
        self.tela = pygame.display.set_mode((largura_tela, altura_tela))
        pygame.display.set_caption("The Tale of an Amethyst")
        self.relogio = pygame.time.Clock()
        self.rodando = True
        self.frames = 0

        # tudo que é lento (gerar sons, preparar retratos) acontece AQUI, antes do menu,
        # e não no meio da partida (onde travaria a música)
        self._carregando("Preparando imagens...", 0.0)
        self.controles = Controles()
        self.hud = HUD()
        self.dialogo = CaixaDialogo()
        self._carregar_imagens()
        self._carregando("Preparando retratos...", 0.15)
        rec.preparar_retratos(lambda f: self._carregando("Preparando retratos...", 0.15 + 0.25 * f))
        self._carregando("Preparando sons...", 0.4)
        self.audio = Audio(lambda f: self._carregando("Preparando sons...", 0.4 + 0.5 * f))
        self.dialogo.ao_digitar = lambda: self.audio.tocar("dialogo")
        self.dialogo.ao_avancar = lambda: self.audio.tocar("dialogo_proximo")
        self._carregando("Conferindo arquivos...", 0.95)
        self.aviso_recursos = self._checar_recursos()

        self.estado = "menu"
        self.menu_sel = 0
        self.opcao_sel = 0
        self.sel_personagem = 0
        self.sel_confirmado = 0
        self.escolhido = "Safira"
        self.jogador = None
        self.mundo = None
        self.cenario = None
        self.dados = None
        self.transicao = None
        self.voltar_para = "menu"
        self.pontos_finais = None
        self.easter_ativo = False
        self.easter_timer = 0
        self.easter_feito = False
        self.musica_antes_egg = None
        self.capturando = False          # Opções: esperando o jogador apertar uma tecla
        self.opcao_slot = 0
        self.mensagem_opcoes = ""
        self.fada_pagina = 0
        self.fada_t = 0
        self.fada_origem = "prologo"
        self.fada_paginas = []
        self.fade_fada = 255
        self.entrar_estado("menu")

    def _carregando(self, mensagem, fracao):
        """Tela de carregamento simples (barra de progresso)."""
        self.tela.fill((60, 30, 100))
        texto(self.tela, "The Tale of an Amethyst", 56, (255, 240, 255), (largura_tela // 2, 210), centro=True)
        texto(self.tela, mensagem, 30, (230, 215, 250), (largura_tela // 2, 300), centro=True)
        pygame.draw.rect(self.tela, (30, 15, 55), (312, 340, 400, 18), border_radius=6)
        pygame.draw.rect(self.tela, (255, 200, 255), (312, 340, int(400 * max(0.0, min(1.0, fracao))), 18),
                         border_radius=6)
        pygame.event.pump()
        pygame.display.flip()

    # ------------------------------------------------------------------ recursos
    def _checar_recursos(self):
        """Confere se todas as sprites/músicas existem e abrem. Se algo faltar,
        mostra um aviso no menu e grava 'diagnostico_recursos.txt' com os detalhes."""
        r = rec.verificar_recursos()
        if r["problemas"]:
            return "Atenção: %d arquivo(s) de imagem com problema - abra diagnostico_recursos.txt" % r["problemas"]
        return ""

    def _carregar_imagens(self):
        casa = rec.imagem_opaca("casa_fada.jpg")
        self.bg_menu = cobrir(casa, largura_tela, altura_tela) if casa is not None else None

        # Tela do menu: o fundo é SÓ a imagem menu.png, esticada para ocupar a tela inteira
        # (nenhum cenário atrás). O título e os botões ficam dentro da área roxa lisa do meio
        # da imagem (posição medida no arquivo original: 7%-93% da largura, 24%-76% da altura).
        painel = rec.imagem("menu.png")
        self.painel = None
        self.miolo = pygame.Rect(0.073 * largura_tela, 0.243 * altura_tela,
                                 0.854 * largura_tela, 0.512 * altura_tela)
        if painel is not None:
            self.painel = pygame.transform.smoothscale(rec.recortar(painel), (largura_tela, altura_tela))

        self.botoes_img = {}
        for nome, arq in (("Jogar", "jogar.png"), ("Opções", "opcoes.png"), ("Créditos", "creditos.png")):
            im = rec.imagem(arq)
            self.botoes_img[nome] = rec.escalar_altura(rec.recortar(im), 40) if im is not None else None
        sair = rec.imagem("sair.png")
        self.botoes_img["Sair"] = rec.escalar_altura(rec.recortar(sair), 40) if sair is not None else None

        # cenário do prólogo
        pro = rec.imagem_opaca("cenario_prologo.jpg")
        self.bg_prologo = cobrir(pro, largura_tela, altura_tela) if pro is not None else None

        amet = rec.imagem("extras/ametista_pequena.png")
        if amet is None:
            grande = rec.imagem("ametista(1).png")
            amet = rec.escalar_altura(rec.recortar(grande), 300, suave=True) if grande is not None else None
        self.ametista = amet

        rel = rec.imagem("extras/relogio_congelar.png")
        self.relogio_img = rec.escalar_largura(rel, 150, suave=True) if rel is not None else None

        # guirlandas de flores de cada princesa (tela de seleção)
        self.guirlandas = {}
        for tipo, arq in (("Safira", "flor_rosa_selecao.png"), ("Louise", "flor_vermelha_selecao.png"),
                          ("Anika", "flor_azul_selecao.png"), ("Meliah", "flor_roxa_selecao.png")):
            im = rec.imagem(arq)
            self.guirlandas[tipo] = rec.escalar_largura(im, 232, suave=True) if im is not None else None

        self.gnomos = []
        for i in range(1, 40):
            im = rec.imagem("extras/gnomo_%02d.png" % i)
            if im is None:
                break
            self.gnomos.append(im)

    # ------------------------------------------------------------------ estados
    def entrar_estado(self, nome):
        self.estado = nome
        self.transicao = None
        if nome == "menu":
            self.audio.musica("menu.mp3")
        elif nome == "creditos":
            self.audio.musica("creditos.mp3")
            self.creditos_y = float(altura_tela)
        elif nome == "selecao":
            self.audio.musica("selecao_personagem.mp3")
            self.sel_confirmado = 0
        elif nome == "prologo":
            self.audio.musica("prologo.ogg")
            self.prologo_y = float(altura_tela)
            self._montar_prologo()
        elif nome == "fada":
            self.audio.tocar("fada")
        elif nome == "derrota":
            self.audio.musica("derrota.mp3", repetir=False)
        elif nome == "vitoria":
            self.audio.musica("vitoria.wav", repetir=False)

    def executar(self):
        while self.rodando:
            self.relogio.tick(fps)
            self.frames += 1
            eventos = pygame.event.get()
            for ev in eventos:
                if ev.type == pygame.QUIT:
                    self.rodando = False
            if not self.rodando:
                break
            getattr(self, "estado_" + self.estado)(eventos)
            pygame.display.flip()
        pygame.quit()

    # ------------------------------------------------------------------ fundo das telas de menu
    def _fundo_menu(self, escuro=60):
        if self.bg_menu is not None:
            self.tela.blit(self.bg_menu, (0, 0))
        else:
            self.tela.fill(cor_fundo)
        escurecer(self.tela, escuro)

    # ================================================================== MENU
    ITENS_MENU = ["Jogar", "Opções", "Créditos", "Sair"]

    def _rects_menu(self):
        rects = []
        for i in range(len(self.ITENS_MENU)):
            r = pygame.Rect(0, 0, 190, 42)
            r.center = (self.miolo.centerx, self.miolo.top + 120 + i * 48)
            rects.append(r)
        return rects

    def _ativar_menu(self, i):
        self.audio.tocar("menu")
        nome = self.ITENS_MENU[i]
        if nome == "Jogar":
            self.entrar_estado("selecao")
        elif nome == "Opções":
            self.opcao_sel = 0
            self.entrar_estado("opcoes")
        elif nome == "Créditos":
            self.voltar_para = "menu"
            self.pontos_finais = None
            self.entrar_estado("creditos")
        else:
            self.rodando = False

    def estado_menu(self, eventos):
        rects = self._rects_menu()
        for ev in eventos:
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP, pygame.K_w):
                    self.menu_sel = (self.menu_sel - 1) % len(rects)
                    self.audio.tocar("menu")
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    self.menu_sel = (self.menu_sel + 1) % len(rects)
                    self.audio.tocar("menu")
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                    self._ativar_menu(self.menu_sel)
            elif ev.type == pygame.MOUSEMOTION:
                for i, r in enumerate(rects):
                    if r.collidepoint(ev.pos) and self.menu_sel != i:
                        self.menu_sel = i
                        self.audio.tocar("menu")
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(rects):
                    if r.collidepoint(ev.pos):
                        self.menu_sel = i
                        self._ativar_menu(i)
        if self.estado != "menu":
            return

        if self.painel is not None:
            self.tela.blit(self.painel, (0, 0))
        else:
            self.tela.fill((95, 53, 165))       # sem menu.png na pasta: só a cor roxa do painel
        texto(self.tela, "The Tale of", 46, (255, 240, 255), (self.miolo.centerx, self.miolo.top + 26), centro=True)
        texto(self.tela, "an Amethyst", 52, (225, 170, 255), (self.miolo.centerx, self.miolo.top + 66), centro=True)
        for i, (nome, r) in enumerate(zip(self.ITENS_MENU, rects)):
            desenhar_botao(self.tela, self.botoes_img.get(nome), nome.upper(), r.center, i == self.menu_sel)
        if self.aviso_recursos:
            r = texto(self.tela, self.aviso_recursos, 24, (255, 225, 120),
                      (largura_tela // 2, altura_tela - 22), centro=True)

    # ================================================================== OPÇÕES
    # Fundo: SÓ a imagem menu.png (a mesma do menu). Volumes à esquerda, teclas à direita.
    NUM_LINHAS_ESQ = 4          # música, efeitos, restaurar teclas, voltar

    def _rect_linha_opcoes(self, i):
        m = self.miolo
        if i < self.NUM_LINHAS_ESQ:
            return pygame.Rect(m.left + 30, m.top + 46 + i * 62, 330, 52)
        return pygame.Rect(m.left + 395, m.top + 68 + (i - self.NUM_LINHAS_ESQ) * 28, 460, 26)

    def _rect_slot(self, i, slot):
        r = self._rect_linha_opcoes(i)
        return pygame.Rect(r.left + 215 + slot * 128, r.top, 120, r.height)

    def _acao_da_linha(self, i):
        return ACOES[i - self.NUM_LINHAS_ESQ][0] if i >= self.NUM_LINHAS_ESQ else None

    def _aplicar_volume_barra(self, i, mx):
        r = self._rect_linha_opcoes(i)
        v = max(0.0, min(1.0, (mx - r.left) / float(r.width)))
        if i == 0:
            self.audio.definir_volume_musica(v)
        else:
            self.audio.definir_volume_sfx(v)
            self.audio.tocar("item")

    def _ativar_opcao(self, i):
        if i == 2:
            self.controles.restaurar_padrao()
            self.mensagem_opcoes = "Teclas restauradas para o padrão."
            self.audio.tocar("tecla_ok")
        elif i == 3:
            self.audio.tocar("ui_voltar")
            self.entrar_estado("menu")
        elif i >= self.NUM_LINHAS_ESQ:
            self.capturando = True
            self.mensagem_opcoes = ""
            self.audio.tocar("menu")

    def _capturar_tecla(self, ev):
        """Recebe a próxima tecla/clique para o slot escolhido."""
        acao = self._acao_da_linha(self.opcao_sel)
        nome_acao = next(r for a, r, _ in ACOES if a == acao)
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                self.capturando = False
                self.mensagem_opcoes = "Cancelado."
                return
            if ev.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                ok = self.controles.atribuir(acao, self.opcao_slot, None)
                self.mensagem_opcoes = "Campo limpo." if ok else "A ação precisa de pelo menos uma tecla."
            else:
                bind = ("k", ev.key)
                ok = self.controles.atribuir(acao, self.opcao_slot, bind)
                self.mensagem_opcoes = ("%s agora usa %s." % (nome_acao, self.controles.nome_bind(bind))) if ok \
                    else "Essa tecla não pode ser usada aqui."
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button in (1, 2, 3):
            bind = ("m", ev.button)
            ok = self.controles.atribuir(acao, self.opcao_slot, bind)
            self.mensagem_opcoes = ("%s agora usa %s." % (nome_acao, self.controles.nome_bind(bind))) if ok \
                else "Botões do mouse só servem para Atirar e Poder especial."
        else:
            return
        self.audio.tocar("tecla_ok" if ok else "ui_erro")
        self.capturando = False

    def estado_opcoes(self, eventos):
        total = self.NUM_LINHAS_ESQ + len(ACOES)
        for ev in eventos:
            if self.capturando:
                self._capturar_tecla(ev)
                continue
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.audio.tocar("ui_voltar")
                    self.entrar_estado("menu")
                    return
                if ev.key in (pygame.K_UP, pygame.K_w):
                    self.opcao_sel = (self.opcao_sel - 1) % total
                    self.audio.tocar("menu")
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    self.opcao_sel = (self.opcao_sel + 1) % total
                    self.audio.tocar("menu")
                elif ev.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                    passo = 1 if ev.key in (pygame.K_RIGHT, pygame.K_d) else -1
                    if self.opcao_sel == 0:
                        self.audio.definir_volume_musica(self.audio.volume_musica + 0.1 * passo)
                    elif self.opcao_sel == 1:
                        self.audio.definir_volume_sfx(self.audio.volume_sfx + 0.1 * passo)
                        self.audio.tocar("item")
                    elif self.opcao_sel >= self.NUM_LINHAS_ESQ:
                        self.opcao_slot = 0 if passo < 0 else 1
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                    self._ativar_opcao(self.opcao_sel)
                    if self.estado != "opcoes":
                        return
            elif ev.type == pygame.MOUSEMOTION:
                for i in range(total):
                    if self._rect_linha_opcoes(i).collidepoint(ev.pos):
                        if i != self.opcao_sel:
                            self.opcao_sel = i
                            self.audio.tocar("menu")
                        if i >= self.NUM_LINHAS_ESQ:
                            for sl in (0, 1):
                                if self._rect_slot(i, sl).collidepoint(ev.pos):
                                    self.opcao_slot = sl
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i in range(total):
                    if not self._rect_linha_opcoes(i).collidepoint(ev.pos):
                        continue
                    self.opcao_sel = i
                    if i < 2:
                        self._aplicar_volume_barra(i, ev.pos[0])
                    elif i >= self.NUM_LINHAS_ESQ:
                        for sl in (0, 1):
                            if self._rect_slot(i, sl).collidepoint(ev.pos):
                                self.opcao_slot = sl
                                self._ativar_opcao(i)
                    else:
                        self._ativar_opcao(i)
                        if self.estado != "opcoes":
                            return

        # ---- desenho: só a imagem do menu como fundo
        if self.painel is not None:
            self.tela.blit(self.painel, (0, 0))
        else:
            self.tela.fill((95, 53, 165))
        m = self.miolo
        texto(self.tela, "Opções", 44, (255, 240, 255), (m.centerx, m.top + 20), centro=True)

        # coluna da esquerda: volumes, restaurar, voltar
        valores = {0: ("Volume da música", self.audio.volume_musica), 1: ("Volume dos efeitos", self.audio.volume_sfx)}
        for i in range(self.NUM_LINHAS_ESQ):
            r = self._rect_linha_opcoes(i)
            sel = i == self.opcao_sel
            cor = (255, 255, 160) if sel else (240, 230, 250)
            if i in valores:
                nome, v = valores[i]
                texto(self.tela, nome, 26, cor, (r.left, r.top))
                pygame.draw.rect(self.tela, (50, 30, 80), (r.left, r.top + 28, r.width - 60, 16), border_radius=6)
                pygame.draw.rect(self.tela, (255, 200, 255), (r.left, r.top + 28, int((r.width - 60) * v), 16), border_radius=6)
                texto(self.tela, "%d%%" % round(v * 100), 24, cor, (r.right - 50, r.top + 24))
            else:
                caixa = pygame.Rect(r.left, r.top + 6, 250, 38)
                pygame.draw.rect(self.tela, (255, 150, 255), caixa, border_radius=6)
                pygame.draw.rect(self.tela, (60, 20, 90), caixa, 3, border_radius=6)
                texto(self.tela, "Restaurar teclas" if i == 2 else "Voltar", 26, (50, 15, 70), caixa.center,
                      centro=True, sombra=False)
            if sel:
                alvo = r if i in valores else pygame.Rect(r.left, r.top + 6, 250, 38)
                pygame.draw.rect(self.tela, (255, 255, 255), alvo.inflate(10, 6), 2, border_radius=8)

        # coluna da direita: teclas
        h = self._rect_linha_opcoes(self.NUM_LINHAS_ESQ)
        texto(self.tela, "Teclas e botões", 24, (255, 225, 150), (h.left, h.top - 26))
        texto(self.tela, "Principal", 20, (230, 215, 250), (self._rect_slot(self.NUM_LINHAS_ESQ, 0).centerx, h.top - 22), centro=True)
        texto(self.tela, "Alternativa", 20, (230, 215, 250), (self._rect_slot(self.NUM_LINHAS_ESQ, 1).centerx, h.top - 22), centro=True)
        for k, (acao, rotulo, _) in enumerate(ACOES):
            i = self.NUM_LINHAS_ESQ + k
            r = self._rect_linha_opcoes(i)
            sel = i == self.opcao_sel
            texto(self.tela, rotulo, 22, (255, 255, 160) if sel else (240, 230, 250), (r.left, r.top + 3))
            for sl in (0, 1):
                caixa = self._rect_slot(i, sl)
                ativo = sel and sl == self.opcao_slot
                pygame.draw.rect(self.tela, (40, 20, 70), caixa, border_radius=5)
                pygame.draw.rect(self.tela, (255, 255, 255) if ativo else (160, 120, 210), caixa, 2 if ativo else 1,
                                 border_radius=5)
                if ativo and self.capturando:
                    if (self.frames // 20) % 2 == 0:
                        texto(self.tela, "aperte...", 20, (255, 255, 120), caixa.center, centro=True, sombra=False)
                else:
                    texto(self.tela, self.controles.nome_bind(self.controles.mapa[acao][sl]), 20,
                          (255, 255, 255) if ativo else (225, 215, 240), caixa.center, centro=True, sombra=False)

        if self.mensagem_opcoes:
            texto(self.tela, self.mensagem_opcoes, 24, (255, 235, 150), (largura_tela // 2, altura_tela - 92), centro=True)
        ajuda = "Aperte a nova tecla (Esc cancela, Backspace limpa)" if self.capturando else \
            "Setas: mover   Enter ou clique: mudar tecla   Backspace: limpar   Esc: voltar"
        texto(self.tela, ajuda, 22, (225, 215, 245), (largura_tela // 2, altura_tela - 62), centro=True)

    # ================================================================== SELEÇÃO DE PERSONAGEM
    def _rects_cartas(self):
        larg, alt, esp = 218, 330, 20
        x0 = (largura_tela - (4 * larg + 3 * esp)) // 2
        return [pygame.Rect(x0 + i * (larg + esp), 92, larg, alt) for i in range(4)]

    def _confirmar_personagem(self):
        self.escolhido = PERSONAGENS[self.sel_personagem]
        self.audio.tocar("selecionar")
        self.audio.voz(nomes_arquivo[self.escolhido], "selecao")
        self.sel_confirmado = 1

    def estado_selecao(self, eventos):
        cartas = self._rects_cartas()
        for ev in eventos:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.entrar_estado("menu")
                    return
                if self.sel_confirmado:
                    if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.sel_confirmado = 9999
                    continue
                if ev.key in (pygame.K_LEFT, pygame.K_a):
                    self.sel_personagem = (self.sel_personagem - 1) % 4
                    self.audio.tocar("menu")
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    self.sel_personagem = (self.sel_personagem + 1) % 4
                    self.audio.tocar("menu")
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._confirmar_personagem()
            elif ev.type == pygame.MOUSEMOTION and not self.sel_confirmado:
                for i, r in enumerate(cartas):
                    if r.collidepoint(ev.pos) and self.sel_personagem != i:
                        self.sel_personagem = i
                        self.audio.tocar("menu")
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and not self.sel_confirmado:
                for i, r in enumerate(cartas):
                    if r.collidepoint(ev.pos):
                        self.sel_personagem = i
                        self._confirmar_personagem()

        if self.sel_confirmado:
            self.sel_confirmado += 1
            if self.sel_confirmado > 170:
                self.entrar_estado("prologo")
                return

        self._fundo_menu(110)
        texto(self.tela, "Escolha sua princesa", 54, (255, 240, 255), (largura_tela // 2, 38), centro=True)
        for i, (tipo, r) in enumerate(zip(PERSONAGENS, cartas)):
            sel = i == self.sel_personagem
            fundo = pygame.Surface(r.size, pygame.SRCALPHA)
            fundo.fill((60, 30, 100, 220) if sel else (30, 18, 55, 190))
            self.tela.blit(fundo, r.topleft)
            pygame.draw.rect(self.tela, (255, 235, 130) if sel else (150, 110, 200), r, 4 if sel else 2,
                             border_radius=6)
            rosto = rec.rosto(tipo)
            if rosto is not None:
                img = rec.escalado(rosto, 160, True, 190)
                self.tela.blit(img, img.get_rect(midbottom=(r.centerx, r.top + 222)))
            guirlanda = self.guirlandas.get(tipo)
            if guirlanda is not None:
                self.tela.blit(guirlanda, guirlanda.get_rect(midtop=(r.centerx, r.top - 24)))
            texto(self.tela, falas.NOME_EXIBIDO[tipo], 40, (255, 255, 255), (r.centerx, r.top + 238), centro=True)
            texto(self.tela, falas.PODERES[tipo][0], 26, (255, 225, 140), (r.centerx, r.top + 270), centro=True)
            y = r.top + 292
            for linha in quebrar_texto(falas.PODERES[tipo][1], 21, r.width - 20)[:2]:
                texto(self.tela, linha, 21, (225, 215, 240), (r.centerx, y), centro=True, sombra=False)
                y += 18

        tipo = PERSONAGENS[self.sel_personagem]
        frase = '"%s"' % falas.FALAS[tipo]["selecao"]
        caixa = pygame.Surface((largura_tela - 120, 70), pygame.SRCALPHA)
        caixa.fill((20, 10, 40, 200))
        self.tela.blit(caixa, (60, 434))
        texto(self.tela, "%s: %s" % (falas.NOME_EXIBIDO[tipo], frase), 32, (255, 255, 255),
              (largura_tela // 2, 469), centro=True)
        if not self.sel_confirmado:
            texto(self.tela, "Setas / mouse para escolher    Enter ou clique para confirmar", 26,
                  (210, 200, 230), (largura_tela // 2, 528), centro=True)
        else:
            texto(self.tela, "Preparando a jornada...", 30, (255, 240, 170),
                  (largura_tela // 2, 528), centro=True)

    # ================================================================== PRÓLOGO
    VELOCIDADE_PROLOGO = 0.30           # pixels por frame (antes 0.6: agora o texto é mais lento)

    def _montar_prologo(self):
        self.prologo_linhas = []
        for par in falas.HISTORIA:
            self.prologo_linhas += quebrar_texto(par, 34, 800)
            self.prologo_linhas.append("")
        self.prologo_altura = len(self.prologo_linhas) * 42

    def _terminar_prologo(self):
        self._iniciar_fada("prologo")

    def estado_prologo(self, eventos):
        for ev in eventos:
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self._terminar_prologo()
                return
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                self._terminar_prologo()
                return
        teclas = pygame.key.get_pressed()
        acelerar = self.controles.tecla("descer", teclas)
        self.prologo_y -= 2.2 if acelerar else self.VELOCIDADE_PROLOGO
        if self.prologo_y + self.prologo_altura < 60:
            self._terminar_prologo()
            return

        # cenário do prólogo (cenario_prologo.jpg) com um leve escurecido para o texto aparecer
        if self.bg_prologo is not None:
            self.tela.blit(self.bg_prologo, (0, 0))
        else:
            self._fundo_menu(60)
        escurecer(self.tela, 85)
        y = int(self.prologo_y)
        for linha in self.prologo_linhas:
            if -40 < y < altura_tela:
                texto(self.tela, linha, 34, (255, 250, 255), (largura_tela // 2, y), centro=True)
            y += 42
        texto(self.tela, "Enter ou clique: pular    %s: acelerar" % self.controles.nome_acao("descer"), 24,
              (235, 225, 245), (largura_tela // 2, altura_tela - 22), centro=True)

    # ================================================================== CASA DA FADA (conversa e tutorial)
    # Cena à parte: fundo casa_fada, SEM inimigos. Aparece depois do prólogo e também
    # quando a jogadora aperta a tecla de interagir perto da Fadinha na fase 1.
    def _dados_tutorial(self):
        d = {k: self.controles.nome_acao(k, " ou ") for k in
             ("esquerda", "direita", "pular", "descer", "atirar", "poder", "interagir", "pausar")}
        nome, desc = falas.PODERES[self.escolhido]
        d.update(custo=custo_poder, poder_nome=nome, poder_desc=desc)
        return d

    def _iniciar_fada(self, origem):
        self.fada_origem = origem
        dados = self._dados_tutorial()
        paginas = []
        if origem == "prologo":
            paginas += [("nenhum", frase) for frase in falas.FADA]
        paginas += [(painel, frase.format(**dados)) for painel, frase in falas.FADA_TUTORIAL]
        self.fada_paginas = paginas
        self.fada_pagina = 0
        self.fada_t = 0
        self.fade_fada = 255            # começa escuro e clareia
        self.fada_saindo = False
        self.estado = "fada"
        self.transicao = None
        self.audio.tocar("fada")

    def _avancar_fada(self):
        if self.fada_saindo:
            return
        frase = self.fada_paginas[self.fada_pagina][1]
        if self.fada_t * VELOCIDADE_DIGITACAO < len(frase):
            self.fada_t = int(len(frase) / VELOCIDADE_DIGITACAO) + 1        # mostra o texto inteiro
            return
        self.audio.tocar("dialogo_proximo")
        self.fada_pagina += 1
        self.fada_t = 0
        if self.fada_pagina >= len(self.fada_paginas):
            self.fada_saindo = True

    def _sair_da_fada(self):
        if self.fada_origem == "prologo":
            self.iniciar_jogo()
        else:
            self.estado = "jogando"
            self.pausado = False

    def estado_fada(self, eventos):
        for ev in eventos:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.fada_saindo = True               # pular a conversa inteira
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER) or \
                        self.controles.evento("interagir", ev):
                    self._avancar_fada()
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                self._avancar_fada()

        # fade de entrada/saída
        if self.fada_saindo:
            self.fade_fada = min(255, self.fade_fada + 10)
            if self.fade_fada >= 255:
                self._sair_da_fada()
                return
        else:
            self.fade_fada = max(0, self.fade_fada - 8)

        # digitação com som
        painel, frase = self.fada_paginas[min(self.fada_pagina, len(self.fada_paginas) - 1)]
        antes, agora = int(self.fada_t * VELOCIDADE_DIGITACAO), int((self.fada_t + 1) * VELOCIDADE_DIGITACAO)
        if agora < len(frase) and agora // 3 != antes // 3:
            self.audio.tocar("dialogo")
        self.fada_t += 1

        self._desenhar_fada(painel, frase)

    def _desenhar_fada(self, painel, frase):
        tela = self.tela
        if self.bg_menu is not None:
            tela.blit(self.bg_menu, (0, 0))          # casa_fada.jpg: nenhum inimigo nesta cena
        else:
            tela.fill((60, 100, 70))

        # a princesa escolhida, à esquerda, olhando para a Fada
        sprites = rec.sprites_princesa(self.escolhido)
        if sprites:
            base = sprites["andar_dir"][0]
            img = rec.escalado(base, base.get_height() * 2, False)
            tela.blit(img, img.get_rect(midbottom=(200, 538)))
        # a Fada, à direita, flutuando
        fada_img = self._img_fada_grande()
        if fada_img is not None:
            bob = int(math.sin(self.frames * 0.05) * 10)
            tela.blit(fada_img, fada_img.get_rect(center=(770, 440 + bob)))

        if painel != "nenhum":
            self._desenhar_painel_fada(painel)

        rosto = rec.rosto("fadinha")
        dica = "[%s / Enter] continuar    [Esc] pular" % self.controles.nome_acao("interagir").split(" / ")[0]
        desenhar_caixa_dialogo(tela, "Fada", frase, rosto, self.fada_t, True, topo=16, dica=dica)
        total = len(self.fada_paginas)
        texto(tela, "%d/%d" % (min(self.fada_pagina + 1, total), total), 22, (255, 255, 255),
              (largura_tela - 40, 164), direita=True)

        if self.fade_fada > 0:
            v = pygame.Surface((largura_tela, altura_tela))
            v.fill((0, 0, 0))
            v.set_alpha(int(self.fade_fada))
            tela.blit(v, (0, 0))

    def _img_fada_grande(self):
        if not hasattr(self, "_fada_grande"):
            base = rec.imagem("fadinha.png")
            if base is None:
                self._fada_grande = None
            else:
                img = rec.escalar_altura(rec.recortar(base), 190, suave=True)
                self._fada_grande = rec.espelhar(img)       # a sprite olha p/ a direita; aqui olha p/ a esquerda
        return self._fada_grande

    # ---- painéis ilustrados da conversa
    def _desenhar_painel_fada(self, tipo):
        tela = self.tela
        area = pygame.Rect(130, 160, 764, 190)
        fundo = pygame.Surface(area.size, pygame.SRCALPHA)
        fundo.fill((25, 12, 45, 205))
        pygame.draw.rect(fundo, (200, 150, 255, 255), fundo.get_rect(), 3, border_radius=8)
        tela.blit(fundo, area.topleft)
        c = self.controles
        cx, cy = area.centerx, area.centery

        def tecla(rotulo, nome, centro, largura=150):
            r = pygame.Rect(0, 0, largura, 44)
            r.center = centro
            pygame.draw.rect(tela, (245, 240, 255), r, border_radius=8)
            pygame.draw.rect(tela, (120, 80, 170), r, 3, border_radius=8)
            texto(tela, nome, 24, (50, 25, 80), r.center, centro=True, sombra=False)
            texto(tela, rotulo, 22, (255, 235, 170), (r.centerx, r.bottom + 18), centro=True)

        def mouse(centro, esq=False, dir_=False):
            corpo = pygame.Rect(0, 0, 54, 82)
            corpo.center = centro
            pygame.draw.rect(tela, (245, 240, 255), corpo, border_radius=24)
            if esq:
                pygame.draw.rect(tela, (255, 120, 160), (corpo.left, corpo.top, 27, 36), border_top_left_radius=24)
            if dir_:
                pygame.draw.rect(tela, (255, 120, 160), (corpo.centerx, corpo.top, 27, 36), border_top_right_radius=24)
            pygame.draw.rect(tela, (120, 80, 170), corpo, 3, border_radius=24)
            pygame.draw.line(tela, (120, 80, 170), (corpo.left, corpo.top + 36), (corpo.right, corpo.top + 36), 2)
            pygame.draw.line(tela, (120, 80, 170), (corpo.centerx, corpo.top), (corpo.centerx, corpo.top + 36), 2)

        if tipo == "controles":
            for k, (acao, rot) in enumerate((("esquerda", "Esquerda"), ("direita", "Direita"),
                                             ("pular", "Pular"), ("descer", "Descer"))):
                tecla(rot, c.nome_acao(acao), (area.left + 100 + k * 188, cy - 14), 160)
        elif tipo == "atirar":
            mouse((area.left + 110, cy), esq=True)
            texto(tela, c.nome_acao("atirar"), 26, (255, 235, 170), (area.left + 110, cy + 62), centro=True)
            sprites = rec.sprites_princesa(self.escolhido)
            if sprites and sprites.get("poder"):
                tiro = pygame.transform.rotate(sprites["poder"][0], 180)      # aponta p/ a direita
                tela.blit(tiro, tiro.get_rect(center=(cx - 20, cy)))
            mira = (area.right - 140, cy)
            pygame.draw.circle(tela, (255, 120, 160), mira, 26, 3)
            pygame.draw.line(tela, (255, 120, 160), (mira[0] - 38, mira[1]), (mira[0] + 38, mira[1]), 3)
            pygame.draw.line(tela, (255, 120, 160), (mira[0], mira[1] - 38), (mira[0], mira[1] + 38), 3)
            texto(tela, "a magia vai até o cursor", 22, (255, 255, 255), (mira[0], mira[1] + 52), centro=True)
        elif tipo == "poder":
            mouse((area.left + 110, cy), dir_=True)
            texto(tela, c.nome_acao("poder"), 26, (255, 235, 170), (area.left + 110, cy + 62), centro=True)
            estrela = item._imagem("Estrela")
            tela.blit(estrela, estrela.get_rect(center=(cx - 60, cy - 12)))
            texto(tela, "- %d" % custo_poder, 40, (170, 220, 255), (cx + 10, cy - 12), centro=True)
            nome, _ = falas.PODERES[self.escolhido]
            texto(tela, nome, 32, (255, 225, 140), (area.right - 190, cy - 12), centro=True)
            texto(tela, "poder da %s" % falas.NOME_EXIBIDO[self.escolhido], 22, (255, 255, 255),
                  (area.right - 190, cy + 24), centro=True)
        elif tipo == "plataformas":
            plat = pygame.Rect(0, 0, 170, 18)
            for k, y in enumerate((cy - 40, cy + 30)):
                plat.center = (area.left + 160 + k * 60, y)
                pygame.draw.rect(tela, (110, 160, 80), plat, border_radius=4)
                pygame.draw.rect(tela, (60, 100, 50), plat, 3, border_radius=4)
            pygame.draw.polygon(tela, (255, 235, 170), [(area.left + 340, cy - 40), (area.left + 322, cy - 62), (area.left + 358, cy - 62)])
            tecla("Descer da plataforma", c.nome_acao("descer"), (area.right - 200, cy - 14), 180)
        elif tipo == "itens":
            itens = (("Maca", "Maçã", "+1 coração"), ("Estrela", "Estrela", "+%d de energia" % ganho_estrela),
                     ("Flor", "Flor", "20 = um segredo"))
            for k, (nome, titulo, efeito) in enumerate(itens):
                x = area.left + 130 + k * 250
                img = item._imagem(nome)
                tela.blit(img, img.get_rect(center=(x, cy - 28)))
                texto(tela, titulo, 28, (255, 235, 170), (x, cy + 22), centro=True)
                texto(tela, efeito, 22, (255, 255, 255), (x, cy + 50), centro=True)
        elif tipo == "inimigos":
            import desenho
            figuras = ((desenho.quadros_planta()["idle"][0].img, 64, "Planta", "morde de perto"),
                       (desenho.quadros_bruxa()["voando"][0][0].img, 70, "Bruxa", "poção = sapo (10 s)"),
                       (desenho.quadros_vespa()[0][0][0].img, 52, "Vespa", "persegue sem parar"))
            for k, (img, h, nome, efeito) in enumerate(figuras):
                x = area.left + 130 + k * 250
                g = rec.escalado(img, h, True)
                tela.blit(g, g.get_rect(center=(x, cy - 26)))
                texto(tela, nome, 28, (255, 235, 170), (x, cy + 28), centro=True)
                texto(tela, efeito, 22, (255, 255, 255), (x, cy + 54), centro=True)
        elif tipo == "objetivo":
            texto(tela, "Derrote todos os inimigos", 32, (255, 255, 255), (area.left + 270, cy - 22), centro=True)
            texto(tela, "e siga para a direita", 32, (255, 235, 170), (area.left + 270, cy + 20), centro=True)
            pygame.draw.polygon(tela, (255, 235, 170), [(area.right - 70, cy), (area.right - 150, cy - 44), (area.right - 150, cy + 44)])
            pygame.draw.rect(tela, (255, 235, 170), (area.right - 250, cy - 16, 110, 32))

    # ================================================================== INÍCIO DO JOGO / FASES
    def iniciar_jogo(self):
        self.jogador = None
        self.vistos = set()
        self.dialogo.limpar()
        self.dialogo.ultimo.clear()
        self.energia_baixa_avisada = False
        self.easter_timer = 0
        self.easter_ativo = False
        self.easter_feito = False
        self.carregar_fase(1)
        self.estado = "jogando"

    def carregar_fase(self, numero, tentativa=False):
        self.fase_num = numero
        self.mundo = Mundo(self.audio)
        self.mundo.controles = self.controles
        self.dados = construir_fase(self.mundo, numero)
        self.cenario = Cenario(self.dados)
        inicio_x = 90 if numero < total_fases else 110
        if self.jogador is None:
            self.jogador = jogador(inicio_x, self.mundo.chao_y, self.escolhido)
        else:
            self.jogador.reposicionar(inicio_x, self.mundo.chao_y)
        j = self.jogador
        if tentativa:
            j.score, j.flowers_collected = self.snap
            j.restaurar_para_nova_tentativa()
            j.reposicionar(inicio_x, self.mundo.chao_y)
        else:
            self.snap = (j.score, j.flowers_collected)

        self.cam_x = 0.0
        self.pausado = False
        self.boss_derrotado = False
        self.morte_timer = 0
        self.transicao = None
        self.banner = [falas.NOMES_FASES[numero][0], falas.NOMES_FASES[numero][1], 170]
        self.audio.musica(self.dados["musica"])
        if numero > 1 and not tentativa:
            self.audio.tocar("fase_nova")

    def proxima_fase(self):
        self.carregar_fase(self.fase_num + 1)

    def falar(self, chave, intervalo=600):
        tipo = self.escolhido
        frase = falas.FALAS[tipo][chave]
        if self.dialogo.mostrar(chave, falas.NOME_EXIBIDO[tipo], frase, rec.rosto(tipo),
                                self.frames, intervalo):
            self.audio.voz(nomes_arquivo[tipo], chave)

    def _sequencia(self, chave, nome, rosto, frases):
        """Várias falas seguidas que pausam o jogo; E / Enter / clique avançam."""
        for i, frase in enumerate(frases):
            self.dialogo.mostrar("%s_%d" % (chave, i), nome, frase, rosto, self.frames,
                                 intervalo=0, bloqueia=True)

    def _interagir(self):
        """Tecla de interagir perto da Fadinha: abre a casa dela (cena sem inimigos)."""
        j = self.jogador
        if j.morta or self.transicao is not None:
            return
        for npc in self.mundo.npcs:
            if npc.perto(j):
                self._iniciar_fada("jogo")
                return

    def usar_poder(self):
        j = self.jogador
        r = j.use_special(self.mundo)
        if r == "ok":
            self.falar("habilidade", 900)
            if j.stars < custo_poder:
                self.falar("pouca_energia", 480)
                self.energia_baixa_avisada = True
        elif r == "sem_energia":
            self.audio.tocar("sem_energia")
            self.falar("pouca_energia", 300)

    def _iniciar_fade(self, acao):
        self.transicao = {"modo": "escurecendo", "alpha": 0, "acao": acao}

    # ================================================================== LOOP DA FASE
    def estado_jogando(self, eventos):
        for ev in eventos:
            c = self.controles
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE or c.evento("pausar", ev):
                    self.pausado = not self.pausado
                    self.audio.tocar("pausa" if self.pausado else "retomar")
                elif self.pausado and ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.pausado = False
                    self.audio.tocar("retomar")
                elif self.pausado and ev.key == pygame.K_m:
                    self.audio.parar_musica()
                    self.entrar_estado("menu")
                    return
                elif self.dialogo.bloqueando and (c.evento("interagir", ev)
                                                  or ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER)):
                    self.dialogo.avancar()
                elif c.evento("interagir", ev):
                    if self.dialogo.atual is not None:
                        self.dialogo.fechar()
                    elif not self.pausado:
                        self._interagir()
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.dialogo.bloqueando:
                self.dialogo.avancar()
            if (c.evento("poder", ev) and not self.pausado and self.transicao is None
                    and not self.jogador.morta and not self.dialogo.bloqueando):
                self.usar_poder()
        if not self.pausado:
            self.atualizar_jogo()
            if self.estado != "jogando":
                return
        self.desenhar_jogo()

    # ------------------------------------------------------------------ atualização
    def atualizar_jogo(self):
        j, m = self.jogador, self.mundo
        m.tempo += 1
        self.dialogo.atualizar()
        if self.dialogo.bloqueando:
            return              # cena de fala: o jogo espera (E / Enter / clique avança)
        for n in m.npcs:
            n.update(m.tempo)

        # ---- transição (fade) entre fases
        t = self.transicao
        if t is not None:
            if t["modo"] == "escurecendo":
                t["alpha"] = min(255, t["alpha"] + 7)
                if t["alpha"] >= 255:
                    t["acao"]()
                    if self.estado == "jogando":
                        self.transicao = {"modo": "clareando", "alpha": 255, "acao": None}
                    return
            else:
                t["alpha"] -= 7
                if t["alpha"] <= 0:
                    self.transicao = None

        morta = j.morta
        controle = self.transicao is None and not morta and not self.boss_derrotado
        teclas = pygame.key.get_pressed() if controle else SEM_TECLAS

        # Meliah congela o tempo dos inimigos
        escala = escala_tempo_congelado if (j.tipo_personagem == "Meliah" and j.special_active
                                           and not j.eh_sapinho) else 1.0

        if not morta:
            j.update(teclas, m)
            if controle and not self.pausado and \
                    self.controles.segurando("atirar", teclas, pygame.mouse.get_pressed()):
                mx, my = pygame.mouse.get_pos()
                j.atirar((mx + int(self.cam_x), my), m.proj_jogador, m)

        if j.stars >= custo_poder:
            if self.energia_baixa_avisada:
                self.audio.tocar("poder_pronto")
            self.energia_baixa_avisada = False
        # alerta sonoro de vida baixa (um batimento a cada 1,5 s)
        if not morta and j.hearts == 1 and m.tempo % 90 == 0:
            self.audio.tocar("coracao_baixo")

        if not morta:
            for e in m.inimigos:
                e.update(j, escala, m)
        for p in m.proj_jogador:
            p.update(1.0, m)
        for p in m.proj_inimigos:
            p.update(escala, m)
        for it in m.itens:
            it.update(m.tempo)
        m.atualizar_particulas()

        if not morta:
            j.atacar_inimigos(m.inimigos, m.proj_inimigos, m)
            self._colisoes()
            self._recompensas()
            self._eventos_do_mundo()
            self._dialogos_automaticos()
            self._progresso_da_fase()

        # ---- morte da jogadora
        if j.morta:
            if self.morte_timer == 0:
                self.audio.parar_musica()
                self.audio.tocar("dano")
                m.emitir(j.rect.centerx, j.rect.centery, (255, 120, 160), n=30, vel=5, vida=40)
                self.dialogo.limpar()
            self.morte_timer += 1
            if self.morte_timer > 110:
                self.entrar_estado("derrota")
                return

        # ---- easter egg: toca easter_egg_musica.mp3 e depois volta para a música da fase
        if self.easter_ativo:
            self.easter_timer -= 1
            terminou = self.audio.ativo and self.audio.musica_atual == "easter_egg_musica.mp3" \
                and not self.audio.tocando()
            if terminou or self.easter_timer <= 0:
                self.easter_ativo = False
                if self.easter_timer <= 0:
                    self.audio.parar_musica()
                self.audio.musica(self.musica_antes_egg or self.dados["musica"])

        # ---- câmera
        alvo = j.rect.centerx - largura_tela / 2
        alvo = max(0, min(alvo, max(0, m.largura - largura_tela)))
        self.cam_x += (alvo - self.cam_x) * 0.15
        if self.banner:
            self.banner[2] -= 1
            if self.banner[2] <= 0:
                self.banner = None

    # ------------------------------------------------------------------ colisões
    def _colisoes(self):
        j, m = self.jogador, self.mundo
        cor = cor_particula.get(j.tipo_personagem, (255, 255, 255))

        # tiros da princesa x inimigos
        for p in list(m.proj_jogador):
            for e in m.inimigos:
                if e.morrendo == 0 and p.rect.colliderect(e.rect):
                    sentido = 1 if p.vx >= 0 else -1
                    if e.receber_dano(p.dano, empurrao=3 * sentido):
                        self.audio.tocar("acerto_" + e.enemy_type.lower())
                        m.emitir(p.rect.centerx, p.rect.centery, cor, n=7, vel=3)
                    p.kill()
                    break

        # tiros/poções dos inimigos x princesa
        for p in list(m.proj_inimigos):
            if not p.rect.colliderect(j.rect):
                continue
            if j.bloqueia(p.rect.centerx):
                self.audio.tocar("bloqueio")
                m.emitir(p.rect.centerx, p.rect.centery, (150, 220, 255), n=8, vel=3)
                p.kill()
                continue
            if j.tempo_invulnerabilidade > 0:
                continue
            if p.transforma and not j.eh_sapinho:
                j.transformar_em_sapinho()
                j.tempo_invulnerabilidade = 60
                self.audio.tocar("sapo")
                m.emitir(j.rect.centerx, j.rect.centery, (90, 230, 90), n=22, vel=4)
                self.falar("bruxa", 900)
                p.kill()
            else:
                if j.receber_dano(p.rect.centerx, forca=p.dano):
                    self.audio.tocar("dano")
                p.estourar(m)

        # contato com inimigos
        for e in m.inimigos:
            if e.morrendo > 0 or not e.area_dano().colliderect(j.rect):
                continue
            if j.bloqueia(e.rect.centerx):
                sentido = 1 if e.rect.centerx >= j.rect.centerx else -1
                e.empurrar(10 * sentido)
                continue
            if j.receber_dano(e.rect.centerx, forca=e.dano_contato):
                self.audio.tocar("dano")
                e.ao_ferir_jogador()

        # itens
        for it in list(m.itens):
            if it.rect.colliderect(j.rect):
                self._coletar(it)

    def _coletar(self, it):
        j, m = self.jogador, self.mundo
        tipo = it.item_type
        if tipo == "Maca":
            if j.hearts < j.coracoes_maximos:
                j.hearts += 1
                j.score += 50
            else:
                j.score += 100
            self.audio.tocar("maca")
            m.emitir(it.rect.centerx, it.rect.centery, (255, 90, 90), n=10)
        elif tipo == "Estrela":
            j.stars = min(estrelas_maximas, j.stars + ganho_estrela)
            j.score += 20
            self.audio.tocar("estrela")
            m.emitir(it.rect.centerx, it.rect.centery, (120, 200, 255), n=10)
        else:
            j.flowers_collected += 1
            j.score += 30
            self.audio.tocar("flor")
            m.emitir(it.rect.centerx, it.rect.centery, (255, 150, 220), n=10)
            if j.flowers_collected == total_flores_easter_egg and not self.easter_feito:
                self.easter_feito = True
                self.easter_ativo = True
                self.easter_timer = 60 * 16                    # limite de segurança (a música tem ~14 s)
                self.musica_antes_egg = self.audio.musica_atual
                self.audio.tocar("easter_egg")
                self.audio.musica("easter_egg_musica.mp3", repetir=False)
        it.kill()

    # ------------------------------------------------------------------ recompensas
    def _recompensas(self):
        j, m = self.jogador, self.mundo
        for e in list(m.inimigos):
            if e.morrendo > 0 and not e.recompensado:
                e.recompensado = True
                j.score += e.pontos
                self.audio.tocar(e.enemy_type.lower() + "_morre")
                m.emitir(e.rect.centerx, e.rect.centery, (255, 220, 120), n=20, vel=5, vida=30)
                if e.enemy_type == "Boss":
                    self.boss_derrotado = True
                    for outro in m.inimigos:
                        if outro is not e and outro.morrendo == 0:
                            outro.morrendo = 26
                            outro.recompensado = True
                    m.proj_inimigos.empty()
                else:
                    # itens soltos são raros e somem depressa (tempo_item_dropado)
                    sorte = random.random()
                    y = min(e.rect.centery, m.chao_y - 30)
                    chance_maca = chance_drop_maca * (2.0 if j.hearts < j.coracoes_maximos else 0.5)
                    if sorte < chance_drop_estrela:
                        m.soltar_item("Estrela", e.rect.centerx, y, ttl=tempo_item_dropado)
                    elif sorte < chance_drop_estrela + chance_maca:
                        m.soltar_item("Maca", e.rect.centerx, y, ttl=tempo_item_dropado)
        # explosões do chefe morrendo
        for e in m.inimigos:
            if e.enemy_type == "Boss" and e.morrendo > 0 and self.frames % 3 == 0:
                m.emitir(e.rect.centerx + random.randint(-40, 40), e.rect.centery + random.randint(-50, 50),
                         random.choice([(255, 220, 120), (230, 120, 255), (255, 255, 255)]),
                         n=8, vel=5, vida=34, raio=5)

    def _eventos_do_mundo(self):
        m = self.mundo
        while m.eventos:
            nome, _ = m.eventos.pop(0)
            if nome == "boss_fase":
                pass    # espaço para falas/efeitos extras de cada fase do chefe

    def _dialogos_automaticos(self):
        m = self.mundo
        area = pygame.Rect(int(self.cam_x), 0, largura_tela, altura_tela)
        # a bruxa se apresenta (e avisa do sapo) na primeira vez que aparece, depois do banner da fase
        if "bruxa_intro" not in self.vistos and self.banner is None:
            if any(e.enemy_type == "Bruxa" and area.colliderect(e.rect) for e in m.inimigos):
                self.vistos.add("bruxa_intro")
                frases = falas.BRUXA_ABERTURA + [falas.BRUXA_PERSONALIZADA[self.escolhido], falas.BRUXA_FINAL]
                self._sequencia("bruxa_intro", "Bruxa", rec.rosto("bruxa"), frases)
        mapa = {"Planta": "planta", "Vespa": "vespa", "Boss": "boss"}
        for e in m.inimigos:
            chave = mapa.get(e.enemy_type)
            if chave and chave not in self.vistos and area.colliderect(e.rect):
                self.vistos.add(chave)
                self.falar(chave, 0)

    def _progresso_da_fase(self):
        j, m = self.jogador, self.mundo
        if self.fase_num < total_fases:
            vivos = [e for e in m.inimigos if e.morrendo == 0]
            if not vivos and not m.fase_limpa:
                m.fase_limpa = True
                m.limite_direito = m.largura + 260
                self.audio.tocar("fase_limpa")
            if m.fase_limpa and j.rect.centerx > m.largura + 20 and self.transicao is None:
                self._iniciar_fade(self.proxima_fase)
        else:
            if self.boss_derrotado and self.transicao is None \
                    and not any(e.enemy_type == "Boss" for e in m.inimigos):
                self.pontos_finais = j.score
                self._iniciar_fade(lambda: self.entrar_estado("vitoria"))

    # ------------------------------------------------------------------ desenho
    def desenhar_jogo(self):
        tela, m, j = self.tela, self.mundo, self.jogador
        cam = int(self.cam_x)

        self.cenario.desenhar(tela, cam)
        for p in m.plataformas:
            if not p.eh_chao and p.rect.right > cam and p.rect.left < cam + largura_tela:
                tela.blit(p.image, (p.rect.x - cam, p.rect.y + p.deslocamento_y))
        for it in m.itens:
            if not it.piscando:
                tela.blit(it.image, it.rect.move(-cam, 0))
        for n in m.npcs:
            img = n.image if j.rect.centerx >= n.rect.centerx else n.image_esq
            tela.blit(img, n.rect.move(-cam, 0))
            if n.perto(j) and self.dialogo.atual is None and not j.morta:
                tecla = self.controles.nome_acao("interagir").split(" / ")[0]
                r = texto(tela, "[%s] Falar com a Fada" % tecla, 26, (255, 245, 170),
                          (n.rect.centerx - cam, n.rect.top - 18), centro=True)
                pygame.draw.rect(tela, (255, 245, 170), r.inflate(14, 8), 2, border_radius=6)
        for e in m.inimigos:
            if e.rect.right > cam - 100 and e.rect.left < cam + largura_tela + 100:
                e.desenhar(tela, cam)
                e.desenhar_barra_vida(tela, cam)

        if j.morta:
            self._desenhar_jogadora_morta(cam)
        else:
            j.desenhar(tela, cam)

        for p in m.proj_jogador:
            tela.blit(p.image, p.image.get_rect(center=(p.rect.centerx - cam, p.rect.centery)))
        for p in m.proj_inimigos:
            tela.blit(p.image, p.image.get_rect(center=(p.rect.centerx - cam, p.rect.centery)))
        m.desenhar_particulas(tela, cam)

        # Meliah: tela arroxeada + relógio
        if j.tipo_personagem == "Meliah" and j.special_active and not j.eh_sapinho:
            if not hasattr(self, "_veu_meliah"):
                self._veu_meliah = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
                self._veu_meliah.fill((120, 90, 200, 55))
                if self.relogio_img is not None:
                    self._relogio_transp = self.relogio_img.copy()
                    self._relogio_transp.set_alpha(150)
            tela.blit(self._veu_meliah, (0, 0))
            if self.relogio_img is not None:
                r = self._relogio_transp
                tela.blit(r, r.get_rect(midtop=(largura_tela // 2, 70)))

        # HUD
        vivos = [e for e in m.inimigos if e.morrendo == 0]
        boss = next((e for e in vivos if e.enemy_type == "Boss"), None)
        setas = []
        if self.fase_num < total_fases and not m.fase_limpa and len(vivos) <= 3:
            for e in vivos:
                if e.rect.right < cam:
                    setas.append(-1)
                elif e.rect.left > cam + largura_tela:
                    setas.append(1)
        info = {
            "nome_fase": falas.NOMES_FASES[self.fase_num], "numero": self.fase_num,
            "limpa": m.fase_limpa, "inimigos": len(vivos), "tempo": m.tempo,
            "boss": boss, "setas": list(set(setas)),
            "tecla_poder": self.controles.nome_acao("poder"),
        }
        if self.fase_num < total_fases:
            info["nome_fase"] = ("Fase %d/%d" % (self.fase_num, total_fases), falas.NOMES_FASES[self.fase_num][1])
        self.hud.desenhar(tela, j, info)

        # seta grande quando a fase está limpa
        if m.fase_limpa and self.fase_num < total_fases and (m.tempo // 20) % 2 == 0:
            y = altura_tela // 2 - 40
            pygame.draw.polygon(tela, (255, 255, 160),
                                [(largura_tela - 20, y), (largura_tela - 70, y - 30), (largura_tela - 70, y + 30)])

        self.dialogo.desenhar(tela)
        self._desenhar_banner()
        self._desenhar_easter_egg()

        if self.pausado:
            escurecer(tela, 170)
            texto(tela, "PAUSADO", 80, (255, 240, 255), (largura_tela // 2, 190), centro=True)
            texto(tela, "Esc / Enter: continuar", 34, (230, 220, 245), (largura_tela // 2, 280), centro=True)
            texto(tela, "M: voltar ao menu", 34, (230, 220, 245), (largura_tela // 2, 320), centro=True)
            cn = self.controles.nome_acao
            controles = ["Andar: %s e %s    Pular: %s    Descer da plataforma: %s" % (
                             cn("esquerda"), cn("direita"), cn("pular"), cn("descer")),
                         "Atirar (segure): %s    Poder especial: %s" % (cn("atirar"), cn("poder")),
                         "Falar com a Fada / avançar falas: %s    Pausar: %s ou Esc" % (cn("interagir"), cn("pausar")),
                         "(para mudar as teclas: menu principal > Opções)"]
            for i, c in enumerate(controles):
                texto(tela, c, 26, (200, 190, 220), (largura_tela // 2, 400 + i * 28), centro=True)

        if self.transicao is not None:
            v = pygame.Surface((largura_tela, altura_tela))
            v.fill((0, 0, 0))
            v.set_alpha(int(max(0, min(255, self.transicao["alpha"]))))
            tela.blit(v, (0, 0))

    def _desenhar_jogadora_morta(self, cam):
        j = self.jogador
        img = None
        if j.sprites:
            img = j.sprites.get("sapo_morto_dir" if j.face > 0 else "sapo_morto_esq")
        r = j.rect.move(-cam, 0)
        if img is not None:
            self.tela.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom + 4)))
        else:
            pygame.draw.rect(self.tela, (120, 60, 80), r)

    def _desenhar_banner(self):
        if not self.banner:
            return
        titulo, sub, restante = self.banner
        alfa = max(0.0, min(1.0, restante / 30.0, (170 - restante) / 20.0))
        faixa = pygame.Surface((largura_tela, 110), pygame.SRCALPHA)
        faixa.fill((20, 10, 40, int(170 * alfa)))
        self.tela.blit(faixa, (0, 150))
        for txt, tam, cor, dy in ((titulo, 40, (255, 225, 140), 185), (sub, 56, (255, 255, 255), 232)):
            img = fonte(tam).render(txt, True, cor)
            img.set_alpha(int(255 * alfa))
            self.tela.blit(img, img.get_rect(center=(largura_tela // 2, dy)))

    def _desenhar_easter_egg(self):
        if not self.easter_ativo or not self.gnomos:
            return
        quadro = self.gnomos[(self.frames // 6) % len(self.gnomos)]
        self.tela.blit(quadro, quadro.get_rect(midbottom=(largura_tela // 2, altura_tela - 6)))
        texto(self.tela, "Você achou as 20 flores! Os gnomos fazem uma dancinha!", 34, (255, 210, 240),
              (largura_tela // 2, 110), centro=True)

    # ================================================================== DERROTA
    def estado_derrota(self, eventos):
        for ev in eventos:
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
                    self.carregar_fase(self.fase_num, tentativa=True)
                    self.estado = "jogando"
                    return
                if ev.key in (pygame.K_ESCAPE, pygame.K_m):
                    self.entrar_estado("menu")
                    return
        self.tela.fill((15, 8, 25))
        j = self.jogador
        img = j.sprites.get("sapo_morto_dir") if j and j.sprites else None
        if img is not None:
            img = rec.escalar_altura(img, 200)
            self.tela.blit(img, img.get_rect(center=(largura_tela // 2, 190)))
        texto(self.tela, "Game Over", 90, (255, 130, 150), (largura_tela // 2, 340), centro=True)
        texto(self.tela, "A Ametista ainda precisa de você...", 34, (230, 215, 245), (largura_tela // 2, 400), centro=True)
        texto(self.tela, "Enter: tentar a fase de novo      Esc: menu", 32, (255, 240, 170),
              (largura_tela // 2, 470), centro=True)

    # ================================================================== VITÓRIA
    def estado_vitoria(self, eventos):
        for ev in eventos:
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self.voltar_para = "menu"
                self.entrar_estado("creditos")
                return
        self._fundo_menu(130)
        texto(self.tela, "Vitória!", 90, (255, 235, 140), (largura_tela // 2, 70), centro=True)
        if self.ametista is not None:
            a = self.ametista
            self.tela.blit(a, a.get_rect(center=(largura_tela // 2, 250 + int(6 * math.sin(self.frames * 0.05)))))
        tipo = self.escolhido
        frase = falas.FALAS[tipo]["vitoria"]
        y = 410
        for linha in quebrar_texto('%s: "%s"' % (falas.NOME_EXIBIDO[tipo], frase), 34, 860):
            texto(self.tela, linha, 34, (255, 255, 255), (largura_tela // 2, y), centro=True)
            y += 34
        j = self.jogador
        if j is not None:
            texto(self.tela, "Pontos: %d    Flores: %d/%d" % (j.score, j.flowers_collected, total_flores_easter_egg),
                  30, (255, 225, 160), (largura_tela // 2, 505), centro=True)
        texto(self.tela, "Enter: continuar", 26, (210, 200, 230), (largura_tela // 2, 545), centro=True)

    # ================================================================== CRÉDITOS
    def estado_creditos(self, eventos):
        for ev in eventos:
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                self.entrar_estado("menu")
                return
        linhas = [("THE TALE OF AN AMETHYST", 60, (255, 235, 140)), ("", 30, None),
                  ("Obrigada por jogar!", 38, (255, 255, 255)), ("", 30, None)]
        if self.pontos_finais is not None:
            linhas += [("Pontuação final: %d" % self.pontos_finais, 36, (255, 225, 160)), ("", 30, None)]
        linhas += [("Arte, roteiro e programação", 34, (225, 170, 255)),
                   ("equipe do projeto", 30, (255, 255, 255)), ("", 30, None),
                   ("Músicas", 40, (225, 170, 255))]
        for cena, obra in falas.CREDITOS_MUSICAS:
            linhas += [(cena, 28, (255, 225, 160)), (obra, 28, (255, 255, 255)), ("", 14, None)]
        linhas += [("", 60, None), ("Fim", 50, (255, 235, 140))]

        self.creditos_y -= 0.9
        self._fundo_menu(150)
        y = self.creditos_y
        for (txt, tam, cor) in linhas:
            if txt and -50 < y < altura_tela + 20:
                texto(self.tela, txt, tam, cor, (largura_tela // 2, int(y)), centro=True)
            y += tam + 12
        if y < 0:
            self.entrar_estado("menu")
