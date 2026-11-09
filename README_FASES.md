# Atualização: jogo completo com 5 fases

Copie TODOS os arquivos deste zip para dentro da pasta do projeto (onde já estão
as imagens e músicas), substituindo os .py antigos. Depois:

    pip install pygame
    python jogo.py

## Controles
A/D (ou setas) mover · W/Espaço pular (solte antes para pular baixo) · S desce das plataformas
Mouse esquerdo (segure): atirar na direção do cursor · Mouse direito: poder especial
E: fechar legenda · Esc/P: pausar

## Fases
1 Plantas · 2 Bruxas (andam e lançam poções em arco; poção = sapinho por 10 s) ·
3 Vespas · 4 Plantas + Bruxas + Vespas · 5 Boss (3 fases de ataque).
Para avançar: matar todos os inimigos e sair andando pela direita.
Edite as fases em `fases.py` (posições de plataformas, inimigos, itens).

## Sons
Músicas: usa os arquivos do projeto. Efeitos: gerados por código; para trocar por
um som real, coloque `sfx_<nome>.wav` na pasta (ex.: `sfx_pulo.wav`; nomes em sons.py).
Dublagem: `dublagem/<personagem>_<fala>.ogg` toca junto com a legenda
(ex.: `dublagem/anika_planta.ogg`; falas: selecao, planta, bruxa, vespa, boss,
pouca_energia, vitoria, habilidade).

## Sprites que ainda faltam (hoje há desenhos de reserva feitos por código)
Ao criar os PNGs com estes nomes, o jogo passa a usá-los sozinho:
bruxa_parada.png, bruxa_andando(1).png, bruxa_andando(2).png, bruxa_lancando.png (viradas p/ direita)
planta_fechada.png, planta_mordendo.png
boss_voando(1).png, boss_voando(2).png (virado p/ direita)

## Balanceamento rápido
Vida do boss: `self.hp` em `Boss` (inimigos.py) · dano do tiro: `dano_tiro_jogador` (configuracoes.py)
Duração do sapinho: `tempo_sapinho` em jogador.py · custo do poder: `custo_poder`
