# Decisions

## 1. Reading the situation

### What hurts

- **Changes don't reach tutors in time.** The tutor drove in twice for called-off lessons. Mai fixes the sheet the next morning. L017 was cancelled 80 minutes before start. L032 says "moved from Sunday", but no Sunday row for that student exists: the move overwrote the original.
- **Double-booking.** L007/L008: one student, two tutors, same slot. L033/L034: one tutor, two rooms, same slot.
- **No "today" view.** The owner wants to open the laptop and see today.
- **Rules live in Mai's head.** She leaves in 8 weeks.

Mentioned but not hurting: scale (the export has 3 tutors, 6 students, 34 lessons), pricing, WhatsApp integration, waitlist, tutor pay.

### Where the brief contradicts itself

- Owner: "if the system allows it, the system is broken". Mai double-books exam pairs on purpose. I read this as a group lesson, not a collision (L009/L010).
- Owner wants the 6-lesson cap enforced. Mai breaks it when desperate. T1 has 7 on Fri 03-06.
- A late cancellation is charged in full and the tutor is paid, yet it frees the slot.
- Tomorrow is final at 16:00 the day before, but Mai messages tutors at 07:00 on the day. Which one is "told"?
- Monday is closed, yet L032 is on a Monday.
- The brief has 12 tutors and 6 rooms, so rooms should be scarce. The export has 3 tutors, one room each, so it cannot show room conflicts.
- The rules table has no rule for a student in two places, but it is the owner's first example.

### Questions for the owner

| # | Question | If the answer is... |
| --- | --- | --- |
| 1 | Is an exam pair one lesson with two students? Who may set it up? | Yes: lesson capacity + participants. No: an override on a normal collision. |
| 2 | Tutor cap of 6: block, or warn with a recorded reason? | Block: constraint in the database. Warn: override record shown on the owner's view. |
| 3 | What counts as "told": the 16:00 publication or Mai's 07:00 message? | Sets the point after which an edit is stored as a visible change. |
| 4 | Who can cancel: family, tutor, the centre (storm, room closed)? Does a late cancellation free the slot? | Adds `cancelled_by` and a note. Only a family cancellation inside 4 hours is charged. |
| 5 | What are the exact lesson hours? Is Monday closed without exception? | Hours are config. Monday: yes means block, no means warn. |

I send 1 to 4 first. The rest use the assumptions below.

### Assumptions

- The receptionist reads and edits. The owner and tutors read only. The tool does not send WhatsApp messages.
- Lessons start at 09:00 or later, end by 21:30, last 60 or 90 minutes, and never run on Monday.
- A student can learn any subject with any tutor.
- A lesson has a capacity: 1 for a normal lesson, 2 for an exam pair, more later. Students are participants.
- Hard rules: a student, a tutor or a room is never in two overlapping active lessons.
- Warnings, saved with a reason: more than 6 lessons for a tutor in a day, and a lesson on a Monday.
- A cancelled lesson occupies nothing and does not count toward the cap. A no-show still does. A lesson can be marked no-show only after its start. Charging is out of scope.
- A pair counts as 1 lesson toward the cap.
- A cancellation records who cancelled (family, tutor or centre) and a note. A family cancellation 4 hours or less before the start is late. Times are Asia/Ho_Chi_Minh.
- A day's schedule is final at 16:00 on the previous open day. Tuesday's is final on Sunday at 16:00.
- A student is identified by name.
- "Today" is pinned to 2026-03-06, the busiest day in the export.
- The seed has 2 real conflicts (L007/L008, L033/L034). They load flagged as `needs_review`, not resolved: Mai decides, not the owner.
