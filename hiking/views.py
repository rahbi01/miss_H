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
    """ عرض جميع المسارات النشطة """
    trails = Trail.objects.filter(status='active')
    return render(request, 'index.html', {'trails': trails})

def trail_detail(request, trail_id):
    """ عرض تفاصيل المسار وقائمة المشاركين (بدون أرقام هواتف) """
    trail = get_object_or_404(Trail, id=trail_id)
    participants = trail.participants.filter(is_active=True)
    
    # معلومات المشاركين العامة (بدون رقم الهاتف)
    public_participants = [{'name': p.name, 'registered_at': p.registered_at} for p in participants]
    
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
    
    if not trail.can_register:
        messages.error(request, 'عذراً، هذا المسار غير متاح للتسجيل حالياً')
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
    trails = Trail.objects.all()
    
    # فلترة حسب الصلاحيات
    if hasattr(request.user, 'profile') and request.user.profile.role == 'user':
        # المستخدم العادي يرى كل المسارات ولكن لا يستطيع تعديلها
        pass
    
    return render(request, 'dashboard/trail_list.html', {'trails': trails})

@login_required
@admin_required
def trail_create(request):
    """ إضافة مسار جديد (للمدير فقط) """
    if request.method == 'POST':
        form = TrailForm(request.POST)
        if form.is_valid():
            trail = form.save()
            messages.success(request, f'تم إضافة المسار {trail.name} بنجاح')
            return redirect('dashboard_trail_list')
    else:
        form = TrailForm()
    
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
    trail.status = 'inactive' if trail.status == 'active' else 'active'
    trail.save()
    messages.success(request, f'تم {"تعطيل" if trail.status == "inactive" else "تفعيل"} المسار {trail.name}')
    return redirect('dashboard_trail_list')

@login_required
@staff_or_admin_required
def participant_list(request, trail_id):
    """ إدارة المشاركين في مسار معين """
    trail = get_object_or_404(Trail, id=trail_id)
    participants = trail.participants.filter(is_active=True)
    
    # المستخدم العادي يرى كل البيانات بما فيها رقم الهاتف
    # المدير يرى نفس الشيء
    
    if request.method == 'POST':
        # تحديث حالة الدفع لعدة مشاركين
        participant_ids = request.POST.getlist('selected_participants')
        payment_status = request.POST.get('bulk_payment_status')
        if participant_ids and payment_status:
            Participant.objects.filter(id__in=participant_ids).update(payment_status=payment_status)
            messages.success(request, f'تم تحديث حالة الدفع لـ {len(participant_ids)} مشارك')
            return redirect('participant_list', trail_id=trail.id)
    
    return render(request, 'dashboard/participant_list.html', {
        'trail': trail,
        'participants': participants,
    })

@login_required
@staff_or_admin_required
def participant_create(request, trail_id):
    """ إضافة مشارك جديد """
    trail = get_object_or_404(Trail, id=trail_id)
    if request.method == 'POST':
        form = ParticipantForm(request.POST)
        if form.is_valid():
            participant = form.save(commit=False)
            participant.trail = trail
            participant.save()
            messages.success(request, f'تم إضافة {participant.name} بنجاح')
            return redirect('participant_list', trail_id=trail.id)
    else:
        form = ParticipantForm()
    
    return render(request, 'dashboard/participant_form.html', {
        'form': form,
        'trail': trail,
        'title': 'إضافة مشارك جديد'
    })

@login_required
@staff_or_admin_required
def participant_edit(request, participant_id):
    """ تعديل بيانات مشارك """
    participant = get_object_or_404(Participant, id=participant_id)
    trail = participant.trail
    
    if request.method == 'POST':
        form = ParticipantForm(request.POST, instance=participant)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تعديل بيانات {participant.name} بنجاح')
            return redirect('participant_list', trail_id=trail.id)
    else:
        form = ParticipantForm(instance=participant)
    
    return render(request, 'dashboard/participant_form.html', {
        'form': form,
        'trail': trail,
        'participant': participant,
        'title': 'تعديل بيانات مشارك'
    })

