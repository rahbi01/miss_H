from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    # الصفحات العامة
    path('', views.index, name='index'),
    path('trail/<int:trail_id>/', views.trail_detail, name='trail_detail'),
    path('trail/<int:trail_id>/register/', views.public_register, name='public_register'),
    path('registration-success/<int:participant_id>/', views.registration_success, name='registration_success'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # لوحة الإدارة - المسارات
    path('dashboard/trails/', views.dashboard_trail_list, name='dashboard_trail_list'),
    path('dashboard/trails/create/', views.trail_create, name='trail_create'),
    path('dashboard/trails/<int:trail_id>/edit/', views.trail_edit, name='trail_edit'),
    path('dashboard/trails/<int:trail_id>/toggle/', views.trail_toggle_status, name='trail_toggle_status'),
    
    # لوحة الإدارة - المشاركين
    path('dashboard/trails/<int:trail_id>/participants/', views.participant_list, name='participant_list'),
    path('dashboard/trails/<int:trail_id>/participants/create/', views.participant_create, name='participant_create'),
    path('dashboard/participants/<int:participant_id>/edit/', views.participant_edit, name='participant_edit'),
    path('dashboard/participants/<int:participant_id>/delete/', views.participant_delete, name='participant_delete'),
    path('dashboard/trails/<int:trail_id>/import/', views.bulk_import_participants, name='bulk_import'),
    
    # إدارة المستخدمين (للمدير فقط)
    path('dashboard/users/', views.user_list, name='user_list'),
    path('dashboard/users/<int:user_id>/toggle/', views.user_toggle_role, name='user_toggle_role'),
    path('dashboard/users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
]
