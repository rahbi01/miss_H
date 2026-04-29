from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

class Trail(models.Model):
    LEVEL_CHOICES = [
        ('easy', '🟢 سهل'),
        ('medium', '🟡 وسط'),
        ('hard', '🔴 صعب'),
    ]
    
    AUDIENCE_CHOICES = [
        ('all', 'الجميع'),
        ('male_only', 'رجال فقط'),
        ('female_only', 'نساء فقط'),
    ]
    
    STATUS_CHOICES = [
        ('active', '🟢 نشط - متاح للتسجيل'),
        ('inactive', '🔴 غير نشط - التسجيل مغلق'),
    ]

    trail_number = models.CharField('رقم المسار', max_length=20, unique=True, blank=True)
    name = models.CharField('اسم المسار', max_length=200)
    location = models.CharField('المكان', max_length=300)
    date = models.DateField('التاريخ')
    distance = models.FloatField('المسافة (كم)', validators=[MinValueValidator(0)])
    level = models.CharField('المستوى', max_length=10, choices=LEVEL_CHOICES)
    meeting_time = models.TimeField('وقت التجمع')
    departure_time = models.TimeField('وقت الانطلاق')
    duration_hours = models.FloatField('الوقت المستغرق (ساعات)', validators=[MinValueValidator(0.5)])
    audience = models.CharField('الفئة المستهدفة', max_length=15, choices=AUDIENCE_CHOICES, default='all')
    min_age = models.IntegerField('السن الأدنى', default=15, validators=[MinValueValidator(15)])
    meeting_location = models.CharField('موقع التجمع', max_length=500)
    google_maps_url = models.URLField('رابط خرائط جوجل', blank=True)
    latitude = models.DecimalField('خط العرض', max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField('خط الطول', max_digits=10, decimal_places=7, null=True, blank=True)
    status = models.CharField('الحالة', max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'trail_number']
        verbose_name = 'مسار'
        verbose_name_plural = 'المسارات'

    def save(self, *args, **kwargs):
        """توليد رقم المسار تلقائياً إذا لم يكن موجوداً"""
        if not self.trail_number:
            last_trail = Trail.objects.all().order_by('-trail_number').first()
            if last_trail and last_trail.trail_number:
                # استخراج الرقم من آخر مسار (متوقع أن يكون الرقم مثل TR001 أو 001)
                try:
                    last_number = int(''.join(filter(str.isdigit, last_trail.trail_number)))
                    new_number = last_number + 1
                    self.trail_number = f"TR{new_number:03d}"  # تنسيق مثل TR001, TR002
                except ValueError:
                    self.trail_number = "TR001"
            else:
                self.trail_number = "TR001"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.trail_number} - {self.name} ({self.date})"
    
    @property
    def participant_count(self):
        return self.participants.filter(is_active=True).count()
    
    @property
    def can_register(self):
        return self.status == 'active'

class Participant(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', '❌ لم يتم الدفع'),
        ('paid', '✅ مدفوع'),
        ('exempt', '🟢 معفي'),
    ]
    
    trail = models.ForeignKey(Trail, on_delete=models.CASCADE, related_name='participants')
    name = models.CharField('الاسم الكامل', max_length=200)
    phone = models.CharField('رقم الهاتف', max_length=20)
    notes = models.TextField('ملاحظات', blank=True)
    payment_status = models.CharField('حالة الدفع', max_length=10, choices=PAYMENT_STATUS_CHOICES, default='unpaid')
    registered_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField('نشط', default=True)
    
    class Meta:
        ordering = ['registered_at']
        verbose_name = 'مشارك'
        verbose_name_plural = 'المشاركون'
    
    def __str__(self):
        return f"{self.name} - {self.trail.name}"
    
    def get_public_info(self):
        """ معلومات عامة بدون رقم الهاتف """
        return {
            'name': self.name,
            'registered_at': self.registered_at,
            'payment_status': self.payment_status,
        }

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'مدير - صلاحية كاملة'),
        ('user', 'مستخدم - إدارة المشاركين فقط'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField('الدور', max_length=10, choices=ROLE_CHOICES, default='user')
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def is_manager(self):
        return self.role == 'admin'
