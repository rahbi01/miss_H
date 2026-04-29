from django import forms
from django.contrib.auth.models import User
from .models import Trail, Participant

class TrailForm(forms.ModelForm):
    distance = forms.FloatField(
        label='المسافة (كم)',
        widget=forms.NumberInput(attrs={'step': '0.5', 'class': 'form-control'})
    )
    
    class Meta:
        model = Trail
        fields = [
            'name', 'location', 'date', 'distance', 'level',
            'meeting_time', 'departure_time', 'duration_hours', 'audience',
            'min_age', 'meeting_location', 'google_maps_url', 'latitude',
            'longitude', 'status'
        ]  # تم إزالة trail_number من القائمة
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'meeting_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'departure_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'duration_hours': forms.NumberInput(attrs={'step': '0.5', 'class': 'form-control'}),
            'min_age': forms.NumberInput(attrs={'min': '15', 'class': 'form-control'}),
            'meeting_location': forms.TextInput(attrs={'class': 'form-control'}),
            'google_maps_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://maps.google.com/...'}),
            'latitude': forms.NumberInput(attrs={'step': '0.0000001', 'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'step': '0.0000001', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['name', 'phone', 'notes', 'payment_status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'payment_status': forms.Select(attrs={'class': 'form-control'}),
        }

class ParticipantPublicForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['name', 'phone', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الاسم الكامل'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr', 'placeholder': '05xxxxxxxx'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ملاحظات إضافية (اختياري)'}),
        }

class BulkImportForm(forms.Form):
    names_text = forms.CharField(
        label='أسماء المشاركين (اسم واحد في كل سطر)',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'أحمد محمد\nسارة علي\nخالد عبدالله...'})
    )
    excel_file = forms.FileField(
        label='ملف Excel',
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )

class UserRoleForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'password', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
