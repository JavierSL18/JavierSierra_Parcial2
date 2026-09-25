# Parcial 2 — HelpDesk EDU (módulo independiente)

Este paquete resuelve los 5 ejercicios de la guía "Etiquetas y encapsulamiento
/ Observadores / Excepciones y polimorfismo / SQL / SQLAlchemy" como un
**módulo autocontenido**, sin tocar tu repositorio real. Incluye una copia
completa y funcional del proyecto base (semanas 7–9) más los cambios de cada
ejercicio, para que puedas correr `pytest` aquí mismo y luego copiar los
archivos a tu repositorio de GitHub.

## Cómo correrlo

```bash
cd parcial2
pip install -e .            # o: pip install sqlalchemy pytest
pytest -q
```

## Bug preexistente que se corrigió

En `app/services/tickets.py`, el método `list(...)` sobreescribe el nombre
`list` dentro de la clase. Cualquier anotación escrita **después** de ese
método (`-> list[Ticket]`, en `list_by_status`, `assigned_to`, `watchers`)
falla con `TypeError: 'function' object is not subscriptable` en Python
3.10+, porque Python resuelve `list` contra el nombre ya definido en la
clase en vez del tipo builtin. **Esto ya viene así en tu .zip original**, no
es algo introducido por los ejercicios — lo comprobé importando tu archivo
tal cual. La solución (ya aplicada aquí) es agregar
`from __future__ import annotations` al inicio del archivo, que difiere la
evaluación de anotaciones y no cambia ningún comportamiento. Debes aplicar
el mismo cambio en tu repositorio real o los tests de las semanas 7–9 fallarán
al importar el módulo.

## Mapa de archivos por ejercicio

| Ejercicio | Archivos modificados/nuevos | Tests |
|---|---|---|
| 1. Etiquetas y encapsulamiento | `app/models/entities.py` (agrega `_tags`, `tags`, `add_tag`) | `tests/test_ex1_tags.py` |
| 2. Observadores | `app/services/tickets.py` (agrega `watchers`) | `tests/test_ex2_watchers.py` |
| 3. Excepciones y polimorfismo | `app/domain/errors.py` (`DuplicateAssignmentError`), `app/services/tickets.py` (chequeo en `assign`), `app/services/notifications.py` (`WebhookNotifier`) | `tests/test_ex3_duplicate_and_webhook.py` |
| 4. SQL e integridad referencial | `docs/database/queries_parcial2.sql` | Evidencia manual en PostgreSQL (ver abajo) |
| 5. SQLAlchemy | `app/repositories/sqlalchemy.py` (nuevo) | `tests/test_ex5_sqlalchemy_repository.py` |

## Ejercicio 1 — Etiquetas y encapsulamiento

- `_tags: list[str] = field(default_factory=list, init=False, repr=False)`:
  colección **por instancia** (cada `Ticket` tiene la suya, no se comparte),
  oculta del `__init__` generado y del `repr`.
- `tags` es una `@property` de solo lectura que devuelve `tuple(self._tags)`.
  Como no tiene `setter`, `ticket.tags = [...]` lanza `AttributeError`
  automáticamente (no hace falta código extra para "bloquearlo").
- `add_tag(tag)` aplica `strip().lower()`, rechaza vacíos con
  `ValidationError` y evita duplicados comparando contra la lista ya
  normalizada.

## Ejercicio 2 — Observadores

`TicketService.watchers(ticket_id)`:
1. Usa `self.require(ticket_id)` (no toca el repositorio directamente).
2. Agrega al solicitante con `self._users.require(ticket.requester_id)`.
3. Si hay técnico asignado, lo agrega con `self._users.require(...)` solo si
   su `id` no está ya en la lista (deduplicación por id, no por identidad de
   objeto).

## Ejercicio 3 — Excepciones y polimorfismo

