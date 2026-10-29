# Bright Path: cancellation and the schedule

Bright Path is a tutoring centre that runs on a shared spreadsheet and WhatsApp. Its tutors often learn about a cancellation too late. This small tool fixes one part of that. A receptionist cancels a lesson or marks a no-show. A tutor or the owner then opens the schedule of a day and sees what changed after that schedule became final at 16:00 the day before.

It is one feature, built for a take-home exercise. **It is not ready for production:** it has no login, no booking and no check against double-booking. [DECISIONS.md](DECISIONS.md) explains the choices, the data model and the API.

## Run

You need [uv](https://docs.astral.sh/uv/). The project uses Python 3.13, FastAPI and SQLite.

```sh
uv sync
uv run python -m scripts.seed      # load data/ into bright_path.db (it also resets the database)
uv run uvicorn app.main:app        # http://localhost:8000, API docs at /docs
uv run pytest                      # run the tests
```

| Setting | Default | Meaning |
| --- | --- | --- |
| `BRIGHT_PATH_NOW` | `2026-03-06T07:00:00+07:00` | The current time. The sample data covers one week in March 2026, so the tool does not use the real clock. |
| `BRIGHT_PATH_DB` | `bright_path.db` | The SQLite file. |
| `BRIGHT_PATH_CLOSED_WEEKDAYS` | `["monday"]` | The weekdays when the centre does not teach. Only the cut-off uses it. |

## API

| Endpoint | What it does |
| --- | --- |
| `GET /schedule/{date}` | Returns the lessons of one day, its state (`draft` or `final`), its cut-off, and the changes made after it. Add `?tutor_id=T3` for one tutor. |
| `POST /lessons/{id}/cancel` | Cancels a booked lesson. Body: `cancelled_by` (`family`, `tutor` or `centre`) and an optional `note`. |
| `POST /lessons/{id}/no-show` | Marks a booked lesson as a no-show. It works only from the start of the lesson. |

## Try it

Start the server, then run the commands in order. The lesson IDs come from the sample data. Each cancel or no-show changes the database, so run the seed again to start over.

| Step | Command | What I saw |
| --- | --- | --- |
| 1 | `curl localhost:8000/schedule/2026-03-05` | `final`, with the cut-off `2026-03-04T16:00:00+07:00`. L015 is a `no_show`. L017 is `cancelled`, with the note "tutor sick". |
| 2 | `curl localhost:8000/schedule/2026-03-03` | L005 shows as cancelled after the cut-off. The cut-off of a Tuesday is Sunday 16:00, because Monday is closed. |
| 3 | `curl localhost:8000/schedule/2026-03-04` | The exam pair L009 shows once, with two students. L007 and L008 both show, with no flag. |
| 4 | `curl -X POST localhost:8000/lessons/L018/cancel -H 'content-type: application/json' -d '{"cancelled_by": "family", "note": "family called"}'` | The lesson returns as `cancelled`, with a `change` and `late: true` (2 hours of notice). `GET /schedule/2026-03-06` shows the change. |
| 5 | The same command again | `409 not_booked` |
| 6 | `curl -X POST localhost:8000/lessons/L019/no-show` | `409 lesson_not_started` |
| 7 | Restart with `BRIGHT_PATH_NOW=2026-03-06T10:00:00+07:00`, then repeat step 6 | `200`. The lesson is `no_show`. |

## What the sample data showed

The export is one week from the centre's spreadsheet. It has 34 rows. They load as 33 lessons, 6 students and 3 changes: an exam pair of two rows becomes one lesson with two students, and the cancellations and the no-show become changes.

The week breaks some of the centre's own rules. The tool loads it as it is and does not flag any of this:

- A student booked with two tutors at the same time.
- A tutor in two rooms at the same time.
- A tutor with 7 lessons on one day. The limit is 6.
- A lesson on a Monday, when the centre is closed.

## Layout

```text
app/
├── core/        settings, database, dependencies, one error format
├── tutors/      Tutor
├── rooms/       Room
├── students/    Student
├── lessons/     Lesson, LessonStudent, LessonChange, cancel and no-show
└── schedule/    the schedule of a day: cut-off, state, changes
scripts/seed.py  loads data/ into the database
tests/
```

A router checks the input and calls a service. A service holds the rules and does not import FastAPI.
