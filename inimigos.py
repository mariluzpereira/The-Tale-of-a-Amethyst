import pygame
import math
from configuracoes import cor_bruxa, cor_planta, cor_vespa, cor_boss
from projeteis import projectil

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
        
        self.shoot_cooldown = 0
        self.direction = 1
        self.origin_x = x

    def update(self, jogador, escala_tempo, grupo_projeteis):
        escala = escala_tempo
        if self.enemy_type == "Planta": return 
            
        if self.enemy_type == "Bruxa":
            self.shoot_cooldown -= 1 * escala
            if self.shoot_cooldown <= 0:
                grupo_projeteis.add(projectile(self.rect.centerx, self.rect.centery, jogador.rect.centerx, jogador.rect.centery, eh_inimigo=True))
                self.shoot_cooldown = 120

        elif self.enemy_type == "Vespa":
            dx = jogador.rect.centerx - self.rect.centerx
            dy = jogador.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist < 300:
                self.rect.x += (dx / dist) * 3 * escala
                self.rect.y += (dy / dist) * 3 * escala

        elif self.enemy_type == "Boss":
            self.rect.x += 2 * self.direction * escala
            if abs(self.rect.x - self.origin_x) > 150:
                self.direction *= -1
                
            self.shoot_cooldown -= 1 * escala
            if self.shoot_cooldown <= 0:
                for offset in [-40, 0, 40]:
                    grupo_projeteis.add(projectile(self.rect.centerx, self.rect.centery, jogador.rect.centerx + offset, jogador.rect.centery, eh_inimigo=True))
                self.shoot_cooldown = 90
