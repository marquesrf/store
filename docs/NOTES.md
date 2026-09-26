# Notas / decisões (ADR-lite)

## T0.1
- `uv init --lib` (não `--app`): layout `src/` com pacote importável, melhor pra
  domínio + testes + futuro empacotamento.
- Ruff faz lint **e** format (substitui black+flake8+isort).
- mypy `--strict` via `[tool.mypy] strict = true` (padrão seguro; `ty` ainda beta).
- Deps de dev no grupo `dev` (`[dependency-groups]`), não em `[project]`.

## T3.2 — Concorrência: quando usar o quê
Regra prática de escolha:
- **asyncio** (`TaskGroup`, 3.11+): tarefas **I/O-bound** e de alta escala — muitas
  chamadas de rede/DB esperando ao mesmo tempo (ex.: buscar preços de N SKUs).
  Um thread só, cooperativo; não acelera CPU. É o caso do exemplo `concurrency.py`.
- **threads** (`ThreadPoolExecutor`): I/O-bound com **libs bloqueantes** que não têm
  API async (drivers legados, `requests`). O GIL não atrapalha aqui porque threads
  esperam I/O.
- **processos** (`ProcessPoolExecutor`): **CPU-bound** (cálculo pesado). Cada processo
  tem seu interpretador → paraleliza CPU de verdade, ao custo de serializar dados
  entre processos.

Estado 2026 (verificar sempre):
- **Free-threading (sem GIL)**: PEP 779 aceita → **não é mais experimental no 3.14**,
  mas **não é o build padrão** e ~metade das libs C ainda não suportam. Quando maduro,
  threads passam a paralelizar CPU também. Hoje: saber que existe, não basear projeto.
- **JIT**: ainda **experimental** no 3.14. Idem — acompanhar, não depender.

Por que `TaskGroup` no exemplo: structured concurrency — espera todas, e se uma falha
cancela as irmãs e levanta `ExceptionGroup` (sem tarefa vazada / resultado parcial).
