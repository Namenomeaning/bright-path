# Decisions

## 1. Reading the situation

### What hurts

- **Changes reach tutors too late.** The tutor drove in twice for lessons that were already called off. Mai fixes the sheet the next morning. L017 was cancelled 80 minutes before it started. L032 says "moved from Sunday", but no Sunday row exists for that student. The move overwrote the original.
- **Double-booking.** L007 and L008 put one student with two tutors in the same slot. L033 and L034 put one tutor in two rooms in the same slot.
- **No "today" view.** The owner wants to open the laptop and see today.
- **The rules are in Mai's head.** She leaves in 8 weeks.

Mentioned, but not a pain: scale (the export has 3 tutors and 34 lessons), pricing, WhatsApp, a waitlist and tutor pay.

### Where the brief contradicts itself

- The owner says "if the system allows it, the system is broken". Mai double-books exam pairs on purpose. I read a pair as one group lesson, not a collision (L009, L010).
- The owner wants the cap of 6 lessons enforced. Mai breaks it when she is desperate. T1 has 7 lessons on Fri 03-06.
- A late cancellation is charged in full and the tutor is paid. It also frees the slot.
- The schedule is final at 16:00 the day before, but Mai messages tutors at 07:00 on the day. Which one means "told"?
- The centre is closed on Monday, but L032 is on a Monday.
- The centre has 12 tutors and 6 rooms, so rooms should be scarce. The export has 3 tutors with one room each, so it cannot show a room conflict.
- The rules table has no rule for a student in two places. This is the owner's first example.

### Questions for the owner

| # | Question | Effect of the answer |
| --- | --- | --- |
| 1 | Is an exam pair one lesson with two students? Who may set it up? | Yes: lesson capacity and participants. No: an override on a normal collision. |
| 2 | Is the cap of 6 a block, or a warning with a recorded reason? | Block: a database constraint. Warning: an override record on the owner's view. |
| 3 | What does "told" mean: the 16:00 publication or Mai's 07:00 message? | Sets the point after which an edit shows as a change. |
| 4 | Who can cancel: the family, the tutor or the centre (storm, room closed)? Does a late cancellation free the slot? Is a family report after the start a late cancellation or a no-show? | Adds `cancelled_by` and a note. Only a family cancellation with less than 4 hours of notice is charged. Sets which endpoint Mai uses after the start. |
| 5 | What are the exact lesson hours? Which days is the centre closed, and does that change? Is a closed day closed without exception? | Hours and closed days are settings. Yes: a lesson on a closed day is a block. No: it is a warning. |

I send questions 1 to 4 first. Until the owner answers, I use the assumptions below.

### Assumptions

- The receptionist reads and edits. The owner and tutors only read. The tool does not send WhatsApp messages.
- Lessons start at 09:00 or later, end by 21:30 and last 60 or 90 minutes. The centre is closed on Monday. `closed_weekdays` is a setting: a list of weekday names, for example `["monday", "sunday"]`. It can change and can hold more than one.
- A student can learn any subject with any tutor.
- A lesson has a capacity: 1 for a normal lesson, 2 for an exam pair, more later. Students are participants.
- Rule, not enforced in this build: a student, a tutor or a room is never in two overlapping active lessons.
- Warnings, saved with a reason: more than 6 lessons for a tutor in a day, and a lesson on a closed day.
- A cancelled lesson occupies nothing and does not count toward the cap. A no-show does both. Mai can mark a no-show only after the start. Charging is out of scope.
- A pair counts as 1 lesson toward the cap.
- A cancellation records who cancelled (family, tutor or centre) and a note. A family cancellation with less than 4 hours of notice is late. Exactly 4 hours of notice is still free, because the brief says "free of charge up to 4 hours before". A cancellation after the start has negative notice, so it is late. Times are Asia/Ho_Chi_Minh.
- A day's schedule is final at 16:00 on the previous open day. Tuesday's schedule is final on Sunday at 16:00.
- The tool identifies a student by name.
- "Today" is 2026-03-06, the busiest day in the export.
- The seed has 2 real conflicts (L007 with L008, and L033 with L034). They load as they are, unresolved. The README reports them. Mai decides, not the owner.

## 2. What to build

### Features this tool needs

