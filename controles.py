"""Teclas e botões do mouse configuráveis (menu Opções).

Cada ação tem 2 "slots" (principal e alternativa). Um slot guarda
('k', código_da_tecla) ou ('m', botão_do_mouse) ou None.
As escolhas ficam salvas em 'config_teclas.json' (mesma pasta do jogo).
"""
import json
import os
import pygame
from configuracoes import pasta_base

ARQUIVO = os.path.join(pasta_base, "config_teclas.json")

# (id, rótulo, aceita botão do mouse?)
ACOES = [
    ("esquerda", "Andar p/ esquerda", False),
    ("direita", "Andar p/ direita", False),
    ("pular", "Pular", False),
    ("descer", "Descer da plataforma", False),
    ("atirar", "Atirar", True),
    ("poder", "Poder especial", True),
    ("interagir", "Falar / avançar", False),
    ("pausar", "Pausar", False),
]

PADRAO = {
    "esquerda": [("k", pygame.K_a), ("k", pygame.K_LEFT)],
    "direita": [("k", pygame.K_d), ("k", pygame.K_RIGHT)],
    "pular": [("k", pygame.K_w), ("k", pygame.K_SPACE)],
    "descer": [("k", pygame.K_s), ("k", pygame.K_DOWN)],
    "atirar": [("m", 1), None],
    "poder": [("m", 3), None],
    "interagir": [("k", pygame.K_e), None],
    "pausar": [("k", pygame.K_p), None],
}

TECLA_RESERVADA = pygame.K_ESCAPE      # Esc sempre pausa / volta: não pode ser reatribuído

_NOMES_PT = {
    "space": "Espaço", "left": "Seta esq", "right": "Seta dir", "up": "Seta cima",
    "down": "Seta baixo", "return": "Enter", "tab": "Tab", "backspace": "Backspace",
    "left shift": "Shift esq", "right shift": "Shift dir", "left ctrl": "Ctrl esq",
    "right ctrl": "Ctrl dir", "left alt": "Alt esq", "right alt": "Alt dir",
    "caps lock": "Caps Lock", "escape": "Esc", "delete": "Delete",
}


def _copiar(mapa):
    return {a: [tuple(b) if b else None for b in slots] for a, slots in mapa.items()}


class Controles:
    def __init__(self):
        self.mapa = _copiar(PADRAO)
        self.carregar()

    # ------------------------------------------------------------ arquivo
    def carregar(self):
        try:
            with open(ARQUIVO, "r", encoding="utf-8") as f:
                dados = json.load(f)
        except (OSError, ValueError):
            return
        for acao, _, aceita_mouse in ACOES:
            slots = dados.get(acao)
            if not isinstance(slots, list) or len(slots) != 2:
                continue
            limpo = []
            for b in slots:
                if isinstance(b, list) and len(b) == 2 and b[0] in ("k", "m") and isinstance(b[1], int):
                    if b[0] == "m" and not aceita_mouse:
                        b = None
                    elif b[0] == "k" and b[1] == TECLA_RESERVADA:
                        b = None
                    else:
                        b = (b[0], b[1])
                else:
                    b = None
                limpo.append(b)
            if any(limpo):
                self.mapa[acao] = limpo

    def salvar(self):
        try:
            with open(ARQUIVO, "w", encoding="utf-8") as f:
                json.dump({a: [list(b) if b else None for b in s] for a, s in self.mapa.items()}, f)
        except OSError:
            pass

    def restaurar_padrao(self):
        self.mapa = _copiar(PADRAO)
        self.salvar()

    # ------------------------------------------------------------ consulta
    def tecla(self, acao, teclas):
        """True se alguma TECLA da ação está pressionada agora."""
        for b in self.mapa[acao]:
            if b and b[0] == "k" and teclas[b[1]]:
                return True
        return False

    def segurando(self, acao, teclas, botoes):
        """True se tecla OU botão do mouse da ação está pressionado agora."""
        if self.tecla(acao, teclas):
            return True
        for b in self.mapa[acao]:
            if b and b[0] == "m" and 1 <= b[1] <= len(botoes) and botoes[b[1] - 1]:
                return True
        return False

    def evento(self, acao, ev):
        """True se o evento (tecla/clique) acabou de acionar a ação."""
        for b in self.mapa[acao]:
            if not b:
                continue
            if ev.type == pygame.KEYDOWN and b[0] == "k" and ev.key == b[1]:
                return True
            if ev.type == pygame.MOUSEBUTTONDOWN and b[0] == "m" and ev.button == b[1]:
                return True
        return False

    # ------------------------------------------------------------ edição
    def aceita_mouse(self, acao):
        return next(m for a, _, m in ACOES if a == acao)

    def atribuir(self, acao, slot, bind):
        """Define um slot. Se a tecla já era de outra ação, as duas trocam de lugar.
        Devolve False se a atribuição não for permitida (e nada muda)."""
        if bind is not None:
            if bind[0] == "m" and not self.aceita_mouse(acao):
                return False
            if bind[0] == "k" and bind[1] == TECLA_RESERVADA:
                return False
        antigo = self.mapa[acao][slot]
        if bind is None:
            # limpar: só se sobrar outra forma de acionar a ação
            if not any(b for i, b in enumerate(self.mapa[acao]) if i != slot):
                return False
            self.mapa[acao][slot] = None
            self.salvar()
            return True
        for outra, slots in self.mapa.items():
            for i, b in enumerate(slots):
                if b == bind and not (outra == acao and i == slot):
                    troca = antigo
                    if troca is not None and troca[0] == "m" and not self.aceita_mouse(outra):
                        troca = None
                    slots[i] = troca
                    if not any(slots):          # deixaria a outra ação sem nada: cancela
                        slots[i] = b
                        return False
        self.mapa[acao][slot] = bind
        self.salvar()
        return True

    # ------------------------------------------------------------ texto
    def nome_bind(self, bind):
        if not bind:
            return "---"
        if bind[0] == "m":
            return {1: "Mouse esq", 2: "Mouse meio", 3: "Mouse dir"}.get(bind[1], "Mouse %d" % bind[1])
        try:
            n = pygame.key.name(bind[1])
        except Exception:
            n = ""
        if not n:
            return "Tecla %d" % bind[1]
        return _NOMES_PT.get(n, n.upper() if len(n) <= 2 else n.capitalize())

    def nome_acao(self, acao, separador=" / "):
        """Texto para mostrar ao jogador: 'A / Seta esq'."""
        nomes = [self.nome_bind(b) for b in self.mapa[acao] if b]
        return separador.join(nomes) if nomes else "---"
