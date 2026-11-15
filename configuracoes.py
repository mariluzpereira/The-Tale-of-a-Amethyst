import os

# ---------------------------------------------------------------- tela
largura_tela = 1024
altura_tela = 576
fps = 60

# ---------------------------------------------------------------- física
gravidade = 0.6

# pasta onde estão os arquivos do jogo (imagens, sons...)
pasta_base = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- balanceamento geral
vida_maxima = 5
estrelas_maximas = 100
estrelas_iniciais = 60           # começa com menos energia (2 usos de poder)
custo_poder = 30
dano_tiro_jogador = 2
escala_tempo_congelado = 0.2     # Meliah: inimigos a 20% da velocidade
total_fases = 5
total_flores_easter_egg = 20

# ---------------------------------------------------------------- DIFICULDADE (mexa aqui para ajustar)
# vida dos inimigos (cada tiro da princesa tira 'dano_tiro_jogador')
hp_planta = 10
hp_bruxa = 10
hp_vespa = 9
hp_boss = 260
# velocidade / agressividade
vel_vespa = 3.0                  # (era 2.5)
vel_bruxa = 2.0                  # (era 1.6)
recarga_bruxa = (80, 125)        # frames entre poções (era 110-170)
recarga_planta = 70              # frames entre mordidas (era 100)
recuo_vespa = 35                 # frames que a vespa recua depois de ferir (era 55)
vel_orbe_boss = 6.0
vel_fogo_boss = 7.5
dano_fogo_boss = 2               # corações que a bola de fogo tira
dano_contato_boss = 2
# itens: raros e difíceis
ganho_estrela = 15               # energia por estrela coletada (era 25)
chance_drop_estrela = 0.10       # chance de um inimigo soltar estrela (era 40%)
chance_drop_maca = 0.04          # chance de soltar maçã (era 22%)
tempo_item_dropado = 420         # frames até o item solto desaparecer (7 s)

# ---------------------------------------------------------------- áudio
volume_musica_padrao = 0.40      # as músicas são masterizadas no máximo: deixe margem
volume_sfx_padrao = 0.50

# ---------------------------------------------------------------- cores (substitutos das sprites)
cor_fundo = (30, 20, 40)
cor_chao = (45, 130, 80)
cor_plataforma = (100, 70, 40)
cor_remans_ui = (20, 20, 20, 150)
cor_texto = (255, 255, 255)

# cores das princesas
cor_safira = (50, 150, 255)   # azul
cor_louise = (220, 220, 50)   # amarelo
cor_anika = (50, 200, 100)    # verde
cor_meliah = (180, 50, 200)   # roxo

# cores dos inimigos
cor_bruxa = (140, 20, 180)
cor_planta = (200, 50, 50)
cor_vespa = (230, 150, 0)
cor_boss = (255, 0, 50)

# ---------------------------------------------------------------- nomes de arquivo de cada princesa
# (no projeto a Meliah aparece como "melia" nos arquivos)
nomes_arquivo = {
    "Safira": "safira",
    "Louise": "louise",
    "Anika": "anika",
    "Meliah": "melia",
}

# arquivos dos ataques básicos: power_<cor>_<nome>(n).png
arquivo_poder = {
    "Safira": "power_rosa_safira",
    "Louise": "power_vermelho_louise",
    "Anika": "power_azul_anika",
    "Meliah": "power_roxo_melia",
}

cor_particula = {
    "Safira": (255, 160, 210),
    "Louise": (235, 80, 80),
    "Anika": (100, 190, 255),
    "Meliah": (180, 140, 240),
}

cores_princesa = {
    "Safira": cor_safira,
    "Louise": cor_louise,
    "Anika": cor_anika,
    "Meliah": cor_meliah,
}
