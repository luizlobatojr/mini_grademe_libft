#!/usr/bin/env python3
"""Mini-Grademe para a Libft.

Uso:
  python3 grademe.py              # continua no próximo exercício por fazer
  python3 grademe.py ft_strlcat   # (re)testa um exercício específico

Escreve as tuas funções em rendu/<nome>.c e carrega Enter para testar.
O rendu/libft.h é criado automaticamente se não existir.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from string import Template

DIR = Path(__file__).resolve().parent
RENDU = DIR / "rendu"
PROGRESS = DIR / ".progress.json"

LIBFT_H = """#ifndef LIBFT_H
# define LIBFT_H

# include <stddef.h>

typedef struct s_list
{
    void            *content;
    struct s_list   *next;
}   t_list;

int             ft_isalpha(int c);
int             ft_isdigit(int c);
int             ft_isalnum(int c);
int             ft_isascii(int c);
int             ft_isprint(int c);
int             ft_toupper(int c);
int             ft_tolower(int c);
size_t          ft_strlen(const char *s);
void            *ft_memset(void *s, int c, size_t n);
void            ft_bzero(void *s, size_t n);
void            *ft_memcpy(void *dest, const void *src, size_t n);
void            *ft_memmove(void *dest, const void *src, size_t n);
size_t          ft_strlcpy(char *dst, const char *src, size_t size);
size_t          ft_strlcat(char *dst, const char *src, size_t size);
char            *ft_strchr(const char *s, int c);
char            *ft_strrchr(const char *s, int c);
void            ft_putchar_fd(char c, int fd);
void            ft_putstr_fd(char *s, int fd);
void            ft_putendl_fd(char *s, int fd);
int             ft_strncmp(const char *s1, const char *s2, size_t n);
void            *ft_memchr(const void *s, int c, size_t n);
int             ft_memcmp(const void *s1, const void *s2, size_t n);
t_list          *ft_lstnew(void *content);
unsigned int    ft_lstsize(t_list *lst);
t_list          *ft_lstlast(t_list *lst);
int             ft_atoi(const char *nptr);
char            *ft_strdup(const char *s);
void            *ft_calloc(size_t nmemb, size_t size);
char            *ft_strnstr(const char *big, const char *little, size_t len);
char            *ft_strjoin(char const *s1, char const *s2);
char            *ft_substr(char const *s, unsigned int start, size_t len);
void            ft_lstadd_front(t_list **lst, t_list *new);
void            ft_lstadd_back(t_list **lst, t_list *new);
char            *ft_strtrim(char const *s1, char const *set);
char            **ft_split(char const *s, char c);
char            *ft_itoa(int n);
char            *ft_strmapi(char const *s, char (*f)(unsigned int, char));
void            ft_striteri(char *s, void (*f)(unsigned int, char*));
void            ft_putnbr_fd(int n, int fd);
void            ft_lstdelone(t_list *lst, void (*del)(void *));
void            ft_lstclear(t_list **lst, void (*del)(void *));
void            ft_lstiter(t_list *lst, void (*f)(void *));
t_list          *ft_lstmap(t_list *lst, void *(*f)(void *),
                    void (*del)(void *));

#endif
"""

# --------------------------------------------------------------------------
# Código C comum a todos os testes
# --------------------------------------------------------------------------
PRELUDE = r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <ctype.h>
#include <stdint.h>
#include <limits.h>
#include <unistd.h>
#include "libft.h"

static int g_n;
static int g_ok;
static int g_pfd[2];

#define SGN(x) (((x) > 0) - ((x) < 0))
#define OFF(p, b) ((p) ? (long)((const char *)(p) - (const char *)(b)) : -1L)

static void check_b(int cond, const char *d)
{
	g_n++;
	if (cond)
	{
		g_ok++;
		printf("Test %2d  %s -> OK\n", g_n, d);
	}
	else
		printf("Test %2d  %s -> KO\n", g_n, d);
}

static void check_l(long e, long r, const char *d)
{
	g_n++;
	if (e == r)
	{
		g_ok++;
		printf("Test %2d  %s -> OK\n", g_n, d);
	}
	else
		printf("Test %2d  %s -> KO (esperado %ld, recebeste %ld)\n",
			g_n, d, e, r);
}

static void check_s(const char *e, const char *r, const char *d)
{
	int same;

	g_n++;
	same = (e == NULL && r == NULL) || (e && r && strcmp(e, r) == 0);
	if (same)
	{
		g_ok++;
		printf("Test %2d  %s -> OK\n", g_n, d);
	}
	else
		printf("Test %2d  %s -> KO (esperado \"%.60s\", recebeste \"%.60s\")\n",
			g_n, d, e ? e : "(null)", r ? r : "(null)");
}

static void cap_begin(void)
{
	if (pipe(g_pfd) != 0)
		exit(2);
}

static void cap_end(char *out, size_t max)
{
	ssize_t n;

	close(g_pfd[1]);
	n = read(g_pfd[0], out, max - 1);
	if (n < 0)
		n = 0;
	out[n] = '\0';
	close(g_pfd[0]);
}

static t_list *mk(void *c, t_list *next)
{
	t_list *n = malloc(sizeof(t_list));

	if (!n)
		exit(2);
	n->content = c;
	n->next = next;
	return (n);
}

static void freelst(t_list *l)
{
	t_list *tmp;

	while (l)
	{
		tmp = l->next;
		free(l);
		l = tmp;
	}
}

static int finish(void)
{
	printf("Resultado: %d/%d %s\n", g_ok, g_n, g_ok == g_n ? "OK" : "KO");
	return (g_ok != g_n);
}
"""

# --------------------------------------------------------------------------
# Corpos dos testes (main)
# --------------------------------------------------------------------------
VALUES = "0,9,32,'0','9','A','Z','a','z','@','[','`','{',47,58,126,127,128,255,-1"

CTYPE_BODY = Template(r"""
int main(void)
{
	int v[] = {${values}};
	int n = sizeof(v) / sizeof(v[0]);
	char d[32];

	for (int i = 0; i < n; i++)
	{
		snprintf(d, sizeof d, "c=%d", v[i]);
		check_l(${norm}(${ref}(v[i])), ${norm}(${ft}(v[i])), d);
	}
	return (finish());
}
""")

