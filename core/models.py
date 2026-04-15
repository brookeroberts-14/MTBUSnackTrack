from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import os


# ---- Django Models ----

class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=20, default='staff')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Classroom(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Snack(models.Model):
    name = models.CharField(max_length=255)
    quantity = models.IntegerField(default=0)
    purchase_price = models.FloatField(default=0)
    quantity_per_box = models.IntegerField(default=1)
    supplier = models.CharField(max_length=255, blank=True, default='')
    low_stock_threshold = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    snack_id_ref = models.IntegerField(null=True)
    snack_name = models.CharField(max_length=255)
    classroom_id_ref = models.IntegerField(null=True)
    classroom_name = models.CharField(max_length=255)
    quantity = models.IntegerField()
    user_id_ref = models.IntegerField(null=True)
    user_name = models.CharField(max_length=255)
    transaction_type = models.CharField(max_length=50, default='usage')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.snack_name} x{self.quantity}"


# ---- User Functions ----

def get_all_users():
    return User.objects.all()


def get_user_by_id(user_id):
    return User.objects.filter(id=user_id).first()


def create_user(name, email, password, role='staff'):
    if User.objects.filter(email=email.lower()).exists():
        raise ValueError('Email already registered')
    return User.objects.create(
        name=name,
        email=email.lower(),
        password_hash=make_password(password),
        role=role,
    )


def update_user(user_id, name, email, role, password=None):
    user = User.objects.get(id=user_id)
    user.name = name
    user.email = email.lower()
    user.role = role
    if password:
        user.password_hash = make_password(password)
    user.save()


def delete_user(user_id):
    User.objects.filter(id=user_id).delete()


def authenticate(email, password):
    user = User.objects.filter(email=email.lower()).first()
    if user and check_password(password, user.password_hash):
        return user
    return None


# ---- Classroom Functions ----

def get_all_classrooms():
    return Classroom.objects.all()


def get_classroom_by_id(classroom_id):
    return Classroom.objects.filter(id=classroom_id).first()


def create_classroom(name):
    Classroom.objects.create(name=name)


def update_classroom(classroom_id, name):
    Classroom.objects.filter(id=classroom_id).update(name=name)


def delete_classroom(classroom_id):
    Classroom.objects.filter(id=classroom_id).delete()


# ---- Snack Functions ----

def get_all_snacks():
    return Snack.objects.all()


def get_snack_by_id(snack_id):
    return Snack.objects.filter(id=snack_id).first()


def create_snack(name, quantity, purchase_price, quantity_per_box, supplier, low_stock_threshold):
    Snack.objects.create(
        name=name, quantity=quantity, purchase_price=purchase_price,
        quantity_per_box=quantity_per_box, supplier=supplier,
        low_stock_threshold=low_stock_threshold,
    )


def update_snack(snack_id, name, quantity, purchase_price, quantity_per_box, supplier, low_stock_threshold):
    Snack.objects.filter(id=snack_id).update(
        name=name, quantity=quantity, purchase_price=purchase_price,
        quantity_per_box=quantity_per_box, supplier=supplier,
        low_stock_threshold=low_stock_threshold,
    )


def delete_snack(snack_id):
    Snack.objects.filter(id=snack_id).delete()


# ---- Transaction Functions ----

def get_recent_transactions(limit=10):
    return Transaction.objects.order_by('-created_at')[:limit]


def record_usage(snack_id, classroom_id, quantity, user_id, user_name):
    snack = Snack.objects.get(id=snack_id)
    if snack.quantity < quantity:
        raise ValueError('Not enough quantity')
    classroom = Classroom.objects.filter(id=classroom_id).first()

    snack.quantity -= quantity
    snack.save()

    return Transaction.objects.create(
        snack_id_ref=snack_id,
        snack_name=snack.name,
        classroom_id_ref=classroom_id,
        classroom_name=classroom.name if classroom else 'Unknown',
        quantity=quantity,
        user_id_ref=user_id,
        user_name=user_name,
        transaction_type='usage',
    )


