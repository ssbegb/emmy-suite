# Emmy Suite

**A suite of tools to help leaders do the right thing.**

Emmy Suite helps leaders make sound, ethical, well-reasoned decisions and follow through on them. It's for people who manage teams, run organizations, or carry responsibility for others.

## Vision

Doing the right thing as a leader is rarely about knowing *what* is right in the abstract. It's about having the clarity, structure, and support to act on it under pressure. Emmy Suite provides that support.

## Planned components

> Early-stage. These are starting ideas, not commitments.

- **Decision compass**: frameworks for working through hard decisions, weighing stakeholders, values, and consequences.
- **Reflection journal**: guided prompts to review decisions and learn from outcomes.
- **Team pulse**: lightweight ways to hear from the people affected by leadership choices.
- **Commitments tracker**: keep promises visible and follow through on them.

## Status

🚧 Early development. The portal works: organizations and companies, users and invitations, roles, the org chart and switching modules on and off. **Decisions** is the first module.

## How it's built

- **Python + Django 5.2** with server-rendered pages; **PostgreSQL 16**.
- **Portal + modules.** The portal (`emmy/`) holds the shared basics: companies, users, roles, departments and people. Each module (`modules/`) is a Django app that declares an `emmy_module` in its `AppConfig` and is switched on per company in *Settings › Modules*.
- **Multi-company.** A *tenant* is one customer organization and is completely sealed off from the others. A tenant can have several companies; users only reach the companies they're a member of.
- **Isolation in the database.** The app connects as a limited PostgreSQL role, and row-level security policies only expose the current tenant's rows. A bug in a query can't leak another customer's data. The tests run as that same role.
- **Sign-in** with django-allauth: email and password, plus Google and Microsoft when configured (both are free). People join a company by invitation from an administrator.

## Running it locally

Requirements: Ubuntu (or similar) with Python 3.12 and PostgreSQL 16.

```bash
sudo apt install -y python3-venv postgresql
sudo -u postgres createuser -s $USER && createdb emmy_suite

# Limited role the app connects as (pick your own password)
psql -d emmy_suite -c "CREATE ROLE emmy_app LOGIN PASSWORD 'change-me' NOBYPASSRLS"

python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env            # then set SECRET_KEY and DB_APP_PASSWORD
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

Open http://localhost:8000, create an account and set up your organization. In development, emails (such as invitations) are printed in the terminal running the server.

Run the tests with `.venv/bin/python manage.py test`.

### Google and Microsoft sign-in (optional)

1. **Google:** in Google Cloud Console, create an OAuth client (type *Web application*) with the redirect URI `http://localhost:8000/accounts/google/login/callback/`.
2. **Microsoft:** in Microsoft Entra, register an app for *any organizational directory and personal accounts* with the redirect URI `http://localhost:8000/accounts/microsoft/login/callback/`.
3. Put the client IDs and secrets in `.env` and restart the server. The sign-in buttons appear automatically.

## Contributing

Open an issue to suggest a feature, share a leadership scenario the suite should support, or report a problem.

## License

Emmy Suite is licensed under the [GNU Affero General Public License v3.0](LICENSE). Anyone who runs a modified version as a service must share their changes.
