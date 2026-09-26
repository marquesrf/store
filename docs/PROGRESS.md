# Progresso (log append-only)

## 2026-09-25 — T0.1 Setup
- `uv init --lib` layout `src/store/` (renomeado de `loja` em T2.1→T2.2); Python 3.14.7; uv 0.12.19.
- Dev deps: pytest, pytest-cov, ruff, mypy, hypothesis.
- Config no pyproject: Ruff (E,F,I,UP,B,C4,SIM, py314), pytest (testpaths=tests), mypy strict.
- Teste smoke `tests/test_smoke.py`.
- Provas: ver saída na revisão (pytest / ruff / mypy).
- Status: **aprovado**.

## 2026-09-25 — T1.1 Value Objects
- `domain/exceptions.py`: `DomainError` + `InvalidMoney`, `CurrencyMismatch`, `InvalidSku`, `InvalidQuantity`.
- `domain/value_objects.py`: `Money` (centavos int, aritmética + ordenação, moeda ISO), `Sku` (normaliza upper/strip, regex), `Quantity` (int >= 1).
- `tests/unit/test_value_objects.py`: 37 testes — parametrize + Hypothesis (roundtrip Money, alnum Sku, soma Quantity).
- Provas: pytest 37 passed; ruff/format limpos; mypy strict limpo; cobertura domain 95% (faltam só `__str__`).
- Decisão: Money em centavos int (float não é exato); mismatch de moeda é erro de domínio, não coerção.
- Status: **aprovado** (comentários migrados p/ inglês; regra registrada em memória).

## 2026-09-25 — T1.2 Order aggregate
- `domain/order.py`: `OrderStatus` (OPEN/PAID/CANCELLED), `OrderLine` (frozen, `subtotal`), `Order` (aggregate root).
- Invariantes: só modifica se OPEN; sem pagar vazio; sem pagar/cancelar 2x; moeda da linha == moeda do pedido; merge de SKU repetido soma quantidade.
- `_lines` privado; `lines` expõe view read-only (tuple). Mutação só via métodos.
- Novas exceções: `OrderNotModifiable`, `EmptyOrder`, `LineNotFound`.
- `tests/unit/test_order.py`: 13 testes por comportamento. Provas: 50 passed; ruff/mypy limpos; order.py cobertura 100%, domain 98%.
- Decisão (ponytail): merge de SKU mantém 1º preço; catálogo real re-precificaria. Comentado no código.
- Status: **aprovado**.

## 2026-09-25 — T1.3 Domain events
- `domain/events.py`: `DomainEvent` base + `OrderPlaced(order_id,total_cents,currency)`, `OutOfStock(sku,requested,available)` (frozen dataclasses).
- `Order`: grava `OrderPlaced` no `pay()`; `pull_events()` retorna e limpa (bus despacha 1x).
- `domain/stock.py`: `StockItem.allocate()` — reserva ou grava `OutOfStock` se faltar. Adicionado pra dar emissor real ao evento (senão ficaria morto/sem teste).
- `tests/unit/test_events.py`: 5 testes (grava/limpa/vazio; alocação ok e faltante).
- Provas: 55 passed; ruff/mypy limpos; domain 99% (faltam só `__str__` de Money).
- Decisão (ponytail): `pull_events` duplicado em Order/StockItem; extrair base só se surgir 3º recorder. Comentado.
- Fim da Fase 1: domínio puro completo (VOs + Order + eventos + estoque mínimo).
- Status: **aprovado**.

## 2026-09-25 — T2.1 Ports + service layer
- `service_layer/ports.py`: `OrderRepository` e `UnitOfWork` como `Protocol` (DIP). `orders` é property read-only (covariância).
- `service_layer/services.py`: `place_order(uow, order_id, items, currency)` — DTO `ItemInput` (primitivos na fronteira), monta domínio, paga, persiste, commit atômico.
- `adapters/memory.py`: `InMemoryOrderRepository` + `InMemoryUnitOfWork` (fake real, sem mock; `committed` observável; rollback ao sair sem commit).
- `tests/unit/test_services.py`: 4 testes com fake — persiste pago, commit, evento OrderPlaced, vazio → EmptyOrder sem commit.
- Provas: 59 passed; ruff/mypy limpos; cobertura total 99%.
- Fix mypy: atributo `orders` no Protocol era invariante → virou property read-only (adapter não precisa importar o port).
- Status: **aprovado**. Depois renomeado o projeto loja→store.

## 2026-09-25 — Rename loja → store
- Dir raiz, pacote `src/store/`, imports, `pyproject name`, docs. uv.lock/.venv regerados. 59 passed.
- Gotcha: `sed` macOS não tem `\b`; usei substituição direta.