@login_required
@staff_or_admin_required
def participant_delete(request, participant_id):
    """ حذف مشارك (ناعم - تعطيل) """
    participant = get_object_or_404(Participant, id=participant_id)
    trail = participant.trail
    participant.is_active = False
    participant.save()
    messages.success(request, f'تم حذف {participant.name} بنجاح')
    return redirect('participant_list', trail_id=trail.id)

@login_required
@staff_or_admin_required
def bulk_import_participants(request, trail_id):
    """ استيراد عدة مشاركين دفعة واحدة """
    trail = get_object_or_404(Trail, id=trail_id)
    
    if request.method == 'POST':
        form = BulkImportForm(request.POST, request.FILES)
        if form.is_valid():
            names_text = form.cleaned_data.get('names_text')
            excel_file = request.FILES.get('excel_file')
            
            participants_to_create = []
            imported_count = 0
            
            # استيراد من النص
            if names_text:
                names = [n.strip() for n in names_text.split('\n') if n.strip()]
                for name in names:
                    participants_to_create.append(Participant(
                        trail=trail,
                        name=name,
                        phone='',
                        notes='تم الاستيراد دفعة واحدة'
                    ))
                imported_count = len(participants_to_create)
            
            # استيراد من Excel
            elif excel_file:
                wb = openpyxl.load_workbook(excel_file)
                sheet = wb.active
                for row in sheet.iter_rows(min_row=2, values_only=True):  # تخطي رأس الجدول
                    if row[0]:  # الاسم موجود
                        name = str(row[0]) if row[0] else ''
                        phone = str(row[1]) if len(row) > 1 and row[1] else ''
                        participants_to_create.append(Participant(
                            trail=trail,
                            name=name,
                            phone=phone,
                            notes='تم الاستيراد من Excel'
                        ))
                imported_count = len(participants_to_create)
            
            if participants_to_create:
                Participant.objects.bulk_create(participants_to_create)
                messages.success(request, f'تم استيراد {imported_count} مشارك بنجاح')
            else:
                messages.warning(request, 'لم يتم العثور على بيانات للاستيراد')
            
            return redirect('participant_list', trail_id=trail.id)
    else:
        form = BulkImportForm()
    
    return render(request, 'dashboard/bulk_import.html', {
        'form': form,
        'trail': trail,
    })

@login_required
@admin_required
def user_list(request):
    """ إدارة المستخدمين (المديرين والمستخدمين) """
    users = User.objects.filter(is_superuser=False).exclude(username='admin')
    
    if request.method == 'POST':
        form = UserRoleForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
                email=form.cleaned_data.get('email', '')
            )
            role = request.POST.get('role', 'user')
            UserProfile.objects.create(user=user, role=role)
            messages.success(request, f'تم إضافة المستخدم {user.username} بنجاح')
            return redirect('user_list')
    else:
        form = UserRoleForm()
    
    return render(request, 'dashboard/user_list.html', {
        'users': users,
        'form': form,
    })

@login_required
@admin_required
def user_toggle_role(request, user_id):
    """ تغيير دور المستخدم """
    user = get_object_or_404(User, id=user_id)
    profile = user.profile
    new_role = 'admin' if profile.role == 'user' else 'user'
    profile.role = new_role
    profile.save()
    messages.success(request, f'تم تغيير دور {user.username} إلى {"مدير" if new_role == "admin" else "مستخدم"}')
    return redirect('user_list')

@login_required
@admin_required
def user_delete(request, user_id):
    """ حذف مستخدم """
    user = get_object_or_404(User, id=user_id)
    username = user.username
    user.delete()
    messages.success(request, f'تم حذف المستخدم {username}')
    return redirect('user_list')
