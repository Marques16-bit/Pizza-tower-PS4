# Pizza Tower PS4 (runner GameMaker via OpenOrbis)

Port de Pizza Tower para PS4 desbloqueado (GoldHEN) usando um runner open source (Butterscotch).
Tudo é editado pelo celular e compilado pelo GitHub Actions.

## Como usar
1. O workflow `.github/workflows/ps4.yml` roda a cada push ou manualmente (Actions > ps4 > Run workflow).
2. Ele baixa o OpenOrbis, baixa o Butterscotch na versão fixada em `project.env`, compila e publica `out/` (artifact `ps4-out`).
3. Os arquivos do jogo NÃO entram no repositório: copie para o PS4 por USB/FTP (veja `mods/README.md`).

## Onde mexer
- `project.env`: versão do Butterscotch e flags do CMake.
- `config/`: preset de vídeo travado e mapa do controle.
- `patches/`: nossas alterações no runner.
- `mods/`: mod de ícones PS4 e patch do menu.
- `docs/ARQUITETURA.md`: como as peças se encaixam e regras de código.
