import pygame
import math
from configuracoes import largura_tela, altura_tela

class projetil(pygame.sprite.Sprite):
    def __init__(self, x, y, alvo_x, alvo_y, eh_inimigo=False):
        super().__init__()
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        self.eh_inimigo = eh_inimigo
        
        if eh_inimigo:
            pygame.draw.circle(self.image, (255, 50, 50), (6, 6), 6)
            self.damage = 1
            velocidade = 5
        else:
            pygame.draw.circle(self.image, (255, 255, 200), (6, 6), 6) 
            pygame.draw.circle(self.image, (0, 255, 255), (6, 6), 4)   
            self.damage = 2  
            velocidade = 12

        self.rect = self.image.get_rect(center=(x, y))
        angulo = math.atan2(alvo_y - y, alvo_x - x)
        self.vx = math.cos(angulo) * velocidade
        self.vy = math.sin(angulo) * velocidade

    def update(self, escala_tempo, plataformas):
        escala = escala_tempo if self.eh_inimigo else 1.0
        self.rect.x += self.vx * escala
        self.rect.y += self.vy * escala
        if self.rect.right < 0 or self.rect.left > largura_tela or self.rect.bottom < 0 or self.rect.top > altura_tela:
            self.kill()
