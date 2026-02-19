from django.conf import settings
from django.db import models


# -------------------------
# Represents a single exercise
# Example: Push-up, Squat, Pull-up
# Stores the name and a YouTube video showing how to perform it
# -------------------------
class Exercise(models.Model):
    name = models.CharField(max_length=120, unique=True)
    youtube_url = models.URLField()
    notes = models.TextField(blank=True)

    # Human-readable name shown in admin and logs
    def __str__(self):
        return self.name


# -------------------------
# Represents a workout plan for a specific date
# Example: Workout planned for 2025-03-20
# Created manually by admin
# -------------------------
class WorkoutPlan(models.Model):
    date = models.DateField(unique=True)
    title = models.CharField(max_length=120, blank=True)

    # User who created the plan (admin/coach)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="plans_created"
    )

    # Automatically stores when the plan was created
    created_at = models.DateTimeField(auto_now_add=True)

    # Human-readable display
    def __str__(self):
        return f"{self.date} - {self.title or 'Workout'}"


# -------------------------
# Represents a single exercise inside a workout plan
# Example: Bench Press – 3 sets x 10 reps, 60s rest
# -------------------------
class WorkoutPlanItem(models.Model):
    plan = models.ForeignKey(
        WorkoutPlan,
        on_delete=models.CASCADE,
        related_name="items"
    )

    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.PROTECT
    )

    # Order of the exercise in the workout (1..7)
    order = models.PositiveSmallIntegerField(default=1)

    # Prescription details
    prescribed_sets = models.PositiveSmallIntegerField(default=3)
    prescribed_reps = models.CharField(
        max_length=20,
        default="10"
    )
    rest_seconds = models.PositiveSmallIntegerField(default=60)

    class Meta:
        # Prevents two items from having the same order inside one plan
        unique_together = [("plan", "order")]

        # Ensures exercises appear in correct order
        ordering = ["order"]

    def __str__(self):
        return f"{self.plan.date}: {self.exercise.name}"


# -------------------------
# Represents a user's submission for a workout plan
# One log per user per plan
# -------------------------
class WorkoutLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workout_logs"
    )

    plan = models.ForeignKey(
        WorkoutPlan,
        on_delete=models.PROTECT,
        related_name="logs"
    )

    # Automatically saved when user submits workout
    submitted_at = models.DateTimeField(auto_now_add=True)

    # Optional general comment about the workout
    general_comment = models.TextField(blank=True)

    class Meta:
        # User can only submit once per plan
        unique_together = [("user", "plan")]

        # Newest logs appear first
        ordering = ["-plan__date"]

    def __str__(self):
        return f"{self.user} @ {self.plan.date}"


# -------------------------
# Represents a single set performed by the user
# Example: Set 1 of Squat → 12 reps
# -------------------------
class SetLog(models.Model):
    log = models.ForeignKey(
        WorkoutLog,
        on_delete=models.CASCADE,
        related_name="set_logs"
    )

    plan_item = models.ForeignKey(
        WorkoutPlanItem,
        on_delete=models.PROTECT,
        related_name="set_logs"
    )

    # Which set number (1,2,3...)
    set_number = models.PositiveSmallIntegerField()

    # How many reps were actually performed
    reps_done = models.PositiveSmallIntegerField()

    # Optional note per set
    comment = models.TextField(blank=True)

    class Meta:
        # Prevent duplicate set numbers for same exercise & log
        unique_together = [("log", "plan_item", "set_number")]

        # Keep sets ordered properly
        ordering = ["plan_item__order", "set_number"]

    def __str__(self):
        return f"{self.plan_item.exercise.name} - set {self.set_number}: {self.reps_done}"
