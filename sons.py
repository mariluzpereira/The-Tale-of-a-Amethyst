"""Áudio do jogo.

* Músicas: usa os arquivos que já estão no projeto (menu.mp3, combate.mp3...).
* Efeitos sonoros: gerados por código (ondas simples), então o jogo já tem
  som mesmo sem nenhum arquivo .wav. Se quiser trocar por sons reais, basta
  colocar um arquivo  sfx_<nome>.wav  na pasta (ex.: sfx_pulo.wav).
* Dublagem: se existir  dublagem/<personagem>_<fala>.ogg  ela toca junto com
  a legenda (ex.: dublagem/anika_planta.ogg).
"""
import array
import math
import random
import pygame
from recursos import achar

TAXA = 44100


class Audio:
    def __init__(self):
        self.ativo = False
        self.musica_atual = None
        self.volume_musica = 0.5
        self.volume_sfx = 0.6
        self.sfx = {}
        self.vozes = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(TAXA, -16, 2, 512)
            self.ativo = True
        except pygame.error:
            self.ativo = False
        if self.ativo:
            self._gerar_efeitos()

    # ------------------------------------------------------------ síntese
    def _onda(self, f0, f1, dur, vol=0.4, tipo="seno", ruido=0.0, vibrato=0.0):
        n = max(1, int(TAXA * dur))
        amostras = []
        fase = 0.0
        for i in range(n):
            t = i / n
            f = f0 + (f1 - f0) * t
            if vibrato:
                f *= 1.0 + vibrato * math.sin(i * 0.004 * 40)
            fase += 2 * math.pi * f / TAXA
            if tipo == "quadrada":
                v = 1.0 if math.sin(fase) >= 0 else -1.0
            elif tipo == "serra":
                v = 2.0 * ((fase / (2 * math.pi)) % 1.0) - 1.0
            else:
                v = math.sin(fase)
            if ruido:
                v = v * (1.0 - ruido) + random.uniform(-1, 1) * ruido
            ataque = min(1.0, i / (TAXA * 0.004))
            env = ataque * (1.0 - t) ** 1.4
            amostras.append(v * env * vol)
        return amostras

    def _criar(self, amostras):
        canais = pygame.mixer.get_init()[2]
        buf = array.array("h")
        for a in amostras:
            s = int(max(-1.0, min(1.0, a)) * 32767)
            for _ in range(canais):
                buf.append(s)
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def _sequencia(self, notas, dur, vol=0.35, tipo="quadrada"):
        total = []
        for f in notas:
            total += self._onda(f, f, dur, vol, tipo)
        return total

    def _gerar_efeitos(self):
        o = self._onda
        receitas = {
            "pulo": lambda: o(280, 620, 0.13, 0.25, "quadrada"),
            "tiro": lambda: o(1000, 350, 0.10, 0.22, "serra"),
            "acerto": lambda: o(260, 90, 0.12, 0.35, "quadrada", ruido=0.5),
            "inimigo_morre": lambda: o(700, 60, 0.38, 0.35, "serra", ruido=0.25),
            "dano": lambda: o(180, 55, 0.30, 0.40, "quadrada", ruido=0.4),
            "item": lambda: o(700, 1400, 0.12, 0.30),
            "maca": lambda: self._sequencia([520, 660, 880], 0.07, 0.30, "seno"),
            "estrela": lambda: self._sequencia([880, 1180, 1480], 0.05, 0.28, "seno"),
            "flor": lambda: self._sequencia([660, 990], 0.06, 0.28, "seno"),
            "pocao_lancada": lambda: o(300, 520, 0.18, 0.22, "seno"),
            "quebra": lambda: o(900, 200, 0.18, 0.35, "serra", ruido=0.7),
            "sapo": lambda: o(420, 160, 0.40, 0.35, "quadrada", vibrato=0.25),
            "destransforma": lambda: self._sequencia([300, 450, 600, 900], 0.06, 0.30),
            "bloqueio": lambda: o(1200, 800, 0.08, 0.30, "quadrada"),
            "poder_safira": lambda: o(300, 950, 0.55, 0.28, "seno", vibrato=0.04),
            "poder_louise": lambda: o(180, 700, 0.60, 0.28, "serra", ruido=0.15),
            "poder_anika": lambda: o(420, 840, 0.40, 0.28, "quadrada"),
            "poder_meliah": lambda: o(900, 180, 0.65, 0.30, "seno", vibrato=0.06),
            "planta_morde": lambda: o(160, 420, 0.10, 0.35, "serra", ruido=0.5),
            "bruxa_ri": lambda: self._sequencia([520, 440, 520, 440], 0.07, 0.22, "quadrada"),
            "vespa": lambda: o(240, 200, 0.22, 0.18, "quadrada", ruido=0.2, vibrato=0.15),
            "boss_tiro": lambda: o(200, 120, 0.25, 0.30, "serra", ruido=0.15),
            "boss_rugido": lambda: o(95, 55, 0.85, 0.45, "serra", ruido=0.3),
            "boss_investida": lambda: o(150, 600, 0.35, 0.35, "serra", ruido=0.2),
            "fase_limpa": lambda: self._sequencia([523, 659, 784, 1047], 0.11, 0.30),
            "fase_nova": lambda: self._sequencia([392, 523, 659], 0.09, 0.28),
            "menu": lambda: o(600, 800, 0.06, 0.22, "quadrada"),
            "selecionar": lambda: self._sequencia([523, 784], 0.07, 0.28),
            "easter_egg": lambda: self._sequencia([523, 659, 784, 659, 784, 1047], 0.09, 0.30, "seno"),
        }
        for nome, fabrica in receitas.items():
            # arquivo próprio tem prioridade: sfx_<nome>.wav / .ogg
            caminho = achar("sfx_%s.wav" % nome) or achar("sfx_%s.ogg" % nome)
            try:
                if caminho:
                    self.sfx[nome] = pygame.mixer.Sound(caminho)
                else:
                    self.sfx[nome] = self._criar(fabrica())
            except (pygame.error, TypeError, ValueError):
                continue
        self._aplicar_volume_sfx()

    # ------------------------------------------------------------ uso
    def _aplicar_volume_sfx(self):
        for s in self.sfx.values():
            s.set_volume(self.volume_sfx)

    def tocar(self, nome):
        if not self.ativo:
            return
        s = self.sfx.get(nome)
        if s is not None:
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

    def parar_musica(self):
        if self.ativo:
            pygame.mixer.music.stop()
        self.musica_atual = None

    def definir_volume_musica(self, v):
        self.volume_musica = max(0.0, min(1.0, v))
        if self.ativo:
            pygame.mixer.music.set_volume(self.volume_musica)

    def definir_volume_sfx(self, v):
        self.volume_sfx = max(0.0, min(1.0, v))
        self._aplicar_volume_sfx()
