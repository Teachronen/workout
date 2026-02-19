from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import WorkoutLog, WorkoutPlan, WorkoutPlanItem, SetLog


@login_required
def today_workout(request):
    """
    Shows today's workout plan for the logged-in user and saves reps-per-set input.
    - If no plan exists for today: shows a friendly message.
    - On POST: creates/updates WorkoutLog and SetLog rows.
    """
    today = timezone.localdate()

    # Get the plan for today's date (admin creates plans manually)
    plan = WorkoutPlan.objects.filter(date=today).first()
    if not plan:
        return render(request, "workouts/today.html", {"today": today, "plan": None})

    # Items are the exercises inside the plan, ordered by 'order'
    items = WorkoutPlanItem.objects.select_related("exercise").filter(plan=plan)

    # Get existing log if user already submitted today
    log = WorkoutLog.objects.filter(user=request.user, plan=plan).first()

    if request.method == "POST":
        # Create the log if it's the first submission
        if not log:
            log = WorkoutLog.objects.create(user=request.user, plan=plan)

        # Save general comment for the whole workout
        log.general_comment = request.POST.get("general_comment", "").strip()
        log.save(update_fields=["general_comment"])

        # For simplicity: on each submit, replace previous set logs for this plan
        SetLog.objects.filter(log=log).delete()

        # For each plan item, read reps for each set (reps_<itemid>_<setnum>)
        for item in items:
            for set_num in range(1, item.prescribed_sets + 1):
                reps_key = f"reps_{item.id}_{set_num}"
                comment_key = f"comment_{item.id}_{set_num}"

                reps_raw = (request.POST.get(reps_key) or "").strip()
                comment_raw = (request.POST.get(comment_key) or "").strip()

                # Skip empty inputs (allows partial entry, but you can enforce required later)
                if reps_raw == "":
                    continue

                # We store reps_done as an integer.
                # For time-based exercises, user can enter seconds.
                try:
                    reps_done = int(reps_raw)
                except ValueError:
                    # If non-integer input is entered, show error and don't save this submission
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

    # Build initial values if a log already exists (so user sees what was saved)
    initial = {}
    if log:
        for s in SetLog.objects.select_related("plan_item", "plan_item__exercise").filter(log=log):
            initial[f"reps_{s.plan_item_id}_{s.set_number}"] = s.reps_done
            initial[f"comment_{s.plan_item_id}_{s.set_number}"] = s.comment or ""

    context = {
        "today": today,
        "plan": plan,
        "items": items,
        "log": log,
        "initial": initial,
    }
    return render(request, "workouts/today.html", context)