- `DuplicateAssignmentError(DomainError)`: se lanza en `assign()` **antes**
  de tocar `ticket.assignee_id`, historial o notificaciones — se agregó el
  chequeo inmediatamente después de `self._ensure_open(ticket)`.
- `WebhookNotifier(Notifier)`: implementa el mismo contrato que
  `NullNotifier`/`ConsoleNotifier`/`RecordingNotifier`. Guarda cada llamada
  como un diccionario en `self.sent_payloads` (sin HTTP, sin `print`). Se
  inyecta por el parámetro `notifier` que `TicketService` ya aceptaba —
  **no se agregó ningún `if isinstance(...)`** en el servicio: es
  polimorfismo puro sobre `Notifier.notify(...)`.

## Ejercicio 4 — SQL e integridad referencial

Archivo: `docs/database/queries_parcial2.sql`. Es autocontenido: recrea el
esquema (`users`, `tickets`, `comments`, `ticket_history`), carga datos de
prueba y luego corre las 4 consultas:

- **(a)** tickets abiertos + nombre del solicitante (`JOIN`).
- **(b)** conteo de tickets por técnico, `GROUP BY id, name`, `HAVING
  COUNT(t.id) > 0`, `ORDER BY ... DESC`.
- **(c)** tickets sin comentarios con `NOT EXISTS` (se deja comentada la
  variante `LEFT JOIN` como referencia).
- **(d)** `BEGIN` → conteo de `ticket_history` antes → `DELETE FROM tickets`
  → conteo después (debe dar 0 por el `ON DELETE CASCADE`) → `ROLLBACK` →
  conteo final (vuelve al valor original).

Para generar tu evidencia:

```bash
psql -U <usuario> -d <tu_base> -f docs/database/queries_parcial2.sql > evidencia_sql.txt
```

y adjunta `evidencia_sql.txt` (o capturas de pantalla) en tu entrega.

## Ejercicio 5 — SQLAlchemy

`app/repositories/sqlalchemy.py` define:

- `TicketORM` (mapeo declarativo mínimo de `tickets`).
- `SqlAlchemyTicketRepository`, que implementa el contrato
  `TicketRepository` **sin modificarlo** (`add`, `by_id`, `list`, `next_id`)
  y agrega `count_by_status() -> dict[str, int]` con:
  ```python
  select(TicketORM.status, func.count()).group_by(TicketORM.status)
  ```
  Devuelve `{}` si no hay tickets, y solo los estados presentes.
- `build_sqlite_engine()` usa `StaticPool` para que una base SQLite en
  memoria persista entre distintas sesiones/`sessionmaker` sobre el mismo
  `engine` (necesario para el requisito de "confirmar, cerrar la sesión y
  consultar desde una sesión nueva").

> Nota: en este entorno de conversación no tengo acceso a internet para
> instalar `sqlalchemy` y ejecutar sus pruebas aquí mismo (sí verifiqué que
> el archivo compila sin errores de sintaxis). Ejecuta `pytest -q` en tu
> máquina para confirmar `tests/test_ex5_sqlalchemy_repository.py`; si algo
> falla por una diferencia de versión de SQLAlchemy, dime el error exacto y
> lo ajustamos.

## Limitaciones / decisiones tomadas

- El esquema SQL del ejercicio 4 es una propuesta mínima (no existía un
  esquema PostgreSQL en tu proyecto todavía, solo modelos en memoria);
  ajusta nombres de tabla/columnas si tu proyecto real ya define un
  `schema.sql` distinto.
- `TicketORM` no mapea `comments`, `history` ni `tags`: el ejercicio 5 pide
  específicamente la agregación por estado, así que se mantuvo el modelo
  ORM mínimo para no inflar el alcance. Si luego integras esto a tu
  repositorio completo, puedes extenderlo con esas relaciones.
- Todo lo demás (formato de errores, notificadores existentes, reglas de
  transición de estado) se dejó intacto, tal como pide la consigna.
