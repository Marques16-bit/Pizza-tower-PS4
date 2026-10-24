# Patches no runner

Nossas alterações no Butterscotch ficam aqui como arquivos `.patch` (git diff).
O `scripts/build_ps4.sh` aplica todos, em ordem alfabética, em `vendor/butterscotch`
antes de compilar. Assim o runner original fica intacto e fácil de atualizar.

Planejados (ainda não escritos):
- 0001-ps4-paths.patch: ler o jogo de /data/pizza-tower/ (ou /mnt/usb0/pizza-tower/)
- 0002-video-lock.patch: aplicar config/ps4_video.ini e neutralizar funções de vídeo
- 0003-ps4-controller.patch: aplicar config/controller_map.ini

Só vamos escrevê-los depois de ver o código do PR de PS4 no log da primeira compilação.
