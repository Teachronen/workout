from django import forms
from django.contrib import admin, messages

from .importers import import_plan_items_from_csv
from .models import Exercise, WorkoutPlan, WorkoutPlanItem, WorkoutLog, SetLog


# ----------------------------
# Allows editing plan items
# directly inside a workout plan
# ----------------------------
class WorkoutPlanItemInline(admin.TabularInline):
    model = WorkoutPlanItem
    extra = 0


# ----------------------------
# Simple admin form to upload a CSV
# ----------------------------
class WorkoutPlanCsvImportForm(forms.Form):
    csv_file = forms.FileField()


# ----------------------------
# Exercise admin configuration
# ----------------------------
@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "youtube_url")
    search_fields = ("name",)


# ----------------------------
# Workout plan admin
# Includes:
# - Inline editing of items
# - Action to import items from CSV
# ----------------------------
@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ("date", "title", "created_by", "created_at")
    list_filter = ("date",)
    inlines = [WorkoutPlanItemInline]
    actions = ["import_items_from_csv"]

    # Admin action: import CSV into selected plan (supports selecting 1 plan)
    def import_items_from_csv(self, request, queryset):
        """
        Imports plan items from a CSV file into a selected WorkoutPlan.
        For safety and clarity, requires selecting exactly one plan.
        """
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly ONE WorkoutPlan.", level=messages.ERROR)
            return

        plan = queryset.first()

        if request.method == "POST" and "apply" in request.POST:
            form = WorkoutPlanCsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data["csv_file"]
                try:
                    result = import_plan_items_from_csv(plan, csv_file)
                except Exception as e:
                    self.message_user(request, f"CSV import failed: {e}", level=messages.ERROR)
                    return

                self.message_user(
                    request,
                    f"Imported {result.created_items} items into {plan.date}. "
                    f"Exercises created: {result.created_exercises}, updated: {result.updated_exercises}.",
                    level=messages.SUCCESS,
                )
                return

        else:
            form = WorkoutPlanCsvImportForm()

        # Render a simple upload page using Django's built-in admin template
        from django.shortcuts import render

        context = {
            "title": "Import WorkoutPlan items from CSV",
            "form": form,
            "plan": plan,
            "queryset": queryset,
            "action_name": "import_items_from_csv",
        }
        return render(request, "admin/workouts/import_csv.html", context)

    import_items_from_csv.short_description = "Import items from CSV (replaces existing items)"


# ----------------------------
# Workout log admin
# ----------------------------
@admin.register(WorkoutLog)
class WorkoutLogAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "submitted_at")
    list_filter = ("user", "plan__date")


# ----------------------------
# Set log admin
# ----------------------------
@admin.register(SetLog)
class SetLogAdmin(admin.ModelAdmin):
    list_display = ("log", "plan_item", "set_number", "reps_done")