1. Schedule: the lessons of one day, by tutor and room.
2. Cancellation: cancel a lesson or mark a no-show, with who and why.
3. Move: change the day or time of a lesson and keep the original.
4. Conflict checks: reject a student, tutor or room in two places.
5. Tutor cap warning: more than 6 lessons in a day, saved with a reason.
6. Waitlist: tell the next family when a slot opens.

### Pick: cancellation and the schedule

The schedule shows a cancellation as a change when it happens after the 16:00 cut-off. It also shows a no-show. The tutor and the owner see what changed without a message.

A cancellation before the cut-off is stored, but the schedule does not mark it. The tutor never saw that lesson, so it just leaves the day. The schedule compares the time of the cancellation with the cut-off and stores nothing extra.

Anyone can view any day at any time. A day is "draft" before its cut-off and "final" after it.

Why this first: it reaches all three roles.

- The schedule serves everyone. The owner wants to "see today, not scroll". The tutor wants one reliable message for the day. Mai builds that day by hand every morning.
- Cancellation is the shared pain of the tutor and Mai. The tutor drove in twice for called-off lessons. Mai fixes the sheet the next morning. L017 was cancelled 80 minutes before the start, after the cut-off.
- Mai's cancellation rules (late, no-show, who cancelled) live in her head. The tool writes them down.

Why the rest wait:

- Move is the same change record with a different kind. The schema holds it. There is no endpoint.
- Conflict checks: not built. The tool cannot create a lesson, so it cannot create a conflict. The seed has two.
- Cap warning: one day in the export breaks it (T1 on 03-06).
- Waitlist: the export has no data on waiting families.
- Not built: messages, new bookings, charging, login.

The cost of this choice: nobody can book or move a lesson in the tool. The seed is the only source of lessons.

## 3. Design

SQLite, FastAPI, Python and uv. Dates are `YYYY-MM-DD`. Times are `HH:MM` local time (Asia/Ho_Chi_Minh). A timestamp is ISO 8601 with the `+07:00` offset.

### Database

```text
tutor 1 --- * lesson * --- 1 room
                |
                +--- * lesson_student * --- 1 student
                |
                +--- * lesson_change
```

**`tutor`** stores the details of a tutor.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | TEXT | Primary key, for example `T1`. |
| `name`, `subject`, `phone` | TEXT | Not null. |

**`room`** stores the rooms a lesson can use. The seed adds R1 to R6.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | TEXT | Primary key, for example `R1`. |
| `name` | TEXT | Not null. |

**`student`** stores the details of a student. The tool identifies a student by name.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | INTEGER | Primary key. |
| `name` | TEXT | Not null, unique. |

**`lesson`** is one lesson in one slot. It holds the current state only.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | TEXT | Primary key. The export `lesson_id`, for example `L001`. |
| `date` | DATE | Not null. |
| `start_time` | TIME | Not null. |
| `duration_min` | INTEGER | Not null. 60 or 90. |
| `tutor_id` | TEXT | Not null. References `tutor`. |
| `room_id` | TEXT | Not null. References `room`. |
| `capacity` | INTEGER | Not null, 1 or more. Default 1. |
| `status` | TEXT | `booked` (default), `cancelled` or `no_show`. |
| `note` | TEXT | The export note of a row that is not cancelled. |

A `booked` or `no_show` lesson occupies its room and slot. A `cancelled` lesson occupies nothing.

**`lesson_student`** lists the students in a lesson. An exam pair is one lesson with two rows.

| Column | Type | Notes |
| --- | --- | --- |
| `lesson_id` | TEXT | References `lesson`. |
| `student_id` | INTEGER | References `student`. |

The primary key is `(lesson_id, student_id)`.

**`lesson_change`** is an append-only log. The code never updates or deletes a row.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | INTEGER | Primary key. |
| `lesson_id` | TEXT | Not null. References `lesson`. |
| `kind` | TEXT | `cancelled`, `no_show` or `moved`. |
| `changed_at` | DATETIME | Not null. Stored as local time and read back with the `+07:00` offset. |
| `cancelled_by` | TEXT | `family`, `tutor` or `centre`. Only when `kind` is `cancelled`. |
| `note` | TEXT | Free text. |
| `old_values` | JSON | The old day, time, tutor and room of a move. |

The API requires `cancelled_by`. The seed leaves it empty, because the export has no such column, and the tool does not infer it from the note. A lesson has at most one `cancelled` or `no_show` row.

### How a change is stored

