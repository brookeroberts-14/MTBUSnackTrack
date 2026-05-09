from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from functools import wraps
import json
import os
import io
import zipfile
from pathlib import Path
from django.utils.html import escape as html_escape

from . import models


# ---- Auth decorators ----

def login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if 'user_id' not in request.session:
            return redirect('login')
        return view(request, *args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if 'user_id' not in request.session:
            return redirect('login')
        if request.session.get('user_role') != 'admin':
            return redirect('staff_dashboard')
        return view(request, *args, **kwargs)
    return wrapper


# ---- Auth views ----

def login_view(request):
    if 'user_id' in request.session:
        if request.session.get('user_role') == 'admin':
            return redirect('admin_dashboard')
        return redirect('staff_dashboard')

    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        user = models.authenticate(email, password)
        if user:
            request.session['user_id'] = user.id
            request.session['user_name'] = user.name
            request.session['user_email'] = user.email
            request.session['user_role'] = user.role
            if user.role == 'admin':
                return redirect('admin_dashboard')
            return redirect('staff_dashboard')
        error = 'Invalid email or password'

    return render(request, 'login.html', {'error': error})


def register_view(request):
    if 'user_id' in request.session:
        return redirect('staff_dashboard')

    error = None
    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        if len(password) < 6:
            error = 'Password must be at least 6 characters'
        else:
            try:
                user = models.create_user(name, email, password, 'staff')
                request.session['user_id'] = user.id
                request.session['user_name'] = user.name
                request.session['user_email'] = user.email
                request.session['user_role'] = 'staff'
                return redirect('staff_dashboard')
            except ValueError as e:
                error = str(e)

    return render(request, 'register.html', {'error': error})


def logout_view(request):
    request.session.flush()
    return redirect('login')


# ---- Admin Dashboard ----

@admin_required
def admin_dashboard(request, default_tab=None):
    tab = request.GET.get('tab', default_tab or 'users')
    context = {
        'tab': tab,
        'users': models.get_all_users(),
        'classrooms': models.get_all_classrooms(),
        'snacks': models.get_all_snacks(),
        'stats': {
            'users': models.User.objects.count(),
            'classrooms': models.Classroom.objects.count(),
            'snacks': models.Snack.objects.count(),
            'transactions': models.Transaction.objects.count(),
        },
        'user_name': request.session.get('user_name', ''),
    }
    return render(request, 'admin_dashboard.html', context)


# ---- Staff Dashboard ----

@login_required
def staff_dashboard(request):
    tab = request.GET.get('tab', 'usage')
    all_snacks = models.get_all_snacks()
    summary = models.get_usage_summary()

    context = {
        'tab': tab,
        'classrooms': models.get_all_classrooms(),
        'available_snacks': [s for s in all_snacks if s.quantity > 0],
        'all_snacks': all_snacks,
        'transactions': models.get_recent_transactions(10),
        'summary': summary,
        'summary_json': json.dumps(summary, default=str),
        'inv_status': models.get_inventory_status(),
        'user_name': request.session.get('user_name', ''),
        'user_role': request.session.get('user_role', 'staff'),
    }
    return render(request, 'staff_dashboard.html', context)


# ---- User CRUD ----

@admin_required
def user_form(request, user_id=None):
    user = models.get_user_by_id(user_id) if user_id else None
    error = None

    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        role = request.POST.get('role', 'staff')
        password = request.POST.get('password', '')
        try:
            if user_id:
                models.update_user(user_id, name, email, role, password or None)
            else:
                models.create_user(name, email, password, role)
            return redirect('admin_dashboard')
        except ValueError as e:
            error = str(e)

    return render(request, 'user_form.html', {'user': user, 'error': error, 'editing': bool(user_id)})


@admin_required
def delete_user(request, user_id):
    models.delete_user(user_id)
    return redirect('admin_dashboard')


# ---- Classroom CRUD ----

@admin_required
def classroom_form(request, classroom_id=None):
    classroom = models.get_classroom_by_id(classroom_id) if classroom_id else None
    error = None

    if request.method == 'POST':
        name = request.POST.get('name', '')
        try:
            if classroom_id:
                models.update_classroom(classroom_id, name)
            else:
                models.create_classroom(name)
            return redirect('admin_classrooms')
        except ValueError as e:
            error = str(e)

    return render(request, 'classroom_form.html', {'classroom': classroom, 'error': error, 'editing': bool(classroom_id)})


@admin_required
def delete_classroom(request, classroom_id):
    models.delete_classroom(classroom_id)
    return redirect('admin_classrooms')


# ---- Snack CRUD ----

@admin_required
def snack_form(request, snack_id=None):
    snack = models.get_snack_by_id(snack_id) if snack_id else None
    error = None

    if request.method == 'POST':
        try:
            name = request.POST.get('name', '')
            quantity = int(request.POST.get('quantity', 0))
            purchase_price = float(request.POST.get('price', 0))
            quantity_per_box = int(request.POST.get('perbox', 1))
            supplier = request.POST.get('supplier', '')
            low_stock_threshold = int(request.POST.get('threshold', 10))
            if snack_id:
                models.update_snack(snack_id, name, quantity, purchase_price, quantity_per_box, supplier, low_stock_threshold)
            else:
                models.create_snack(name, quantity, purchase_price, quantity_per_box, supplier, low_stock_threshold)
            return redirect('admin_inventory')
        except ValueError as e:
            error = str(e)

    return render(request, 'snack_form.html', {'snack': snack, 'error': error, 'editing': bool(snack_id)})


@admin_required
def delete_snack(request, snack_id):
    models.delete_snack(snack_id)
    return redirect('admin_inventory')


# ---- Record Usage ----

@login_required
@require_POST
def record_usage_view(request):
    snack_id = request.POST.get('snack_id', '')
    classroom_id = request.POST.get('classroom_id', '')
    quantity = int(request.POST.get('quantity', 1))
    try:
        models.record_usage(
            snack_id, classroom_id, quantity,
            request.session.get('user_id', ''),
            request.session.get('user_name', ''),
        )
        return redirect('staff_dashboard')
    except ValueError as e:
        return redirect('staff_dashboard')


# ---- Data Management ----

@admin_required
def export_data(request):
    data = models.export_all_data()
    response = HttpResponse(json.dumps(data, default=str, indent=2), content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="snacktrack-backup.json"'
    return response


@admin_required
@require_POST
def import_data_view(request):
    file = request.FILES.get('file')
    if file:
        try:
            data = json.loads(file.read().decode('utf-8'))
            models.import_data(data)
        except Exception:
            pass
    return redirect('admin_data')


@admin_required
@require_POST
def clear_data(request):
    models.clear_all_data()
    return redirect('admin_data')


# ---- Code Viewer ----

def code_view(request):
    base = Path(__file__).resolve().parent.parent
    file_list = [
        ('core/views.py', 'views.py'),
        ('core/models.py', 'models.py'),
        ('core/urls.py', 'urls.py'),
        ('core/apps.py', 'apps.py'),
        ('MTBUSolutions/settings.py', 'settings.py'),
        ('MTBUSolutions/urls.py', 'project urls.py'),
        ('MTBUSolutions/asgi.py', 'asgi.py'),
        ('MTBUSolutions/wsgi.py', 'wsgi.py'),
        ('manage.py', 'manage.py'),
        ('local_requirements.txt', 'requirements.txt'),
        ('README.md', 'README'),
        ('core/templates/base.html', 'base.html'),
        ('core/templates/login.html', 'login.html'),
        ('core/templates/register.html', 'register.html'),
        ('core/templates/admin_dashboard.html', 'admin_dashboard.html'),
        ('core/templates/staff_dashboard.html', 'staff_dashboard.html'),
        ('core/templates/user_form.html', 'user_form.html'),
        ('core/templates/classroom_form.html', 'classroom_form.html'),
        ('core/templates/snack_form.html', 'snack_form.html'),
    ]

    active_index = int(request.GET.get('file', 0))
    if active_index < 0 or active_index >= len(file_list):
        active_index = 0

    files = [{'label': label, 'path': path} for path, label in file_list]
    path, label = file_list[active_index]
    content = (base / path).read_text()

    active_file = {
        'path': path,
        'label': label,
        'content': content,
        'content_json': json.dumps(content),
        'lines': content.count('\n') + 1,
    }

    return render(request, 'code.html', {
        'files': files,
        'active_file': active_file,
        'active_index': active_index,
    })


def download_zip(request):
    """Download entire project as a ZIP file."""
    base = Path(__file__).resolve().parent.parent
    project_files = [
        'manage.py',
        'local_requirements.txt',
        'README.md',
        'MTBUSolutions/__init__.py',
        'MTBUSolutions/settings.py',
        'MTBUSolutions/urls.py',
        'MTBUSolutions/asgi.py',
        'MTBUSolutions/wsgi.py',
        'core/__init__.py',
        'core/apps.py',
        'core/models.py',
        'core/views.py',
        'core/urls.py',
        'core/templates/login.html',
        'core/templates/register.html',
        'core/templates/admin_dashboard.html',
        'core/templates/staff_dashboard.html',
        'core/templates/user_form.html',
        'core/templates/classroom_form.html',
        'core/templates/snack_form.html',
        'core/templates/code.html',
    ]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for rel_path in project_files:
            full_path = base / rel_path
            if full_path.exists():
                zf.writestr(f'SnackTrack/{rel_path}', full_path.read_text())

    buf.seek(0)
    response = HttpResponse(buf.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="SnackTrack.zip"'
    return response
