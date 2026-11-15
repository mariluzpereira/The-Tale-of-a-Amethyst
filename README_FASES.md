# The Tale of an Amethyst - jogo com 5 fases

Copie TODOS os arquivos deste zip (inclusive a pasta `extras/`) para a pasta do projeto,
substituindo os .py antigos. Depois:

    pip install pygame
    python jogo.py

Na primeira abertura o jogo prepara os retratos e os efeitos sonoros (uns segundos, com barra de
carregamento) e guarda tudo em `extras/` e `sfx_cache_v4/`; nas próximas abre direto.

## Fluxo
Menu > Escolha da princesa > Prólogo (cenário + texto lento) > Casa da Fada (conversa e tutorial,
sem inimigos) > Fases 1 a 5 > Vitória > Créditos.
Na fase 1 a Fadinha fica perto do início: chegue perto e aperte a tecla de interagir para rever o tutorial.

## Controles (todos podem ser mudados em Opções)
Padrão: A/D ou setas = andar · W ou Espaço = pular · S ou seta p/ baixo = descer da plataforma ·
mouse esquerdo = atirar (segure) · mouse direito = poder especial · E = falar/avançar · P ou Esc = pausar.
Opções: setas navegam, Enter (ou clique) em uma tecla e aperte a nova; Backspace limpa; Esc cancela.
Se a tecla já era de outra ação, as duas trocam de lugar. As escolhas ficam em `config_teclas.json`.

## Dificuldade e itens (tudo em configuracoes.py, seção DIFICULDADE)
Vida: planta 10, bruxa 10, vespa 9, chefe 260 · vespas e bruxas mais rápidas · plantas mordem
mais cedo e de mais longe · chefe com mais ataques, fogo e contato que tiram 2 corações.
Começa com 60 estrelas; estrela = +15; inimigos raramente soltam itens (10% estrela, 4% maçã) e o
item solto some em 7 s. Os itens da fase ficam em "torres" de plataformas altas (ver fases.py);
as 20 flores estão todas nos degraus mais altos.

## Sons
Músicas: arquivos do projeto (easter_egg_musica.mp3 toca ao juntar as 20 flores).
Efeitos (57): passos, pulo, pouso, tiro de cada princesa, acerto/morte de cada inimigo, itens, poderes,
vida baixa, poder pronto, falas (som de digitação), menus, teclas, pausa... Para trocar um por um
som seu, coloque `sfx_<nome>.wav` na pasta (nomes em sons.py). Dublagem: `dublagem/<personagem>_<fala>.ogg`.

## Chiado / travamento da música
1. Rode `python testar_audio.py` (e também `python testar_audio.py 512`) e escute: ele toca cada
   música fora do jogo. As instruções para interpretar estão no topo do arquivo.
2. O jogo agora usa buffer de áudio 2048, evita sons iguais empilhados e prepara tudo antes do menu.
3. Se aparecer chiado só dentro do jogo, abaixe o volume da música em Opções (os arquivos já vêm no máximo).

## Se alguma sprite não aparecer
Ao abrir, o jogo confere todas as imagens e músicas. Se algo faltar (ou não abrir), aparece um aviso
amarelo no menu e é gravado `diagnostico_recursos.txt`. O jogo procura também em subpastas.

## Sprites usadas (se faltar o arquivo, entra um desenho feito por código)
Princesas: *_movimentacao_direita/esquerda(1..3), *_pulo (novo), *_sapo_*, power_*; menu: menu, jogar,
opcoes, creditos, sair (novo); prólogo: cenario_prologo.jpg (novo); Fada: fadinha.png + retrato.
Bruxa, Planta, Boss, Vespa: ver o topo de desenho.py.
Aviso sobre a arte: no `safira_movimentacao_*(2).png` a Safira está ~1,7x maior que nos quadros 1 e 3;
o jogo corrige isso automaticamente, mas o ideal é reexportar o quadro 2 no mesmo tamanho.
