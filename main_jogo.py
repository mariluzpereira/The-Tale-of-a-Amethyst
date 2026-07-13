import pygame
import sys
import math
from configuracoes import *
from jogador import player
from inimigos import enemy
from projeteis import projectile
from objetos import platform, item

class gameengine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((largura_tela, altura_tela))
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
        self.platforms.add(platform(0, altura_tela - 40, largura_tela, 40, eh_chao=True))
        
        self.platforms.add(platform(150, 420, 200, 20))
        self.platforms.add(platform(450, 320, 250, 20))
        self.platforms.add(platform(200, 200, 150, 20))
        self.platforms.add(platform(750, 220, 200, 20))
        
        self.player = player(50, altura_tela - 120, self.selected_princess)
        
        for x in [200, 500, 800]: self.items.add(item(x, altura_tela - 70, "Maca"))
        for x in [250, 550, 300]: self.items.add(item(x, 150, "Estrela"))
        
        for i in range(22):
            self.items.add(item(180 + (i * 25), 380 if i%2==0 else 280, "Flor"))

        self.enemies.add(enemy(250, 370, "Planta"))
        self.enemies.add(enemy(550, 270, "Bruxa"))
        self.enemies.add(enemy(800, 150, "Vespa"))
        
        self.boss = enemy(850, 120, "Boss")
        self.enemies.add(self.boss)

    def trigger_dialogue(self, texto, texto_audio, proximo_estado):
        self.state = 'DIALOGUE'
        self.dialogue_text = texto
        self.dialogue_voice_substitute = f"[Dublagem Executando]: \"{texto_audio}\""
        self.next_state_after_dialogue = proximo_estado

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(fps)

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
                        self.player_projectiles.add(projectile(self.player.rect.centerx, self.player.rect.centery, mx, my, eh_inimigo=False))
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
                elif self.state in ['CREDITS', 'GAMEOVER', 'VICTORY']:
                    if event.key in [pygame.K_ESCAPE, pygame.K_RETURN]:
                        self.state = 'MENU'
                elif self.state == 'DIALOGUE':
                    if event.key == pygame.K_e: 
                        self.state = self.next_state_after_dialogue
                        pygame.key.set_mods(0) 

    #alterar dialogo eventualmente
    def start_game(self): 
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
                    
                    #alterar mensagem 
                    if enemy.hp <= 0:
                        if enemy.enemy_type == "Boss":
                            if self.player.score > 200:
                                self.trigger_dialogue("Voce salvou o rei e purificou o reino!", "Final Bom alcancado com gloria!", 'VITÓRIA')
                            else:
                                self.trigger_dialogue("O rei foi derrotado, mas cicatrizes profundas ficaram.", "Final Neutro obtido.", 'VITÓRIA')
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
        self.screen.fill(cor_fundo)
        
        if self.state == 'MENU':
            self.draw_text_centered("The Tale of an Amethyst", self.font_title, altura_tela // 4, (180, 100, 255))
            self.draw_text_centered("[1] Jogar", self.font, altura_tela // 2 - 40)
            self.draw_text_centered("[2] Creditos", self.font, altura_tela // 2 + 10)
            self.draw_text_centered("[3] Sair", self.font, altura_tela // 2 + 60)
            
        elif self.state == 'CHAR_SELECT':
            self.draw_text_centered("Escolha sua Princesa", self.font_title, 100, cor_texto)
            self.draw_text_centered("[1] Safira (Poder: Flutuar)", self.font, 220, cor_safira)
            self.draw_text_centered("[2] Louise (Poder: Furacao de Area)", self.font, 270, cor_louise)
            self.draw_text_centered("[3] Anika (Poder: Escudo Frontal)", self.font, 320, cor_anika)
            self.draw_text_centered("[4] Meliah (Poder: Congelar o Tempo)", self.font, 370, cor_meliah)

        elif self.state == 'CREDITS':
            self.draw_text_centered("CREDITOS", self.font_title, 150, (100, 200, 255))
            self.draw_text_centered("Desenvolvido focado em acessibilidade e acao.", self.font, 250)
            self.draw_text_centered("Pressione ENTER ou ESC para retornar", self.font, 400, (150, 150, 150))

        elif self.state in ['GAMEPLAY', 'DIALOGUE']:
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
            self.draw_text_centered("GAME OVER", self.font_title, altura_tela // 3, (255, 50, 50))
            self.draw_text_centered("Pressione ENTER para voltar ao Menu", self.font, altura_tela // 2)

        elif self.state == 'VICTORY':
            self.draw_text_centered("REINO SALVO!", self.font_title, altura_tela // 3, (50, 255, 50))
            self.draw_text_centered("Obrigado por jogar The Tale of an Amethyst!", self.font, altura_tela // 2)
            self.draw_text_centered("Pressione ENTER para fechar a jornada.", self.font, altura_tela // 2 + 60)

        pygame.display.flip()

    def draw_hud(self):
        ui_surface = pygame.Surface((largura_tela, 50), pygame.SRCALPHA)
        ui_surface.fill(cor_remans_ui)
        self.screen.blit(ui_surface, (0, 0))
        
        hearts_str = "S2 " * self.player.hearts
        self.screen.blit(self.font.render(f"Vida: {hearts_str}", True, (255, 50, 100)), (20, 12))
        
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
        dialogue_surf = pygame.Surface((largura_tela - 40, box_h), pygame.SRCALPHA)
        dialogue_surf.fill((10, 10, 10, 220))
        pygame.draw.rect(dialogue_surf, (150, 100, 220), (0, 0, largura_tela - 40, box_h), 2)
        
        self.screen.blit(dialogue_surf, (20, altura_tela - box_h - 20))
        self.screen.blit(self.font.render(self.dialogue_text, True, cor_texto), (40, altura_tela - box_h - 5))
        self.screen.blit(self.font.render(self.dialogue_voice_substitute, True, (150, 255, 150)), (40, altura_tela - box_h + 30))
        self.screen.blit(self.font.render("[Pressione 'E' para Continuar]", True, (180, 180, 180)), (700, altura_tela - 50))

    def draw_text_centered(self, text, font, y_pos, color=cor_texto):
        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect(center=(largura_tela // 2, y_pos))
        self.screen.blit(text_surf, text_rect)