## 2026-09-25 — T2.2 Persistência (data mapper) + Alembic
- Decisão (com o usuário): **data mapper manual**, não imperative mapping — domínio frozen+slots ficaria enfraquecido pelo ORM. Domínio intacto.
- `adapters/orm.py`: tabelas Core (`orders`, `order_lines`) — FK CASCADE, unique (order_id, sku). Só schema, sem mapear nas classes.
- `adapters/sqlalchemy.py`: `SqlAlchemyOrderRepository` (traduz linha↔objeto via `select`/`insert`), `SqlAlchemyUnitOfWork` (session, commit/rollback, close). Rehydrate constrói OPEN + set status direto (não re-emite OrderPlaced).
- Alembic: `migrations/`, `env.py` → `orm.metadata`, url sqlite:///store.db. Migração inicial autogerada, script conferido à mão, `upgrade head` cria tabelas.
- Teste integração `tests/integration/`: SQLite in-memory (StaticPool + conexão única compartilhada). 4 testes: roundtrip, sem evento no rehydrate, rollback em erro, get inexistente.
- Config: `migrations/` excluído de ruff e mypy (autogerado). `store.db` no gitignore.
- Provas: 63 passed; ruff/mypy limpos; migração aplica do zero.
- Nota (ponytail): SQLite precisa `render_as_batch=True` no env.py pra ALTER futuro; adiciono quando surgir migração que altera coluna.
- Status: **aprovado**.

## 2026-09-25 — T2.3 FastAPI ponta-a-ponta
- `config.py`: `Settings` (pydantic-settings, prefixo STORE_, .env), `database_url` default sqlite:///store.db.
- `entrypoints/api.py`: `POST /orders` (201), `GET /orders/{id}`. Pydantic v2 DTOs só na borda (ItemPayload/PlaceOrderRequest/OrderResponse). UoW via `Depends(get_uow)` (override em teste). Mapa de erro: IntegrityError→409, DomainError→400, ausente→404, validação Pydantic→422.
- Logging: `logger.info` key=value com %-args (lazy) na service layer ao pagar pedido.
- Rota fina: zero regra de negócio; só parse→service→map.
- Teste e2e `tests/e2e/test_api.py`: TestClient + SQLite in-memory (dependency_overrides). 4 testes: place→fetch, items vazio→422, duplicado→409, ausente→404.
- Fix ruff: B008 (Depends em default) é idioma FastAPI → `extend-immutable-calls`.
- Provas: 67 passed; ruff/mypy limpos.
- Fim da Fase 2: domínio + service + adapters (memória/SQLAlchemy) + HTTP, todos plugados via Protocols.
- Status: **aprovado**.

## 2026-09-25 — T3.1 Message bus
- `service_layer/messagebus.py`: `MessageBus` — dict `type[DomainEvent] -> [handlers]`, `handle(events)` roteia por tipo. Registry `Callable[[Any], None]` (evita contravariância).
- `service_layer/handlers.py`: handlers default (log OrderPlaced/OutOfStock), `DEFAULT_HANDLERS`, `make_bus()` (composition point).
- `place_order` ganhou `bus: MessageBus | None = None`; despacha `order.pull_events()` **após commit** (fora do with) — handler nunca reage a algo que deu rollback. Opcional → não quebrou chamadas antigas.
- `entrypoints/api.py`: `_bus = make_bus()`, passado no `post_order`.
- Testes: `tests/unit/test_messagebus.py` (4: rota, múltiplos handlers, por tipo, sem handler=no-op) + 1 em test_services (dispatch pós-place).
- Provas: 72 passed; ruff/mypy limpos.
- Status: **aprovado**.

## 2026-09-25 — T3.2 Concorrência
- `src/store/concurrency.py`: `fetch_prices` com `asyncio.TaskGroup` (3.11+) — structured concurrency, roda `-m store.concurrency`.
- `tests/unit/test_concurrency.py`: 2 testes via `asyncio.run` (sem pytest-asyncio) — resultado concorrente + `ExceptionGroup` quando uma task falha.
- NOTES: regra threads(I/O bloqueante) vs processos(CPU) vs async(I/O escala); estado free-threading (não-experimental 3.14, não-default) e JIT (experimental).
- Provas: 74 passed; ruff/mypy limpos; demo imprime {'a':100,'bb':200,'ccc':300}.
- Status: **aprovado**.

## 2026-09-26 — T3.3 Produção (Docker + CI + pre-commit)
- `Dockerfile`: multi-stage com uv (builder faz `uv sync --frozen --no-dev`; runtime python-slim, non-root, uvicorn). `.dockerignore` enxuga contexto.
- `.github/workflows/ci.yml`: uv (setup-uv, cache) → sync --frozen → ruff check → ruff format --check → mypy → pytest.
- `.pre-commit-config.yaml`: ruff (--fix) + ruff-format + mypy (hook local via venv).
- Deps: uvicorn (runtime), pre-commit (dev). uv.lock frozen ok.
- Provas: sequência de CI rodada localmente toda verde (74 passed); Docker build NÃO executado (daemon off) — validar com Docker Desktop ligado.
- Fim da Fase 3 → **projeto completo**.
- Status: **em revisão**.
