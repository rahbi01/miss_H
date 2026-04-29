from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from .models import Trail, Participant, UserProfile
from .forms import TrailForm, ParticipantForm, ParticipantPublicForm, BulkImportForm, UserRoleForm
from .decorators import admin_required, staff_or_admin_required
import openpyxl
from io import BytesIO
from django.contrib.auth.models import User

# ==================== الصفحات العامة ====================

def index(request):
    """ عرض جميع المسارات (النشطة وغير النشطة) مع تمييزها """
    # جلب جميع المسارات مرتبة من الأحدث للأقدم
    all_trails = Trail.objects.all().order_by('-date')
    
    # فصل المسارات إلى نشطة وغير نشطة
    active_trails = all_trails.filter(status='active')
    inactive_trails = all_trails.filter(status='inactive')
    
    return render(request, 'index.html', {
        'active_trails': active_trails,
        'inactive_trails': inactive_trails,
    })

def trail_detail(request, trail_id):
    """ عرض تفاصيل المسار وقائمة المشاركين (بدون أرقام هواتف) """
    trail = get_object_or_404(Trail, id=trail_id)
    participants = trail.participants.filter(is_active=True)
    
    # معلومات المشاركين العامة (بدون رقم الهاتف)
    public_participants = [{'name': p.name, 'registered_at': p.registered_at} for p in participants]
    
    # التحقق من إمكانية التسجيل (فقط للمسارات النشطة)
    can_register = trail.can_register
    
    return render(request, 'trail_detail.html', {
        'trail': trail,
        'participants': public_participants,
        'participant_count': len(public_participants),
        'can_register': can_register,
    })

def public_register(request, trail_id):
    """ صفحة تسجيل المشارك العام """
    trail = get_object_or_404(Trail, id=trail_id)
    
    # التأكد من أن المسار نشط قبل السماح بالتسجيل
    if not trail.can_register:
        messages.error(request, 'عذراً، هذا المسار غير متاح للتسجيل حالياً (المسار غير نشط)')
        return redirect('trail_detail', trail_id=trail.id)
    
    if request.method == 'POST':
        form = ParticipantPublicForm(request.POST)
        if form.is_valid():
            participant = form.save(commit=False)
            participant.trail = trail
            participant.save()
            messages.success(request, f'تم تسجيل {participant.name} بنجاح في مسار {trail.name}')
            return redirect('registration_success', participant_id=participant.id)
    else:
        form = ParticipantPublicForm()
    
    return render(request, 'register.html', {
        'trail': trail,
        'form': form,
    })

def registration_success(request, participant_id):
    """ صفحة تأكيد نجاح التسجيل """
    participant = get_object_or_404(Participant, id=participant_id)
    return render(request, 'registration_success.html', {'participant': participant})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard_trail_list')
            return redirect(next_url)
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('index')

# ==================== لوحة الإدارة ====================

@login_required
@staff_or_admin_required
def dashboard_trail_list(request):
    """ قائمة المسارات (للمدير والمستخدم) """
    trails = Trail.objects.all().order_by('-date')
    return render(request, 'dashboard/trail_list.html', {'trails': trails})

@login_required
@admin_required
def trail_create(request):
    """ إضافة مسار جديد (للمدير فقط) - رقم المسار يتولد تلقائياً """
    if request.method == 'POST':
        form = TrailForm(request.POST)
        if form.is_valid():
            trail = form.save(commit=False)
            # رقم المسار سيتولد تلقائياً في دالة save() في الموديل
            trail.save()
            messages.success(request, f'تم إضافة المسار {trail.name} برقم {trail.trail_number} بنجاح')
            return redirect('dashboard_trail_list')
    else:
        form = TrailForm()
        # عرض آخر رقم مسار للمستخدم كمرجع
        last_trail = Trail.objects.all().order_by('-trail_number').first()
        next_number = "TR001"
        if last_trail and last_trail.trail_number:
            try:
                last_num = int(''.join(filter(str.isdigit, last_trail.trail_number)))
                next_number = f"TR{last_num + 1:03d}"
            except:
                pass
        
        messages.info(request, f'سيتم توليد رقم المسار تلقائياً: {next_number}')
    
    return render(request, 'dashboard/trail_form.html', {'form': form, 'title': 'إضافة مسار جديد'})

@login_required
@admin_required
def trail_edit(request, trail_id):
    """ تعديل مسار (للمدير فقط) """
    trail = get_object_or_404(Trail, id=trail_id)
    if request.method == 'POST':
        form = TrailForm(request.POST, instance=trail)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تعديل المسار {trail.name} بنجاح')
            return redirect('dashboard_trail_list')
    else:
        form = TrailForm(instance=trail)
    
    return render(request, 'dashboard/trail_form.html', {'form': form, 'title': 'تعديل المسار'})

@login_required
@admin_required
def trail_toggle_status(request, trail_id):
    """ تعطيل أو تفعيل مسار """
    trail = get_object_or_404(Trail, id=trail_id)
    old_status = trail.status
    trail.status = 'inactive' if trail.status == 'active' else 'active'
    trail.save()
    
    if trail.status == 'active':
        messages.success(request, f'تم تفعيل المسار {trail.name} - أصبح متاحاً للتسجيل')
    else:
        messages.warning(request, f'تم تعطيل المسار {trail.name} - لن يتمكن المشاركون من التسجيل فيه')
    
    return redirect('dashboard_trail_list')

# باقي الـ views كما هي (participant_list, participant_create, participant_edit, participant_delete, bulk_import_participants, user_list, user_toggle_role, user_delete)
# ... (الأكواد الأخرى كما هي من المرة السابقة)
