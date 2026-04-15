from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboards
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/classrooms/', views.admin_dashboard, {'default_tab': 'classrooms'}, name='admin_classrooms'),
    path('admin-dashboard/inventory/', views.admin_dashboard, {'default_tab': 'inventory'}, name='admin_inventory'),
    path('admin-dashboard/data/', views.admin_dashboard, {'default_tab': 'data'}, name='admin_data'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),

    # User CRUD
    path('users/add/', views.user_form, name='add_user'),
    path('users/edit/<str:user_id>/', views.user_form, name='edit_user'),
    path('users/delete/<str:user_id>/', views.delete_user, name='delete_user'),

    # Classroom CRUD
    path('classrooms/add/', views.classroom_form, name='add_classroom'),
    path('classrooms/edit/<str:classroom_id>/', views.classroom_form, name='edit_classroom'),
    path('classrooms/delete/<str:classroom_id>/', views.delete_classroom, name='delete_classroom'),

    # Snack CRUD
    path('snacks/add/', views.snack_form, name='add_snack'),
    path('snacks/edit/<str:snack_id>/', views.snack_form, name='edit_snack'),
    path('snacks/delete/<str:snack_id>/', views.delete_snack, name='delete_snack'),

    # Staff actions
    path('usage/record/', views.record_usage_view, name='record_usage'),

    # Data management
    path('data/export/', views.export_data, name='export_data'),
    path('data/import/', views.import_data_view, name='import_data'),
    path('data/clear/', views.clear_data, name='clear_data'),

    # Code viewer
    path('code/', views.code_view, name='code_view'),
    path('download/', views.download_zip, name='download_zip'),
]
