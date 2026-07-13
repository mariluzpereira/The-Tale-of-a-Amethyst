import pygame
import math
from configuracoes import cor_bruxa, cor_planta, cor_vespa, cor_boss
from projeteis import projetil

class inimigo(pygame.sprite.Sprite):
    def __init__(self, x, y, tipo_inimigo):
        super().__init__()
        self.enemy_type = tipo_inimigo  
        self.image = pygame.Surface((40, 40))
        
        if tipo_inimigo == "Bruxa": 
            self.color = cor_bruxa
            self.hp = 6  
        elif tipo_inimigo == "Planta": 
            self.color = cor_planta
            self.hp = 6  
        elif tipo_inimigo == "Vespa": 
            self.color = cor_vespa
            self.hp = 6  
        else: 
            self.image = pygame.Surface((70, 90))
            self.color = cor_boss
            self.hp = 60 
            
        self.image.fill(self.color)
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.tempo_recarga_tiro = 0
        self.direcao = 1
        self.x_origem = x

    def update(self, jogador_alvo, escala_tempo, grupo_projeteis):
        escala = escala_tempo
        if self.enemy_type == "Planta": return 
            
        if self.enemy_type == "Bruxa":
            self.tempo_recarga_tiro -= 1 * escala
            if self.tempo_recarga_tiro <= 0:
                grupo_projeteis.add(projetil(self.rect.centerx, self.rect.centery, jogador_alvo.rect.centerx, jogador_alvo.rect.centery, eh_inimigo=True))
                self.tempo_recarga_tiro = 120

        elif self.enemy_type == "Vespa":
            dx = jogador_alvo.rect.centerx - self.rect.centerx
            dy = jogador_alvo.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist < 300:
                self.rect.x += (dx / dist) * 3 * escala
                self.rect.y += (dy / dist) * 3 * escala

        elif self.enemy_type == "Boss":
            self.rect.x += 2 * self.direcao * escala
            if abs(self.rect.x - self.x_origem) > 150:
                self.direcao *= -1
                
            self.tempo_recarga_tiro -= 1 * escala
            if self.tempo_recarga_tiro <= 0:
                for desvio in [-40, 0, 40]:
                    grupo_projeteis.add(projetil(self.rect.centerx, self.rect.centery, jogador_alvo.rect.centerx + desvio, jogador_alvo.rect.centery, eh_inimigo=True))
                self.tempo_recarga_tiro = 90
