from django import forms
from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from .importers import import_plan_items_from_csv
from .models import Exercise, WorkoutPlan, WorkoutPlanItem, WorkoutLog, SetLog


class WorkoutPlanItemInline(admin.TabularInline):
    model = WorkoutPlanItem
    extra = 0


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("name", "youtube_url")
    search_fields = ("name",)


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ("date", "title", "created_by", "created_at", "import_csv_link")
    list_filter = ("date",)
    inlines = [WorkoutPlanItemInline]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:plan_id>/import-csv/",
                self.admin_site.admin_view(self.import_csv_view),
                name="workouts_workoutplan_import_csv",
            )
        ]
        return custom_urls + urls

    def import_csv_link(self, obj):
        url = reverse("admin:workouts_workoutplan_import_csv", args=[obj.id])
        return format_html('<a href="{}">Import CSV</a>', url)

    import_csv_link.short_description = "CSV Import"

    def import_csv_view(self, request, plan_id):
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
                    f"Exercises created: {result.created_exercises}, "
                    f"updated: {result.updated_exercises}.",
                )
                change_url = reverse("admin:workouts_workoutplan_change", args=[plan.id])
                return redirect(change_url)
        else:
            form = CsvImportForm()

        context = {
            **self.admin_site.each_context(request),
            "title": f"Import CSV into plan: {plan}",
            "plan": plan,
            "form": form,
            "opts": self.model._meta,
        }
        return render(request, "admin/workouts/import_csv.html", context)


@admin.register(WorkoutLog)
class WorkoutLogAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "submitted_at")
    list_filter = ("user", "plan__date")


@admin.register(SetLog)
class SetLogAdmin(admin.ModelAdmin):
    list_display = ("log", "plan_item", "set_number", "reps_done")