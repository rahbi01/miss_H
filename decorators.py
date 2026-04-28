from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'الرجاء تسجيل الدخول أولاً')
            return redirect('login')
        
        if hasattr(request.user, 'profile') and request.user.profile.is_manager():
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'عذراً، هذه الصفحة متاحة للمديرين فقط')
            return redirect('dashboard_trail_list')
    return wrapper

def staff_or_admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'الرجاء تسجيل الدخول أولاً')
            return redirect('login')
        
        if request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role in ['admin', 'user']):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'عذراً، هذه الصفحة متاحة للموظفين فقط')
            return redirect('index')
    return wrapper
