"""Textos do jogo (extraídos do arquivo 'dialogos' e 'História')."""

NOME_EXIBIDO = {"Safira": "Safira", "Louise": "Louise", "Anika": "Anika", "Meliah": "Meliah"}

FALAS = {
    "Anika": {
        "selecao": "Nenhum ataque passa por mim. Vamos nessa!",
        "planta": "Que criatura desagradável. Vou acabar com isso rapidamente.",
        "bruxa": "Poções? Truques baratos não vão funcionar comigo!",
        "vespa": "Não tenho tempo para lidar com você.",
        "boss": "Esse poder está consumindo você. Precisa parar!",
        "pouca_energia": "Preciso recuperar minhas forças.",
        "vitoria": "Conseguimos! A Ametista está segura. Agora podemos restaurar o equilíbrio.",
        "habilidade": "Vamos ver quem consegue atravessar!",
    },
    "Louise": {
        "selecao": "Abre espaço que o furacão tá passando!",
        "planta": "Cuidado com essa mordida! Vai acabar machucando alguém.",
        "bruxa": "EI! Eu não pedi uma transformação! Quero meu cabelo de volta!",
        "vespa": "Por que será que os insetos sempre querem me perseguir?!",
        "boss": "Ei! O que aconteceu com o Rei das Fadas?!",
        "pouca_energia": "Ops... minha energia está acabando!",
        "vitoria": "A Ametista está de volta! Da próxima vez, podiam simplesmente pedir emprestado...",
        "habilidade": "Hora de fazer uma bagunça!",
    },
    "Meliah": {
        "selecao": "Até o tempo adormece quando pedimos com gentileza.",
        "planta": "Ora, ora... acho que alguém esqueceu as boas maneiras.",
        "bruxa": "Transformar alguém sem consentimento? Que falta de delicadeza...",
        "vespa": "Oh, querida... acho que você está um pouco agitada.",
        "boss": "A Ametista precisa voltar ao seu lugar. Seu poder não deveria estar em suas mãos.",
        "pouca_energia": "Talvez seja melhor descansar um pouquinho.",
        "vitoria": "A Ametista finalmente poderá voltar ao seu lar. O equilíbrio será restaurado.",
        "habilidade": "Um momento de tranquilidade...",
    },
    "Safira": {
        "selecao": "Eai? Pronto pra dar uma voltinha?",
        "planta": "ECA! Essa planta precisa urgentemente de um dentista!",
        "bruxa": "Um sapo?! Ah, não! Isso definitivamente não combina comigo!",
        "vespa": "Está me seguindo por quê? Gostou de mim?",
        "boss": "Todo esse poder e ainda não foi suficiente pra você? Que folgado!",
        "pouca_energia": "Acho que preciso recarregar.",
        "vitoria": "Joia recuperada, problema resolvido. E ainda dá tempo de fazer as unhas!",
        "habilidade": "O céu parece um lugar melhor para ficar.",
    },
}

PODERES = {
    "Safira": ("Flutuar", "Ignora a gravidade por alguns segundos (a tecla de pular sobe, a de descer desce)."),
    "Louise": ("Pirueta Furacão", "Dano em área contínuo e repele os inimigos."),
    "Anika": ("Escudo Mágico", "Bloqueia ataques e poções vindos da frente."),
    "Meliah": ("Congelar o Tempo", "Inimigos e projéteis ficam em câmera lenta."),
}

NOMES_FASES = {
    1: ("Fase 1", "O Jardim Faminto"),
    2: ("Fase 2", "A Trilha das Bruxas"),
    3: ("Fase 3", "O Enxame da Floresta"),
    4: ("Fase 4", "O Caminho Corrompido"),
    5: ("Fase Final", "O Rei das Fadas Corrompido"),
}

HISTORIA = [
    "Há muitos séculos, quando o mundo ainda era jovem, os povos antigos selaram a maior de todas as alianças. "
    "Elfos, humanos e anões uniram suas essências para forjar um artefato sem igual: uma gema extraordinária que "
    "entrelaçava a profunda conexão élfica com a natureza, a magia arcana dos humanos e a inabalável força das "
    "profundezas mantida pelos anões.",
    "Sob a luz dessa pedra lendária, a terra prosperou. A flora e a fauna floresceram em uma abundância nunca antes "
    "vista, as correntes de magia se expandiram para abençoar todos os seres arcanos, e a vitalidade soprada naqueles "
    "povos concedeu-lhes vidas longas e livres de enfermidades.",
    "Contudo, nas sombras daquela era de ouro, a amargura se enraizou. As fadas, tomadas pelo ressentimento por terem "
    "sido excluídas do grande pacto, tramaram em segredo. Sob as ordens de seu rei, executaram um plano audacioso e "
    "roubaram a gema.",
    "Mas o que deveria ser o triunfo dos seres alados tornou-se a ruína de todos. Sem o equilíbrio da união original, "
    "a Ametista se corrompeu, vertendo uma escuridão profana que começou a se alastrar lentamente pelo mundo, "
    "sufocando a vida e distorcendo a magia.",
    "Diante do abismo iminente e tomados pelo desespero, os três reinos deixaram suas divergências de lado mais uma "
    "vez. Unindo suas últimas esperanças, convocaram e enviaram quatro campeãs humanas em uma jornada épica para "
    "recuperar a Ametista e salvar o mundo da penumbra eterna.",
]

