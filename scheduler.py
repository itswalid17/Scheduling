"""Core single-machine scheduling rules and metrics.

Assumptions:
- One machine is available.
- All jobs are available at time zero.
- Jobs are non-preemptive.
- No setup times or sequence-dependent constraints.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations
from math import isfinite
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Task:
    name: str
    processing_time: float
    due_date: float


def validate_tasks(raw_tasks: Iterable[dict | Task]) -> list[Task]:
    """Validate and normalize task records."""
    tasks: list[Task] = []
    seen_names: set[str] = set()

    for index, item in enumerate(raw_tasks, start=1):
        if isinstance(item, Task):
            task = item
        else:
            name = str(item.get("name", "")).strip()
            if not name:
                raise ValueError(f"Task on row {index} needs a name.")
            try:
                processing_time = float(item.get("processing_time"))
                due_date = float(item.get("due_date"))
            except (TypeError, ValueError):
                raise ValueError(f"Task '{name}': processing time and due date must be numbers.") from None
            task = Task(name, processing_time, due_date)

        normalized_name = task.name.strip()
        if not normalized_name:
            raise ValueError(f"Task on row {index} needs a name.")
        if normalized_name.casefold() in seen_names:
            raise ValueError(f"Duplicate task name: '{normalized_name}'. Names must be unique.")
        if not isfinite(task.processing_time) or task.processing_time <= 0:
            raise ValueError(f"Task '{normalized_name}': processing time must be a positive finite number.")
        if not isfinite(task.due_date) or task.due_date < 0:
            raise ValueError(f"Task '{normalized_name}': due date must be a non-negative finite number.")

        seen_names.add(normalized_name.casefold())
        tasks.append(Task(normalized_name, float(task.processing_time), float(task.due_date)))

    if not tasks:
        raise ValueError("Add at least one task before running the scheduler.")
    return tasks


def calculate_schedule(sequence: Sequence[Task]) -> dict:
    """Build a schedule and calculate standard single-machine metrics."""
    current_time = 0.0
    rows: list[dict] = []

    for position, task in enumerate(sequence, start=1):
        start = current_time
        completion = start + task.processing_time
        lateness = completion - task.due_date
        tardiness = max(0.0, lateness)
        rows.append(
            {
                "Position": position,
                "Task": task.name,
                "Processing time (P)": task.processing_time,
                "Due date (D)": task.due_date,
                "Start": start,
                "Completion (C)": completion,
                "Lateness (L)": lateness,
                "Tardiness (T)": tardiness,
                "On time": "Yes" if tardiness == 0 else "No",
            }
        )
        current_time = completion

    latenesses = [row["Lateness (L)"] for row in rows]
    tardiness_values = [row["Tardiness (T)"] for row in rows]
    completion_times = [row["Completion (C)"] for row in rows]

    metrics = {
        "Makespan (Cmax)": current_time,
        "Total completion time (ΣCj)": sum(completion_times),
        "Average completion time": sum(completion_times) / len(rows),
        "Maximum lateness (Lmax)": max(latenesses),
        "Maximum tardiness (Tmax)": max(tardiness_values),
        "Total tardiness (ΣTj)": sum(tardiness_values),
        "Tardy jobs": sum(value > 0 for value in tardiness_values),
    }
    return {"schedule": rows, "metrics": metrics, "sequence": [task.name for task in sequence]}


def run_spt(tasks: Sequence[Task]) -> dict:
    """Shortest Processing Time: optimal for minimizing sum of completion times."""
    ordered = sorted(tasks, key=lambda task: task.processing_time)  # stable for ties
    return calculate_schedule(ordered)


def run_edd(tasks: Sequence[Task]) -> dict:
    """Earliest Due Date: optimal for minimizing maximum lateness."""
    ordered = sorted(tasks, key=lambda task: task.due_date)  # stable for ties
    return calculate_schedule(ordered)


EXACT_OBJECTIVES = {
    "Total completion time (ΣCj)": "Total completion time (ΣCj)",
    "Maximum lateness (Lmax)": "Maximum lateness (Lmax)",
    "Total tardiness (ΣTj)": "Total tardiness (ΣTj)",
    "Tardy jobs": "Tardy jobs",
}


def run_exact(
    tasks: Sequence[Task],
    objective: str = "Total tardiness (ΣTj)",
    max_jobs: int = 9,
) -> dict:
    """Brute-force exact search over all job permutations for small instances.

    Returns the sequence minimizing the chosen objective. Complexity is O(n! * n),
    so this method is intentionally limited to small instances.
    """
    if objective not in EXACT_OBJECTIVES:
        raise ValueError(f"Unsupported exact objective: {objective}")
    if len(tasks) > max_jobs:
        raise ValueError(f"Exact search is limited to {max_jobs} tasks; received {len(tasks)}.")

    best_result = None
    best_value = float("inf")
    best_key = None

    for order in permutations(tasks):
        result = calculate_schedule(order)
        value = result["metrics"][EXACT_OBJECTIVES[objective]]
        # The second part gives deterministic tie-breaking by the task-name sequence.
        key = (value, tuple(result["sequence"]))
        if best_key is None or key < best_key:
            best_key = key
            best_value = value
            best_result = result

    assert best_result is not None
    best_result["exact_objective"] = objective
    best_result["exact_objective_value"] = best_value
    best_result["permutations_checked"] = _factorial(len(tasks))
    return best_result


def _factorial(n: int) -> int:
    result = 1
    for value in range(2, n + 1):
        result *= value
    return result