STRLEN_BODY = r"""
int main(void)
{
	const char *v[] = {"", "a", "42", "Hello, World!", "abc\0def",
		"   espacos   ", "tab\there"};
	char big[2001];
	char d[32];

	for (size_t i = 0; i < sizeof v / sizeof v[0]; i++)
	{
		snprintf(d, sizeof d, "len=%zu", strlen(v[i]));
		check_l((long)strlen(v[i]), (long)ft_strlen(v[i]), d);
	}
	memset(big, 'x', 2000);
	big[2000] = '\0';
	check_l(2000, (long)ft_strlen(big), "string com 2000 chars");
	return (finish());
}
"""

PUTCHAR_BODY = r"""
int main(void)
{
	char c[] = {'A', 'z', '0', ' ', '\n', '~'};
	char out[8], e[2], d[32];

	for (size_t i = 0; i < sizeof c; i++)
	{
		e[0] = c[i];
		e[1] = '\0';
		snprintf(d, sizeof d, "c=%d", c[i]);
		cap_begin();
		ft_putchar_fd(c[i], g_pfd[1]);
		cap_end(out, sizeof out);
		check_s(e, out, d);
	}
	return (finish());
}
"""

PUTSTR_BODY = r"""
int main(void)
{
	const char *v[] = {"Hello", "", "42 Lisboa\n", "tab\tx", "a\0b"};
	char out[4096], big[3001], d[32];

	for (size_t i = 0; i < sizeof v / sizeof v[0]; i++)
	{
		snprintf(d, sizeof d, "string #%zu", i + 1);
		cap_begin();
		ft_putstr_fd((char *)v[i], g_pfd[1]);
		cap_end(out, sizeof out);
		check_s(v[i], out, d);
	}
	memset(big, 'x', 3000);
	big[3000] = '\0';
	cap_begin();
	ft_putstr_fd(big, g_pfd[1]);
	cap_end(out, sizeof out);
	check_s(big, out, "string com 3000 chars");
	return (finish());
}
"""

PUTENDL_BODY = r"""
int main(void)
{
	const char *v[] = {"Hello", "", "42 Lisboa", "tab\tx", "a\0b"};
	char out[4096], big[3001], e[3100], d[32];

	for (size_t i = 0; i < sizeof v / sizeof v[0]; i++)
	{
		snprintf(d, sizeof d, "string #%zu", i + 1);
		snprintf(e, sizeof e, "%s\n", v[i]);
		cap_begin();
		ft_putendl_fd((char *)v[i], g_pfd[1]);
		cap_end(out, sizeof out);
		check_s(e, out, d);
	}
	memset(big, 'x', 3000);
	big[3000] = '\0';
	snprintf(e, sizeof e, "%s\n", big);
	cap_begin();
	ft_putendl_fd(big, g_pfd[1]);
	cap_end(out, sizeof out);
	check_s(e, out, "string com 3000 chars");
	return (finish());
}
"""

BZERO_BODY = r"""
int main(void)
{
	int t[][2] = {{0, 0}, {0, 1}, {0, 16}, {3, 5}, {10, 0}, {0, 32}, {31, 1}};
	unsigned char a[32], b[32];
	char d[48];

	for (size_t i = 0; i < sizeof t / sizeof t[0]; i++)
	{
		for (int k = 0; k < 32; k++)
			a[k] = b[k] = 'a' + k % 26;
		bzero(a + t[i][0], t[i][1]);
		ft_bzero(b + t[i][0], t[i][1]);
		snprintf(d, sizeof d, "off=%d n=%d", t[i][0], t[i][1]);
		check_b(memcmp(a, b, 32) == 0, d);
	}
	return (finish());
}
"""

MEMSET_BODY = r"""
struct tc { int off; int c; size_t n; };

int main(void)
{
	struct tc t[] = {{0, 'A', 0}, {0, 'A', 5}, {3, 0, 10}, {0, 255, 32},
		{5, 321, 8}, {0, -1, 4}, {31, 'x', 1}};
	unsigned char a[32], b[32];
	void *r;
	char d[48];

	for (size_t i = 0; i < sizeof t / sizeof t[0]; i++)
	{
		for (int k = 0; k < 32; k++)
			a[k] = b[k] = 'a' + k % 26;
		memset(a + t[i].off, t[i].c, t[i].n);
		r = ft_memset(b + t[i].off, t[i].c, t[i].n);
		snprintf(d, sizeof d, "off=%d c=%d n=%zu", t[i].off, t[i].c, t[i].n);
		check_b(memcmp(a, b, 32) == 0 && r == b + t[i].off, d);
	}
	return (finish());
}
"""

STRCHR_BODY = Template(r"""
struct tc { const char *s; int c; };

int main(void)
{
	struct tc t[] = {{"Hello World", 'l'}, {"Hello World", 'H'},
		{"Hello World", 'd'}, {"Hello World", 'x'}, {"Hello World", '\0'},
		{"", '\0'}, {"", 'a'}, {"Hello World", 'l' + 256}, {"42", '4'},
		{"aaa", 'a'}};
	char d[64];
	char *e, *r;

	for (size_t i = 0; i < sizeof t / sizeof t[0]; i++)
	{
		e = ${ref}(t[i].s, t[i].c);
		r = ${ft}(t[i].s, t[i].c);
		snprintf(d, sizeof d, "${ref}(\"%s\", %d) [offset, -1=NULL]",
			t[i].s, t[i].c);
		check_l(OFF(e, t[i].s), OFF(r, t[i].s), d);
	}
	return (finish());
}
""")

STRNCMP_BODY = r"""
struct tc { const char *a; const char *b; size_t n; };

int main(void)
{
	struct tc t[] = {{"abc", "abc", 3}, {"abc", "abd", 3}, {"abd", "abc", 3},
		{"abc", "abd", 2}, {"abc", "abc", 10}, {"abc", "ab", 3},
		{"ab", "abc", 3}, {"", "", 5}, {"abc", "abd", 0},
		{"a\x80", "a\x7f", 2}, {"test\0abc", "test\0xyz", 8}};
	char d[64];

	for (size_t i = 0; i < sizeof t / sizeof t[0]; i++)
	{
		snprintf(d, sizeof d, "strncmp #%zu n=%zu [sinal]", i + 1, t[i].n);
		check_l(SGN(strncmp(t[i].a, t[i].b, t[i].n)),
			SGN(ft_strncmp(t[i].a, t[i].b, t[i].n)), d);
	}
	return (finish());
}
"""

