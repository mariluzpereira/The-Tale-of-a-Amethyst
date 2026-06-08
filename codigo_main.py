import pygame
import sys
import math
import random


SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 576
FPS = 60

# Cores (Substitutos das Sprites)
COLOR_BG = (30, 20, 40)
COLOR_GROUND = (45, 130, 80)
COLOR_PLATFORM = (100, 70, 40)
COLOR_UI_BG = (20, 20, 20, 150)
COLOR_TEXT = (255, 255, 255)

# Cores das Princesas
COLOR_SAFIRA = (50, 150, 255)   # Azul
COLOR_LOUISE = (220, 220, 50)   # Amarelo/Vento
COLOR_ANIKA = (50, 200, 100)    # Verde/Escudo
COLOR_MELIAH = (180, 50, 200)   # Roxo/Tempo

# Cores dos Inimigos
COLOR_BRUXA = (140, 20, 180)
COLOR_PLANTA = (200, 50, 50)
COLOR_VESPA = (230, 150, 0)
COLOR_BOSS = (255, 0, 50)

# Gravidade padrão do jogo
GRAVITY = 0.6



class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, is_enemy=False):
        super().__init__()
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        self.is_enemy = is_enemy
        
        if is_enemy:
            pygame.draw.circle(self.image, (255, 50, 50), (6, 6), 6)
            self.damage = 1
            speed = 5
        else:
            pygame.draw.circle(self.image, (255, 255, 200), (6, 6), 6) 
            pygame.draw.circle(self.image, (0, 255, 255), (6, 6), 4)   
            self.damage = 2  
            speed = 12

        self.rect = self.image.get_rect(center=(x, y))
        angle = math.atan2(target_y - y, target_x - x)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def update(self, time_scale, platforms):
        scale = time_scale if self.is_enemy else 1.0
        self.rect.x += self.vx * scale
        self.rect.y += self.vy * scale
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, char_type):
        super().__init__()
        self.char_type = char_type
        self.image = pygame.Surface((40, 60))
        
        if char_type == "Safira": self.color = COLOR_SAFIRA
        elif char_type == "Louise": self.color = COLOR_LOUISE
        elif char_type == "Anika": self.color = COLOR_ANIKA
        else: self.color = COLOR_MELIAH
            
        self.image.fill(self.color)
        self.rect = self.image.get_rect(topleft=(x, y))
        
        # Física
        self.vx = 0
        self.vy = 0
        self.speed = 5
        self.jump_power = -13
        self.is_grounded = False
        
        # Status
        self.max_hearts = 5
        self.hearts = 5
        self.stars = 100 
        self.score = 0
        self.flowers_collected = 0
        
        # Habilidades e Mecânicas de Cooldown (Tempo de Espera)
        self.special_active = False
        self.special_timer = 0
        self.cooldown_timer = 0    # <--- Controlador do tempo de espera
        self.max_cooldown = 300    # 5 segundos de espera (60 frames * 5)
        self.invulnerable_timer = 0

    def update(self, keys, platforms):
        # Reduzir timers frame a frame
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1
            if self.invulnerable_timer % 4 == 0: self.image.set_alpha(100)
            else: self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1

        self.vx = 0
        if keys[pygame.K_a]: self.vx = -self.speed
        if keys[pygame.K_d]: self.vx = self.speed

        # Lógica especial de gravidade da Safira
        if self.char_type == "Safira" and self.special_active:
            self.vy = 1  
            self.special_timer -= 1
            if self.special_timer <= 0: 
                self.special_active = False
                self.cooldown_timer = self.max_cooldown # Inicia espera ao terminar o poder
        else:
            self.vy += GRAVITY

        if self.vy > 15: self.vy = 15

        if (keys[pygame.K_w] or keys[pygame.K_SPACE]) and self.is_grounded:
            self.vy = self.jump_power
            self.is_grounded = False

        # Gerenciamento de tempo para as outras princesas
        if self.special_active and self.char_type != "Safira":
            self.special_timer -= 1
            if self.special_timer <= 0: 
                self.special_active = False
                self.cooldown_timer = self.max_cooldown # Inicia espera ao terminar o poder

        self.rect.x += self.vx
        self.handle_collision(platforms, 'x')
        self.rect.y += self.vy
        self.is_grounded = False
        self.handle_collision(platforms, 'y')

    def handle_collision(self, platforms, direction):
        for plat in platforms:
            if self.rect.colliderect(plat.rect):
                if direction == 'x':
                    if self.vx > 0: self.rect.right = plat.rect.left
                    if self.vx < 0: self.rect.left = plat.rect.right
                elif direction == 'y':
                    if self.vy > 0:
                        self.rect.bottom = plat.rect.top
                        self.vy = 0
                        self.is_grounded = True
                    if self.vy < 0:
                        self.rect.top = plat.rect.bottom
                        self.vy = 0

    def use_special(self):
        # Só ativa se tiver energia suficiente E se não estiver no tempo de espera (cooldown)
        if self.stars >= 30 and not self.special_active and self.cooldown_timer <= 0:
            self.stars -= 30
            self.special_active = True
            if self.char_type == "Safira": self.special_timer = 180 
            elif self.char_type == "Louise": self.special_timer = 45  
            elif self.char_type == "Anika": self.special_timer = 150 
            elif self.char_type == "Meliah": self.special_timer = 180 

    def take_damage(self):
        if self.invulnerable_timer <= 0:
            self.hearts -= 1
            self.invulnerable_timer = 60 

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type):
        super().__init__()
        self.enemy_type = enemy_type
        self.image = pygame.Surface((40, 40))
        
        
        if enemy_type == "Bruxa": 
            self.color = COLOR_BRUXA
            self.hp = 6  # Requer 3 tiros (6 de dano total)
        elif enemy_type == "Planta": 
            self.color = COLOR_PLANTA
            self.hp = 6  # Requer 3 tiros
        elif enemy_type == "Vespa": 
            self.color = COLOR_VESPA
            self.hp = 6  # Requer 3 tiros
        else: 
            # O Rei das Fadas Corrompido verdadeiro Boss
            self.image = pygame.Surface((70, 90))
            self.color = COLOR_BOSS
            self.hp = 60 # Requer 30 tiros certeiros de 2 de dano cada
            
        self.image.fill(self.color)
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.shoot_cooldown = 0
        self.direction = 1
        self.origin_x = x

    def update(self, player, time_scale, projectiles_group):
        scale = time_scale
        if self.enemy_type == "Planta": return 
            
        if self.enemy_type == "Bruxa":
            self.shoot_cooldown -= 1 * scale
            if self.shoot_cooldown <= 0:
                projectiles_group.add(Projectile(self.rect.centerx, self.rect.centery, player.rect.centerx, player.rect.centery, is_enemy=True))
                self.shoot_cooldown = 120

        elif self.enemy_type == "Vespa":
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist < 300:
                self.rect.x += (dx / dist) * 3 * scale
                self.rect.y += (dy / dist) * 3 * scale

        elif self.enemy_type == "Boss":
            self.rect.x += 2 * self.direction * scale
            if abs(self.rect.x - self.origin_x) > 150:
                self.direction *= -1
                
            self.shoot_cooldown -= 1 * scale
            if self.shoot_cooldown <= 0:
                for offset in [-40, 0, 40]:
                    projectiles_group.add(Projectile(self.rect.centerx, self.rect.centery, player.rect.centerx + offset, player.rect.centery, is_enemy=True))
                self.shoot_cooldown = 90



