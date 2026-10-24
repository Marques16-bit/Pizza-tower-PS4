#!/usr/bin/env python3
"""Injeta no main.c do PS4 (Butterscotch) a checagem prévia dos arquivos do jogo.

- Troca qualquer caminho "...data.win" do main.c por /data/pizza-tower/data.win.
- Antes de iniciar o runner, confere se esse data.win existe e começa com "FORM".
  Se não existir, cria /data/pizza-tower/ com um aviso em texto e encerra sem rodar o jogo.
Uso: python3 scripts/inject_preflight.py vendor/butterscotch/src/ps4/main.c
"""
import pathlib
import re
import sys

GAME_DIR = "/data/pizza-tower"
MARK = "PT_PREFLIGHT"

BLOCK = r'''/* ---- PT_PREFLIGHT: inserido por scripts/inject_preflight.py ---- */
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <dirent.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>

#define PT_GAME_DIR "@DIR@"
#define PT_GAME_WIN PT_GAME_DIR "/data.win"
#define PT_LOG_FILE PT_GAME_DIR "/log.txt"

static const char PT_HELP[] =
    "PIZZA TOWER PS4\n"
    "\n"
    "Os arquivos do jogo nao foram encontrados.\n"
    "Copie a pasta do seu Pizza Tower (com o mod de icones PS4 ja aplicado) para esta pasta, por FTP:\n"
    "\n"
    "  " PT_GAME_DIR "/data.win\n"
    "  e o resto da pasta do jogo (sons, idiomas etc.)\n"
    "\n"
    "O data.win precisa ficar direto nesta pasta, sem subpasta no meio.\n"
    "Depois abra o app de novo. O que o app fez fica em log.txt, nesta pasta.\n";

/* Manda stdout e stderr para log.txt (sem buffer, para sobrar registro mesmo se travar). */
static void pt_log_start(void) {
    FILE *t;
    mkdir(PT_GAME_DIR, 0777);
    t = fopen(PT_LOG_FILE, "w");
    if (t) fclose(t);
    if (freopen(PT_LOG_FILE, "a", stdout)) setvbuf(stdout, NULL, _IONBF, 0);
    if (freopen(PT_LOG_FILE, "a", stderr)) setvbuf(stderr, NULL, _IONBF, 0);
    printf("[PizzaTower] log iniciado\n");
}

static void pt_list_dir(void) {
    int count = 0;
    struct dirent *e;
    DIR *d = opendir(PT_GAME_DIR);
    if (!d) {
        printf("[PizzaTower] nao consegui abrir %s (errno=%d)\n", PT_GAME_DIR, errno);
        return;
    }
    printf("[PizzaTower] conteudo de %s:\n", PT_GAME_DIR);
    while ((e = readdir(d)) != NULL && count < 200) {
        printf("  %s\n", e->d_name);
        count++;
    }
    closedir(d);
}

static int pt_data_win_ok(void) {
    unsigned char m[4] = {0, 0, 0, 0};
    size_t n;
    FILE *f = fopen(PT_GAME_WIN, "rb");
    if (!f) {
        printf("[PizzaTower] fopen(%s) falhou, errno=%d\n", PT_GAME_WIN, errno);
        return 0;
    }
    n = fread(m, 1, sizeof(m), f);
    fclose(f);
    printf("[PizzaTower] primeiros bytes do data.win: %02x %02x %02x %02x (lidos=%u)\n",
           m[0], m[1], m[2], m[3], (unsigned)n);
    return n == sizeof(m) && memcmp(m, "FORM", 4) == 0;
}

static void pt_write_help(void) {
    FILE *f;
    mkdir(PT_GAME_DIR, 0777);
    f = fopen(PT_GAME_DIR "/COLOQUE_OS_ARQUIVOS_DO_JOGO_AQUI.txt", "wb");
    if (!f) return;
    fputs(PT_HELP, f);
    fclose(f);
}

/* Retorna 1 se o jogo pode iniciar; 0 se faltam arquivos. */
static int pt_preflight(void) {
    pt_log_start();
    pt_list_dir();
    if (!pt_data_win_ok()) {
        printf("[PizzaTower] data.win ausente ou invalido: o jogo nao sera iniciado\n");
        pt_write_help();
        return 0;
    }
    if (chdir(PT_GAME_DIR) != 0) {
        printf("[PizzaTower] chdir(%s) falhou, errno=%d\n", PT_GAME_DIR, errno);
    }
    printf("[PizzaTower] data.win ok; iniciando o runner\n");
    return 1;
}
/* ---- fim PT_PREFLIGHT ---- */

'''.replace("@DIR@", GAME_DIR)

MAIN_RE = re.compile(r'^[ \t]*(?:static\s+)?int\s+main\s*\([^)]*\)\s*\{', re.M)
PATH_RE = re.compile(r'"[^"\n]*data\.win"')


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = pathlib.Path(sys.argv[1])
    src = path.read_text(encoding="utf-8")

    if MARK in src:
        print("preflight já injetado; nada a fazer")
        return 0

    m = MAIN_RE.search(src)
    if not m:
        print("ERRO: não achei 'int main(...) {' em", path, file=sys.stderr)
        for i, line in enumerate(src.splitlines(), 1):
            if "main" in line:
                print(f"  {i}: {line}", file=sys.stderr)
        return 1

    print("main encontrado:", m.group(0).strip())

    # 1) caminho do data.win
    found = PATH_RE.findall(src)
    src = PATH_RE.sub('"' + GAME_DIR + '/data.win"', src)
    if found:
        for old in found:
            print(f"caminho trocado: {old} -> \"{GAME_DIR}/data.win\"")
    else:
        print("AVISO: nenhum caminho 'data.win' literal no main.c; "
              "o runner pode receber o caminho de outro jeito (precisa ser ligado à mão).")

    # 2) chamada no começo do main e bloco antes dele (chamada primeiro: posição mais à frente)
    m = MAIN_RE.search(src)
    call = "\n    if (!pt_preflight()) { return 0; } /* PT_PREFLIGHT */"
    src = src[:m.end()] + call + src[m.end():]
    src = src[:m.start()] + BLOCK + src[m.start():]

    path.write_text(src, encoding="utf-8")
    print("preflight injetado em", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