The `lesson` row holds the current state. The `lesson_change` row holds what happened and when. A move saves the old values in its change row, so the original survives. L032 lost its original.

The schedule decides what "after the tutor was told" means. It compares `changed_at` with the cut-off of the lesson's day. The database stores no flag for it.

### Where each rule lives

| Rule | Where | Why |
| --- | --- | --- |
| Duration is 60 or 90. Status, kind and `cancelled_by` have fixed values. `cancelled_by` only on a cancellation. At most one cancellation or no-show for each lesson. A lesson has a real tutor and room. | Database | These checks are cheap. Nobody overrides them. |
| Draft or final. After the cut-off. Late cancellation. | Code, derived | A stored value goes stale. |
| No overlap for a student, tutor or room. More than 6 lessons for a tutor in a day. A lesson on a closed day. Lesson hours. Students within capacity. | Not built | The tool cannot create or move a lesson. Mai can override some of them, and question 5 is open. |

When booking comes, the overlap rule goes in the database first, because the API and the seed both write.

### API

The tool reads the current time from `BRIGHT_PATH_NOW`. The default is `2026-03-06T07:00:00+07:00`.

An error returns `{"error": {"code": "...", "message": "..."}}`. Besides the codes below, an unknown path returns `not_found`, any other HTTP error returns `http_error`, and an unexpected failure returns `internal_error` with status 500.

`BRIGHT_PATH_DB` is the SQLite file. The default is `bright_path.db`.

Derived values:

- **Cut-off of a day:** 16:00 on the previous open day. Skip each closed day. The cut-off of Tuesday is Sunday 16:00 while Monday is the only closed day.
- **State of a day:** `final` at or after the cut-off. Otherwise `draft`.
- **After the cut-off:** `changed_at` is later than the cut-off of the lesson's day.
- **Late:** a family cancellation with less than 4 hours of notice. Exactly 4 hours is not late. It is `null` for any other change.

#### `GET /schedule/{date}`

Returns the schedule of one day. Any day can be requested at any time. The optional `tutor_id` parameter limits the result to one tutor.

The list has every `booked` and `no_show` lesson. It also has every `cancelled` lesson whose cancellation came after the cut-off. A lesson cancelled before the cut-off is left out, because the tutor never saw it. Lessons are sorted by `start_time`.

```json
{
  "date": "2026-03-05",
  "state": "final",
  "cutoff": "2026-03-04T16:00:00+07:00",
  "lessons": [
    {
      "id": "L017",
      "start_time": "16:00",
      "end_time": "17:00",
      "tutor": {"id": "T3", "name": "Le Thu"},
      "room": "R3",
      "students": [{"id": 4, "name": "Do Van Kien"}],
      "status": "cancelled",
      "change": {
        "kind": "cancelled",
        "changed_at": "2026-03-05T14:40:00+07:00",
        "cancelled_by": null,
        "note": "tutor sick",
        "late": null
      }
    }
  ]
}
```

A person is an object with `id` and `name`. A room is its `id` string. `change` is `null` when the lesson has no cancellation or no-show. Errors: `404 tutor_not_found`, `422 invalid_request`.

#### `POST /lessons/{id}/cancel`

Cancels a `booked` lesson at any time.

```json
{"cancelled_by": "family", "note": "family called"}
```

`cancelled_by` is required. `note` is optional. In one transaction the server sets the status to `cancelled` and adds a change row with the current time. It returns the lesson, in the same shape as above.

Errors: `404 lesson_not_found`, `409 not_booked`, `422 invalid_request`.

#### `POST /lessons/{id}/no-show`

Marks a `booked` lesson as a no-show. There is no body. In one transaction the server sets the status to `no_show` and adds a change row with the current time. It returns the lesson.

Errors: `404 lesson_not_found`, `409 not_booked`, `409 lesson_not_started` (the lesson has not started).

Cancel and no-show are two endpoints because their rules differ. A cancellation can come at any time, needs `cancelled_by` and frees the room and slot. A no-show comes only after the start, has no `cancelled_by` and frees nothing.

**Rejected: `DELETE /lessons/{id}`.** A delete erases what the tutor was told. This is how L032 lost its original row. A lesson is cancelled, never deleted.

### Seed

The seed reads `data/tutors.csv` and `data/lessons_export.csv`. It numbers students in order of first appearance. Running it again resets the database.