MEMCHR_BODY = r"""
struct tc { int c; size_t n; };

int main(void)
{
	unsigned char data[] = {1, 2, 3, 4, 0, 5, 6, 255};
	struct tc t[] = {{3, 8}, {0, 8}, {255, 8}, {6, 8}, {7, 8}, {4, 3},
		{0, 0}, {3 + 256, 8}, {1, 1}, {255, 7}};
	char d[64];
	void *e, *r;

	for (size_t i = 0; i < sizeof t / sizeof t[0]; i++)
	{
		e = memchr(data, t[i].c, t[i].n);
		r = ft_memchr(data, t[i].c, t[i].n);
		snprintf(d, sizeof d, "memchr c=%d n=%zu [offset, -1=NULL]",
			t[i].c, t[i].n);
		check_l(OFF(e, data), OFF(r, data), d);
	}
	return (finish());
}
"""

MEMCMP_BODY = r"""
struct tc { unsigned char a[4]; unsigned char b[4]; size_t n; };

int main(void)
{
	struct tc t[] = {
		{{1, 2, 0, 4}, {1, 2, 0, 5}, 4},
		{{1, 2, 0, 4}, {1, 2, 0, 5}, 3},
		{{1, 2, 3, 4}, {1, 2, 3, 4}, 4},
		{{9, 9, 9, 9}, {1, 1, 1, 1}, 0},
		{{255, 0, 0, 0}, {1, 0, 0, 0}, 1},
		{{1, 0, 0, 0}, {255, 0, 0, 0}, 1},
		{{0, 0, 0, 0}, {0, 0, 1, 0}, 4}};
	char d[64];

	for (size_t i = 0; i < sizeof t / sizeof t[0]; i++)
	{
		snprintf(d, sizeof d, "memcmp #%zu n=%zu [sinal]", i + 1, t[i].n);
		check_l(SGN(memcmp(t[i].a, t[i].b, t[i].n)),
			SGN(ft_memcmp(t[i].a, t[i].b, t[i].n)), d);
	}
	return (finish());
}
"""

ATOI_BODY = r"""
int main(void)
{
	const char *v[] = {"42", "-42", "+42", "   42", "\t\n\v\f\r 42", "0",
		"-0", "42abc", "abc", "", "- 42", "--42", "+-42", "2147483647",
		"-2147483648", "  +0012", "12 34"};
	char d[64];

	for (size_t i = 0; i < sizeof v / sizeof v[0]; i++)
	{
		snprintf(d, sizeof d, "atoi(\"%.20s\")", v[i]);
		check_l(atoi(v[i]), ft_atoi(v[i]), d);
	}
	return (finish());
}
"""

MEMCPY_BODY = r"""
int main(void)
{
	int t[][3] = {{0, 0, 0}, {0, 0, 10}, {5, 3, 12}, {0, 0, 32}, {31, 0, 1}};
	unsigned char src[32], a[32], b[32];
	void *r;
	char d[48];

	for (int k = 0; k < 32; k++)
		src[k] = 'a' + k % 26;
	for (size_t i = 0; i < sizeof t / sizeof t[0]; i++)
	{
		memset(a, '.', 32);
		memset(b, '.', 32);
		memcpy(a + t[i][0], src + t[i][1], t[i][2]);
		r = ft_memcpy(b + t[i][0], src + t[i][1], t[i][2]);
		snprintf(d, sizeof d, "dst+%d src+%d n=%d", t[i][0], t[i][1], t[i][2]);
		check_b(memcmp(a, b, 32) == 0 && r == b + t[i][0], d);
	}
	return (finish());
}
"""

STRDUP_BODY = r"""
int main(void)
{
	char big[501];
	char *v[] = {"Hello", "", "42 Lisboa", big};
	char *r;
	char d[32];

	memset(big, 'z', 500);
	big[500] = '\0';
	for (size_t i = 0; i < sizeof v / sizeof v[0]; i++)
	{
		r = ft_strdup(v[i]);
		snprintf(d, sizeof d, "strdup #%zu", i + 1);
		check_b(r != NULL && r != v[i] && strcmp(r, v[i]) == 0, d);
		free(r);
	}
	return (finish());
}
"""

CALLOC_BODY = r"""
int main(void)
{
	unsigned char *z;
	void *p;
	size_t i;
	int ok;

	p = malloc(256);
	memset(p, 'X', 256);
	free(p);
	z = ft_calloc(64, 4);
	ok = (z != NULL);
	for (i = 0; ok && i < 256; i++)
		if (z[i] != 0)
			ok = 0;
	check_b(ok, "calloc(64, 4) devolve memória a zero");
	free(z);
	z = ft_calloc(10, 1);
	ok = (z != NULL);
	for (i = 0; ok && i < 10; i++)
		if (z[i] != 0)
			ok = 0;
	check_b(ok, "calloc(10, 1) devolve memória a zero");
	free(z);
	p = ft_calloc(0, 0);
	check_b(p != NULL, "calloc(0, 0) != NULL");
	free(p);
	p = ft_calloc(0, 5);
	check_b(p != NULL, "calloc(0, 5) != NULL");
	free(p);
	p = ft_calloc(5, 0);
	check_b(p != NULL, "calloc(5, 0) != NULL");
	free(p);
	p = ft_calloc(SIZE_MAX, 2);
	check_b(p == NULL, "overflow: calloc(SIZE_MAX, 2) == NULL");
	free(p);
	return (finish());
}
"""

LSTNEW_BODY = r"""
int main(void)
{
	int x = 42;
	t_list *n;

	n = ft_lstnew(&x);
	check_b(n != NULL, "lstnew != NULL");
	check_b(n && n->content == &x, "content aponta para o argumento");
	check_b(n && n->next == NULL, "next == NULL");
	free(n);
	n = ft_lstnew(NULL);
	check_b(n && n->content == NULL && n->next == NULL, "content NULL");
	free(n);
	return (finish());
}
"""

LSTSIZE_BODY = r"""
int main(void)
{
	t_list *l;
	char d[32];

	check_l(0, (long)ft_lstsize(NULL), "lista vazia (NULL)");
	l = NULL;
	for (int n = 1; n <= 5; n += 4)
	{
		for (int k = 0; k < (n == 1 ? 1 : 4); k++)
			l = mk(NULL, l);
		snprintf(d, sizeof d, "lista com %d nós", n);
		check_l(n, (long)ft_lstsize(l), d);
	}
	freelst(l);
	return (finish());
}
"""

LSTLAST_BODY = r"""
int main(void)
{
	t_list *last, *l;

	check_b(ft_lstlast(NULL) == NULL, "lista vazia -> NULL");
	last = mk(NULL, NULL);
	check_b(ft_lstlast(last) == last, "lista com 1 nó");
	l = last;
	for (int k = 0; k < 3; k++)
		l = mk(NULL, l);
	check_b(ft_lstlast(l) == last, "lista com 4 nós");
	freelst(l);
	return (finish());
}
"""

