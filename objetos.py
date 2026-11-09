import math
import pygame
import recursos as rec
import desenho
from configuracoes import cor_chao, cor_plataforma


class plataforma(pygame.sprite.Sprite):
    """Chão (sólido e invisível: o cenário já desenha o chão) ou
    plataforma suspensa (unidirecional: pode-se pular por baixo)."""

    def __init__(self, x, y, w, h, eh_chao=False, estilo=1):
        super().__init__()
        self.eh_chao = eh_chao
        self.unidirecional = not eh_chao
        self.rect = pygame.Rect(x, y, w, h)
        self.deslocamento_y = 0
        if eh_chao:
            self.image = pygame.Surface((w, h), pygame.SRCALPHA)   # invisível
        else:
            nome = "plataforma(1).png" if estilo == 1 else "Plataforma (2).png"
            base = rec.imagem(nome)
            altura_visual = 20
            if base is not None:
                self.image = pygame.transform.scale(rec.recortar(base), (w, altura_visual))
                self.deslocamento_y = -4
            else:
                self.image = pygame.Surface((w, h))
                self.image.fill(cor_plataforma)
                pygame.draw.rect(self.image, cor_chao, (0, 0, w, 5))


class item(pygame.sprite.Sprite):
    """tipo_item: 'Maca' (+1 coração), 'Estrela' (+energia) ou 'Flor' (easter egg)."""

    _cache = {}

    def __init__(self, x, y, tipo_item):
        super().__init__()
        self.item_type = tipo_item
        self.base_y = y
        self.fase = (x * 0.013) % 6.28
        self.image = self._imagem(tipo_item)
        self.rect = self.image.get_rect(center=(x, y))

    @classmethod
    def _imagem(cls, tipo):
        if tipo in cls._cache:
            return cls._cache[tipo]
        if tipo == "Maca":
            base = rec.imagem("maca.png")
            img = rec.escalar_altura(rec.recortar(base), 30) if base is not None else None
            if img is None:
                img = pygame.Surface((24, 24), pygame.SRCALPHA)
                pygame.draw.circle(img, (230, 50, 50), (12, 12), 11)
        elif tipo == "Flor":
            base = rec.imagem("Flor.png")
            img = rec.escalar_altura(rec.recortar(base), 42) if base is not None else None
            if img is None:
                img = pygame.Surface((20, 30), pygame.SRCALPHA)
                pygame.draw.circle(img, (255, 120, 200), (10, 8), 8)
        else:  # Estrela
            img = desenho.desenhar_estrela(30)
        cls._cache[tipo] = img
        return img

    def update(self, tempo):
        self.rect.centery = int(self.base_y + math.sin(tempo * 0.06 + self.fase) * 5)