CREDITOS_MUSICAS = [
    ("Menu Principal", "Town Theme RPG - cynicmusic"),
    ("Prólogo", "Medieval - Miguel Herrero"),
    ("Seleção de Personagem", "Movie Theater Intro - Matthew Pablo"),
    ("Combate (Fases 1 a 4)", "Blackmoor Tides (Epic Pirate Battle Theme) - Matthew Pablo"),
    ("Batalha de Chefe (Fase 5)", "A Slave To No One (RPG Orchestral Essentials) - InspectorJ"),
    ("Tela de Vitória", "Lively Meadow (Victory Fanfare and Song) - Matthew Pablo"),
    ("Créditos Finais", "Southern Pastures (Miniature Suite for Orchestra) - Matthew Pablo"),
    ("Tela de Derrota", "Spiritwatcher - Matthew Pablo"),
]


# ---------------------------------------------------------------- falas em sequência (E avança)
FADA = [
    "Por favor, escutem... O Rei das Fadas está escondido além da Floresta Encantada, nas profundezas do antigo santuário.",
    "Foi lá que ele levou a Ametista. Desde então, seu poder está completamente desequilibrado.",
    "Eu sei que não posso desfazer tudo o que aconteceu, mas... em nome do meu povo, peço desculpas por todo o sofrimento que causamos a vocês.",
    "Não deveríamos ter cobiçado a joia.",
    "Por favor, encontrem o Rei. Talvez ainda seja possível restaurar o equilíbrio.",
]

# a bruxa fala assim que aparece pela primeira vez (a 5ª fala muda para cada princesa)
BRUXA_ABERTURA = [
    "Olha só quem resolveu aparecer! Uma princesinha querendo bancar a heroína?",
    "Que gracinha! Mas não se preocupe, querida... já pensei em um destino perfeito para você.",
    "Vou transformá-la no meu bichinho favorito!",
    "Isso mesmo... UM SAPO!",
]
BRUXA_PERSONALIZADA = {
    "Anika": "Uma princesa tão corajosa! Que desperdício... Acho que vou transformá-la em um sapinho bem pequenininho. "
             "Quero ver essa coragem toda depois!",
    "Louise": "Ah, você parece ter energia de sobra! Perfeito! Vai ser uma sapinha saltitante. "
              "Aposto que vou me divertir muito com você!",
    "Meliah": "Uma princesa tão educada... seria uma pena perder essas boas maneiras. "
              "Mas não se preocupe, querida. Sapos também sabem coaxar com delicadeza!",
    "Safira": "Olha só, uma princesa que gosta de voar! Que tal experimentar a vida de um sapo? "
              "Nada de voar, querida... só pulinhos e lagoas!",
}
BRUXA_FINAL = "Agora fique quietinha... sua nova vida está prestes a começar!"


# a Fada ensina o jogo (as {chaves} são trocadas pelas teclas escolhidas em Opções)
# cada página: (painel que aparece em cima, texto)
FADA_TUTORIAL = [
    ("controles", "Antes de partirem, deixem-me ensinar o básico. Para andar, use {esquerda} e {direita}. "
                  "Para pular, use {pular}: segure para um pulo alto e solte cedo para um pulinho."),
    ("atacar", "Para atacar, segure {atirar}: sua magia sai na direção do cursor do mouse. "
               "Os inimigos aguentam vários golpes, então mire bem e não pare de se mover!"),
    ("poder", "Cada princesa tem um poder especial. Use {poder} para ativá-lo; ele gasta {custo} estrelas. "
              "O seu é {poder_nome}: {poder_desc}"),
    ("plataformas", "As plataformas no alto podem ser atravessadas por baixo. Para descer de uma delas, "
                    "segure {descer}. Algumas ficam bem altas: vá subindo de degrau em degrau!"),
    ("itens", "Os itens são raros, então aproveitem cada um: a Maçã devolve um coração; a Estrela recarrega a "
              "energia do seu poder; e a Flor... dizem que quem reúne 20 delas descobre um segredo dos gnomos. "
              "Itens soltos pelos inimigos somem rápido!"),
    ("inimigos", "Cuidado com o caminho: as Plantas mordem quando você chega perto; as Bruxas jogam poções que "
                 "transformam em sapinho por 10 segundos: sapinhos não atacam, mas correm e pulam mais alto que qualquer princesa; as Vespas perseguem sem parar."),
    ("objetivo", "Em cada região, derrote todos os inimigos e siga para a direita para avançar. Use {pausar} ou Esc "
                 "para pausar e {interagir} para falar comigo quando precisarem de ajuda. Boa sorte!"),
]
