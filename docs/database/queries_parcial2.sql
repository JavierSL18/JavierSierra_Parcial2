DROP TABLE IF EXISTS ticket_history CASCADE;
DROP TABLE IF EXISTS comments CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
    id      SERIAL PRIMARY KEY,
    name    TEXT NOT NULL,
    email   TEXT NOT NULL UNIQUE,
    role    TEXT NOT NULL
);

CREATE TABLE tickets (
    id            SERIAL PRIMARY KEY,
    title         TEXT NOT NULL,
    description   TEXT NOT NULL DEFAULT '',
    category      TEXT NOT NULL,
    priority      TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'open',
    requester_id  INTEGER NOT NULL REFERENCES users(id),
    assignee_id   INTEGER REFERENCES users(id),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE comments (
    id          SERIAL PRIMARY KEY,
    ticket_id   INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    author_id   INTEGER NOT NULL REFERENCES users(id),
    body        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE ticket_history (
    id          SERIAL PRIMARY KEY,
    ticket_id   INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    actor_id    INTEGER NOT NULL REFERENCES users(id),
    event_type  TEXT NOT NULL,
    detail      TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);


INSERT INTO users (name, email, role) VALUES
    ('Sofia Solicitante', 'sofia@school.edu', 'requester'),
    ('Tomas Tecnico',     'tomas@school.edu', 'technician'),
    ('Carla Supervisora', 'carla@school.edu', 'supervisor');

INSERT INTO tickets (title, description, category, priority, status, requester_id, assignee_id) VALUES
    ('No puedo conectarme al WiFi', 'La red institucional no autentica', 'Network',  'High',   'open',        1, 2), -- id 1: tiene historial y comentario
    ('Impresora no responde',       'La impresora del 3er piso no imprime', 'Hardware', 'Medium', 'in_progress', 1, 2), -- id 2: tiene historial, sin comentarios
    ('Solicitud de licencia',       'Necesita licencia de Office',          'Software', 'Low',    'open',        1, NULL); -- id 3: sin técnico, sin comentarios

INSERT INTO comments (ticket_id, author_id, body) VALUES
    (1, 2, 'Estamos revisando el punto de acceso');

INSERT INTO ticket_history (ticket_id, actor_id, event_type, detail) VALUES
    (1, 2, 'assigned', 'assigned to Tomas Tecnico'),
    (1, 2, 'commented', 'comment added'),
    (2, 2, 'assigned', 'assigned to Tomas Tecnico');

SELECT
    t.id,
    t.title,
    t.status,
    u.name AS requester_name
FROM tickets t
JOIN users u ON u.id = t.requester_id
WHERE t.status = 'open'
ORDER BY t.id;



SELECT
    u.id   AS technician_id,
    u.name AS technician_name,
    COUNT(t.id) AS ticket_count
FROM users u
JOIN tickets t ON t.assignee_id = u.id
GROUP BY u.id, u.name
HAVING COUNT(t.id) > 0
ORDER BY ticket_count DESC;



SELECT
    t.id,
    t.title
FROM tickets t
WHERE NOT EXISTS (
    SELECT 1
    FROM comments c
    WHERE c.ticket_id = t.id
)
ORDER BY t.id;


BEGIN;

SELECT COUNT(*) AS history_before_delete
FROM ticket_history
WHERE ticket_id = 1;

DELETE FROM tickets WHERE id = 1;

SELECT COUNT(*) AS history_after_delete
FROM ticket_history
WHERE ticket_id = 1;

ROLLBACK;

SELECT COUNT(*) AS history_after_rollback
FROM ticket_history
WHERE ticket_id = 1;

SELECT COUNT(*) AS tickets_total FROM tickets;