# ---- Reports ----

def get_usage_summary():
    transactions = Transaction.objects.filter(transaction_type='usage')
    usage_by_snack = {}
    usage_by_classroom = {}
    daily_trend = {}
    total_usage = 0

    for t in transactions:
        key = t.snack_name
        if key not in usage_by_snack:
            usage_by_snack[key] = {'snack_name': key, 'total': 0}
        usage_by_snack[key]['total'] += t.quantity

        ckey = t.classroom_name
        if ckey not in usage_by_classroom:
            usage_by_classroom[ckey] = {'classroom_name': ckey, 'total': 0}
        usage_by_classroom[ckey]['total'] += t.quantity

        date_str = t.created_at.strftime('%Y-%m-%d')
        daily_trend[date_str] = daily_trend.get(date_str, 0) + t.quantity

        total_usage += t.quantity

    return {
        'usage_by_snack': sorted(usage_by_snack.values(), key=lambda x: x['total'], reverse=True),
        'usage_by_classroom': sorted(usage_by_classroom.values(), key=lambda x: x['total'], reverse=True),
        'daily_trend': sorted([{'date': k, 'total': v} for k, v in daily_trend.items()], key=lambda x: x['date']),
        'total_usage': total_usage,
        'total_transactions': transactions.count(),
    }


def get_inventory_status():
    snacks = Snack.objects.all()
    low = sum(1 for s in snacks if 0 < s.quantity <= s.low_stock_threshold)
    out = sum(1 for s in snacks if s.quantity == 0)
    return {
        'total_items': snacks.count(),
        'total_quantity': sum(s.quantity for s in snacks),
        'low_stock_count': low + out,
    }


# ---- Export / Import / Clear ----

def _model_to_dict(obj, fields):
    return {f: getattr(obj, f) for f in fields}


def export_all_data():
    return {
        'users': [_model_to_dict(u, ['id', 'name', 'email', 'role']) for u in User.objects.all()],
        'classrooms': [_model_to_dict(c, ['id', 'name']) for c in Classroom.objects.all()],
        'snacks': [_model_to_dict(s, ['id', 'name', 'quantity', 'purchase_price', 'quantity_per_box', 'supplier', 'low_stock_threshold']) for s in Snack.objects.all()],
        'transactions': [_model_to_dict(t, ['id', 'snack_name', 'classroom_name', 'quantity', 'user_name', 'transaction_type']) for t in Transaction.objects.all()],
    }


def import_data(data):
    if 'classrooms' in data:
        for c in data['classrooms']:
            Classroom.objects.create(name=c.get('name', ''))
    if 'snacks' in data:
        for s in data['snacks']:
            Snack.objects.create(
                name=s.get('name', ''), quantity=s.get('quantity', 0),
                purchase_price=s.get('purchase_price', 0), quantity_per_box=s.get('quantity_per_box', 1),
                supplier=s.get('supplier', ''), low_stock_threshold=s.get('low_stock_threshold', 10),
            )
    if 'transactions' in data:
        for t in data['transactions']:
            Transaction.objects.create(
                snack_name=t.get('snack_name', ''), classroom_name=t.get('classroom_name', ''),
                quantity=t.get('quantity', 0), user_name=t.get('user_name', ''),
                transaction_type=t.get('transaction_type', 'usage'),
            )


def clear_all_data():
    User.objects.all().delete()
    Classroom.objects.all().delete()
    Snack.objects.all().delete()
    Transaction.objects.all().delete()
    seed_admin()


# ---- Seed ----

def seed_admin():
    email = os.environ.get('ADMIN_EMAIL', 'admin@snacktrack.com')
    password = os.environ.get('ADMIN_PASSWORD', 'Admin123!')
    if not User.objects.filter(email=email.lower()).exists():
        create_user('Admin', email, password, 'admin')