LSTADD_FRONT_BODY = r"""
int main(void)
{
	t_list *head = NULL;
	t_list *a = mk("a", NULL);
	t_list *b = mk("b", NULL);
	t_list *c = mk("c", NULL);

	ft_lstadd_front(&head, a);
	check_b(head == a && a->next == NULL, "em lista vazia");
	ft_lstadd_front(&head, b);
	check_b(head == b && b->next == a, "2.º nó fica à frente");
	ft_lstadd_front(&head, c);
	check_b(head == c && c->next == b && b->next == a && a->next == NULL,
		"3.º nó fica à frente, ordem mantida");
	freelst(head);
	return (finish());
}
"""

LSTADD_BACK_BODY = r"""
int main(void)
{
	t_list *head = NULL;
	t_list *a = mk("a", NULL);
	t_list *b = mk("b", NULL);
	t_list *c = mk("c", NULL);

	ft_lstadd_back(&head, a);
	check_b(head == a && a->next == NULL, "em lista vazia");
	ft_lstadd_back(&head, b);
	check_b(head == a && a->next == b && b->next == NULL, "2.º nó no fim");
	ft_lstadd_back(&head, c);
	check_b(head == a && a->next == b && b->next == c && c->next == NULL,
		"3.º nó no fim, ordem mantida");
	freelst(head);
	return (finish());
}
"""

MEMMOVE_BODY = r"""
int main(void)
{
	int t[][3] = {{0, 2, 8}, {2, 0, 8}, {0, 0, 8}, {5, 5, 0}, {0, 16, 10},
		{16, 0, 10}, {1, 0, 31}, {0, 1, 31}, {4, 0, 20}};
	unsigned char a[32], b[32];
	void *r;
	char d[64];

	for (size_t i = 0; i < sizeof t / sizeof t[0]; i++)
	{
		for (int k = 0; k < 32; k++)
			a[k] = b[k] = 'a' + k % 26;
		memmove(a + t[i][0], a + t[i][1], t[i][2]);
		r = ft_memmove(b + t[i][0], b + t[i][1], t[i][2]);
		snprintf(d, sizeof d, "dst+%d src+%d n=%d", t[i][0], t[i][1], t[i][2]);
		check_b(memcmp(a, b, 32) == 0 && r == b + t[i][0], d);
	}
	return (finish());
}
"""

STRLCPY_BODY = r"""
struct tc { const char *src; size_t size; const char *exp; size_t ret; };

int main(void)
{
	struct tc t[] = {{"Hello", 20, "Hello", 5}, {"Hello", 6, "Hello", 5},
		{"Hello", 5, "Hell", 5}, {"Hello", 1, "", 5}, {"Hello", 0, "", 5},
		{"", 5, "", 0}, {"42 Lisboa", 3, "42", 9}};
	char buf[32], ebuf[32];
	size_t r;
	char d[64];

	for (size_t i = 0; i < sizeof t / sizeof t[0]; i++)
	{
		memset(buf, 'X', 32);
		memset(ebuf, 'X', 32);
		if (t[i].size > 0)
			strcpy(ebuf, t[i].exp);
		r = ft_strlcpy(buf, t[i].src, t[i].size);
		snprintf(d, sizeof d, "strlcpy(\"%s\", size=%zu)", t[i].src, t[i].size);
		check_b(r == t[i].ret && memcmp(buf, ebuf, 32) == 0, d);
	}
	return (finish());
}
"""

STRLCAT_BODY = r"""
struct tc { const char *dst; const char *src; size_t size;
	const char *exp; size_t ret; };

int main(void)
{
	struct tc t[] = {
		{"Hello", " World", 20, "Hello World", 11},
		{"Hello", " World", 8, "Hello W", 11},
		{"Hello", " World", 5, "Hello", 11},
		{"Hello", " World", 3, "Hello", 9},
		{"Hello", " World", 0, "Hello", 6},
		{"", "abc", 10, "abc", 3},
		{"", "abc", 3, "ab", 3},
		{"abc", "", 10, "abc", 3},
		{"abc", "def", 7, "abcdef", 6},
		{"abc", "def", 6, "abcde", 6}};
	char buf[32], ebuf[32];
	size_t r;
	char d[64];

	for (size_t i = 0; i < sizeof t / sizeof t[0]; i++)
	{
		memset(buf, 'X', 32);
		memset(ebuf, 'X', 32);
		strcpy(buf, t[i].dst);
		strcpy(ebuf, t[i].exp);
		r = ft_strlcat(buf, t[i].src, t[i].size);
		snprintf(d, sizeof d, "strlcat(\"%s\", \"%s\", size=%zu)",
			t[i].dst, t[i].src, t[i].size);
		check_b(r == t[i].ret && memcmp(buf, ebuf, 32) == 0, d);
	}
	return (finish());
}
"""

STRNSTR_BODY = r"""
struct tc { const char *big; const char *little; size_t len; long off; };

int main(void)
{
	struct tc t[] = {
		{"Hello World", "World", 11, 6},
		{"Hello World", "World", 10, -1},
		{"Hello World", "", 5, 0},
		{"Hello World", "xyz", 11, -1},
		{"abc", "abcd", 10, -1},
		{"aaabcabcd", "abcd", 9, 5},
		{"aaabcabcd", "abcd", 8, -1},
		{"", "a", 5, -1},
		{"abc", "c", 3, 2},
		{"abc", "c", 2, -1},
		{"abc", "", 0, 0},
		{"abc", "a", 0, -1}};
	char *r;
	char d[96];

	for (size_t i = 0; i < sizeof t / sizeof t[0]; i++)
	{
		r = ft_strnstr(t[i].big, t[i].little, t[i].len);
		snprintf(d, sizeof d, "strnstr(\"%s\", \"%s\", %zu) [offset, -1=NULL]",
			t[i].big, t[i].little, t[i].len);
		check_l(t[i].off, OFF(r, t[i].big), d);
	}
	return (finish());
}
"""

