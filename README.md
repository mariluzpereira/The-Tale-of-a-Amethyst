# The-Tale-of-a-Amethyst


1. Título do Jogo:

The Tale of an Amethyst



2. Descrição Geral:

Tipo: Aventura Side-scrolling (Plataforma 2D).

Ambiente: Reino Mágico (Florestas, Jardins e Castelos).

Ideia Principal: Um jogo desenvolvido em Pygame focado em quatro princesas que usam poderes elementais e temporais para salvar seu reino. O jogo destaca o combate com mouse, dublagem para acessibilidade e escolhas narrativas.



3. Objetivo do Jogo:

Meta Principal: Atravessar as fases e derrotar o Rei das Fadas Corrompido.

Condição de Vitória: Vencer o Boss final. O final varia conforme as escolhas feitas nos diálogos.



4. Personagens Principais:

As protagonistas possuem habilidades únicas que consomem a barra de energia (estrelas)

Safira: Capacidade de Flutuar, ignorando a gravidade por alguns segundos.

Louise: Realiza Piruetas Furacão, causando dano em área e repelindo ameaças.

Anika: Ativa um Escudo Mágico que bloqueia ataques frontais.

Meliah: Pode Congelar o Tempo, deixando inimigos e projéteis em slow motion.



5. Inimigos e Obstáculos:

Bruxa: Ataca com projéteis mágicos à distância.

Planta Carnívora: Obstáculo estático que causa dano ao contato.

Vespa: Inimigo voador que persegue o jogador velozmente.

Rei das Fadas Corrompido: Boss final com padrões complexos de ataque.



6. Cenário (Mapa):

O mapa é composto por tiles de chão, plataformas suspensas e abismos. Os itens (Maçãs, Estrelas e Flores) estão distribuídos pelo caminho, e o objetivo final fica na extremidade direita de cada nível.



7. Sistema de Pontuação:

Ganho de Pontos: Ao derrotar inimigos e coletar itens.

Easter Egg: Ao coletar 20 Flores, dois gnomos ou fadas aparecem e realizam uma dança especial na tela.



8. Sistema de Vida (Corações):

Quantidade Inicial: O jogador possui 5 corações.

Mecânica de Dano: Cada colisão com inimigos ou projéteis faz um coração sumir.

Recuperação: Coletar Maçãs restaura corações perdidos.

Derrota: Se todos os corações sumirem, a tela de Game Over surge.



9. Controles:

Teclas A / D: Movimentação lateral.

Tecla W / Espaço: Pular.

Botão Esquerdo do Mouse: Ataque básico (direcionado pelo cursor).

Botão Direito do Mouse: Ativar Poder Especial da princesa escolhida.

Tecla E: Interagir com NPCs e avançar diálogos.



10. Fluxo do Jogo:

O jogo inicia no Menu Principal com a seleção de personagem. Durante a partida, o jogador enfrenta fases de plataforma e combate, intercaladas por diálogos dublados. O jogo termina com a batalha contra o Boss e o desfecho da história.



11. Regras do Jogo:

Respeitar os limites físicos do mapa (não atravessar paredes).

Ataques só funcionam se a mira do mouse estiver sobre o alvo ou na trajetória correta.

O uso de poderes especiais é limitado pela barra de estrelas disponível.



12. Estrutura do Projeto:

A organização do projeto no GitHub deve seguir esta divisão de responsabilidades:

Arquivo Raiz (main.py): Ponto de entrada que executa o loop do jogo e gerencia as trocas de tela.

Pasta de Código (src): Contém os scripts player.py (lógica das princesas e poderes), enemies.py (comportamento dos vilões), map.py (carregamento de níveis) e ui.py (exibição de corações e legendas).

Pasta de Ativos (assets): Organizada em subpastas para images (sprites e cenários), audio (músicas e efeitos) e voice (arquivos de dublagem para os diálogos).

Documentação (README.md): Arquivo de texto explicando o jogo e como instalá-lo.



13. Funcionalidades Mínimas (MVP):

Movimentação completa e sistema de pulo.

Interface com os 5 corações funcionando (perdendo vida ao colidir).

Ataque básico seguindo a posição do mouse.

Sistema de diálogo com áudio e texto na tela.



14. Melhorias Futuras:

Inclusão de efeitos visuais (partículas) para cada poder especial.

Sistema de salvamento de progresso (Save Game).

Novos tipos de ataques básicos desbloqueáveis.

Modo de acessibilidade com alto contraste para as legendas.
