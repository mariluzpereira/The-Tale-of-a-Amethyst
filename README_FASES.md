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
Músicas: arquivos do projeto (easter_egg_musica.mp3: ver Easter egg abaixo).
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

## Easter egg (as 20 flores)
Ao coletar a 20ª flor nada é anunciado: um gnomo passa a espiar do canto inferior direito da tela.
Clique nele (o clique não vira tiro): ele vai para o meio da tela e dança por 10 s; a música do easter egg
começa só quando ele começa a dançar. Ao sumir, a música dele acaba e volta a música da fase.
O jogo fica parado enquanto ele dança. Dura/tempos: constantes GNOMO_* em main_jogo.py.

## Falas antes do combate
As falas ligadas a cada inimigo (princesa e bruxa) acontecem no INÍCIO da fase e param o jogo: enquanto
houver fala (ou a faixa com o nome da fase) os inimigos ficam parados e não atacam nem ferem.
O combate só começa quando a última fala termina e a faixa some. Cada fala toca uma vez por partida.

## Ajustes recentes
* **Easter egg do gnomo**: ao juntar as 20 flores NADA aparece no meio da tela. Um gnomo passa a espiar
  escondido no canto inferior direito (só a pontinha do chapéu e a cabeça aparecem). Clique nele: ele vai
  para o meio da tela e dança por ~10 s. A música dele só começa quando a dança começa; a música da fase
  fica em pausa e, quando o gnomo some, a dele termina junto e a da fase continua de onde parou.
  O jogo fica parado durante a dança. (Constantes GNOMO_* em main_jogo.py)
* **Diálogos antes do combate**: as falas da fase (princesa e bruxa) acontecem assim que a fase começa e
  o jogo fica parado até terminarem: nenhum inimigo se mexe, ataca ou machuca. Depois da fala ainda há a
  faixa com o nome da fase; só então o combate começa. Cada tipo de inimigo é apresentado uma vez por partida.
* **Sapinho**: pula mais alto (~210 px contra ~155 da princesa) e mais depressa (pulinho de ~38 frames
  contra ~46) e anda mais rápido (6,5 contra 5,0). Consegue subir sozinho nas plataformas do 2º degrau.
  Valores em configuracoes.py (sapo_*).

## Mais ajustes
* **Avisos sobre a personagem**: um quadrinho pequeno aparece em cima dela e some sozinho em 5 s
  (o tempo não corre durante a pausa ou as falas): "Poder pronto!" (energia recarregada ou fim da
  recarga), "Energia baixa!/Sem energia!" e "Vida acabando!" (ao chegar em 1 coração). Eles substituem
  as falas grandes de "pouca energia". Textos e cores em `_checar_avisos` / `usar_poder` (main_jogo.py).
* **Menu de pausa**: Esc (ou a tecla de pausar) abre o menu com a mesma imagem do menu principal:
  Continuar, Opções, Menu principal e Sair. As Opções abertas na pausa voltam para a pausa.
* **Final do jogo**: depois da vitória e dos créditos aparece a tela "Obrigada por jogarem!".
  O espaço da animação das personagens já está pronto: quando ela existir, salve os quadros como
  `animacao_final(1).png`, `animacao_final(2).png`... na pasta do jogo e ela aparece sozinha acima da mensagem.
* **Prólogo**: o texto da história rola dentro de uma caixa roxa, legível sobre qualquer cenário.

## Sprites das princesas (v7)
* **Parada**: a princesa parada usa o quadro `*_movimentacao_direita(2)` / `*_movimentacao_esquerda(2)`.
* **Atingida**: ao levar dano mostra `*_atingida_direita/esquerda(1)` por ~0,6 s; depois pisca como antes.
* **Derrotada**: ao perder, aparece `*_derrotada(1)` (no jogo e, grande, na tela de Game Over).
  Se perder como sapinho, aparece o sapinho morto.
* **Furacão da Louise**: usa `furacão_sprite(1..3)`.
* **Sapinho**: o jogo confere para onde cada sprite olha (pelos olhos) e espelha sozinho se estiver
  virada para o lado errado. Hoje isso corrige `anika_sapo_pulo_direita/esquerda.png`, que estão trocados.
* Aviso de arte: `safira_movimentacao_*(2).png` é bem maior que os quadros 1 e 3; o jogo ajusta o tamanho
  automaticamente, mas as proporções do quadro (cabeça maior) ficam diferentes.
* **Fadinha**: usa `fadinha (2).png` (ou `fadinha.png`); na casa dela ficou menor e perto da porta.
* **Animação final**: `animacao_final(1..N).png` aparece numa moldura ao lado de "Obrigada por jogarem!".
* `cenario_prologo.jpg` não veio no último zip: sem ele o prólogo usa a casa da fada como fundo.

## Imagens leves (relógio da Meliah, gnomo, retratos)
O relógio do poder da Meliah, os quadros do gnomo e os retratos vêm de `extras/`. Se essa pasta não
existir, o jogo gera as versões leves sozinho na primeira abertura (a partir de
`habilidade_congelar_tempo_relogio(1).png`, `gnomo_easter_egg.gif`, `*_sprite_dialogo(1).png`) e guarda em
`extras/`. Para os quadros do gnomo é preciso o Pillow (`pip install pillow`); sem ele aparece um
quadro só, dançando em pulinhos. Se nem o arquivo do relógio abrir, um relógio desenhado por código é usado.
