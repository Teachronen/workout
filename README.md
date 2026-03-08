# Workout Tracker

A simple and extensible **workout tracking web application** built with **Django**.

The system allows users to view daily workouts, log completed sets, and track their training over time. It was designed as a lightweight personal training log that can later evolve into a full fitness tracking platform.

---

# Features

Current capabilities:

* User authentication
* Daily workout view
* Logging repetitions for each set
* Workout comments
* Admin interface for workout management
* CSV import for workout plans
* Multiple users (family / small training group)

Future planned features:

* Workout history dashboard
* Progress graphs
* Personal record tracking
* Exercise statistics
* REST API
* Mobile-optimized UI

---

# Tech Stack

Backend

* Python 3.12
* Django 6.0
* Gunicorn

Frontend

* Django Templates
* HTML
* CSS

Infrastructure

* Ubuntu VPS
* Nginx
* systemd
* GitHub

Database

* SQLite (current)
* PostgreSQL planned

---

# Architecture

Production architecture:

```
Internet
   │
   ▼
Nginx
   │
   ▼
Gunicorn
   │
   ▼
Django Application
   │
   ▼
Database
```

Nginx handles:

* static files
* reverse proxy

Gunicorn runs the Django application.

---

# Project Structure

```
workout/
│
├── manage.py
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│
├── workouts/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│
├── templates/
│
├── staticfiles/
│
├── requirements.txt
│
└── Dockerfile
```

---

# Core Data Models

The application is based on five core models.

### Exercise

Represents a physical exercise.

Example:

* Pull-up
* Plank
* Ring row

Fields

```
name
youtube_url
```

---

### WorkoutPlan

Represents a workout scheduled for a specific date.

Fields

```
date
title
created_by
created_at
```

---

### WorkoutPlanItem

Represents an exercise within a workout plan.

Fields

```
plan
exercise
order
prescribed_sets
prescribed_reps
rest_seconds
```

---

### WorkoutLog

Represents a completed workout.

Fields

```
user
plan
submitted_at
general_comment
```

---

### SetLog

Represents results of a specific set.

Fields

```
log
plan_item
set_number
reps_done
comment
```

---

# Local Development Setup

Clone repository:

```
git clone https://github.com/Teachronen/workout.git
cd workout
```

Create virtual environment:

```
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```
pip install -r requirements.txt
```

Run migrations:

```
python manage.py migrate
```

Create admin user:

```
python manage.py createsuperuser
```

Run development server:

```
python manage.py runserver
```

Open:

```
http://127.0.0.1:8000
```

---

# Production Deployment

The application is deployed on a VPS using:

* Ubuntu
* Nginx
* Gunicorn
* systemd

Deployment workflow:

```
git pull

source venv/bin/activate

pip install -r requirements.txt

python manage.py migrate

python manage.py collectstatic

sudo systemctl restart gunicorn
```

---

# Static Files

Static files are collected using:

```
python manage.py collectstatic
```

Served by Nginx from:

```
/home/rotem/workout/staticfiles
```

---

# Domain

Production domain:

```
workout.deeplearninghuman.com
```

---

# Security

Production settings include:

```
DEBUG = False
ALLOWED_HOSTS configured
HTTPS (planned)
```

HTTPS will be enabled using **Let's Encrypt / Certbot**.

---

# Roadmap

Planned improvements:

* workout history
* progress analytics
* mobile UI
* REST API
* PostgreSQL database
* Docker deployment
* CI/CD pipeline

---

# License

Personal project. License to be defined.