SUBSTR_BODY = r"""
struct tc { const char *s; unsigned int start; size_t len; const char *exp; };

int main(void)
{
	struct tc t[] = {
		{"Hello World", 0, 5, "Hello"},
		{"Hello World", 6, 5, "World"},
		{"Hello World", 6, 100, "World"},
		{"Hello World", 11, 5, ""},
		{"Hello World", 100, 5, ""},
		{"Hello", 0, 0, ""},
		{"", 0, 5, ""},
		{"Hello", 1, 3, "ell"},
		{"Hello", 4, 1, "o"},
		{"Hello", 0, (size_t)-1, "Hello"}};
	char *r;
	char d[96];

	for (size_t i = 0; i < sizeof t / sizeof t[0]; i++)
	{
		r = ft_substr(t[i].s, t[i].start, t[i].len);
		snprintf(d, sizeof d, "substr(\"%s\", %u, %zu)",
			t[i].s, t[i].start, t[i].len);
		check_s(t[i].exp, r, d);
		free(r);
	}
	return (finish());
}
"""

STRJOIN_BODY = r"""
struct tc { const char *s1; const char *s2; const char *exp; };

int main(void)
{
	struct tc t[] = {
		{"Hello", " World", "Hello World"},
		{"", "abc", "abc"},
		{"abc", "", "abc"},
		{"", "", ""},
		{"a", "b", "ab"},
		{"42 ", "Lisboa", "42 Lisboa"}};
	char *r;
	char d[64];

	for (size_t i = 0; i < sizeof t / sizeof t[0]; i++)
	{
		r = ft_strjoin(t[i].s1, t[i].s2);
		snprintf(d, sizeof d, "strjoin(\"%s\", \"%s\")", t[i].s1, t[i].s2);
		check_s(t[i].exp, r, d);
		free(r);
	}
	return (finish());
}
"""



PUTNBR_BODY = r"""
int main(void)
{
	int v[] = {0, 42, -42, 7, -1, 100, 1000000, 2147483647, INT_MIN};
	char out[32], e[32], d[32];

	for (size_t i = 0; i < sizeof v / sizeof v[0]; i++)
	{
		snprintf(e, sizeof e, "%d", v[i]);
		snprintf(d, sizeof d, "n=%d", v[i]);
		cap_begin();
		ft_putnbr_fd(v[i], g_pfd[1]);
		cap_end(out, sizeof out);
		check_s(e, out, d);
	}
	return (finish());
}
"""

STRITERI_BODY = r"""
static int g_calls;

static void set_idx(unsigned int i, char *c)
{
	g_calls++;
	*c = '0' + i % 10;
}

static void alt_case(unsigned int i, char *c)
{
	g_calls++;
	if (i % 2 == 0)
		*c = toupper(*c);
}

int main(void)
{
	char s[32];

	strcpy(s, "hello world");
	g_calls = 0;
	ft_striteri(s, alt_case);
	check_s("HeLlO WoRlD", s, "alterna maiúsculas pelo índice");
	check_l(11, g_calls, "f chamada uma vez por caractere");
	strcpy(s, "abcdefghijkl");
	ft_striteri(s, set_idx);
	check_s("012345678901", s, "f recebe o índice e o endereço do char");
	strcpy(s, "");
	g_calls = 0;
	ft_striteri(s, set_idx);
	check_l(0, g_calls, "string vazia: f não é chamada");
	return (finish());
}
"""

LSTITER_BODY = r"""
static char g_log[16];
static int g_logn;

static void inc(void *c)
{
	(*(int *)c)++;
}

static void logc(void *c)
{
	g_log[g_logn++] = *(char *)c;
	g_log[g_logn] = '\0';
}

int main(void)
{
	int v[3] = {1, 2, 3};
	char a = 'a', b = 'b', c = 'c';
	t_list *l;

	l = mk(&v[0], mk(&v[1], mk(&v[2], NULL)));
	ft_lstiter(l, inc);
	check_b(v[0] == 2 && v[1] == 3 && v[2] == 4,
		"f aplicada ao content de cada nó");
	freelst(l);
	l = mk(&a, mk(&b, mk(&c, NULL)));
	g_log[0] = '\0';
	ft_lstiter(l, logc);
	check_s("abc", g_log, "ordem de iteração");
	freelst(l);
	ft_lstiter(NULL, inc);
	check_b(1, "lista NULL não crasha");
	return (finish());
}
"""

LSTDELONE_BODY = r"""
static int g_del;

static void del(void *c)
{
	g_del++;
	free(c);
}

int main(void)
{
	t_list *a, *b;

	a = mk(strdup("a"), NULL);
	g_del = 0;
	ft_lstdelone(a, del);
	check_l(1, g_del, "del chamada 1 vez sobre o content");
	a = mk(strdup("a"), NULL);
	b = mk(strdup("b"), NULL);
	a->next = b;
	g_del = 0;
	ft_lstdelone(a, del);
	check_l(1, g_del, "nó com sucessor: del chamada 1 vez");
	check_b(strcmp((char *)b->content, "b") == 0,
		"o nó seguinte NÃO é libertado");
	free(b->content);
	free(b);
	return (finish());
}
"""

LSTCLEAR_BODY = r"""
static int g_del;

static void del(void *c)
{
	g_del++;
	free(c);
}

int main(void)
{
	t_list *l = NULL;

	for (int k = 0; k < 4; k++)
		l = mk(strdup("x"), l);
	g_del = 0;
	ft_lstclear(&l, del);
	check_l(4, g_del, "del chamada 1 vez por nó");
	check_b(l == NULL, "*lst == NULL no fim");
	l = mk(strdup("x"), NULL);
	g_del = 0;
	ft_lstclear(&l, del);
	check_b(g_del == 1 && l == NULL, "lista com 1 nó");
	l = NULL;
	g_del = 0;
	ft_lstclear(&l, del);
	check_b(g_del == 0 && l == NULL, "lista vazia não crasha");
	return (finish());
}
"""

STRMAPI_BODY = r"""
static char alt(unsigned int i, char c)
{
	return (i % 2 == 0 ? toupper(c) : tolower(c));
}

static char idx(unsigned int i, char c)
{
	(void)c;
	return ('0' + i % 10);
}

int main(void)
{
	char *r;

	r = ft_strmapi("Hello World", alt);
	check_s("HeLlO WoRlD", r, "alterna maiúsculas pelo índice");
	free(r);
	r = ft_strmapi("", alt);
	check_s("", r, "string vazia");
	free(r);
	r = ft_strmapi("abc", idx);
	check_s("012", r, "f recebe o índice");
	free(r);
	r = ft_strmapi("ABCDEFGHIJKL", idx);
	check_s("012345678901", r, "12 caracteres");
	free(r);
	return (finish());
}
"""

