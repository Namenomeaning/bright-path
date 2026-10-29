# Bright Path: cancellation and the schedule

An internal tool for a tutoring centre in Da Nang. It does one thing: record a cancellation or a no-show, and show the schedule of a day so that a tutor sees what changed after the 16:00 cut-off.

[DECISIONS.md](DECISIONS.md) holds the reading of the brief, the choice of this feature, and the database and API design.

## Run

You need [uv](https://docs.astral.sh/uv/). The project uses Python 3.13, FastAPI and SQLite.

```sh
uv sync
uv run python -m scripts.seed          # load data/ into bright_path.db
uv run uvicorn app.main:app            # http://localhost:8000, API docs at /docs
uv run pytest                          # run the tests
```

Cancel and no-show change the database. Run the seed again to reset it.

| Setting | Default | Meaning |
| --- | --- | --- |
| `BRIGHT_PATH_NOW` | `2026-03-06T07:00:00+07:00` | The current time. The seed covers one week, so the tool does not use the real clock. |
| `BRIGHT_PATH_DB` | `bright_path.db` | The SQLite file. |
| `BRIGHT_PATH_CLOSED_WEEKDAYS` | `["monday"]` | Weekdays when the centre does not teach. Only the cut-off reads it. |

## Try it

Start the server with the default time, then run each command.

| Step | Command | What I saw |
| --- | --- | --- |
| 1 | `curl localhost:8000/schedule/2026-03-05` | `final`, cut-off `2026-03-04T16:00:00+07:00`. L015 is marked `no_show`. L017 is `cancelled`, note "tutor sick". |
| 2 | `curl localhost:8000/schedule/2026-03-03` | L005 shows as cancelled after the cut-off. The cut-off of Tuesday is Sunday 16:00, because Monday is closed. |
| 3 | `curl localhost:8000/schedule/2026-03-04` | The exam pair L009 shows once with two students. L007 and L008 both show, with no flag. |
| 4 | `curl -X POST localhost:8000/lessons/L018/cancel -H 'content-type: application/json' -d '{"cancelled_by": "family", "note": "family called"}'` | The lesson returns `cancelled` with a `change` and `late: true` (the cancellation is 2 hours before the start). `GET /schedule/2026-03-06` shows it as a change. |
| 5 | The same command again | `409 not_booked` |
| 6 | `curl -X POST localhost:8000/lessons/L019/no-show` | `409 lesson_not_started` |
| 7 | Restart with `BRIGHT_PATH_NOW=2026-03-06T10:00:00+07:00`, then repeat step 6 | `200`, the lesson is `no_show`. |

`GET /schedule/{date}?tutor_id=T3` limits the schedule to one tutor.

## What the seed showed

The export has 34 rows. They load as 33 lessons, 6 students and 3 changes. The centre ran some weeks outside its own rules, and the tool loads those rows as they are:

- L007 and L008 put one student with two tutors at 09:00 on 2026-03-04.
- L033 and L034 put one tutor in two rooms at 09:00 on 2026-03-10.
- L009 and L010 are an exam pair. The seed merges them into one lesson with two students.
- T1 has 7 lessons on 2026-03-06. The brief caps a tutor at 6.
- L032 is on a Monday, when the centre is closed.

The tool does not detect or flag any of these. See "Not built" in [DECISIONS.md](DECISIONS.md).

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
