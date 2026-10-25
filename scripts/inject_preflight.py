#!/usr/bin/env python3
"""Ajusta o main.c do PS4 (Butterscotch) para o projeto Pizza Tower.

1. Troca qualquer caminho "...data.win" por /data/pizza-tower/data.win.
2. Antes de iniciar o runner: confere data.win (existe e começa com "FORM"),
   grava log em /data/pizza-tower/log.txt com escrita direta em arquivo,
   testa quanta memória o app consegue alocar, registra sinais de falha e a saída do app.
   Se faltar o jogo, cria a pasta com um aviso em texto e encerra sem rodar o runner.
3. Move a pasta de saves para /data/pizza-tower/save e registra o início e o fim do loop().
Uso: python3 scripts/inject_preflight.py vendor/butterscotch/src/ps4/main.c
"""
import pathlib
import re
import sys

GAME_DIR = "/data/pizza-tower"
MARK = "PT_PREFLIGHT"

BLOCK = r'''/* ---- PT_PREFLIGHT: inserido por scripts/inject_preflight.py ---- */
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
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

/* Log por escrita direta: abre, grava e fecha a cada linha (sobra registro mesmo se o app cair). */
void pt_log(const char *fmt, ...) {
    char buf[512];
    int n, fd;
    va_list ap;
    va_start(ap, fmt);
    n = vsnprintf(buf, sizeof(buf) - 1, fmt, ap);
    va_end(ap);
    if (n < 0) return;
    if (n > (int)sizeof(buf) - 2) n = (int)sizeof(buf) - 2;
    buf[n++] = '\n';
    fd = open(PT_LOG_FILE, O_WRONLY | O_CREAT | O_APPEND, 0666);
    if (fd < 0) return;
    (void)!write(fd, buf, (size_t)n);
    close(fd);
}

static void pt_log_reset(void) {
    int fd;
    mkdir(PT_GAME_DIR, 0777);
    fd = open(PT_LOG_FILE, O_WRONLY | O_CREAT | O_TRUNC, 0666);
    if (fd >= 0) close(fd);
}

/* Manda stdout e stderr (mensagens do runner) para o mesmo arquivo. */
static void pt_redirect_std(void) {
    int fd = open(PT_LOG_FILE, O_WRONLY | O_CREAT | O_APPEND, 0666);
    if (fd < 0) return;
    dup2(fd, 1);
    dup2(fd, 2);
    if (fd > 2) close(fd);
}

static void pt_on_exit(void) {
    pt_log("[PizzaTower] app encerrando (exit)");
}

static void pt_on_signal(int sig) {
    char b[48] = "[PizzaTower] SINAL ";
    int i = 19, fd;
    if (sig >= 10) b[i++] = (char)('0' + (sig / 10) % 10);
    b[i++] = (char)('0' + sig % 10);
    b[i++] = '\n';
    fd = open(PT_LOG_FILE, O_WRONLY | O_CREAT | O_APPEND, 0666);
    if (fd >= 0) {
        (void)!write(fd, b, (size_t)i);
        close(fd);
    }
    _exit(128 + sig);
}

static void pt_list_dir(void) {
    int count = 0;
    struct dirent *e;
    DIR *d = opendir(PT_GAME_DIR);
    if (!d) {
        pt_log("[PizzaTower] nao consegui abrir %s (errno=%d)", PT_GAME_DIR, errno);
        return;
    }
    pt_log("[PizzaTower] conteudo de %s:", PT_GAME_DIR);
    while ((e = readdir(d)) != NULL && count < 200) {
        pt_log("  %s", e->d_name);
        count++;
    }
    closedir(d);
}

static int pt_data_win_ok(void) {
    unsigned char m[4] = {0, 0, 0, 0};
    size_t n;
    long size = -1;
    FILE *f = fopen(PT_GAME_WIN, "rb");
    if (!f) {
        pt_log("[PizzaTower] fopen(%s) falhou, errno=%d", PT_GAME_WIN, errno);
        return 0;
    }
    n = fread(m, 1, sizeof(m), f);
    if (fseek(f, 0, SEEK_END) == 0) size = ftell(f);
    fclose(f);
    pt_log("[PizzaTower] primeiros bytes do data.win: %02x %02x %02x %02x (lidos=%u)",
           m[0], m[1], m[2], m[3], (unsigned)n);
    pt_log("[PizzaTower] data.win tem %ld bytes", size);
    return n == sizeof(m) && memcmp(m, "FORM", 4) == 0;
}

static int pt_file_exists(const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) return 0;
    fclose(f);
    return 1;
}

/* Mesma funcao do libkernel, com nome local para nao conflitar com nenhum header. */
extern int pt_load_start_module(const char *name, unsigned long argc, const void *argv,
                                unsigned flags, void *opt, int *res) __asm__("sceKernelLoadStartModule");

/* Tenta carregar o modulo e registra o codigo: 0x80020002 = arquivo ausente, 0x8002000D = arquivo danificado. */
static void pt_try_module(const char *path) {
    int res = 0;
    int h;
    if (!pt_file_exists(path)) return;
    h = pt_load_start_module(path, 0, NULL, 0, NULL, &res);
    pt_log("[PizzaTower] sceKernelLoadStartModule(%s) = 0x%08x (res=%d)", path, (unsigned)h, res);
}

/* Modulos de video que o SDL do PS4 pede (copiados do proprio console; nao vao no repositorio). */
static void pt_log_env(void) {
    static const char *const mods[] = {
        "/app0/sce_module/libScePigletv2VSH.sprx",
        "/app0/sce_module/libSceShaccVSH.sprx",
        "/data/self/system/common/lib/libScePigletv2VSH.sprx",
        "/data/self/system/common/lib/libSceShaccVSH.sprx",
        "/system/common/lib/libScePigletv2VSH.sprx",
        "/system/common/lib/libSceShaccVSH.sprx"
    };
    size_t i;
#ifdef ENABLE_SW_RENDERER
    pt_log("[PizzaTower] build: renderer por CPU (ENABLE_SW_RENDERER)");
#else
    pt_log("[PizzaTower] build: renderer OpenGL (sem ENABLE_SW_RENDERER)");
#endif
#ifdef ENABLE_MODERN_GL
    pt_log("[PizzaTower] build: ENABLE_MODERN_GL ligado");
#endif
    for (i = 0; i < sizeof(mods) / sizeof(mods[0]); i++) {
        pt_log("[PizzaTower] %s: %s", mods[i], pt_file_exists(mods[i]) ? "EXISTE" : "nao existe");
    }
    pt_try_module("/data/self/system/common/lib/libSceShaccVSH.sprx");
    pt_try_module("/data/self/system/common/lib/libScePigletv2VSH.sprx");
}

#ifdef SDL_h_
static void pt_sdl_log(void *ud, int category, SDL_LogPriority pr, const char *msg) {
    (void)ud; (void)category; (void)pr;
    pt_log("[SDL] %s", msg);
}
#endif

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
    pt_log_reset();
    pt_log("== Pizza Tower PS4: log ==");
    pt_log("[PizzaTower] injetor v11 | trace SDL: @TRACE@");
    atexit(pt_on_exit);
    signal(SIGSEGV, pt_on_signal);
    signal(SIGBUS, pt_on_signal);
    signal(SIGILL, pt_on_signal);
    signal(SIGFPE, pt_on_signal);
    signal(SIGABRT, pt_on_signal);
    pt_log_env();
    pt_list_dir();
    if (!pt_data_win_ok()) {
        pt_log("[PizzaTower] data.win ausente ou invalido: o jogo nao sera iniciado");
        pt_write_help();
        return 0;
    }
    pt_redirect_std();
#ifdef SDL_h_
    SDL_LogSetAllPriority(SDL_LOG_PRIORITY_VERBOSE);
    SDL_LogSetOutputFunction(pt_sdl_log, NULL);
#endif
    if (chdir(PT_GAME_DIR) != 0) {
        pt_log("[PizzaTower] chdir(%s) falhou, errno=%d", PT_GAME_DIR, errno);
    }
    pt_log("[PizzaTower] data.win ok; iniciando o runner");
    return 1;
}
/* ---- fim PT_PREFLIGHT ---- */

'''.replace("@DIR@", GAME_DIR)


