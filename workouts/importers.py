import csv
from dataclasses import dataclass
from typing import Tuple

from django.db import transaction

from .models import Exercise, WorkoutPlan, WorkoutPlanItem


@dataclass
class ImportResult:
    created_exercises: int
    updated_exercises: int
    created_items: int


def _parse_sets(value: str) -> int:
    """
    Parses Sets value (e.g. '3' or '1-2') and returns an integer.
    For ranges, returns the max (e.g. '1-2' -> 2).
    """
    s = (value or "").strip()
    if not s:
        return 1
    if "-" in s:
        parts = [p.strip() for p in s.split("-") if p.strip()]
        nums = [int(p) for p in parts]
        return max(nums) if nums else 1
    return int(s)


@transaction.atomic
def import_plan_items_from_csv(plan: WorkoutPlan, csv_file) -> ImportResult:
    """
    Imports plan items from a CSV file into the given WorkoutPlan.
    Creates Exercises if missing, updates YouTube URL if changed,
    and creates WorkoutPlanItem rows in CSV order.
    """
    decoded = csv_file.read().decode("utf-8-sig").splitlines()
    reader = csv.DictReader(decoded)

    required = {"Exercise", "Sets", "Reps_or_Time", "Rest_Seconds", "YouTube_URL"}
    if not required.issubset(set(reader.fieldnames or [])):
        missing = required - set(reader.fieldnames or [])
        raise ValueError(f"Missing required CSV columns: {', '.join(sorted(missing))}")

    created_exercises = 0
    updated_exercises = 0
    created_items = 0

    # Optional: wipe existing items for that plan before importing
    WorkoutPlanItem.objects.filter(plan=plan).delete()

    order = 1
    for row in reader:
        name = (row.get("Exercise") or "").strip()
        youtube_url = (row.get("YouTube_URL") or "").strip()
        reps_or_time = (row.get("Reps_or_Time") or "").strip()
        rest_seconds_raw = (row.get("Rest_Seconds") or "").strip()
        sets_raw = (row.get("Sets") or "").strip()

        if not name:
            continue  # skip blank lines

        prescribed_sets = _parse_sets(sets_raw)
        rest_seconds = int(rest_seconds_raw) if rest_seconds_raw else 0

        exercise, created = Exercise.objects.get_or_create(
            name=name,
            defaults={"youtube_url": youtube_url},
        )
        if created:
            created_exercises += 1
        else:
            # Update YouTube URL if changed and provided
            if youtube_url and exercise.youtube_url != youtube_url:
                exercise.youtube_url = youtube_url
                exercise.save(update_fields=["youtube_url"])
                updated_exercises += 1

        WorkoutPlanItem.objects.create(
            plan=plan,
            exercise=exercise,
            order=order,
            prescribed_sets=prescribed_sets,
            prescribed_reps=reps_or_time or "10",
            rest_seconds=rest_seconds,
        )
        created_items += 1
        order += 1

    return ImportResult(
        created_exercises=created_exercises,
        updated_exercises=updated_exercises,
        created_items=created_items,
    )
