from django import forms
from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.html import format_html


from .importers import import_plan_items_from_csv
from .models import Exercise, WorkoutPlan, WorkoutPlanItem, WorkoutLog, SetLog



class WorkoutPlanItemInline(admin.TabularInline):
    """Allows editing plan items directly inside a workout plan."""
    model = WorkoutPlanItem
    extra = 0


class CsvImportForm(forms.Form):
    """Simple form for uploading a CSV file to import plan items."""
    csv_file = forms.FileField()


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    """Admin configuration for Exercise."""
    list_display = ("name", "youtube_url")
    search_fields = ("name",)


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    """Admin configuration for WorkoutPlan, including CSV import view."""
    list_display = ("date", "title", "created_by", "created_at", "import_csv_link")
    list_filter = ("date",)
    inlines = [WorkoutPlanItemInline]

    def get_urls(self):
        """Adds a custom admin URL for importing CSV into a specific plan."""
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:plan_id>/import-csv/",
                self.admin_site.admin_view(self.import_csv_view),
                name="workoutplan_import_csv",
            )
        ]
        return custom_urls + urls

    def import_csv_link(self, obj):
        """Shows a clickable link in the list view to import CSV into this plan."""
        url = reverse("admin:workoutplan_import_csv", args=[obj.id])
        return format_html('<a href="{}">Import CSV</a>', url)





    def import_csv_view(self, request, plan_id):
        """Handles the CSV upload and imports items into the selected plan."""
        plan = get_object_or_404(WorkoutPlan, pk=plan_id)

        if request.method == "POST":
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = form.cleaned_data["csv_file"]
                try:
                    result = import_plan_items_from_csv(plan, csv_file)
                except Exception as e:
                    messages.error(request, f"CSV import failed: {e}")
                    return redirect(request.path)

                messages.success(
                    request,
                    f"Imported {result.created_items} items. "
                    f"Exercises created: {result.created_exercises}, updated: {result.updated_exercises}.",
                )
                # Go back to the plan edit page so you immediately see inline items populated
                change_url = reverse("admin:workouts_workoutplan_change", args=[plan.id])
                return redirect(change_url)
        else:
            form = CsvImportForm()

        context = {
            "title": f"Import CSV into plan: {plan}",
            "plan": plan,
            "form": form,
        }
        return render(request, "admin/workouts/import_csv.html", context)


@admin.register(WorkoutLog)
class WorkoutLogAdmin(admin.ModelAdmin):
    """Admin configuration for WorkoutLog."""
    list_display = ("user", "plan", "submitted_at")
    list_filter = ("user", "plan__date")


@admin.register(SetLog)
class SetLogAdmin(admin.ModelAdmin):
    """Admin configuration for SetLog."""
    list_display = ("log", "plan_item", "set_number", "reps_done")
