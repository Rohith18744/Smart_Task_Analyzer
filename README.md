# Smart Task Analyzer

Mini-application for scoring and prioritizing work based on urgency, importance, effort, and dependencies. Built with Django REST Framework and a vanilla HTML/JS frontend.

## Quick Start

1. **Install dependencies**
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Run migrations & start the API**
   ```powershell
   cd backend
   ..\venv\Scripts\python.exe manage.py migrate
   ..\venv\Scripts\python.exe manage.py runserver
   ```
3. **Open the frontend** at `http://127.0.0.1:8000/`.
4. **Execute tests**
   ```powershell
   ..\venv\Scripts\python.exe manage.py test
   ```

## API Surface

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/v1/tasks/analyze/` | Validates tasks and returns all tasks sorted by computed priority plus diagnostic scores. |
| `POST` | `/api/v1/tasks/suggest/` | Returns the top three ranked tasks with natural language explanations. |
| `GET` | `/api/v1/health/` | Lightweight health probe used by the frontend. |

All payloads follow:

```json
{
  "tasks": [
    {"title": "Fix login bug", "due_date": "2025-11-30", "estimated_hours": 3, "importance": 8, "dependencies": []}
  ],
  "strategy": "smart_balance"
}
```

## Algorithm Explanation (≈350 words)

The scoring engine lives in `tasks/scoring.py` and is centered around the `TaskScorer` class. Each task is run through four factor calculators and a final weighted sum. The system first normalizes raw input (defaulting missing due dates to seven days out, coercing ISO timestamps, clamping importance between 1 and 10, and forcing estimated hours to be positive). This ensures we can reason about imperfect data coming from either the API or the ORM hook on `Task.save()`.

1. **Urgency** – I compute `days_until_due` relative to `datetime.now().date()`. Overdue work immediately receives a score of at least 80, climbing by four points per day until capped at 100. Items due today get a 95. Forthcoming work decays piecewise: 0–3 days stays above 75, up to two weeks sits between 50–70, and distant work gently drifts toward single digits. This mix gives overdue and imminent items a clear advantage while still differentiating medium-range deadlines.

2. **Importance** – Users rate impact on a 1–10 scale. I convert this linearly to 0–100, then boost ratings ≥8 by 10% (capped at 100). That gentle non-linearity mirrors real-world behavior where “mission critical” items deserve disproportionate attention.

3. **Effort** – Smaller work delivers momentum, so I invert estimated hours: sub-30-minute tasks score 95, ≤1 h scores 85, ≤2 h scores 75, etc., sliding down to a floor of 10 for very long initiatives. This is intentionally coarse; users should recognize whether the system is nudging a “quick win” or penalizing a multi-day effort.

4. **Dependencies** – The analyzer counts how many tasks list the current task in their `dependencies`. Blocking nothing yields 10 points, while each additional dependent adds 15 points until capped at 100. This favors unblocking teams before starting isolated work.

Strategies (`smart_balance`, `fastest_wins`, `high_impact`, `deadline_driven`) simply provide alternative weight dictionaries over the same factors. Example: `fastest_wins` assigns 50% of the weight to effort, while `deadline_driven` allocates 70% to urgency. Because all factor calculators return normalized (0–100) scores, weight changes remain intuitive and easy to extend in the future.

Edge cases receive dedicated handling: missing fields fall back to safe defaults, cyclic dependency graphs are detected via DFS and surfaced as API errors, and string due dates tolerate ISO timestamps. The result is a flexible engine that can be tuned without rewriting the underlying logic.

## Design Decisions

- **Single scorer class** keeps the heuristics centralized and makes strategy swaps trivial (just change a weight profile).
- **Serializer-first validation** catches malformed payloads before the algorithm runs, while the scorer still guards against missing data for reuse from the model layer.
- **Vanilla frontend** (no build step) to keep setup fast for reviewers; it talks to `/api/v1` via `fetch` and renders explanations inline.
- **Task model hook** uses the same scorer to compute a complexity metric, showcasing reuse and guaranteeing stored records always have a priority snapshot.
- **Tests cover behavior** (13 cases) so we can refactor the algorithm with confidence.

## Time Breakdown

| Work Item | Approx. Time |
| --- | --- |
| Algorithm design & implementation | 1h 30m |
| API wiring, serializers, model integration | 45m |
| Frontend (UI + fetch integration + UX polish) | 45m |
| Testing & debugging | 20m |
| Documentation & cleanup | 20m |

Total ≈ 3h 40m.

## Bonus Challenges

None attempted due to timebox. My next pick would be an Eisenhower matrix visualization fed by the same scoring metadata.

## Future Improvements

- Persist tasks through the API (currently in-memory) and expose CRUD endpoints.
- Add auth & multi-user support so strategies can be saved per user.
- Track feedback on suggestions, enabling a reinforcement loop that tunes weights automatically.
- Visualize dependency cycles directly on the frontend instead of just returning an error message.

