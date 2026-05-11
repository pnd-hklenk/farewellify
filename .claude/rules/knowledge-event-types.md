# Knowledge: Event Types (Farewell vs. 5-Year Anniversary)

> Persistent project knowledge. Loaded automatically by PandaOS via `.claude/rules/`.
> Do not delete without reading the "Decisions" section below first.

This codebase serves **two event types** from one data model and one Flask app:

| Mode | Trigger | Purpose |
|------|---------|---------|
| `farewell` | Someone is leaving Pandata | Collect farewell card |
| `anniversary` | Someone celebrates 5 years at Pandata | Collect 5-year anniversary book |

The mode is stored on each event row in `farewell_events.event_type` (Postgres `text`, `CHECK IN ('farewell','anniversary')`, default `'farewell'`).

---

## "Where do I touch X?" index

### Backend copy (emails, Miro, ZIP)
- **Single source of truth:** `MODE_COPY` dict at the top of `app.py` (after `allowed_file`).
- Helpers: `get_event_mode(event_data)`, `get_copy(mode)` — both defensive, both fall back to `'farewell'`.
- Anywhere a user-facing string varies by mode, fetch it from `MODE_COPY`. Do **not** add new hardcoded farewell-specific strings to email/Miro/ZIP code.

### API surface
- `POST /api/events` — accepts `eventType` (camelCase) in JSON body. Defaults to `'farewell'`. Invalid values are coerced to `'farewell'`.
- `GET /api/events/<event_id>` — returns `event_type` (snake_case, raw from Supabase). Used by submit page.
- `GET /api/admin/<code>` — returns `eventType` (camelCase, normalised via `get_event_mode`). Used by admin page.
- All other endpoints derive mode from the loaded event row when needed.

### Templates
- **`index.html`** — radio toggle is the source of truth before creation. `MODE_UI` JS dict + `applyModeUI()` swap tagline, honoree question, submit-button label, success-modal copy, and the auto-generated message template.
- **`submit.html`** — `LABELS` JS dict + branch on `event.event_type` (snake_case from API). Swaps page heading, greeting subline, step-1 label, message placeholder, document title.
- **`admin.html`** — branch on `data.event.eventType` (camelCase from API). Swaps header label and document title.

### Google Drive
- `gmail_auth.py` → `create_farewell_folder(first_name, event_date, event_type='farewell')`.
- Folder names: `YYMM FirstName` (farewell) or `YYMM 5Y FirstName` (anniversary).
- Same parent folder for both (`FAREWELL_CARDS_FOLDER_ID`). See "Open questions" below.

### Honoree deactivation rule (CRITICAL)
- `POST /api/events`: when `event_type == 'farewell'`, the honoree's `employees.is_active` is flipped to `false`.
- For `event_type == 'anniversary'`, the honoree **stays active** — they're not leaving.
- Do not collapse this check; it's the most important behavioural difference between the two modes.

---

## Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | One `farewell_events` table for both modes (not a second table) | Identical schema; a `event_type` discriminator keeps queries simple and avoids migration churn. |
| 2 | Kept the table name `farewell_events` despite the broader scope | Renaming breaks every query, RLS policy, and migration. Not worth it. |
| 3 | Default `event_type = 'farewell'` on existing rows | Backwards compatible — existing events behave identically to before. |
| 4 | `MODE_COPY` lives in `app.py` (Python), `MODE_UI` / `LABELS` mirrored in template JS | Avoids a round-trip to fetch labels; the dicts are small. Trade-off: copy must be kept in sync if changed (search for the string in both places). |
| 5 | Honoree auto-deactivation only on farewells | Anniversary honoree stays employed; deactivating would remove them from future events and notifications. |
| 6 | `eventType` is validated against `MODE_COPY` keys at the API boundary and coerced to `'farewell'` if invalid | Defensive — protects against malformed clients. The DB `CHECK` constraint is a second line of defence. |
| 7 | Same Google Drive parent for both modes; folders distinguished by `5Y` prefix | No env var for a separate anniversary parent yet. Single parent + visible marker is the minimum viable change. |
| 8 | `deadline` column reused: last day (farewell) or anniversary date (anniversary) | Renaming would be breaking. The semantic shift is documented in `docs/DATABASE.md`. |
| 9 | Email date format `Thursday, 29.01.` is mode-agnostic (no year) | Consistent with prior behaviour. If anniversary-specific year display is wanted later, add it via `MODE_COPY` (e.g. extend the `invite_intro` template to accept a `year` field). |

---

## Open questions / future improvements

- **Separate Drive parent folder for anniversaries.** Add an `ANNIVERSARY_BOOKS_FOLDER_ID` env var and branch in `create_farewell_folder` if/when wanted.
- **Year in anniversary email date.** Could extend `MODE_COPY` to include a `{year}` placeholder for anniversaries only.
- **More event types.** The dict-based design scales — just add another key to `MODE_COPY` / `MODE_UI` / `LABELS` and update the DB `CHECK` constraint via a migration. The radio toggle in `index.html` would need a third option.

---

## Things NOT to do

- ❌ Don't add a new hardcoded farewell-specific string anywhere in app.py / templates without putting it into `MODE_COPY` (or `MODE_UI` / `LABELS` on the frontend).
- ❌ Don't remove the `event_type == 'farewell'` guard on honoree deactivation. Doing so will silently break anniversary events (the honoree will be deactivated and dropped from future invites).
- ❌ Don't rename the `farewell_events` table casually — it ripples through every query.
- ❌ Don't fetch labels via a new API endpoint. The mirrored dicts are intentional.

---

## Schema migration history

- `add_event_type_to_farewell_events` (2026-05-11) — added `event_type text NOT NULL DEFAULT 'farewell'` with `CHECK (event_type IN ('farewell','anniversary'))`.
