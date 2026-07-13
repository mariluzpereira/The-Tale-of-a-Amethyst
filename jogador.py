import pygame
from configuracoes import (
    gravidade, cor_safira, cor_louise, cor_anika, cor_meliah
)

class jogador(pygame.sprite.Sprite):
    def __init__(self, x, y, tipo_personagem):
        super().__init__()
        self.char_type = tipo_personagem
        self.image = pygame.Surface((40, 60))
        
        if tipo_personagem == "Safira": self.color = cor_safira
        elif tipo_personagem == "Louise": self.color = cor_louise
        elif tipo_personagem == "Anika": self.color = cor_anika
        else: self.color = cor_meliah
            
        self.image.fill(self.color)
        self.rect = self.image.get_rect(topleft=(x, y))
        
        # consertar fisica
        self.vx = 0
        self.vy = 0
        self.speed = 5
        self.jump_power = -13
        self.is_grounded = False
        
        # informções do jogador
        self.max_hearts = 5
        self.hearts = 5
        self.stars = 100 
        self.score = 0
        self.flowers_collected = 0
        
        # habilidades/tempo de recarga
        self.special_active = False
        self.special_timer = 0
        self.cooldown_timer = 0    
        self.max_cooldown = 300    
        self.invulnerable_timer = 0

    def update(self, teclas, plataformas):
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1
            if self.invulnerable_timer % 4 == 0: self.image.set_alpha(100)
            else: self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1

        self.vx = 0
        if teclas[pygame.K_a]: self.vx = -self.speed
        if teclas[pygame.K_d]: self.vx = self.speed

        if self.char_type == "Safira" and self.special_active:
            self.vy = 1  
            self.special_timer -= 1
            if self.special_timer <= 0: 
                self.special_active = False
                self.cooldown_timer = self.max_cooldown 
        else:
            self.vy += gravidade

        if self.vy > 15: self.vy = 15

        if (teclas[pygame.K_w] or teclas[pygame.K_SPACE]) and self.is_grounded:
            self.vy = self.jump_power
            self.is_grounded = False

        if self.special_active and self.char_type != "Safira":
            self.special_timer -= 1
            if self.special_timer <= 0: 
                self.special_active = False
                self.cooldown_timer = self.max_cooldown 

        self.rect.x += self.vx
        self.tratar_colisao(plataformas, 'x')
        self.rect.y += self.vy
        self.is_grounded = False
        self.tratar_colisao(plataformas, 'y')

    def tratar_colisao(self, plataformas, direcao):
        for plat in plataformas:
            if self.rect.colliderect(plat.rect):
                if direcao == 'x':
                    if self.vx > 0: self.rect.right = plat.rect.left
                    if self.vx < 0: self.rect.left = plat.rect.right
                elif direcao == 'y':
                    if self.vy > 0:
                        self.rect.bottom = plat.rect.top
                        self.vy = 0
                        self.is_grounded = True
                    if self.vy < 0:
                        self.rect.top = plat.rect.bottom
                        self.vy = 0

    def use_special(self):
        if self.stars >= 30 and not self.special_active and self.cooldown_timer <= 0:
            self.stars -= 30
            self.special_active = True
            if self.char_type == "Safira": self.special_timer = 180 
            elif self.char_type == "Louise": self.special_timer = 45  
            elif self.char_type == "Anika": self.special_timer = 150 
            elif self.char_type == "Meliah": self.special_timer = 180 

    def receber_dano(self):
        if self.invulnerable_timer <= 0:
            self.hearts -= 1
            self.invulnerable_timer = 60
