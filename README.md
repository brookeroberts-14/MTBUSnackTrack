# SnackTrack Setup

## 1. Install Python packages
```
pip install -r requirements.txt
```

## 2. Create the database
```
python manage.py makemigrations core
python manage.py migrate
```

## 3. Run the server
```
python manage.py runserver
```

## 4. Open in browser
```
http://127.0.0.1:8000/
```

## Login
- Email: admin@snacktrack.com
- Password: Admin123!

## Folder Structure
```
your-project/
  manage.py
  requirements.txt
  MTBUSolutions/
    __init__.py
    settings.py
    urls.py
    asgi.py
    wsgi.py
  core/
    __init__.py
    apps.py
    models.py
    views.py
    urls.py
    migrations/
    templates/
      base.html
      login.html
      register.html
      admin_dashboard.html
      staff_dashboard.html
      user_form.html
      classroom_form.html
      snack_form.html
```
