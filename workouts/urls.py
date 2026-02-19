from django.urls import path
from . import views

urlpatterns = [
    # Shows today's workout plan and lets the user submit reps per set
    path("today/", views.today_workout, name="today_workout"),
]