SDL_TRACE_FUNCS = [
    "SDL_Init", "SDL_InitSubSystem", "SDL_CreateWindow", "SDL_CreateRenderer",
    "SDL_CreateTexture", "SDL_GetWindowSurface", "SDL_CreateRGBSurfaceFrom",
    "SDL_CreateRGBSurface", "SDL_GL_CreateContext", "SDL_GL_SetAttribute",
    "SDL_NumJoysticks", "SDL_JoystickOpen", "SDL_OpenAudioDevice",
    "SDL_UpdateWindowSurface", "SDL_UpdateTexture", "SDL_RenderCopy",
    "SDL_SetWindowFullscreen", "SDL_GetNumVideoDisplays", "SDL_GetCurrentDisplayMode",
]

TRACE_HEADER = r"""
/* ---- PT_TRACE: inserido por scripts/inject_preflight.py ---- */
extern void pt_log(const char *fmt, ...);
#define PT_TRACE(name, call) ({ \
    static int pt_n; \
    int pt_on = (pt_n++ < 3); \
    if (pt_on) pt_log("[trace] " name " ..."); \
    __typeof__(call) pt_r = (call); \
    if (pt_on) pt_log("[trace] " name " -> %ld [%s]", (long)pt_r, SDL_GetError()); \
    pt_r; })
"""