class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, is_ground=False):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(COLOR_GROUND if is_ground else COLOR_PLATFORM)
        self.rect = self.image.get_rect(topleft=(x, y))

class Item(pygame.sprite.Sprite):
    def __init__(self, x, y, item_type):
        super().__init__()
        self.item_type = item_type
        self.image = pygame.Surface((15, 15), pygame.SRCALPHA)
        
        if item_type == "Maca": color = (230, 50, 50)
        elif item_type == "Estrela": color = (240, 240, 50)
        else: color = (200, 100, 255) 
            
        pygame.draw.circle(self.image, color, (7, 7), 7)
        self.rect = self.image.get_rect(center=(x, y))



class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("The Tale of an Amethyst")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 22)
        self.font_title = pygame.font.SysFont("Arial", 50, bold=True)
        
        self.state = 'MENU'
        self.selected_princess = "Safira"
        self.easter_egg_active = False
        self.easter_egg_timer = 0
        
        self.dialogue_text = ""
        self.dialogue_voice_substitute = ""
        self.next_state_after_dialogue = 'GAMEPLAY'
        
        self.init_groups()

    def init_groups(self):
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player_projectiles = pygame.sprite.Group()
        self.enemy_projectiles = pygame.sprite.Group()
        self.items = pygame.sprite.Group()

    def build_level(self):
        self.init_groups()
        self.platforms.add(Platform(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40, is_ground=True))
        
        self.platforms.add(Platform(150, 420, 200, 20))
        self.platforms.add(Platform(450, 320, 250, 20))
        self.platforms.add(Platform(200, 200, 150, 20))
        self.platforms.add(Platform(750, 220, 200, 20))
        
        self.player = Player(50, SCREEN_HEIGHT - 120, self.selected_princess)
        
        for x in [200, 500, 800]: self.items.add(Item(x, SCREEN_HEIGHT - 70, "Maca"))
        for x in [250, 550, 300]: self.items.add(Item(x, 150, "Estrela"))
        
        for i in range(22):
            self.items.add(Item(180 + (i * 25), 380 if i%2==0 else 280, "Flor"))

        self.enemies.add(Enemy(250, 370, "Planta"))
        self.enemies.add(Enemy(550, 270, "Bruxa"))
        self.enemies.add(Enemy(800, 150, "Vespa"))
        
        self.boss = Enemy(850, 120, "Boss")
        self.enemies.add(self.boss)

    def trigger_dialogue(self, text, audio_text, next_st):
        self.state = 'DIALOGUE'
        self.dialogue_text = text
        self.dialogue_voice_substitute = f"[Dublagem Executando]: \"{audio_text}\""
        self.next_state_after_dialogue = next_st

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def handle_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == 'GAMEPLAY':
                    mx, my = pygame.mouse.get_pos()
                    if event.button == 1: 
                        self.player_projectiles.add(Projectile(self.player.rect.centerx, self.player.rect.centery, mx, my, is_enemy=False))
                    elif event.button == 3: 
                        self.player.use_special()
                        
            if event.type == pygame.KEYDOWN:
                if self.state == 'MENU':
                    if event.key == pygame.K_1: self.state = 'CHAR_SELECT'
                    elif event.key == pygame.K_2: self.state = 'CREDITS'
                    elif event.key == pygame.K_3: 
                        pygame.quit()
                        sys.exit()
                elif self.state == 'CHAR_SELECT':
                    if event.key == pygame.K_1: self.selected_princess = "Safira"; self.start_game()
                    elif event.key == pygame.K_2: self.selected_princess = "Louise"; self.start_game()
                    elif event.key == pygame.K_3: self.selected_princess = "Anika"; self.start_game()
                    elif event.key == pygame.K_4: self.selected_princess = "Meliah"; self.start_game()
                elif self.state == 'CREDITS' or self.state == 'GAMEOVER' or self.state == 'VICTORY':
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                        self.state = 'MENU'
                elif self.state == 'DIALOGUE':
                    if event.key == pygame.K_e: 
                        self.state = self.next_state_after_dialogue

    def start_game(self): #exemplo de diálogo será mudado
        self.build_level()
        self.trigger_dialogue(
            "Princesa, o Reino esta corrompido! Derrote o Rei das Fadas.",
            "Aviso real: O destino de Amethyst depende de suas acoes imediatas agora!",
            'GAMEPLAY'
        )

    def update(self):
        if self.state == 'GAMEPLAY':
            keys = pygame.key.get_pressed()
            time_scale = 0.3 if (self.player.char_type == "Meliah" and self.player.special_active) else 1.0
            
            self.player.update(keys, self.platforms)
            self.enemies.update(self.player, time_scale, self.enemy_projectiles)
            self.player_projectiles.update(1.0, self.platforms)
            self.enemy_projectiles.update(time_scale, self.platforms)
            
            if self.player.char_type == "Louise" and self.player.special_active:
                for proj in self.enemy_projectiles:
                    if self.player.rect.inflate(60, 60).colliderect(proj.rect):
                        proj.kill()
                        self.player.score += 5
            
            for proj in self.player_projectiles:
                hit_enemies = pygame.sprite.spritecollide(proj, self.enemies, False)
                for enemy in hit_enemies:
                    proj.kill()
                    enemy.hp -= proj.damage 
                    
                    if enemy.hp <= 0:
                        if enemy.enemy_type == "Boss":
                            if self.player.score > 200:
                                self.trigger_dialogue("Voce salvou o rei e purificou o reino!", "Final Bom alcancado com gloria!", 'VICTORY')
                            else:
                                self.trigger_dialogue("O rei foi derrotado, mas cicatrizes profundas ficaram.", "Final Neutro obtido.", 'VICTORY')
                        enemy.kill()
                        self.player.score += 50

            shielded = (self.player.char_type == "Anika" and self.player.special_active)
            if not shielded:
                if pygame.sprite.spritecollideany(self.player, self.enemies) or pygame.sprite.spritecollideany(self.player, self.enemy_projectiles):
                    self.player.take_damage()
                    pygame.sprite.spritecollide(self.player, self.enemy_projectiles, True)

            collected_items = pygame.sprite.spritecollide(self.player, self.items, True)
            for item in collected_items:
                if item.item_type == "Maca":
                    if self.player.hearts < self.player.max_hearts: self.player.hearts += 1
                elif item.item_type == "Estrela":
                    self.player.stars = min(100, self.player.stars + 25)
                elif item.item_type == "Flor":
                    self.player.flowers_collected += 1
                    self.player.score += 10
                    if self.player.flowers_collected == 20:
                        self.easter_egg_active = True
                        self.easter_egg_timer = 180 

            if self.player.hearts <= 0:
                self.state = 'GAMEOVER'
                
            if self.easter_egg_active:
                self.easter_egg_timer -= 1
                if self.easter_egg_timer <= 0:
                    self.easter_egg_active = False

    def draw(self):
        self.screen.fill(COLOR_BG)
        
        if self.state == 'MENU':
            self.draw_text_centered("The Tale of an Amethyst", self.font_title, SCREEN_HEIGHT // 4, (180, 100, 255))
            self.draw_text_centered("[1] Jogar", self.font, SCREEN_HEIGHT // 2 - 40)
            self.draw_text_centered("[2] Creditos", self.font, SCREEN_HEIGHT // 2 + 10)
            self.draw_text_centered("[3] Sair", self.font, SCREEN_HEIGHT // 2 + 60)
            
        elif self.state == 'CHAR_SELECT':
            self.draw_text_centered("Escolha sua Princesa", self.font_title, 100, COLOR_TEXT)
            self.draw_text_centered("[1] Safira (Poder: Flutuar)", self.font, 220, COLOR_SAFIRA)
            self.draw_text_centered("[2] Louise (Poder: Furacao de Area)", self.font, 270, COLOR_LOUISE)
            self.draw_text_centered("[3] Anika (Poder: Escudo Frontal)", self.font, 320, COLOR_ANIKA)
            self.draw_text_centered("[4] Meliah (Poder: Congelar o Tempo)", self.font, 370, COLOR_MELIAH)

        elif self.state == 'CREDITS':
            self.draw_text_centered("CREDITOS", self.font_title, 150, (100, 200, 255))
            self.draw_text_centered("Desenvolvido focado em acessibilidade e acao.", self.font, 250)
            self.draw_text_centered("Pressione ENTER ou ESC para retornar", self.font, 400, (150, 150, 150))

        elif self.state == 'GAMEPLAY' or self.state == 'DIALOGUE':
            self.platforms.draw(self.screen)
            self.items.draw(self.screen)
            self.enemies.draw(self.screen)
            self.player_projectiles.draw(self.screen)
            self.enemy_projectiles.draw(self.screen)
            
            pygame.draw.rect(self.screen, self.player.color, self.player.rect)
            if self.player.char_type == "Anika" and self.player.special_active:
                pygame.draw.rect(self.screen, (0, 255, 255), (self.player.rect.right, self.player.rect.top, 8, self.player.rect.height))
            elif self.player.char_type == "Louise" and self.player.special_active:
                pygame.draw.circle(self.screen, (255, 255, 255), self.player.rect.center, 50, 2)
            
            self.draw_hud()
            
            if self.easter_egg_active:
                dance_y_offset = math.sin(pygame.time.get_ticks() * 0.01) * 15
                pygame.draw.rect(self.screen, (255, 105, 180), (300, 200 + dance_y_offset, 30, 30))
                pygame.draw.rect(self.screen, (0, 255, 127), (650, 200 - dance_y_offset, 30, 30))
                self.draw_text_centered("!! FESTA DOS GNOMOS ATIVADA !!", self.font, 150, (255, 255, 100))

            if self.state == 'DIALOGUE':
                self.draw_dialogue_ui()

        elif self.state == 'GAMEOVER':
            self.draw_text_centered("GAME OVER", self.font_title, SCREEN_HEIGHT // 3, (255, 50, 50))
            self.draw_text_centered("Pressione ENTER para voltar ao Menu", self.font, SCREEN_HEIGHT // 2)

        elif self.state == 'VICTORY':
            self.draw_text_centered("REINO SALVO!", self.font_title, SCREEN_HEIGHT // 3, (50, 255, 50))
            self.draw_text_centered("Obrigado por jogar The Tale of an Amethyst!", self.font, SCREEN_HEIGHT // 2)
            self.draw_text_centered("Pressione ENTER para fechar a jornada.", self.font, SCREEN_HEIGHT // 2 + 60)

        pygame.display.flip()

    def draw_hud(self):
        ui_surface = pygame.Surface((SCREEN_WIDTH, 50), pygame.SRCALPHA)
        ui_surface.fill(COLOR_UI_BG)
        self.screen.blit(ui_surface, (0, 0))
        
        hearts_str = "S2 " * self.player.hearts
        self.screen.blit(self.font.render(f"Vida: {hearts_str}", True, (255, 50, 100)), (20, 12))
        
        # Exibição do Estado da Habilidade (Pronto / Ativo / Recarregando)
        if self.player.special_active:
            status_especial = "ATIVO"
            cor_status = (0, 255, 255)
        elif self.player.cooldown_timer > 0:
            segundos_restantes = math.ceil(self.player.cooldown_timer / 60)
            status_especial = f"AGUARDE ({segundos_restantes}s)"
            cor_status = (230, 100, 50)
        else:
            status_especial = "PRONTO (Botao Direito)"
            cor_status = (100, 255, 100)
            
        self.screen.blit(self.font.render(f"Especial: {status_especial}", True, cor_status), (250, 12))
        self.screen.blit(self.font.render(f"Energia: {self.player.stars}%", True, (255, 215, 0)), (540, 12))
        self.screen.blit(self.font.render(f"Flores: {self.player.flowers_collected}", True, (200, 100, 255)), (720, 12))
        self.screen.blit(self.font.render(f"Score: {self.player.score}", True, (255, 255, 255)), (880, 12))

    def draw_dialogue_ui(self):
        box_h = 110
        dialogue_surf = pygame.Surface((SCREEN_WIDTH - 40, box_h), pygame.SRCALPHA)
        dialogue_surf.fill((10, 10, 10, 220))
        pygame.draw.rect(dialogue_surf, (150, 100, 220), (0, 0, SCREEN_WIDTH - 40, box_h), 2)
        
        self.screen.blit(dialogue_surf, (20, SCREEN_HEIGHT - box_h - 20))
        self.screen.blit(self.font.render(self.dialogue_text, True, COLOR_TEXT), (40, SCREEN_HEIGHT - box_h - 5))
        self.screen.blit(self.font.render(self.dialogue_voice_substitute, True, (150, 255, 150)), (40, SCREEN_HEIGHT - box_h + 30))
        self.screen.blit(self.font.render("[Pressione 'E' para Continuar]", True, (180, 180, 180)), (700, SCREEN_HEIGHT - 50))

    def draw_text_centered(self, text, font, y_pos, color=COLOR_TEXT):
        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
        self.screen.blit(text_surf, text_rect)


if __name__ == "__main__":
    game = GameEngine()
    game.run()

