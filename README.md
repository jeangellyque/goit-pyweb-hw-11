# Contacts API

A FastAPI REST API that stores contacts in PostgreSQL. Interactive API documentation
is available at `/docs`.

## Setup and run

Requires Python 3.10+ and Docker Compose with PostgreSQL 16.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose up -d db
uvicorn app.main:app --reload
```

The API reads `DATABASE_URL` from the environment or the local `.env` file.
The example file configures both the Compose database and API connection;
replace its sample password before using it beyond local development.
PostgreSQL is exposed on host port `5432` by default; set `POSTGRES_PORT` in
`.env` to use another available host port, and update the port in `DATABASE_URL`
to match.
Tables are created automatically when the application starts.
Open <http://127.0.0.1:8000/docs> for interactive Swagger documentation or
<http://127.0.0.1:8000/redoc> for ReDoc.

## Endpoints

- `POST /contacts` — create a contact (returns `201`).
- `GET /contacts` — list contacts. Optional `search` searches first name, last
  name, and email; `first_name`, `last_name`, and `email` can also filter
  individually.
- `GET /contacts/birthdays` — list contacts whose birthday falls today or in the
  next six days, including across the end of the year.
- `GET /contacts/{contact_id}` — retrieve a contact.
- `PUT /contacts/{contact_id}` or `PATCH /contacts/{contact_id}` — update a
  contact; both accept partial fields.
- `DELETE /contacts/{contact_id}` — delete a contact (returns `204`).

Contact fields are `first_name`, `last_name`, `email`, `phone`, `birthday`
(ISO `YYYY-MM-DD`), and optional `extra_data`. Email addresses must be valid and
unique. Invalid input returns `422`, missing contacts return `404`, and duplicate
emails return `409`.

## Example requests

Create a contact:

```bash
curl -X POST http://127.0.0.1:8000/contacts \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Ada","last_name":"Lovelace","email":"ada@example.com","phone":"+441234567890","birthday":"1815-12-10","extra_data":"Mathematician"}'
```

List contacts, search all name/email fields, get upcoming birthdays, update one
field, and delete a contact:

```bash
curl http://127.0.0.1:8000/contacts
curl 'http://127.0.0.1:8000/contacts?search=ada'
curl http://127.0.0.1:8000/contacts/birthdays
curl -X PATCH http://127.0.0.1:8000/contacts/1 \
  -H 'Content-Type: application/json' \
  -d '{"phone":"+441234567891"}'
curl -X DELETE http://127.0.0.1:8000/contacts/1
```

## Run tests

```bash
python -m unittest discover -s tests -v
```
