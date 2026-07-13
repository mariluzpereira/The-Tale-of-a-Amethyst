import pygame
from configuracoes import cor_chao, cor_plataforma

class plataforma(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, eh_chao=False):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(cor_chao if eh_chao else cor_plataforma)
        self.rect = self.image.get_rect(topleft=(x, y))

class item(pygame.sprite.Sprite):
    def __init__(self, x, y, tipo_item):
        super().__init__()
        self.item_type = tipo_item  # Mantido para conversar com o motor principal
       
        self.image = pygame.Surface((15, 15), pygame.SRCALPHA)
        
        if tipo_item == "Maca": 
            cor_item = (230, 50, 50)
        elif tipo_item == "Estrela": 
            cor_item = (240, 240, 50)
        else: 
            cor_item = (200, 100, 255) 
            
        pygame.draw.circle(self.image, cor_item, (7.5, 7.5), 7)
        self.rect = self.image.get_rect(center=(x, y))