STRTRIM_BODY = r"""
struct tc { const char *s1; const char *set; const char *exp; };

int main(void)
{
	struct tc t[] = {
		{"  hello  ", " ", "hello"},
		{"xxhelloxx", "x", "hello"},
		{"hello", "", "hello"},
		{"", "abc", ""},
		{"   ", " ", ""},
		{"abcabc", "abc", ""},
		{"  hello world  ", " ", "hello world"},
		{"xyhixyx", "xy", "hi"},
		{"hello", "xyz", "hello"},
		{"\t\n hi \n\t", " \n\t", "hi"},
		{"aXa", "a", "X"},
		{"abXba", "ab", "X"},
		{"  a  b  ", " ", "a  b"}};
	char *r;
	char d[64];

	for (size_t i = 0; i < sizeof t / sizeof t[0]; i++)
	{
		r = ft_strtrim(t[i].s1, t[i].set);
		snprintf(d, sizeof d, "strtrim(\"%.20s\", \"%s\")", t[i].s1, t[i].set);
		check_s(t[i].exp, r, d);
		free(r);
	}
	return (finish());
}
"""

ITOA_BODY = r"""
int main(void)
{
	int v[] = {0, 1, -1, 42, -42, 10, 100, 12345, -12345, 1000000,
		2147483647, INT_MIN};
	char e[16], d[32];
	char *r;

	for (size_t i = 0; i < sizeof v / sizeof v[0]; i++)
	{
		r = ft_itoa(v[i]);
		snprintf(e, sizeof e, "%d", v[i]);
		snprintf(d, sizeof d, "itoa(%d)", v[i]);
		check_s(e, r, d);
		free(r);
	}
	return (finish());
}
"""

SPLIT_BODY = r"""
struct tc { const char *s; char c; int n; const char *exp[6]; };

int main(void)
{
	struct tc t[] = {
		{"hello world foo", ' ', 3, {"hello", "world", "foo"}},
		{"  hello   world  ", ' ', 2, {"hello", "world"}},
		{"", ' ', 0, {NULL}},
		{"   ", ' ', 0, {NULL}},
		{"hello", ' ', 1, {"hello"}},
		{"a,b,c", ',', 3, {"a", "b", "c"}},
		{",a,,b,", ',', 2, {"a", "b"}},
		{"abc", 'x', 1, {"abc"}},
		{"xxabcxx", 'x', 1, {"abc"}},
		{"a b", '\0', 1, {"a b"}},
		{"one", 'o', 1, {"ne"}},
		{"split  this   for   me  !", ' ', 5,
			{"split", "this", "for", "me", "!"}}};
	char **r;
	char d[64];
	int ok, cnt, k;

	for (size_t i = 0; i < sizeof t / sizeof t[0]; i++)
	{
		r = ft_split(t[i].s, t[i].c);
		ok = (r != NULL);
		cnt = 0;
		while (r && cnt < 16 && r[cnt])
			cnt++;
		ok = ok && cnt == t[i].n;
		for (k = 0; ok && k < t[i].n; k++)
			if (strcmp(r[k], t[i].exp[k]) != 0)
				ok = 0;
		snprintf(d, sizeof d, "split(\"%.24s\", %d) -> %d palavras",
			t[i].s, t[i].c, t[i].n);
		check_b(ok, d);
		for (k = 0; r && k < 16 && r[k]; k++)
			free(r[k]);
		free(r);
	}
	return (finish());
}
"""

LSTMAP_BODY = r"""
static int g_del;

static void del(void *c)
{
	g_del++;
	free(c);
}

static void *up(void *c)
{
	char *s = strdup((char *)c);

	if (s)
		s[0] = toupper(s[0]);
	return (s);
}

int main(void)
{
	const char *exp[] = {"A", "B", "C"};
	t_list *l, *r, *p;
	int ok, k;

	l = mk("a", mk("b", mk("c", NULL)));
	r = ft_lstmap(l, up, del);
	check_b(r != NULL, "devolve uma lista nova");
	ok = (r != NULL);
	for (p = r, k = 0; k < 3; k++, p = (p ? p->next : NULL))
		if (!p || !p->content || strcmp((char *)p->content, exp[k]) != 0)
			ok = 0;
	check_b(ok && p == NULL, "3 nós, content transformado, ordem mantida");
	check_b(r != l && strcmp((char *)l->content, "a") == 0,
		"a lista original não é alterada");
	if (r != l)
	{
		for (p = r; p; p = p->next)
			free(p->content);
		freelst(r);
	}
	freelst(l);
	check_b(ft_lstmap(NULL, up, del) == NULL, "lista NULL -> NULL");
	return (finish());
}
"""


# --------------------------------------------------------------------------
# Lista de exercícios (do mais fácil ao mais difícil)
# --------------------------------------------------------------------------
def ctype_ex(name, ref, norm, subject):
    body = CTYPE_BODY.substitute(ft=name, ref=ref, norm=norm, values=VALUES)
    return {"name": name, "subject": subject, "test": PRELUDE + body}


def str2_ex(name, ref, subject):
    body = STRCHR_BODY.substitute(ft=name, ref=ref)
    return {"name": name, "subject": subject, "test": PRELUDE + body}


def ex(name, subject, body, heap=False):
    return {"name": name, "subject": subject, "test": PRELUDE + body, "heap": heap}


