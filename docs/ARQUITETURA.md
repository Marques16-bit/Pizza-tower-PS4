# Arquitetura

Pizza Tower é um jogo GameMaker sem código-fonte público. Em vez de portar o jogo, portamos o RUNNER:
o Butterscotch lê o data.win (bytecode) e reimplementa o motor do GameMaker em C.

## Peças
1. Runner: Butterscotch no commit fixado em project.env (baixado no build, não versionado).
2. Backend PS4: vem do PR #647 do Butterscotch (OpenOrbis, entrada/áudio/tempo via SDL, renderizador por CPU).
   Estado em 24/10/2026: PR aberto, testado só no emulador shadPS4; sem confirmação em PS4 real.
3. Dados: data.win + mod de ícones, copiados pelo usuário para o PS4. Fora do repositório.
4. CI: .github/workflows/ps4.yml (OpenOrbis + build + artifact).

## Estado conhecido do Pizza Tower no Butterscotch (outubro/2026)
Entra no jogo, ainda instável; o áudio depende de uma reimplementação do FMOD que o jogo usa.

## Regras de código (evitar memory leaks)
- Toda alocação tem um dono explícito; quem aloca documenta quem libera.
- Alocar/liberar só por funções em src/core (contador de alocações em build debug).
- Build debug termina imprimindo alocações pendentes; qualquer valor diferente de zero é bug.
- Sem variáveis globais com ponteiros próprios; passar contexto por parâmetro.
- Mudanças no runner entram como patches pequenos e documentados, um assunto por patch.
