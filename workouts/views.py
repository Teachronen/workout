"""
Workout Views

This module contains the main view responsible for displaying and saving
workouts for authenticated users.

The primary view is `today_workout`, which serves as the main page of the
application.

Responsibilities of this view:

1. Determine which workout plan should be shown.
   - If there is a WorkoutPlan scheduled for today, it is displayed.
   - If there is no workout for today, the next upcoming workout is displayed.

2. Display the exercises for the selected workout plan.
   - Exercises are retrieved through WorkoutPlanItem objects.
   - Each item contains the exercise, number of sets, target reps/time,
     and rest time.

3. Handle workout logging.
   - When the workout belongs to today, the user can submit their results.
   - The system creates or updates a WorkoutLog for the user and the plan.
   - Individual sets are stored as SetLog records.

4. Validate input.
   - Reps or time values must be whole numbers.
   - Invalid input triggers an error message.

5. Provide context to the template.
   The template receives:
   - today's date
   - the workout plan being displayed
   - exercise items
   - previously saved logs (if they exist)
   - a list of upcoming workout plans

This view acts as the core interaction point between the user interface
(template) and the workout data models.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import WorkoutLog, WorkoutPlan, WorkoutPlanItem, SetLog


@login_required
def today_workout(request):
    today = timezone.localdate()

    # Today's plan
    plan = WorkoutPlan.objects.filter(date=today).first()

    # Upcoming plans after today
    upcoming_plans = WorkoutPlan.objects.filter(date__gt=today).order_by("date")

    # If there is no plan for today, optionally show the next one
    display_plan = plan if plan else upcoming_plans.first()

    if not display_plan:
        return render(
            request,
            "workouts/today.html",
            {
                "today": today,
                "plan": None,
                "display_plan": None,
                "upcoming_plans": [],
            },
        )

    items = WorkoutPlanItem.objects.select_related("exercise").filter(plan=display_plan)

    log = None
    initial = {}

    # Only allow saving when this is actually today's workout
    if plan and display_plan.id == plan.id:
        log = WorkoutLog.objects.filter(user=request.user, plan=display_plan).first()

        if request.method == "POST":
            if not log:
                log = WorkoutLog.objects.create(user=request.user, plan=display_plan)

            log.general_comment = request.POST.get("general_comment", "").strip()
            log.save(update_fields=["general_comment"])

            SetLog.objects.filter(log=log).delete()

            for item in items:
                for set_num in range(1, item.prescribed_sets + 1):
                    reps_key = f"reps_{item.id}_{set_num}"
                    comment_key = f"comment_{item.id}_{set_num}"

                    reps_raw = (request.POST.get(reps_key) or "").strip()
                    comment_raw = (request.POST.get(comment_key) or "").strip()

                    if reps_raw == "":
                        continue

                    try:
                        reps_done = int(reps_raw)
                    except ValueError:
                        messages.error(
                            request,
                            f"Invalid reps/time value '{reps_raw}' for {item.exercise.name} set {set_num}. "
                            f"Please enter a whole number (e.g., 10 or 60).",
                        )
                        return redirect("today_workout")

                    SetLog.objects.create(
                        log=log,
                        plan_item=item,
                        set_number=set_num,
                        reps_done=reps_done,
                        comment=comment_raw,
                    )

            messages.success(request, "Workout saved successfully!")
            return redirect("today_workout")

        if log:
            for s in SetLog.objects.select_related("plan_item", "plan_item__exercise").filter(log=log):
                initial[f"reps_{s.plan_item_id}_{s.set_number}"] = s.reps_done
                initial[f"comment_{s.plan_item_id}_{s.set_number}"] = s.comment or ""

    context = {
        "today": today,
        "plan": plan,
        "display_plan": display_plan,
        "items": items,
        "log": log,
        "initial": initial,
        "upcoming_plans": upcoming_plans,
        "is_today_plan": plan is not None and display_plan.id == plan.id,
    }
    return render(request, "workouts/today.html", context)