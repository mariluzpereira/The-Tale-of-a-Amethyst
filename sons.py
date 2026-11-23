"""Áudio do jogo.

* Músicas: arquivos do projeto (menu.mp3, combate.mp3, easter_egg_musica.mp3...).
* Efeitos sonoros: gerados por código na 1ª vez e guardados em 'sfx_cache/'
  (nas próximas vezes carregam na hora). Para usar um som seu, coloque
  sfx_<nome>.wav (ou .ogg) na pasta do jogo: ele tem prioridade.
* Dublagem: dublagem/<personagem>_<fala>.ogg toca junto com a legenda.

Cuidados contra chiado/travamento:
  - buffer do mixer maior (ver main_jogo: pre_init com 2048);
  - sons iguais não se empilham (intervalo mínimo entre repetições);
  - volumes padrão com margem, porque as músicas já vêm no volume máximo.
"""
import array
import math
import os
import random
import wave
import pygame
from configuracoes import pasta_base, volume_musica_padrao, volume_sfx_padrao
from recursos import achar

VERSAO_CACHE = "v4"
PASTA_CACHE = os.path.join(pasta_base, "sfx_cache_" + VERSAO_CACHE)

# intervalo mínimo (ms) entre duas execuções do mesmo efeito
INTERVALO_MS = {"passo": 160, "dialogo": 55, "acerto": 50, "tiro": 60, "item": 50}
INTERVALO_PADRAO = 45