EXOS = [
    ctype_ex("ft_isalpha", "isalpha", "!!",
             "int ft_isalpha(int c);\nDevolve 1 se c for letra, senão 0."),
    ctype_ex("ft_isdigit", "isdigit", "!!",
             "int ft_isdigit(int c);\nDevolve 1 se c for dígito, senão 0."),
    ctype_ex("ft_isalnum", "isalnum", "!!",
             "int ft_isalnum(int c);\nDevolve 1 se c for letra ou dígito, senão 0."),
    ctype_ex("ft_isascii", "isascii", "!!",
             "int ft_isascii(int c);\nDevolve 1 se c estiver em 0-127, senão 0."),
    ctype_ex("ft_isprint", "isprint", "!!",
             "int ft_isprint(int c);\nDevolve 1 se c for imprimível, senão 0."),
    ctype_ex("ft_toupper", "toupper", "",
             "int ft_toupper(int c);\nComo toupper(3)."),
    ctype_ex("ft_tolower", "tolower", "",
             "int ft_tolower(int c);\nComo tolower(3)."),
    ex("ft_strlen", "size_t ft_strlen(const char *s);\nComo strlen(3).",
       STRLEN_BODY),
    ex("ft_putchar_fd",
       "void ft_putchar_fd(char c, int fd);\n"
       "Escreve o caractere c no file descriptor fd (usa write).",
       PUTCHAR_BODY),
    ex("ft_putstr_fd",
       "void ft_putstr_fd(char *s, int fd);\n"
       "Escreve a string s no file descriptor fd (usa write).",
       PUTSTR_BODY),
    ex("ft_putendl_fd",
       "void ft_putendl_fd(char *s, int fd);\n"
       "Escreve a string s no file descriptor fd, seguida de '\\n'.",
       PUTENDL_BODY),
    ex("ft_bzero", "void ft_bzero(void *s, size_t n);\nComo bzero(3).",
       BZERO_BODY),
    ex("ft_memset",
       "void *ft_memset(void *s, int c, size_t n);\nComo memset(3).",
       MEMSET_BODY),
    str2_ex("ft_strchr", "strchr",
            "char *ft_strchr(const char *s, int c);\n"
            "Como strchr(3). Atenção: c == '\\0' devolve o terminador."),
    str2_ex("ft_strrchr", "strrchr",
            "char *ft_strrchr(const char *s, int c);\n"
            "Como strrchr(3). Procura a ÚLTIMA ocorrência."),
    ex("ft_strncmp",
       "int ft_strncmp(const char *s1, const char *s2, size_t n);\n"
       "Como strncmp(3). Compara como unsigned char.",
       STRNCMP_BODY),
    ex("ft_memchr",
       "void *ft_memchr(const void *s, int c, size_t n);\n"
       "Como memchr(3). Não pára no '\\0'.",
       MEMCHR_BODY),
    ex("ft_memcmp",
       "int ft_memcmp(const void *s1, const void *s2, size_t n);\n"
       "Como memcmp(3). Compara como unsigned char.",
       MEMCMP_BODY),
    ex("ft_atoi", "int ft_atoi(const char *nptr);\nComo atoi(3).", ATOI_BODY),
    ex("ft_memcpy",
       "void *ft_memcpy(void *dest, const void *src, size_t n);\n"
       "Como memcpy(3).",
       MEMCPY_BODY),
    ex("ft_strdup",
       "char *ft_strdup(const char *s);\nComo strdup(3) (usa malloc).",
       STRDUP_BODY, heap=True),
    ex("ft_calloc",
       "void *ft_calloc(size_t nmemb, size_t size);\n"
       "Como calloc(3). Se nmemb ou size for 0, devolve um ponteiro único\n"
       "que possa ser passado ao free(). Protege contra overflow.",
       CALLOC_BODY, heap=True),
    ex("ft_lstnew",
       "t_list *ft_lstnew(void *content);\n"
       "Aloca um nó novo: content = argumento, next = NULL.",
       LSTNEW_BODY, heap=True),
    ex("ft_lstsize",
       "unsigned int ft_lstsize(t_list *lst);\nConta os nós da lista.",
       LSTSIZE_BODY, heap=True),
    ex("ft_lstlast",
       "t_list *ft_lstlast(t_list *lst);\nDevolve o último nó da lista.",
       LSTLAST_BODY, heap=True),
    ex("ft_lstadd_front",
       "void ft_lstadd_front(t_list **lst, t_list *new);\n"
       "Adiciona o nó 'new' no início da lista.",
       LSTADD_FRONT_BODY, heap=True),
    ex("ft_lstadd_back",
       "void ft_lstadd_back(t_list **lst, t_list *new);\n"
       "Adiciona o nó 'new' no fim da lista (lista vazia incluída).",
       LSTADD_BACK_BODY, heap=True),
    ex("ft_memmove",
       "void *ft_memmove(void *dest, const void *src, size_t n);\n"
       "Como memmove(3). Tem de funcionar com zonas que se sobrepõem.",
       MEMMOVE_BODY),
    ex("ft_strlcpy",
       "size_t ft_strlcpy(char *dst, const char *src, size_t size);\n"
       "Como strlcpy(3) (BSD): copia no máx. size-1 bytes, termina com '\\0',\n"
       "devolve strlen(src).",
       STRLCPY_BODY),
    ex("ft_strlcat",
       "size_t ft_strlcat(char *dst, const char *src, size_t size);\n"
       "Como strlcat(3) (BSD): devolve o comprimento que tentou criar\n"
       "(min(size, strlen(dst)) + strlen(src)).",
       STRLCAT_BODY),
    ex("ft_substr",
       "char *ft_substr(char const *s, unsigned int start, size_t len);\n"
       "Aloca e devolve uma substring de s, a começar em start, com no\n"
       "máximo len caracteres. NULL se a alocação falhar.",
       SUBSTR_BODY, heap=True),
    ex("ft_strjoin",
       "char *ft_strjoin(char const *s1, char const *s2);\n"
       "Aloca e devolve s1 concatenada com s2. NULL se a alocação falhar.",
       STRJOIN_BODY, heap=True),
    ex("ft_strnstr",
       "char *ft_strnstr(const char *big, const char *little, size_t len);\n"
       "Como strnstr(3) (BSD): procura little em big, até len caracteres.\n"
       "little vazio -> devolve big.",
       STRNSTR_BODY),
    ex("ft_putnbr_fd",
       "void ft_putnbr_fd(int n, int fd);\n"
       "Escreve o inteiro n no file descriptor fd. Atenção ao INT_MIN.",
       PUTNBR_BODY),
    ex("ft_striteri",
       "void ft_striteri(char *s, void (*f)(unsigned int, char*));\n"
       "Aplica f a cada caractere de s (índice, endereço do char).",
       STRITERI_BODY),
    ex("ft_lstiter",
       "void ft_lstiter(t_list *lst, void (*f)(void *));\n"
       "Aplica f ao content de cada nó, por ordem.",
       LSTITER_BODY),
    ex("ft_lstdelone",
       "void ft_lstdelone(t_list *lst, void (*del)(void *));\n"
       "Liberta o content com del e depois o nó. NÃO liberta o seguinte.",
       LSTDELONE_BODY, heap=True),
    ex("ft_lstclear",
       "void ft_lstclear(t_list **lst, void (*del)(void *));\n"
       "Apaga o nó dado e todos os seguintes (del + free). No fim, *lst = NULL.",
       LSTCLEAR_BODY, heap=True),
    ex("ft_strmapi",
       "char *ft_strmapi(char const *s, char (*f)(unsigned int, char));\n"
       "Aplica f a cada caractere (índice, char) e devolve a nova string\n"
       "(malloc) com os resultados. NULL se a alocação falhar.",
       STRMAPI_BODY, heap=True),
    ex("ft_strtrim",
       "char *ft_strtrim(char const *s1, char const *set);\n"
       "Devolve uma cópia (malloc) de s1 sem os caracteres de 'set'\n"
       "no início e no fim.",
       STRTRIM_BODY, heap=True),
    ex("ft_itoa",
       "char *ft_itoa(int n);\n"
       "Devolve (malloc) a string que representa n. Trata negativos e INT_MIN.",
       ITOA_BODY, heap=True),
    ex("ft_lstmap",
       "t_list *ft_lstmap(t_list *lst, void *(*f)(void *), void (*del)(void *));\n"
       "Aplica f ao content de cada nó e cria uma lista NOVA com os resultados.\n"
       "Se a alocação falhar, usa del para limpar e devolve NULL.",
       LSTMAP_BODY, heap=True),
    ex("ft_split",
       "char **ft_split(char const *s, char c);\n"
       "Divide s usando c como delimitador. Devolve um array de strings\n"
       "(malloc) terminado em NULL. Delimitadores repetidos não geram strings\n"
       "vazias.",
       SPLIT_BODY, heap=True),
]

