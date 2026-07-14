import pygame
from configuracoes import (
    gravidade, cor_safira, cor_louise, cor_anika, cor_meliah, largura_tela
)

class jogador(pygame.sprite.Sprite):
    def __init__(self, x, y, tipo_personagem):
        super().__init__()
        self.tipo_personagem = tipo_personagem
        self.image = pygame.Surface((40, 60))
        
        if tipo_personagem == "Safira": self.color = cor_safira
        elif tipo_personagem == "Louise": self.color = cor_louise
        elif tipo_personagem == "Anika": self.color = cor_anika
        else: self.color = cor_meliah
            
        self.image.fill(self.color)
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.vx = 0
        self.vy = 0
        self.velocidade = 5
        self.forca_pulo = -13
        self.esta_no_chao = False
        
        self.coracoes_maximos = 5
        self.hearts = 5  
        self.stars = 100  
        self.score = 0  
        self.flowers_collected = 0  
        
        self.special_active = False  
        self.tempo_especial = 0
        self.cooldown_timer = 0  
        self.tempo_recarga_maximo = 300    
        self.tempo_invulnerabilidade = 0

    def update(self, teclas, plataformas):
        if self.tempo_invulnerabilidade > 0:
            self.tempo_invulnerabilidade -= 1
            if self.tempo_invulnerabilidade % 4 == 0: self.image.set_alpha(100)
            else: self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1

        self.vx = 0
        if teclas[pygame.K_a]: self.vx = -self.velocidade
        if teclas[pygame.K_d]: self.vx = self.velocidade

        if self.tipo_personagem == "Safira" and self.special_active:
            self.vy = -2  
            self.esta_no_chao = False 
            self.tempo_especial -= 1
            if self.tempo_especial <= 0: 
                self.special_active = False
                self.cooldown_timer = self.tempo_recarga_maximo 
        else:
            self.vy += gravidade

        if self.vy > 15: self.vy = 15

        if (teclas[pygame.K_w] or teclas[pygame.K_SPACE]) and self.esta_no_chao:
            self.vy = self.forca_pulo
            self.esta_no_chao = False

        if self.special_active and self.tipo_personagem != "Safira":
            self.tempo_especial -= 1
            if self.tempo_especial <= 0: 
                self.special_active = False
                self.cooldown_timer = self.tempo_recarga_maximo 

        self.rect.x += self.vx
        self.tratar_colisao(plataformas, 'x')
        
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > largura_tela:
            self.rect.right = largura_tela

        self.rect.y += self.vy
        self.esta_no_chao = False
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
                        self.esta_no_chao = True
                    if self.vy < 0:
                        self.rect.top = plat.rect.bottom
                        self.vy = 0

    def use_special(self):
        if self.stars >= 30 and not self.special_active and self.cooldown_timer <= 0:
            self.stars -= 30
            self.special_active = True
            if self.tipo_personagem == "Safira": self.tempo_especial = 180   
            elif self.tipo_personagem == "Louise": self.tempo_especial = 60  
            elif self.tipo_personagem == "Anika": self.tempo_especial = 150 
            elif self.tipo_personagem == "Meliah": self.tempo_especial = 180 

    def receber_dano(self):
        if self.tempo_invulnerabilidade <= 0:
            self.hearts -= 1
            self.tempo_invulnerabilidade = 60

    def atacar_inimigos(self, grupo_inimigos):
        if self.tipo_personagem == "Louise" and self.special_active:
            area_furacao = self.rect.inflate(100, 40) 
            
            for inimigo_alvo in grupo_inimigos:
                if area_furacao.colliderect(inimigo_alvo.rect):
                    if hasattr(inimigo_alvo, 'receber_dano'):
                        inimigo_alvo.receber_dano(dano=1) 
                    elif hasattr(inimigo_alvo, 'kill'):
                        inimigo_alvo.kill() 

                    if inimigo_alvo.rect.centerx < self.rect.centerx:
                        inimigo_alvo.rect.x -= 15  
                    else:
                        inimigo_alvo.rect.x += 15
