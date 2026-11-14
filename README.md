# Mini-Grademe para a Libft

Ferramenta de treino em linha de comandos que compila e testa automaticamente as funções da tua **Libft**, exercício a exercício, do mais fácil ao mais difícil. Inspirada no Grademe da 42.

Escreves a função num ficheiro `.c`, carregas Enter, e o script diz-te se passaste (`✅ Success`) ou onde falhou (`KO (esperado X, recebeste Y)`). Quando passas, desbloqueia o exercício seguinte.

> Esta ferramenta serve **apenas para treinar**. Não substitui a avaliação entre pares nem a Deepthought. Passar aqui não garante passar lá (ver [Limitações](#limitações)).

---

## Requisitos

| Obrigatório | Opcional |
|---|---|
| Python 3.8+ | `norminette` (verifica a Norm em cada `.c`) |
| `cc` (gcc ou clang) | `valgrind` (deteta leaks nos exercícios com `malloc`) |
| `ar` | |

Testado em Linux. Em macOS deve funcionar, mas o Valgrind normalmente não está disponível (o passo é simplesmente ignorado).

---

## Instalação

Não há nada para instalar. Põe o `grademe.py` numa pasta tua (fora do repositório da Libft, ou dentro e ignorado pelo Git) e corre-o:

```bash
python3 grademe.py
```

Na primeira execução é criada a pasta `rendu/` com um `libft.h` já preparado.

---

## Estrutura de pastas

```
grademe.py          # o script
.progress.json      # progresso (criado automaticamente)
rendu/              # AQUI é que escreves o teu código
├── libft.h         # criado automaticamente se não existir
├── ft_isalpha.c
├── ft_isdigit.c
└── ...
```

Cada exercício tem **um ficheiro com o nome da função**: `rendu/ft_strlen.c`, `rendu/ft_split.c`, etc.

---

## Uso

### Continuar de onde ficaste

```bash
python3 grademe.py
```

Mostra o enunciado do próximo exercício por fazer. Escreve o código em `rendu/<nome>.c` e usa:

- **Enter** → correr o Grademe
- **q** → sair (o progresso fica guardado)

### (Re)testar um exercício específico

```bash
python3 grademe.py ft_strlcat
```

Útil para voltar a um exercício já feito (por exemplo depois de alterares uma função da qual outras dependem).

### Recomeçar do zero

Apaga o ficheiro de progresso:

```bash
rm .progress.json
```

---

## O que acontece quando carregas Enter

1. **Norminette** (só se estiver instalada): corre sobre o teu `.c`. Erro de Norm = falha, como na 42.
2. **Compilação** do teu ficheiro com `cc -Wall -Wextra -Werror -I rendu`.
3. **Ligação** com um `main` de teste gerado pelo script. Se a tua função usar outras funções tuas (por exemplo `ft_lstadd_back` a chamar `ft_lstlast`), os outros `rendu/ft_*.c` que compilem são ligados automaticamente.
4. **Execução** dos testes (limite de 5 segundos).
5. **Valgrind** (só se estiver instalado e só nos exercícios com `malloc`): falha se houver leaks ou erros de memória.

### Exemplo de saída

```
========================================================
Exercício 1/43: ft_isalpha  (0 feitos)
========================================================
int ft_isalpha(int c);
Devolve 1 se c for letra, senão 0.

Escreve o teu código em rendu/ft_isalpha.c

[Enter] = Grademe   [q] = sair >
✔ Compilação OK
Test  1  c=   0 -> OK
Test  2  c=   9 -> OK
...
Test  7  c=  90 -> KO (esperado 1, recebeste 0)
...
Resultado: 19/20 KO
Resultado: ❌ tenta outra vez.
```

Quando passa tudo:

```
Resultado: 20/20 OK
✅ Success! (1m23s)
```

---

## Mensagens de erro comuns

| Mensagem | O que significa |
|---|---|
| `Ficheiro não encontrado` | O ficheiro não existe em `rendu/` ou tem o nome errado. |
| `Erro de compilação` | O teu `.c` não compila com `-Wall -Wextra -Werror`. Lê o erro do compilador. |
| `Erro ao ligar com os testes` | Protótipo diferente do esperado, ou usas uma função tua que não existe / não compila. |
| `Crash (sinal 11)` | Segmentation fault na tua função. |
| `Timeout` | Ciclo infinito (ou demasiado lento). |
| `KO (esperado X, recebeste Y)` | Resultado diferente do da função original. |
| `Valgrind: leaks ou erros de memória` | Memória não libertada, leitura/escrita inválida, etc. |

Nos testes de ponteiros (`strchr`, `memchr`, `strnstr`…) os valores mostrados são **offsets** relativos ao início da string, e `-1` significa `NULL`. Em `strncmp` e `memcmp` compara-se apenas o **sinal** (-1, 0, 1), porque o valor exato varia entre implementações.

---

## Exercícios (por ordem)

| # | Função | Notas |
|--:|---|---|
| 1–5 | `ft_isalpha`, `ft_isdigit`, `ft_isalnum`, `ft_isascii`, `ft_isprint` | Devolvem 1 ou 0. Testados contra a libc. |
| 6–7 | `ft_toupper`, `ft_tolower` | Incluem valores limite (0, 127, 128, 255, -1). |
| 8 | `ft_strlen` | Inclui string vazia e string com `\0` no meio. |
| 9–12 | `ft_putchar_fd`, `ft_putstr_fd`, `ft_putendl_fd`, `ft_putnbr_fd` | Saída capturada por um pipe. `putnbr_fd` testa `INT_MIN`. |
| 13 | `ft_striteri` | Índice e endereço do char. |
| 14–15 | `ft_bzero`, `ft_memset` | Offsets, `n = 0`, valor > 255 (conversão para `unsigned char`). |
| 16–17 | `ft_strchr`, `ft_strrchr` | Procurar `'\0'` devolve o terminador. |
| 18–20 | `ft_strncmp`, `ft_memcmp`, `ft_memchr` | Comparação como `unsigned char`; `memchr` não pára no `\0`. |
| 21 | `ft_atoi` | Espaços, sinais múltiplos, lixo no fim, limites do `int`. |
| 22 | `ft_memcpy` | |
| 23–24 | `ft_strdup`, `ft_calloc` | `calloc(0, 0)` não pode devolver `NULL`; protege contra overflow. |
| 25–29 | `ft_lstnew`, `ft_lstsize`, `ft_lstlast`, `ft_lstadd_front`, `ft_lstadd_back` | Incluindo lista vazia. |
| 30–32 | `ft_lstiter`, `ft_lstdelone`, `ft_lstclear` | `lstdelone` não pode libertar o nó seguinte; `lstclear` põe `*lst = NULL`. |
| 33 | `ft_memmove` | Zonas sobrepostas nos dois sentidos. |
| 34–35 | `ft_strlcpy`, `ft_strlcat` | Truncagem, `size` pequeno ou 0, valor devolvido. |
| 36–37 | `ft_substr`, `ft_strjoin` | `start` além do fim, `len` enorme, strings vazias. |
| 38–40 | `ft_strmapi`, `ft_strtrim`, `ft_itoa` | `itoa` testa negativos e `INT_MIN`. |
| 41 | `ft_strnstr` | Falsos arranques (ex.: procurar `"abcd"` em `"aaabcabcd"`). |
| 42 | `ft_lstmap` | Cria lista nova; original intacta. |
| 43 | `ft_split` | Delimitadores repetidos, string vazia, array terminado em `NULL`. |

A ordem é uma sugestão de dificuldade. Podes alterá-la na lista `ORDER` no fim da definição dos exercícios em `grademe.py`.

---

## Sobre o `libft.h`

O script gera `rendu/libft.h` (com o `t_list` e todos os protótipos) se ele não existir. Os teus ficheiros devem fazer `#include "libft.h"` quando precisarem do `t_list` ou dos protótipos.

Se já tens o teu próprio `libft.h`, ele é usado tal como está. Neste caso confirma que contém **todos** os protótipos; se acrescentaste funções novas à ferramenta e o teu header é antigo, apaga-o ou atualiza-o.

---

## Adicionar ou alterar exercícios

Cada exercício é uma entrada em `EXOS` criada com `ex(nome, enunciado, corpo_do_teste, heap=...)`. O corpo do teste é o `main` em C; já tens disponíveis os auxiliares:

- `check_b(cond, desc)`: verifica uma condição.
- `check_l(esperado, recebido, desc)`: compara inteiros.
- `check_s(esperado, recebido, desc)`: compara strings (aceita `NULL`).
- `cap_begin()` / `cap_end()`: capturam o que é escrito num file descriptor.
- `mk()` / `freelst()`: criam e libertam listas.
- `finish()`: imprime `Resultado` e devolve o código de saída.

Depois acrescenta o nome à lista `ORDER`. O script verifica no arranque que `ORDER` e `EXOS` têm exatamente os mesmos nomes.

Usa `heap=True` nos exercícios que alocam memória para ativar o Valgrind. Garante que o teste liberta tudo o que aloca, senão dá falsos positivos.

---

## Limitações

Esta ferramenta **não verifica**:

- O `Makefile` (regras `$(NAME)`, `all`, `clean`, `fclean`, `re`, relink desnecessário).
- A criação do `libft.a` com `ar` na raiz do repositório.
- Variáveis globais, funções externas proibidas ou uso de funções da libc dentro das tuas (ex.: chamar `strlen` em vez de `ft_strlen`).
- A Norm do `libft.h` (só dos `.c`, e só se a `norminette` estiver instalada).
- Falhas de `malloc`.
- Comportamento com argumentos `NULL` (indefinido na maioria das funções da libc).

Os testes cobrem muitos casos limite, mas não todos. Na defesa, o avaliador pode testar outros e pedir-te para explicar e modificar o código. Escreve também os teus próprios testes.

---

## Resolução de problemas

**`cc: command not found`**: instala um compilador (`sudo apt install build-essential` em Debian/Ubuntu).

**`undefined reference to ft_xxx`**: a tua função chama outra função tua que não existe em `rendu/` ou que não compila com `-Wall -Wextra -Werror`.

**Passa sem Valgrind mas queres a verificação de leaks**: `sudo apt install valgrind`.

**Norminette não corre**: `pip install norminette` (ou usa a versão da tua escola).

**Falha num teste que achas correto**: confirma o comportamento no `man` da função. Se tens a certeza de que é um erro do teste, ajusta-o em `grademe.py`.

---

## README da tua Libft (modelo)

O `README.md` que entregas no repositório da Libft tem regras próprias no enunciado (capítulo V). Um esqueleto que cumpre os requisitos:

````markdown
*This project has been created as part of the 42 curriculum by <login>.*

## Description

Libft é a minha biblioteca C com funções de uso geral: reimplementação de
funções da libc, funções adicionais de strings/memória/ficheiros e
manipulação de listas ligadas.

## Instructions

```bash
make        # compila e cria libft.a
make clean  # remove os .o
make fclean # remove os .o e libft.a
make re     # recompila tudo
```

Para usar: `#include "libft.h"` e compilar com `cc main.c -L. -lft`.

## Library

Descrição detalhada das funções:

- **Parte 1 – Libc:** `ft_isalpha`, `ft_strlen`, `ft_memcpy`, ...
- **Parte 2 – Adicionais:** `ft_substr`, `ft_split`, `ft_itoa`, ...
- **Parte 3 – Listas:** `ft_lstnew`, `ft_lstadd_back`, `ft_lstmap`, ...

(Explica aqui as escolhas de implementação mais relevantes.)

## Resources

- `man 3 <função>` para cada função da libc.
- (artigos, tutoriais, documentação que usaste)
- **Uso de IA:** descreve para que tarefas e em que partes do projeto usaste
  IA (por exemplo, geração do script de testes `grademe.py`), de forma honesta.
````
