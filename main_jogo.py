import pygame
import sys
import math
from configuracoes import *
from jogador import jogador
from inimigos import inimigo
from projeteis import projetil
from objetos import plataforma, item

class motorjogo:
    def __init__(self):
        pygame.init()
        self.tela = pygame.display.set_mode((largura_tela, altura_tela))
        pygame.display.set_caption("The Tale of an Amethyst")
        self.relogio = pygame.time.Clock()
        self.fonte = pygame.font.SysFont("Arial", 22)
        self.fonte_titulo = pygame.font.SysFont("Arial", 50, bold=True)
        
        self.estado = 'MENU'
        self.princesa_selecionada = "Safira"
        self.easter_egg_ativo = False
        self.temporizador_easter_egg = 0
        
        self.texto_dialogo = ""
        self.substituto_voz_dialogo = ""
        self.proximo_estado_pos_dialogo = 'GAMEPLAY'
        
        self.inicializar_grupos()

    def inicializar_grupos(self):
        self.plataformas = pygame.sprite.Group()
        self.inimigos = pygame.sprite.Group()
        self.projeteis_jogador = pygame.sprite.Group()
        self.projeteis_inimigo = pygame.sprite.Group()
        self.itens = pygame.sprite.Group()

    def construir_fase(self):
        self.inicializar_grupos()
        self.plataformas.add(plataforma(0, altura_tela - 40, largura_tela, 40, eh_chao=True))
        
        self.plataformas.add(plataforma(150, 420, 200, 20))
        self.plataformas.add(plataforma(450, 320, 250, 20))
        self.plataformas.add(plataforma(200, 200, 150, 20))
        self.plataformas.add(plataforma(750, 220, 200, 20))
        
        self.jogador = jogador(50, altura_tela - 120, self.princesa_selecionada)
        
        for x in [200, 500, 800]: self.itens.add(item(x, altura_tela - 70, "Maca"))
        for x in [250, 550, 300]: self.itens.add(item(x, 150, "Estrela"))
        
        for i in range(22):
            self.itens.add(item(180 + (i * 25), 380 if i % 2 == 0 else 280, "Flor"))

        self.inimigos.add(inimigo(250, 370, "Planta"))
        self.inimigos.add(inimigo(550, 270, "Bruxa"))
        self.inimigos.add(inimigo(800, 150, "Vespa"))
        
        self.boss = inimigo(850, 120, "Boss")
        self.inimigos.add(self.boss)

    def disparar_dialogo(self, texto, texto_audio, proximo_estado):
        self.estado = 'DIALOGUE'
        self.texto_dialogo = texto
        self.substituto_voz_dialogo = f"[Dublagem Executando]: \"{texto_audio}\""
        self.proximo_estado_pos_dialogo = proximo_estado

    def executar(self):
        while True:
            self.tratar_eventos()
            self.atualizar()
            self.desenhar()
            self.relogio.tick(fps)

    def tratar_eventos(self):
        eventos = pygame.event.get()
        for evento in eventos:
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if self.estado == 'GAMEPLAY':
                    mx, my = pygame.mouse.get_pos()
                    if evento.button == 1: 
                        self.projeteis_jogador.add(projetil(self.jogador.rect.centerx, self.jogador.rect.centery, mx, my, eh_inimigo=False))
                    elif evento.button == 3: 
                        self.jogador.use_special()
                        
            if evento.type == pygame.KEYDOWN:
                if self.estado == 'MENU':
                    if evento.key == pygame.K_1: self.estado = 'CHAR_SELECT'
                    elif evento.key == pygame.K_2: self.estado = 'CREDITS'
                    elif evento.key == pygame.K_3: 
                        pygame.quit()
                        sys.exit()
                elif self.estado == 'CHAR_SELECT':
                    if evento.key == pygame.K_1: self.princesa_selecionada = "Safira"; self.iniciar_jogo()
                    elif evento.key == pygame.K_2: self.princesa_selecionada = "Louise"; self.iniciar_jogo()
                    elif evento.key == pygame.K_3: self.princesa_selecionada = "Anika"; self.iniciar_jogo()
                    elif evento.key == pygame.K_4: self.princesa_selecionada = "Meliah"; self.iniciar_jogo()
                elif self.estado in ['CREDITS', 'GAMEOVER', 'VICTORY']:
                    if evento.key in [pygame.K_ESCAPE, pygame.K_RETURN]:
                        self.estado = 'MENU'
                elif self.estado == 'DIALOGUE':
                    if evento.key == pygame.K_e: 
                        self.estado = self.proximo_estado_pos_dialogo
                        pygame.key.set_mods(0) 

    def iniciar_jogo(self): 
        self.construir_fase()
        self.disparar_dialogo(
            "Princesa, o reino esta corrompido! Derrote o Rei das Fadas.",
            "Botão direito ativa habilidade, botão esquerdo atira",
            'GAMEPLAY'
        )

    def atualizar(self):
        if self.estado == 'GAMEPLAY':
            teclas = pygame.key.get_pressed()
            escala_tempo = 0.3 if (self.jogador.tipo_personagem == "Meliah" and self.jogador.special_active) else 1.0
            
            self.jogador.update(teclas, self.plataformas)
            self.inimigos.update(self.jogador, escala_tempo, self.projeteis_inimigo)
            self.projeteis_jogador.update(1.0, self.plataformas)
            self.projeteis_inimigo.update(escala_tempo, self.plataformas)
            
            if self.jogador.tipo_personagem == "Louise" and self.jogador.special_active:
                self.jogador.atacar_inimigos(self.inimigos) 
                
                for proj in self.projeteis_inimigo:
                    if self.jogador.rect.inflate(60, 60).colliderect(proj.rect):
                        proj.kill()
                        self.jogador.score += 5
            
            for proj in self.projeteis_jogador:
                inimigos_atingidos = pygame.sprite.spritecollide(proj, self.inimigos, False)
                for inimigo_alvo in inimigos_atingidos:
                    proj.kill()
                    inimigo_alvo.hp -= proj.damage 
                    
                    if inimigo_alvo.hp <= 0:
                        if inimigo_alvo.enemy_type == "Boss":
                            if self.jogador.score > 200:
                                self.disparar_dialogo("Voce salvou o rei e purificou o reino!", "Final Bom alcancado com gloria!", 'VICTORY')
                            else:
                                self.disparar_dialogo("O rei foi derrotado, mas cicatrizes profundas ficaram.", "Final Neutro obtido.", 'VICTORY')
                        inimigo_alvo.kill()
                        self.jogador.score += 50

            protegido = (self.jogador.tipo_personagem == "Anika" and self.jogador.special_active)
            if not protegido:
                if pygame.sprite.spritecollideany(self.jogador, self.inimigos) or pygame.sprite.spritecollideany(self.jogador, self.projeteis_inimigo):
                    self.jogador.receber_dano() 
                    pygame.sprite.spritecollide(self.jogador, self.projeteis_inimigo, True)

            itens_coletados = pygame.sprite.spritecollide(self.jogador, self.itens, True)
            for objeto_item in itens_coletados:
                if objeto_item.item_type == "Maca":
                    if self.jogador.hearts < self.jogador.coracoes_maximos: self.jogador.hearts += 1
                elif objeto_item.item_type == "Estrela":
                    self.jogador.stars = min(100, self.jogador.stars + 25)
                elif objeto_item.item_type == "Flor":
                    self.jogador.flowers_collected += 1
                    self.jogador.score += 10
                    if self.jogador.flowers_collected == 20:
                        self.easter_egg_ativo = True
                        self.temporizador_easter_egg = 180 

            if self.jogador.hearts <= 0:
                self.estado = 'GAMEOVER'
                
            if self.easter_egg_ativo:
                self.temporizador_easter_egg -= 1
                if self.temporizador_easter_egg <= 0:
                    self.easter_egg_ativo = False

    def desenhar(self):
        self.tela.fill(cor_fundo)
        
        if self.estado == 'MENU':
            self.desenhar_texto_centralizado("The Tale of an Amethyst", self.fonte_titulo, altura_tela // 4, (180, 100, 255))
            self.desenhar_texto_centralizado("[1] Jogar", self.fonte, altura_tela // 2 - 40)
            self.desenhar_texto_centralizado("[2] Creditos", self.fonte, altura_tela // 2 + 10)
            self.desenhar_texto_centralizado("[3] Sair", self.fonte, altura_tela // 2 + 60)
            
        elif self.estado == 'CHAR_SELECT':
            self.desenhar_texto_centralizado("Escolha sua Princesa", self.fonte_titulo, 100, cor_texto)
            self.desenhar_texto_centralizado("[1] Safira (Poder: Flutuar)", self.fonte, 220, cor_safira)
            self.desenhar_texto_centralizado("[2] Louise (Poder: Furacao de Area)", self.fonte, 270, cor_louise)
            self.desenhar_texto_centralizado("[3] Anika (Poder: Escudo Frontal)", self.fonte, 320, cor_anika)
            self.desenhar_texto_centralizado("[4] Meliah (Poder: Congelar o Tempo)", self.fonte, 370, cor_meliah)

        elif self.estado == 'CREDITS':
            self.desenhar_texto_centralizado("CREDITOS", self.fonte_titulo, 150, (100, 200, 255))
            self.desenhar_texto_centralizado("Desenvolvido por Aimée e Mariluz.", self.fonte, 250)
            self.desenhar_texto_centralizado("Pressione ENTER ou ESC para retornar", self.fonte, 400, (150, 150, 150))

        elif self.estado in ['GAMEPLAY', 'DIALOGUE']:
            self.plataformas.draw(self.tela)
            self.itens.draw(self.tela)
            self.inimigos.draw(self.tela)
            self.projeteis_jogador.draw(self.tela)
            self.projeteis_inimigo.draw(self.tela)
            
            pygame.draw.rect(self.tela, self.jogador.color, self.jogador.rect)
            
            if self.jogador.tipo_personagem == "Anika" and self.jogador.special_active:
                escudo_surface = pygame.Surface((30, self.jogador.rect.height + 20), pygame.SRCALPHA)
                pygame.draw.ellipse(escudo_surface, (0, 255, 255, 80), (0, 0, 25, self.jogador.rect.height + 20))
                pygame.draw.ellipse(escudo_surface, (200, 255, 255, 255), (0, 0, 25, self.jogador.rect.height + 20), 3)
                self.tela.blit(escudo_surface, (self.jogador.rect.right - 5, self.jogador.rect.top - 10))
                
            elif self.jogador.tipo_personagem == "Louise" and self.jogador.special_active:
                pygame.draw.circle(self.tela, (255, 255, 255), self.jogador.rect.center, 50, 2)
            
            self.desenhar_hud()
            
            if self.easter_egg_ativo:
                deslocamento_y_danca = math.sin(pygame.time.get_ticks() * 0.01) * 15
                pygame.draw.rect(self.tela, (255, 105, 180), (300, 200 + deslocamento_y_danca, 30, 30))
                pygame.draw.rect(self.tela, (0, 255, 127), (650, 200 - deslocamento_y_danca, 30, 30))
                self.desenhar_texto_centralizado("Easter egg", self.fonte, 150, (255, 255, 100))

            if self.estado == 'DIALOGUE':
                self.desenhar_ui_dialogo()

        elif self.estado == 'GAMEOVER':
            self.desenhar_texto_centralizado("GAME OVER", self.fonte_titulo, altura_tela // 3, (255, 50, 50))
            self.desenhar_texto_centralizado("Pressione ENTER para voltar ao Menu", self.fonte, altura_tela // 2)

        elif self.estado == 'VICTORY':
            self.desenhar_texto_centralizado("Reino Salvo!", self.fonte_titulo, altura_tela // 3, (50, 255, 50))
            self.desenhar_texto_centralizado("Obrigado por jogar The Tale of an Amethyst!", self.fonte, altura_tela // 2)
            self.desenhar_texto_centralizado("Pressione ENTER para fechar a jornada.", self.fonte, altura_tela // 2 + 60)

        pygame.display.flip()

    def desenhar_hud(self):
        superficie_ui = pygame.Surface((largura_tela, 50), pygame.SRCALPHA)
        superficie_ui.fill(cor_remans_ui)
        self.tela.blit(superficie_ui, (0, 0))
        
        texto_coracoes = "S2 " * self.jogador.hearts
        self.tela.blit(self.fonte.render(f"Vida: {texto_coracoes}", True, (255, 50, 100)), (20, 12))
        
        if self.jogador.special_active:
            status_especial = "ATIVO"
            cor_status = (0, 255, 255)
        elif self.jogador.cooldown_timer > 0:
            segundos_restantes = math.ceil(self.jogador.cooldown_timer / 60)
            status_especial = f"AGUARDE ({segundos_restantes}s)"
            cor_status = (230, 100, 50)
        else:
            status_especial = "PRONTO (Botao Direito)"
            cor_status = (100, 255, 100)
            
        self.tela.blit(self.fonte.render(f"Especial: {status_especial}", True, cor_status), (250, 12))
        self.tela.blit(self.fonte.render(f"Energia: {self.jogador.stars}%", True, (255, 215, 0)), (540, 12))
        self.tela.blit(self.fonte.render(f"Flores: {self.jogador.flowers_collected}", True, (200, 100, 255)), (720, 12))
        self.tela.blit(self.fonte.render(f"Score: {self.jogador.score}", True, (255, 255, 255)), (880, 12))

    def desenhar_ui_dialogo(self):
        altura_caixa = 110
        superficie_dialogo = pygame.Surface((largura_tela - 40, altura_caixa), pygame.SRCALPHA)
        superficie_dialogo.fill((10, 10, 10, 220))
        pygame.draw.rect(superficie_dialogo, (150, 100, 220), (0, 0, largura_tela - 40, altura_caixa), 2)
        
        self.tela.blit(superficie_dialogo, (20, altura_tela - altura_caixa - 20))
        self.tela.blit(self.fonte.render(self.texto_dialogo, True, cor_texto), (40, altura_tela - altura_caixa - 5))
        self.tela.blit(self.fonte.render(self.substituto_voz_dialogo, True, (150, 255, 150)), (40, altura_tela - altura_caixa + 30))
        self.tela.blit(self.fonte.render("[Pressione 'E' para Continuar]", True, (180, 180, 180)), (700, altura_tela - 50))

    def desenhar_texto_centralizado(self, texto, fonte, pos_y, cor=cor_texto):
        superficie_texto = fonte.render(texto, True, cor)
        retangulo_texto = superficie_texto.get_rect(center=(largura_tela // 2, pos_y))
        self.tela.blit(superficie_texto, retangulo_texto)
