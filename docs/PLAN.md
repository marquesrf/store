# Projeto store — backlog (fases → tarefas)

Modelo: uma tarefa por vez em auto mode; paro para revisão antes da próxima.
Cada tarefa fecha com sua **prova de conclusão** passando.

## Fase 0 — Setup
- [x] **T0.1** — `uv init` layout `src/`, deps dev, config Ruff/pytest/mypy strict, teste smoke verde.

## Fase 1 — Domínio puro (sem banco/framework)
- [x] **T1.1** — Value Objects `Money`, `Sku`, `Quantity` (frozen+slots, validação) + testes.
- [x] **T1.2** — `Order` aggregate root protegendo invariantes + testes.
- [x] **T1.3** — Domain events `OrderPlaced`, `OutOfStock` + testes.

## Fase 2 — Arquitetura e infraestrutura
- [x] **T2.1** — Ports (`Protocol`) `Repository`/`UnitOfWork`, fake em memória, service layer + testes.
- [x] **T2.2** — SQLAlchemy 2.0 (data mapper manual) + Alembic + repo real + teste integração.
- [x] **T2.3** — FastAPI (1 endpoint ponta-a-ponta) + Pydantic v2 + settings + logging + teste e2e.

## Fase 3 — Avançado
- [x] **T3.1** — Message bus despachando domain events.
- [x] **T3.2** — Concorrência: asyncio/TaskGroup + nota threads/processos/async.
- [x] **T3.3** — Docker (uv) + CI GitHub Actions (ruff+pytest+mypy) + pre-commit.

**Projeto completo** — todas as fases fechadas (2026-09-26).