ORDER = [
    "ft_isalpha", "ft_isdigit", "ft_isalnum", "ft_isascii", "ft_isprint",
    "ft_toupper", "ft_tolower", "ft_strlen", "ft_putchar_fd", "ft_putstr_fd",
    "ft_putendl_fd", "ft_putnbr_fd", "ft_striteri", "ft_bzero", "ft_memset",
    "ft_strchr", "ft_strrchr", "ft_strncmp", "ft_memchr", "ft_memcmp",
    "ft_atoi", "ft_memcpy", "ft_strdup", "ft_calloc", "ft_lstnew",
    "ft_lstsize", "ft_lstlast", "ft_lstadd_front", "ft_lstadd_back",
    "ft_lstiter", "ft_lstdelone", "ft_lstclear", "ft_memmove", "ft_strlcpy",
    "ft_strlcat", "ft_substr", "ft_strjoin", "ft_strmapi", "ft_strtrim",
    "ft_itoa", "ft_strnstr", "ft_lstmap", "ft_split",
]
assert sorted(ORDER) == sorted(e["name"] for e in EXOS), "ORDER != EXOS"
EXOS.sort(key=lambda e: ORDER.index(e["name"]))


# --------------------------------------------------------------------------
# Motor
# --------------------------------------------------------------------------
def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def grade(ex):
    src = RENDU / f"{ex['name']}.c"
    if not src.exists():
        print(f"❌ Ficheiro não encontrado: {src}")
        return False

    if shutil.which("norminette"):
        r = run(["norminette", str(src)])
        if r.returncode != 0:
            print("❌ Norminette:\n" + r.stdout)
            return False
        print("✔ Norminette OK")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        obj, test_c, exe = tmp / "s.o", tmp / "t.c", tmp / "t"
        inc = ["-I", str(RENDU)]

        # Flags rígidas aplicam-se só ao código do aluno
        r = run(["cc", "-Wall", "-Wextra", "-Werror", *inc,
                 "-c", str(src), "-o", str(obj)])
        if r.returncode != 0:
            print("❌ Erro de compilação (cc -Wall -Wextra -Werror):\n" + r.stderr)
            return False
        print("✔ Compilação OK")

        # Outras funções tuas (ex.: ft_lstlast usada em ft_lstadd_back)
        deps = []
        for other in sorted(RENDU.glob("ft_*.c")):
            if other.name == src.name:
                continue
            o = tmp / (other.stem + ".o")
            r = run(["cc", "-Wall", "-Wextra", "-Werror", *inc,
                     "-c", str(other), "-o", str(o)])
            if r.returncode == 0:
                deps.append(str(o))
        link = [str(test_c), str(obj)]
        if deps:
            run(["ar", "rcs", str(tmp / "deps.a"), *deps])
            link.append(str(tmp / "deps.a"))

        test_c.write_text(ex["test"])
        r = run(["cc", "-w", *inc, *link, "-o", str(exe)])
        if r.returncode != 0:
            print("❌ Erro ao ligar com os testes (protótipo errado ou "
                  "dependência em falta?):\n" + r.stderr)
            print("Dica: se usas outras funções tuas, têm de existir e "
                  "compilar em rendu/.")
            return False

        try:
            r = run([str(exe)], timeout=5)
        except subprocess.TimeoutExpired:
            print("❌ Timeout (ciclo infinito?)")
            return False

        print(r.stdout)
        if r.returncode < 0:
            print(f"❌ Crash (sinal {-r.returncode}) — segfault?")
            return False
        if r.returncode != 0:
            return False

        if ex.get("heap") and shutil.which("valgrind"):
            try:
                v = run(["valgrind", "-q", "--leak-check=full",
                         "--error-exitcode=42", str(exe)], timeout=60)
            except subprocess.TimeoutExpired:
                print("❌ Valgrind: timeout")
                return False
            if v.returncode == 42:
                print("❌ Valgrind: leaks ou erros de memória:\n" + v.stderr[-1500:])
                return False
            print("✔ Valgrind OK (sem leaks)")
        return True


def load():
    try:
        return set(json.loads(PROGRESS.read_text()))
    except (OSError, ValueError):
        return set()


def main():
    RENDU.mkdir(exist_ok=True)
    header = RENDU / "libft.h"
    if not header.exists():
        header.write_text(LIBFT_H)
        print("ℹ rendu/libft.h criado automaticamente.")

    done = load()
    only = sys.argv[1] if len(sys.argv) > 1 else None
    if only:
        todo = [e for e in EXOS if e["name"] == only]
        if not todo:
            print(f"Exercício desconhecido: {only}")
            return
    else:
        todo = [e for e in EXOS if e["name"] not in done]

    for ex in todo:
        idx = EXOS.index(ex) + 1
        print("=" * 56)
        print(f"Exercício {idx}/{len(EXOS)}: {ex['name']}  "
              f"({len(done)} feitos)")
        print("=" * 56)
        print(ex["subject"])
        print(f"\nEscreve o teu código em rendu/{ex['name']}.c")
        start = time.time()
        while True:
            cmd = input("\n[Enter] = Grademe   [q] = sair > ").strip().lower()
            if cmd == "q":
                return
            if grade(ex):
                mins, secs = divmod(int(time.time() - start), 60)
                print(f"✅ Success! ({mins}m{secs:02d}s)\n")
                done.add(ex["name"])
                PROGRESS.write_text(json.dumps(sorted(done)))
                break
            print("Resultado: ❌ tenta outra vez.")
    print("🎉 Fizeste todos os exercícios!")


if __name__ == "__main__":
    main()
