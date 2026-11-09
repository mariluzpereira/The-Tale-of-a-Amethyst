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
        "planta": "ECA! Essa planta precisa urgentemente de um dentista!",
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
        "planta": "Cuidado com a mordida! Não quero perder um pedaço.",
        "bruxa": "Um sapo?! Ah, não! Isso definitivamente não combina comigo!",
        "vespa": "Está me seguindo por quê? Gostou de mim?",
        "boss": "Todo esse poder e ainda não foi suficiente pra você? Que ganância!",
        "pouca_energia": "Acho que preciso recarregar.",
        "vitoria": "Joia recuperada, problema resolvido. Estou louca pra tirar um cochilo!",
        "habilidade": "O céu parece um lugar melhor para ficar.",
    },
}

PODERES = {
    "Safira": ("Flutuar", "Ignora a gravidade por alguns segundos (W sobe, S desce)."),
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
    ("Menu", "Town Theme RPG - cynicmusic"),
    ("Prólogo", "Medieval - Miguel Herrero"),
    ("Seleção de personagem", "Movie Theater Intro - Matthew Pablo"),
    ("Combate", "Blackmoor Tides (Epic Pirate Battle Theme) - Matthew Pablo"),
    ("Boss", "A Slave To No One (RPG Orchestral Essentials) - InspectorJ"),
    ("Vitória", "Lively Meadow (Victory Fanfare and Song) - Matthew Pablo"),
    ("Créditos", "Southern Pastures (Miniature Suite for Orchestra) - Matthew Pablo"),
    ("Derrota", "Spiritwatcher - Matthew Pablo"),
]
