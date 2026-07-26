# Day 3 — SQLAlchemy 2.x + PostgreSQL
> **Theme:** Giving the application memory. Data now persists beyond the lifecycle of a request.

---

## Why This Day Exists

After Day 1 and Day 2, the API could receive data and validate it. But the moment the server restarted, everything was gone. A clinic system that forgets appointments on restart is not an application — it is a simulation. Day 3 solves that by introducing PostgreSQL as the persistence layer and SQLAlchemy as the tool that lets Python talk to it.

---

## Why PostgreSQL

Patient records, doctor assignments, appointment slots — this is structured, relational data. Relationships between entities are not optional here, they are the core of the domain. PostgreSQL enforces those relationships at the database level. It will not let you create an appointment for a doctor that does not exist. In a healthtech context, that kind of constraint is not just good practice — it is a compliance requirement.

---

## Why SQLAlchemy, Not Raw SQL

Raw SQL works. But it does not scale when models get complex, it is vulnerable to injection if handled carelessly, and you lose all type safety and IDE support. SQLAlchemy lets you define your tables as Python classes and work with Python objects. The translation to SQL happens behind the scenes.

---

## The SQLAlchemy 2.x Shift

The old 1.x pattern used a factory function and an imperative query style:

```python
Base = declarative_base()          # factory — old way
session.query(User).filter(...)    # imperative — old way
```

The 2.x pattern is class-based and uses SQL expression style:

```python
class Base(DeclarativeBase): pass  # class-based — new way
session.scalars(select(User).where(...))  # expression — new way
```

The reason this matters: 2.x is built for async from the ground up. The old session factory does not compose with asyncio. Since production AI APIs are I/O heavy, async DB support is non-negotiable.

---

## Docker and Why It Was Used Here

PostgreSQL was run inside a Docker container rather than installed directly on the machine. The reason is isolation — Docker lets you spin up a database service in a contained environment and throw it away cleanly when done. The machine stays unaffected.

Key concepts from the `docker-compose.yml`:

- `image: postgres:16` — pulls the official PostgreSQL image
- `environment` — sets the username, password, and database name that PostgreSQL needs on startup
- `ports: 5432:5432` — left side is your machine, right side is inside the container
- `volumes: pgdata:/var/lib/postgresql/data` — mirrors PostgreSQL's internal data folder to a named volume on your machine so data survives container restarts
- `restart: unless-stopped` — restarts automatically on crashes or reboots, but respects manual stops

### `unless-stopped` vs `always`

| Situation | `always` | `unless-stopped` |
|---|---|---|
| Container crashed on its own | Restarts | Restarts |
| Machine rebooted, container was running | Restarts | Restarts |
| You manually stopped it, then machine rebooted | Restarts anyway | Stays stopped |

`unless-stopped` is the right choice for local development. It survives accidents but respects intent.

---

## The Three Models and Why They Are Structured This Way

### Doctor and Patient

Straightforward entities. Each has its own table with its own fields. The relationship between them is many-to-many at its core — a patient can see many doctors, a doctor can see many patients.

### Why Appointment Is Not Just a Junction Table

SQLAlchemy supports automatic many-to-many relationships where it silently creates a bridge table for you. That works when the link between two entities carries no data of its own — like a student-course enrollment where you only care that the link exists.

An Appointment is different. It carries:
- A scheduled datetime
- Clinical notes
- A status (future: confirmed, cancelled, completed)

The moment a junction carries its own data, it stops being a silent bridge and becomes a real entity. That is why Appointment has its own model instead of being handled automatically.

---

## Lazy vs Eager Loading

When you fetch an Appointment, SQLAlchemy needs to decide: should it also fetch the related Doctor and Patient automatically, or wait until you actually access them?

### The Three Strategies Used

**`lazy="select"` (default)**
Fires a second query only when you access the relationship. Fine for single-object reads. Dangerous in loops — causes the N+1 problem.

**`lazy="joined"`**
Adds a JOIN to the original query. Related data comes back in the same query. Good for many-to-one sides where you almost always need the related object.

**`lazy="selectin"`**
Fires one additional IN (...) query after the original to fetch all related rows at once. The best choice for one-to-many collections, especially in async contexts.

### The N+1 Problem

If you fetch 100 appointments with `lazy="select"` on the doctor relationship and then loop through them accessing `appointment.doctor`, SQLAlchemy fires 1 query for the appointments and then 100 separate queries for each doctor. 101 queries total for what should be one. This is the N+1 problem and it is one of the most common performance mistakes in ORM usage.

---

## Explicit Joins vs `lazy="joined"` — Do Not Use Both

During the seed script, a redundant SQL pattern appeared in the output. SQLAlchemy was joining the doctors and patients tables twice — once from `lazy="joined"` on the relationship, and once from the explicit `.join()` calls in the select statement. The generated SQL looked like this:

```sql
FROM appointments
JOIN doctors ON doctors.id = appointments.doctor_id
JOIN patients ON patients.id = appointments.patient_id
LEFT OUTER JOIN doctors AS doctors_1 ON doctors_1.id = appointments.doctor_id
LEFT OUTER JOIN patients AS patients_1 ON patients_1.id = appointments.patient_id
```

The rule that comes from this:

> Either rely on `lazy="joined"` on the model, or write explicit `.join()` calls in your query. Never both at the same time.

The preferred approach in production is explicit joins — they give you control at the query level rather than a blanket rule baked into every query across the entire codebase.

---

## Two Ways to Execute a Query

```python
# Option 1 — shortcut, cleaner for ORM objects
session.scalars(stmt).all()

# Option 2 — two step, more control over raw results
session.execute(stmt).scalars().all()
```

Use `session.scalars()` when selecting ORM objects. Use `session.execute()` when selecting raw rows, tuples, or specific columns where you need to inspect the result before unwrapping.

---

## The Seed File — What It Is and Why It Exists

A seed file is a plain Python script with one job: insert known, controlled data into the database so there is something to work with during development and testing. It is not a framework feature — you write it yourself.

Every seed file must have:
1. An engine — the connection to the database
2. Table creation — `Base.metadata.create_all(engine)` before inserting anything
3. A session as a context manager — ensures it closes cleanly even on failure
4. Object creation in the right order — foreign key dependencies must exist before the rows that reference them
5. A commit — nothing hits the database until this line
6. A verification query — always read back what you inserted to confirm it actually worked

---

## What `echo=True` on the Engine Does

Setting `echo=True` when creating the engine prints every SQL statement SQLAlchemy generates to the console. This is invaluable during learning and debugging — it shows you exactly what queries are firing, in what order, and lets you spot redundancy or unexpected behaviour like the double join above. Turn it off in production.

---

## Key Decisions Made and Why

| Decision | Reason |
|---|---|
| PostgreSQL over SQLite | Relational constraints, production parity, healthtech data integrity requirements |
| SQLAlchemy 2.x over 1.x | Async compatibility, typed API, modern pattern |
| Appointment as explicit model | It carries its own data — datetime, notes — not just a link |
| `unless-stopped` over `always` | Respects manual stops while surviving crashes and reboots |
| Explicit joins over `lazy="joined"` | Query-level control, no blanket behaviour baked into every query |
| `echo=True` on engine | Visibility into generated SQL during development |
