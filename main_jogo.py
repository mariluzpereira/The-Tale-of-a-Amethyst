import math
import random
import pygame

import falas
import recursos as rec
from configuracoes import (
    largura_tela, altura_tela, fps, cor_fundo, nomes_arquivo, cor_particula,
    escala_tempo_congelado, custo_poder, total_fases, total_flores_easter_egg, estrelas_maximas,
)
from sons import Audio
from jogador import jogador
from mundo import Mundo
from fases import construir_fase
from interface import (
    HUD, CaixaDialogo, texto, fonte, quebrar_texto, cobrir, escurecer, desenhar_botao,
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
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.tela = pygame.display.set_mode((largura_tela, altura_tela))
        pygame.display.set_caption("The Tale of an Amethyst")
        self.relogio = pygame.time.Clock()
        self.rodando = True
        self.frames = 0

        self.audio = Audio()
        self.hud = HUD()
        self.dialogo = CaixaDialogo()
        self._carregar_imagens()

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
        self.entrar_estado("menu")

    # ------------------------------------------------------------------ recursos
    def _carregar_imagens(self):
        casa = rec.imagem_opaca("casa_fada.jpg")
        self.bg_menu = cobrir(casa, largura_tela, altura_tela) if casa is not None else None

        painel = rec.imagem("menu.png")
        self.painel = None
        self.miolo = pygame.Rect(262, 180, 500, 280)
        if painel is not None:
            p = rec.recortar(painel)
            altura = 540
            largura = int(p.get_width() * altura / p.get_height())
            self.painel = pygame.transform.scale(p, (largura, altura))
            pr = self.painel.get_rect(center=(largura_tela // 2, altura_tela // 2))
            self.painel_pos = pr.topleft
            # região lisa (roxa) no meio do painel, medida na imagem original
            self.miolo = pygame.Rect(pr.x + 0.073 * largura, pr.y + 0.243 * altura,
                                     0.854 * largura, 0.512 * altura)

        self.botoes_img = {}
        for nome, arq in (("Jogar", "jogar.png"), ("Opções", "opcoes.png"), ("Créditos", "creditos.png")):
            im = rec.imagem(arq)
            self.botoes_img[nome] = rec.escalar_altura(rec.recortar(im), 40) if im is not None else None
        self.botoes_img["Sair"] = None

        amet = rec.imagem("extras/ametista_pequena.png")
        if amet is None:
            grande = rec.imagem("ametista(1).png")
            amet = rec.escalar_altura(rec.recortar(grande), 300, suave=True) if grande is not None else None
        self.ametista = amet

        rel = rec.imagem("extras/relogio_congelar.png")
        self.relogio_img = rec.escalar_largura(rel, 150, suave=True) if rel is not None else None

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
            r.center = (self.miolo.centerx, self.miolo.top + 124 + i * 46)
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

        self._fundo_menu(40)
        if self.painel is not None:
            self.tela.blit(self.painel, self.painel_pos)
        else:
            pygame.draw.rect(self.tela, (95, 53, 165), self.miolo)
        texto(self.tela, "The Tale of", 46, (255, 240, 255), (self.miolo.centerx, self.miolo.top + 26), centro=True)
        texto(self.tela, "an Amethyst", 52, (225, 170, 255), (self.miolo.centerx, self.miolo.top + 66), centro=True)
        for i, (nome, r) in enumerate(zip(self.ITENS_MENU, rects)):
            desenhar_botao(self.tela, self.botoes_img.get(nome), nome.upper(), r.center, i == self.menu_sel)

    # ================================================================== OPÇÕES
    def estado_opcoes(self, eventos):
        for ev in eventos:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.entrar_estado("menu")
                    return
                if ev.key in (pygame.K_UP, pygame.K_w):
                    self.opcao_sel = (self.opcao_sel - 1) % 3
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    self.opcao_sel = (self.opcao_sel + 1) % 3
                elif ev.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                    passo = 0.1 if ev.key in (pygame.K_RIGHT, pygame.K_d) else -0.1
                    if self.opcao_sel == 0:
                        self.audio.definir_volume_musica(self.audio.volume_musica + passo)
                    elif self.opcao_sel == 1:
                        self.audio.definir_volume_sfx(self.audio.volume_sfx + passo)
                        self.audio.tocar("item")
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE) and self.opcao_sel == 2:
                    self.entrar_estado("menu")
                    return

        self._fundo_menu(120)
        texto(self.tela, "Opções", 64, (255, 240, 255), (largura_tela // 2, 90), centro=True)
        linhas = [("Volume da música", self.audio.volume_musica),
                  ("Volume dos efeitos", self.audio.volume_sfx), ("Voltar", None)]
        for i, (nome, valor) in enumerate(linhas):
            y = 200 + i * 80
            cor = (255, 255, 160) if i == self.opcao_sel else (230, 220, 245)
            texto(self.tela, nome, 40, cor, (240, y))
            if valor is not None:
                pygame.draw.rect(self.tela, (50, 30, 80), (520, y + 6, 260, 22), border_radius=6)
                pygame.draw.rect(self.tela, (200, 140, 255), (520, y + 6, int(260 * valor), 22), border_radius=6)
                texto(self.tela, "%d%%" % round(valor * 100), 30, cor, (800, y + 4))
            if i == self.opcao_sel:
                pygame.draw.polygon(self.tela, (255, 255, 160), [(210, y + 16), (196, y + 6), (196, y + 26)])
        texto(self.tela, "Setas: escolher / ajustar    Esc: voltar", 26, (200, 190, 220),
              (largura_tela // 2, altura_tela - 40), centro=True)

    # ================================================================== SELEÇÃO DE PERSONAGEM
    def _rects_cartas(self):
        larg, alt, esp = 218, 330, 20
        x0 = (largura_tela - (4 * larg + 3 * esp)) // 2
        return [pygame.Rect(x0 + i * (larg + esp), 70, larg, alt) for i in range(4)]

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
                img = rec.escalar_altura(rosto, 190, suave=True)
                if img.get_width() > 190:
                    img = rec.escalar_largura(img, 190, suave=True)
                self.tela.blit(img, img.get_rect(midbottom=(r.centerx, r.top + 215)))
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
        self.tela.blit(caixa, (60, 425))
        texto(self.tela, "%s: %s" % (falas.NOME_EXIBIDO[tipo], frase), 32, (255, 255, 255),
              (largura_tela // 2, 460), centro=True)
        if not self.sel_confirmado:
            texto(self.tela, "Setas / mouse para escolher    Enter ou clique para confirmar", 26,
                  (210, 200, 230), (largura_tela // 2, 520), centro=True)
        else:
            texto(self.tela, "Preparando a jornada...", 30, (255, 240, 170),
                  (largura_tela // 2, 520), centro=True)

    # ================================================================== PRÓLOGO
    def _montar_prologo(self):
        self.prologo_linhas = []
        for par in falas.HISTORIA:
            self.prologo_linhas += quebrar_texto(par, 34, 780)
            self.prologo_linhas.append("")
        self.prologo_altura = len(self.prologo_linhas) * 40

    def estado_prologo(self, eventos):
        acelerar = False
        for ev in eventos:
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                    self.iniciar_jogo()
                    return
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            acelerar = True
        self.prologo_y -= 2.4 if acelerar else 0.6
        if self.prologo_y + self.prologo_altura < 60:
            self.iniciar_jogo()
            return

        self._fundo_menu(150)
        y = int(self.prologo_y)
        for linha in self.prologo_linhas:
            if -40 < y < altura_tela:
                texto(self.tela, linha, 34, (255, 245, 255), (largura_tela // 2, y), centro=True)
            y += 40
        texto(self.tela, "Enter: pular    Seta p/ baixo: acelerar", 24, (200, 190, 220),
              (largura_tela // 2, altura_tela - 22), centro=True)

    # ================================================================== INÍCIO DO JOGO / FASES
    def iniciar_jogo(self):
        self.jogador = None
        self.vistos = set()
        self.dialogo.limpar()
        self.dialogo.ultimo.clear()
        self.energia_baixa_avisada = False
        self.easter_timer = 0
        self.easter_feito = False
        self.carregar_fase(1)
        self.estado = "jogando"

    def carregar_fase(self, numero, tentativa=False):
        self.fase_num = numero
        self.mundo = Mundo(self.audio)
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

    def usar_poder(self):
        j = self.jogador
        r = j.use_special(self.mundo)
        if r == "ok":
            self.falar("habilidade", 900)
            if j.stars < custo_poder:
                self.falar("pouca_energia", 480)
                self.energia_baixa_avisada = True
        elif r == "sem_energia":
            self.falar("pouca_energia", 300)

    def _iniciar_fade(self, acao):
        self.transicao = {"modo": "escurecendo", "alpha": 0, "acao": acao}

    # ================================================================== LOOP DA FASE
    def estado_jogando(self, eventos):
        for ev in eventos:
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_p):
                    self.pausado = not self.pausado
                elif self.pausado and ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.pausado = False
                elif self.pausado and ev.key == pygame.K_m:
                    self.audio.parar_musica()
                    self.entrar_estado("menu")
                    return
                elif ev.key == pygame.K_e:
                    self.dialogo.fechar()
            elif (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 3 and not self.pausado
                  and self.transicao is None and not self.jogador.morta):
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
            if controle and pygame.mouse.get_pressed()[0] and not self.pausado:
                mx, my = pygame.mouse.get_pos()
                j.atirar((mx + int(self.cam_x), my), m.proj_jogador, m)

        if j.stars >= custo_poder:
            self.energia_baixa_avisada = False

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

        # ---- easter egg
        if self.easter_timer > 0:
            self.easter_timer -= 1

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
                        self.audio.tocar("acerto")
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
                if j.receber_dano(p.rect.centerx):
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
            if j.receber_dano(e.rect.centerx):
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
            j.stars = min(estrelas_maximas, j.stars + 25)
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
                self.easter_timer = 420
                self.audio.tocar("easter_egg")
        it.kill()

    # ------------------------------------------------------------------ recompensas
    def _recompensas(self):
        j, m = self.jogador, self.mundo
        for e in list(m.inimigos):
            if e.morrendo > 0 and not e.recompensado:
                e.recompensado = True
                j.score += e.pontos
                self.audio.tocar("inimigo_morre")
                m.emitir(e.rect.centerx, e.rect.centery, (255, 220, 120), n=20, vel=5, vida=30)
                if e.enemy_type == "Boss":
                    self.boss_derrotado = True
                    self.audio.tocar("boss_rugido")
                    for outro in m.inimigos:
                        if outro is not e and outro.morrendo == 0:
                            outro.morrendo = 26
                            outro.recompensado = True
                    m.proj_inimigos.empty()
                else:
                    sorte = random.random()
                    y = min(e.rect.centery, m.chao_y - 30)
                    if sorte < 0.40:
                        m.soltar_item("Estrela", e.rect.centerx, y)
                    elif sorte < (0.62 if j.hearts < j.coracoes_maximos else 0.50):
                        m.soltar_item("Maca", e.rect.centerx, y)
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
            tela.blit(it.image, it.rect.move(-cam, 0))
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
            v = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
            v.fill((120, 90, 200, 55))
            tela.blit(v, (0, 0))
            if self.relogio_img is not None:
                r = self.relogio_img.copy()
                r.set_alpha(150)
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
            controles = ["A / D: mover    W / Espaço: pular    S: descer das plataformas",
                         "Mouse esquerdo: atirar (segure)    Mouse direito: poder especial",
                         "E: fechar legenda"]
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
        if self.easter_timer <= 0 or not self.gnomos:
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