def instrument_sdl(main_path: pathlib.Path) -> str:
    """Registra no log (antes e depois) as primeiras chamadas SDL do backend sdl2.c."""
    sdl_c = main_path.parent.parent / "backends" / "sdl2.c"
    if not sdl_c.exists():
        print("AVISO: src/backends/sdl2.c não encontrado; sem trace do SDL")
        return "inativo (sdl2.c nao encontrado)"
    text = sdl_c.read_text(encoding="utf-8")
    if "PT_TRACE" in text:
        print("trace do SDL já injetado")
        return "ativo (ja injetado)"
    used = [f for f in SDL_TRACE_FUNCS if re.search(r'\b' + f + r'\s*\(', text)]
    inc = re.search(r'^[ \t]*#[ \t]*include[ \t]*[<"][^>"]*SDL\.h[>"][^\n]*\n', text, re.M)
    if not used or not inc:
        print("AVISO: sem chamadas SDL conhecidas ou sem include do SDL.h em sdl2.c; sem trace")
        return "inativo (sem chamadas SDL conhecidas ou sem include)"
    macros = TRACE_HEADER
    for f in used:
        macros += f'#define {f}(...) PT_TRACE("{f}", {f}(__VA_ARGS__))\n'
    macros += "/* ---- fim PT_TRACE ---- */\n"
    text = text[:inc.end()] + macros + text[inc.end():]
    sdl_c.write_text(text, encoding="utf-8")
    print("trace do SDL injetado em sdl2.c para:", ", ".join(used))
    return "ativo: " + " ".join(used)

MAIN_RE = re.compile(r'^[ \t]*(?:static\s+)?int\s+main\s*\([^)]*\)\s*\{', re.M)
PATH_RE = re.compile(r'"[^"\n]*data\.win"')
LOOP_RE = re.compile(r'^([ \t]*)int\s+ret\s*=\s*loop\((.*)\);[ \t]*$', re.M)


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

    # 2) pasta de saves dentro da pasta do jogo
    n_save = src.count('"/data/butterscotch"')
    if n_save:
        src = src.replace('"/data/butterscotch"', '"' + GAME_DIR + '/save"')
        print(f"pasta de saves trocada em {n_save} lugar(es): {GAME_DIR}/save")
    else:
        print("AVISO: literal \"/data/butterscotch\" não encontrado (pasta de saves não trocada)")

    # 3) registra o caminho final e o início/fim do loop()
    if "args.dataWinPath = dataWinPath;" in src:
        src = src.replace(
            "args.dataWinPath = dataWinPath;",
            'args.dataWinPath = dataWinPath;\n    pt_log("[PizzaTower] dataWinPath=%s", dataWinPath);',
            1,
        )
    else:
        print("AVISO: 'args.dataWinPath = dataWinPath;' não encontrado (sem log do caminho)")

    lm = LOOP_RE.search(src)
    if lm:
        ind, rest = lm.group(1), lm.group(2)
        new = (f'{ind}pt_log("[PizzaTower] chamando loop()");\n'
               f'{ind}int ret = loop({rest});\n'
               f'{ind}pt_log("[PizzaTower] loop() retornou %d", ret);')
        src = src[:lm.start()] + new + src[lm.end():]
    else:
        print("AVISO: chamada 'int ret = loop(...)' não encontrada (sem log do loop)")

    # 4) chamada no começo do main e bloco antes dele (chamada primeiro: posição mais à frente)
    trace_status = instrument_sdl(path)
    m = MAIN_RE.search(src)
    call = "\n    if (!pt_preflight()) { return 0; } /* PT_PREFLIGHT */"
    src = src[:m.end()] + call + src[m.end():]
    src = src[:m.start()] + BLOCK.replace("@TRACE@", trace_status) + src[m.start():]

    path.write_text(src, encoding="utf-8")
    print("preflight injetado em", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