- 34 export rows give 33 lessons. L009 and L010 become one lesson `L009` with capacity 2 and two students.
- A cancelled row becomes a `cancelled` change row. `changed_at` is the export `cancelled_at`, `note` is the export note, and `cancelled_by` stays empty.
- The export has no time for the no-show row (L015). Its change row uses the start time of the lesson, the earliest moment Mai can mark a no-show.
- Any other export note stays in `lesson.note`.
- The 2 real conflicts (L007 with L008, L033 with L034) and L032 (Monday) load as they are. The tool does not detect or flag them.

### What a reviewer sees

The README holds the commands. With the default clock (2026-03-06 at 07:00), a reviewer can check the feature in six steps.

| Step | Result |
| --- | --- |
| `GET /schedule/2026-03-05` | The day is `final`. L015 shows as a no-show and L017 as cancelled after the cut-off, with the note "tutor sick". |
| `GET /schedule/2026-03-03` | L005 shows as cancelled after the cut-off. The cut-off of Tuesday is Sunday 16:00, because Monday is closed. |
| `GET /schedule/2026-03-04` | The exam pair shows once, with two students. L007 and L008 both appear, with no flag. |
| `POST /lessons/L018/cancel` with `cancelled_by` | The lesson returns with a `change`. `GET /schedule/2026-03-06` shows it as a change. |
| `POST /lessons/L018/cancel` again | `409 not_booked`. |
| `POST /lessons/L019/no-show` | `409 lesson_not_started`, because the lesson starts at 09:00. With `BRIGHT_PATH_NOW` set to 10:00 it succeeds. |

## 4. Reflection

### What I would build next

1. Booking and moving a lesson. The overlap rule goes in the database first (a student, a tutor or a room never in two lessons), with a list of the 2 conflicts in the seed for Mai to resolve.
2. A `received_at` time on cancel. Today `changed_at` is the time Mai types the cancellation. A family that calls at night is entered the next morning, so the tool can call a cancellation late when it was not.
3. Login with roles. Only the receptionist writes.
4. The warnings that are not built: more than 6 lessons for a tutor in a day, and a lesson on a closed day, each saved with a reason.
5. A record that the tutor saw a change. The tool shows the change, but nobody knows if the tutor read it. This is the tutor's real pain.
6. The owner's answers to questions 1 to 5.

### What I know is weak

- There is no login. Anyone who reaches the API can cancel a lesson. The assumption that the owner and the tutors only read is not enforced.
- `changed_at` is the entry time, not the time the family called. See next step 2.
- "Told" means the 16:00 cut-off. Question 3 has no answer, so the marker may not match what tutors saw in Mai's 07:00 messages.
- Four readings are mine: a late cancellation is less than 4 hours of notice, the cut-off of Tuesday is Sunday 16:00, an exam pair is two rows with the same tutor, room and start, and a no-show in the seed happened at the lesson start.
- A student is identified by name. Two students with the same name would merge.
- After the start, a family report can be a late cancellation or a no-show. The tool accepts both and has no rule. Question 4 asks the owner.
- The tests check my reading of the rules, not the owner's. I checked the steps in the README by hand against the running server.
- A cancelled lesson with no change row leaves the schedule. The seed and the API cannot create one.
- One SQLite file and one clock setting for all requests.

### Where the AI assistant helped

- It read the PDF and checked the export with a script against every rule. This found L007 with L008, L033 with L034, the 7 lessons of T1 on 03-06, L032 on a Monday, and the notice of L005 and L017.
- It drafted this file, the first schema and API, the FastAPI structure from the blog, and the tests.
- I chose the scope (cancellation and the schedule), the closed weekdays as a list, the name `schedule`, and the cuts: overlap enforcement and the status `needs_review`.
- The assistant added things I had not asked for, and I had to catch them. I dropped `needs_review`. I kept the `lesson.note` column and the rule of one cancellation or no-show for each lesson, because both protect real data.

### A suggestion I threw away

The assistant proposed to fill `cancelled_by` in the seed from the export note: "tutor sick" gives `tutor`, any other cancellation gives `family`. I said no.

I was right because `cancelled_by` decides who pays. A family cancellation with less than 4 hours of notice is charged. A guess from free text would look like a real record in that field, and nobody could tell the two apart. The field stays empty on seed rows, and the note stays in the change row where a person can read it. The cost is that `late` is `null` for every seed row.
