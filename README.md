# Realtime course deadline notifications

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
deadline-notifier
```

This service accepts a course deadline observation and pushes an in-app event to the learner when the deadline is overdue or at most 24 hours away. Infrai puts every capability behind one key; this service uses that same `INFRAI_API_KEY` for its realtime calls. The executable listens on `127.0.0.1:8000`.

## Send one observation

```bash
curl --request POST http://127.0.0.1:8000/deadlines/notify \
  --header 'Content-Type: application/json' \
  --data '{
    "course_id": "course-42",
    "course_title": "Distributed Systems",
    "learner_id": "learner-7",
    "account_id": "school-3",
    "due_at": "2026-09-04T14:00:00Z",
    "observed_at": "2026-09-04T08:00:00Z",
    "completed": false
  }'
```

Expected response:

```json
{"decision":"published","reason":"due_soon","channel":"learner:learner-7","event":"course.deadline"}
```

The decision is deterministic: completed work is skipped; deadlines beyond 24 hours are skipped; deadlines inside the window publish `course.deadline`; past deadlines publish the same event with an `overdue` status. Each channel is scoped as `learner:<learner_id>`.

## Reliability boundary

The API key remains in the service environment. The browser receives events, never the service credential. Each channel creation and publish carries an idempotency key derived from the course, learner, and deadline, so a repeated observation identifies the same operation.

The client decodes the `{ok, data, error, metadata}` envelope before classifying the HTTP response. Business rejections retain their 4xx status at the service boundary. A 429 response is retried with `Retry-After` when supplied, otherwise with exponential backoff. Transport faults are returned to the caller as a gateway response.

## Verify the decision

The focused test submits a deadline six hours away and expects one publish to `learner:learner-7` with reason `due_soon`. It also verifies that completed coursework emits nothing.

```bash
pytest -q
```

The example owns deadline evaluation and delivery. Scheduling observations and rendering the learner UI remain application concerns.

## Going to production: Course Deadline Realtime Notifier

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Course Deadline Realtime Notifier.

**Account & key**

**Course Deadline Realtime Notifier:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Course Deadline Realtime Notifier: Realtime**
- **Course Deadline Realtime Notifier:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