class Audio:
    def __init__(self, progresso=None):
        self.ativo = False
        self.musica_atual = None
        self.volume_musica = volume_musica_padrao
        self.volume_sfx = volume_sfx_padrao
        self.sfx = {}
        self.vozes = {}
        self._ultimo = {}
        self._extra = None              # trilha curta tocada POR CIMA (música pausada)
        self._canal_extra = None
        self.taxa = 44100
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 2, 2048)
            self.taxa = pygame.mixer.get_init()[0]
            try:
                pygame.mixer.set_num_channels(24)
            except pygame.error:
                pass
            self.ativo = True
        except pygame.error:
            self.ativo = False
        if self.ativo:
            self._gerar_efeitos(progresso)

    # ------------------------------------------------------------ síntese
    def _onda(self, f0, f1, dur, vol=0.4, tipo="seno", ruido=0.0, vibrato=0.0):
        taxa = self.taxa
        n = max(1, int(taxa * dur))
        amostras = []
        fase = 0.0
        for i in range(n):
            t = i / n
            f = f0 + (f1 - f0) * t
            if vibrato:
                f *= 1.0 + vibrato * math.sin(i * 0.16 * 44100.0 / taxa)
            fase += 2 * math.pi * f / taxa
            if tipo == "quadrada":
                v = 1.0 if math.sin(fase) >= 0 else -1.0
            elif tipo == "serra":
                v = 2.0 * ((fase / (2 * math.pi)) % 1.0) - 1.0
            else:
                v = math.sin(fase)
            if ruido:
                v = v * (1.0 - ruido) + random.uniform(-1, 1) * ruido
            ataque = min(1.0, i / (taxa * 0.004))
            env = ataque * (1.0 - t) ** 1.4
            amostras.append(v * env * vol)
        return amostras

    def _sequencia(self, notas, dur, vol=0.35, tipo="quadrada"):
        total = []
        for f in notas:
            total += self._onda(f, f, dur, vol, tipo)
        return total

    def _silencio(self, dur):
        return [0.0] * int(self.taxa * dur)

    def _buffer(self, amostras):
        canais = pygame.mixer.get_init()[2]
        buf = array.array("h")
        for a in amostras:
            s = int(max(-1.0, min(1.0, a)) * 32767)
            for _ in range(canais):
                buf.append(s)
        return buf, canais

    def _criar(self, amostras, nome):
        buf, canais = self._buffer(amostras)
        # guarda em disco para a próxima abertura do jogo ser instantânea
        try:
            os.makedirs(PASTA_CACHE, exist_ok=True)
            with wave.open(os.path.join(PASTA_CACHE, nome + ".wav"), "wb") as w:
                w.setnchannels(canais)
                w.setsampwidth(2)
                w.setframerate(self.taxa)
                w.writeframes(buf.tobytes())
        except (OSError, wave.Error):
            pass
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def _receitas(self):
        o, seq, sil = self._onda, self._sequencia, self._silencio
        r = {
            # --- movimento
            "pulo": lambda: o(280, 620, 0.13, 0.25, "quadrada"),
            "pulo_sapo": lambda: o(200, 520, 0.12, 0.25, "seno", vibrato=0.1),
            "passo": lambda: o(220, 130, 0.045, 0.14, "seno", ruido=0.85),
            "pouso": lambda: o(160, 70, 0.09, 0.22, "seno", ruido=0.6),
            # --- tiros de cada princesa
            "tiro": lambda: o(1000, 350, 0.10, 0.22, "serra"),
            "tiro_safira": lambda: o(1150, 420, 0.10, 0.22, "seno", vibrato=0.05),
            "tiro_louise": lambda: o(900, 260, 0.11, 0.22, "serra", ruido=0.1),
            "tiro_anika": lambda: o(780, 520, 0.10, 0.22, "quadrada"),
            "tiro_meliah": lambda: o(1250, 700, 0.12, 0.20, "seno", vibrato=0.1),
            # --- acertos e mortes por tipo de inimigo
            "acerto": lambda: o(260, 90, 0.12, 0.35, "quadrada", ruido=0.5),
            "acerto_planta": lambda: o(230, 120, 0.10, 0.30, "serra", ruido=0.4),
            "acerto_bruxa": lambda: o(520, 300, 0.10, 0.25, "quadrada"),
            "acerto_vespa": lambda: o(900, 500, 0.07, 0.25, "serra"),
            "acerto_boss": lambda: o(130, 70, 0.14, 0.38, "serra", ruido=0.35),
            "inimigo_morre": lambda: o(700, 60, 0.38, 0.35, "serra", ruido=0.25),
            "planta_morre": lambda: o(320, 60, 0.38, 0.30, "serra", ruido=0.5),
            "bruxa_morre": lambda: seq([620, 520, 420, 320, 220], 0.08, 0.22, "quadrada"),
            "vespa_morre": lambda: o(850, 90, 0.30, 0.25, "serra", ruido=0.3),
            "boss_morre": lambda: o(110, 35, 1.3, 0.42, "serra", ruido=0.4),
            # --- jogadora
            "dano": lambda: o(180, 55, 0.30, 0.40, "quadrada", ruido=0.4),
            "coracao_baixo": lambda: o(75, 60, 0.12, 0.30, "seno") + sil(0.12) + o(75, 60, 0.12, 0.30, "seno"),
            "sapo": lambda: o(420, 160, 0.40, 0.35, "quadrada", vibrato=0.25),
            "destransforma": lambda: seq([300, 450, 600, 900], 0.06, 0.30),
            "bloqueio": lambda: o(1200, 800, 0.08, 0.30, "quadrada"),
            "poder_safira": lambda: o(300, 950, 0.55, 0.28, "seno", vibrato=0.04),
            "poder_louise": lambda: o(180, 700, 0.60, 0.28, "serra", ruido=0.15),
            "poder_anika": lambda: o(420, 840, 0.40, 0.28, "quadrada"),
            "poder_meliah": lambda: o(900, 180, 0.65, 0.30, "seno", vibrato=0.06),
            "poder_pronto": lambda: seq([880, 1320], 0.06, 0.22, "seno"),
            "sem_energia": lambda: seq([300, 220], 0.08, 0.25, "quadrada"),
            # --- itens
            "item": lambda: o(700, 1400, 0.12, 0.30),
            "maca": lambda: seq([520, 660, 880], 0.07, 0.30, "seno"),
            "estrela": lambda: seq([880, 1180, 1480], 0.05, 0.28, "seno"),
            "flor": lambda: seq([660, 990], 0.06, 0.28, "seno"),
            "item_surge": lambda: o(500, 900, 0.10, 0.18, "seno"),
            "gnomo_aparece": lambda: o(900, 620, 0.12, 0.07, "seno", ruido=0.6),   # farfalhar baixinho
            "easter_egg": lambda: seq([523, 659, 784, 659, 784, 1047], 0.09, 0.30, "seno"),
            # --- inimigos
            "pocao_lancada": lambda: o(300, 520, 0.18, 0.22, "seno"),
            "quebra": lambda: o(900, 200, 0.18, 0.35, "serra", ruido=0.7),
            "planta_morde": lambda: o(160, 420, 0.10, 0.35, "serra", ruido=0.5),
            "bruxa_ri": lambda: seq([520, 440, 520, 440], 0.07, 0.22, "quadrada"),
            "vespa": lambda: o(240, 200, 0.22, 0.18, "quadrada", ruido=0.2, vibrato=0.15),
            "boss_tiro": lambda: o(200, 120, 0.25, 0.30, "serra", ruido=0.15),
            "boss_fogo": lambda: o(260, 80, 0.35, 0.33, "serra", ruido=0.5),
            "boss_rugido": lambda: o(95, 55, 0.85, 0.45, "serra", ruido=0.3),
            "boss_investida": lambda: o(150, 600, 0.35, 0.35, "serra", ruido=0.2),
            # --- fases, falas e menus
            "fase_limpa": lambda: seq([523, 659, 784, 1047], 0.11, 0.30),
            "fase_nova": lambda: seq([392, 523, 659], 0.09, 0.28),
            "fada": lambda: seq([1047, 1319, 1568, 2093], 0.06, 0.18, "seno"),
            "dialogo": lambda: o(520, 540, 0.025, 0.10, "quadrada"),
            "dialogo_proximo": lambda: seq([600, 760], 0.04, 0.18, "quadrada"),
            "menu": lambda: o(600, 800, 0.06, 0.22, "quadrada"),
            "selecionar": lambda: seq([523, 784], 0.07, 0.28),
            "ui_voltar": lambda: seq([620, 420], 0.05, 0.22, "quadrada"),
            "ui_erro": lambda: seq([260, 200], 0.07, 0.25, "quadrada"),
            "tecla_ok": lambda: seq([700, 900, 1100], 0.04, 0.22, "seno"),
            "pausa": lambda: seq([520, 380], 0.06, 0.22, "quadrada"),
            "retomar": lambda: seq([380, 520], 0.06, 0.22, "quadrada"),
        }
        return r

    def _gerar_efeitos(self, progresso=None):
        receitas = self._receitas()
        total = len(receitas)
        for i, (nome, fabrica) in enumerate(receitas.items()):
            # prioridade: arquivo do usuário > cache em disco > gerar agora
            caminho = achar("sfx_%s.wav" % nome) or achar("sfx_%s.ogg" % nome)
            if not caminho:
                em_cache = os.path.join(PASTA_CACHE, nome + ".wav")
                caminho = em_cache if os.path.exists(em_cache) else None
            try:
                if caminho:
                    self.sfx[nome] = pygame.mixer.Sound(caminho)
                else:
                    self.sfx[nome] = self._criar(fabrica(), nome)
            except (pygame.error, TypeError, ValueError, OSError):
                pass
            if progresso and i % 4 == 0:
                progresso((i + 1) / float(total))
        self._aplicar_volume_sfx()

    # ------------------------------------------------------------ efeitos
    def _aplicar_volume_sfx(self):
        for s in self.sfx.values():
            s.set_volume(self.volume_sfx)

    def tocar(self, nome):
        """Toca um efeito. Se o efeito específico não existir, tenta o genérico
        (ex.: 'acerto_planta' -> 'acerto')."""
        if not self.ativo:
            return
        s = self.sfx.get(nome)
        if s is None and "_" in nome:
            nome = nome.split("_")[0]
            s = self.sfx.get(nome)
        if s is None:
            return
        agora = pygame.time.get_ticks()
        if agora - self._ultimo.get(nome, -10 ** 6) < INTERVALO_MS.get(nome, INTERVALO_PADRAO):
            return                       # evita empilhar o mesmo som (causa estalos)
        self._ultimo[nome] = agora
        s.play()

    def voz(self, personagem, fala):
        """Toca a dublagem da fala se o arquivo existir."""
        if not self.ativo:
            return
        chave = (personagem, fala)
        if chave not in self.vozes:
            nome = "%s_%s" % (personagem.lower(), fala)
            caminho = achar("dublagem/%s.ogg" % nome) or achar("dublagem/%s.wav" % nome) \
                or achar("dublagem/%s.mp3" % nome)
            try:
                self.vozes[chave] = pygame.mixer.Sound(caminho) if caminho else None
            except pygame.error:
                self.vozes[chave] = None
        som = self.vozes[chave]
        if som is not None:
            som.set_volume(min(1.0, self.volume_sfx + 0.3))
            som.play()

    # ------------------------------------------------------------ música
    def musica(self, arquivo, repetir=True):
        if not self.ativo or arquivo == self.musica_atual:
            return
        caminho = achar(arquivo)
        if not caminho:
            return
        try:
            pygame.mixer.music.load(caminho)
            pygame.mixer.music.set_volume(self.volume_musica)
            pygame.mixer.music.play(-1 if repetir else 0)
            self.musica_atual = arquivo
        except pygame.error:
            self.musica_atual = None

    def tocando(self):
        """True enquanto a música atual ainda está tocando."""
        return bool(self.ativo and pygame.mixer.music.get_busy())

    def parar_musica(self):
        if self.ativo:
            pygame.mixer.music.stop()
        self.musica_atual = None

    # ---- trilha extra: toca um arquivo por cima enquanto a música da fase fica em pausa
    # e continua exatamente de onde parou quando a trilha extra termina (easter egg do gnomo).
    def iniciar_trilha_extra(self, arquivo):
        """Devolve True se conseguiu. Se não der (arquivo/codec), o chamador usa musica()."""
        if not self.ativo:
            return False
        caminho = achar(arquivo)
        if not caminho:
            return False
        try:
            som = pygame.mixer.Sound(caminho)
        except pygame.error:
            return False
        pygame.mixer.music.pause()
        self._extra = som
        som.set_volume(self.volume_musica)
        self._canal_extra = som.play()
        return True

    def trilha_extra_tocando(self):
        return bool(self._canal_extra is not None and self._canal_extra.get_busy())

    def volume_trilha_extra(self, fator):
        if self._extra is not None:
            self._extra.set_volume(self.volume_musica * max(0.0, min(1.0, fator)))

    def parar_trilha_extra(self):
        """Para a trilha extra e retoma a música pausada de onde estava."""
        if self._extra is None:
            return
        self._extra.stop()
        self._extra = None
        self._canal_extra = None
        if self.ativo:
            pygame.mixer.music.unpause()

    def volume_temporario(self, fator):
        """Baixa/sobe o volume da música sem mexer na configuração (usado para sumir aos poucos).
        Não trava o jogo, ao contrário de mixer.music.fadeout()."""
        if self.ativo:
            pygame.mixer.music.set_volume(self.volume_musica * max(0.0, min(1.0, fator)))

    def definir_volume_musica(self, v):
        self.volume_musica = max(0.0, min(1.0, v))
        if self.ativo:
            pygame.mixer.music.set_volume(self.volume_musica)

    def definir_volume_sfx(self, v):
        self.volume_sfx = max(0.0, min(1.0, v))
        self._aplicar_volume_sfx()
