"""Teste de áudio SEM abrir o jogo: descobre se o chiado/travamento vem do
arquivo de música, do jogo ou do computador.

Uso (na pasta do jogo):
    python testar_audio.py              -> toca cada música por 15 s com buffer 2048
    python testar_audio.py 512          -> mesmo teste com buffer 512 (o antigo do jogo)
    python testar_audio.py 4096 30      -> buffer 4096, 30 s por música
    python testar_audio.py 2048 15 sfx  -> também dispara muitos efeitos junto com a música

Como interpretar (escute com fones/caixas que você usa para jogar):
  * chia só com buffer 512 e fica limpo com 2048/4096  -> era o buffer (o jogo agora usa 2048)
  * chia sempre numa música específica, em qualquer buffer -> problema do ARQUIVO (reexporte em OGG)
  * chia em todas as músicas, em qualquer buffer           -> problema do COMPUTADOR
        (driver de áudio, fone Bluetooth, modo economia de energia, CPU ocupada)
  * só chia quando o modo 'sfx' dispara os efeitos         -> sons empilhando/estalando (clipping):
        abaixe o volume da música/efeitos em Opções
  * limpo aqui, mas chia dentro do jogo                    -> o jogo estava pesado (veja a seção do README)
"""
import sys
import pygame

buffer = int(sys.argv[1]) if len(sys.argv) > 1 else 2048
segundos = int(sys.argv[2]) if len(sys.argv) > 2 else 15
com_sfx = len(sys.argv) > 3 and sys.argv[3] == "sfx"

pygame.mixer.pre_init(44100, -16, 2, buffer)
pygame.init()
print("mixer aberto:", pygame.mixer.get_init(), "(frequência, formato, canais) | buffer pedido:", buffer)

from recursos import achar
musicas = ["menu.mp3", "selecao_personagem.mp3", "prologo.ogg", "combate.mp3", "boss.mp3",
           "vitoria.wav", "derrota.mp3", "creditos.mp3", "easter_egg_musica.mp3"]
audio = None
if com_sfx:
    from sons import Audio
    audio = Audio()
    nomes = [n for n in ("tiro_safira", "acerto_planta", "pulo", "dano", "item", "boss_tiro", "passo") if n in audio.sfx]

for nome in musicas:
    caminho = achar(nome)
    if not caminho:
        print("[falta] %s" % nome)
        continue
    print(">> tocando %s por %d s ..." % (nome, segundos))
    try:
        pygame.mixer.music.load(caminho)
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play()
    except pygame.error as e:
        print("   ERRO ao abrir o arquivo:", e)
        continue
    for t in range(segundos * 10):
        pygame.event.pump()
        if audio and t % 3 == 0:
            audio.tocar(nomes[(t // 3) % len(nomes)])
        pygame.time.wait(100)
        if not pygame.mixer.music.get_busy():
            break
    pygame.mixer.music.stop()
print("fim.")
