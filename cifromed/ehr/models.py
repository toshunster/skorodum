# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.formats import localize
from ehr.items.fields import ThumbnailImageField, MyFileSystemStorage
#from captcha.fields import CaptchaField
from django.forms import extras
from django import forms

from django.db.models.signals import post_save
from django.dispatch import receiver

#import core
import datetime
from datetime import date, timedelta

USER_TYPE_CHOICES = (
    (0, 'Пользователь'),
    (1, 'Врач'),
    (2, 'Администратор'),
)

BLOOD_TYPE_CHOICES = (
    ('I', 'I'),
    ('II', 'II'),
    ('III', 'III'),
    ('IV', 'IV'),
)

SEX_CHOICES = (
    (u'Муж.', 'Мужчина'),
    (u'Жен.', 'Женщина'),
)

RH_FACTOR_CHOICES = (
    ( '(-)', 'Отрицательный' ),
    ( '(+)', 'Положительный' ),
)

class City(  models.Model ):
   city_id = models.IntegerField(default=0, blank=True)
   city_name = models.CharField(max_length=40, default="", blank=True)
   
   def __unicode__(self):
    return self.city_name
   
   class Meta:
     verbose_name="город"
     verbose_name_plural = "города"


class Metric(models.Model):
    head_circumference = models.FloatField(verbose_name=u"Окружность головы", blank=True, null=True)
    chest_circumference = models.FloatField(verbose_name=u"Окружность груди", blank=True, null=True)
    waist_circumference = models.FloatField(verbose_name=u"Окружность талии", blank=True, null=True)
    height = models.FloatField(verbose_name=u"Рост", blank=True, null=True)
    weight = models.FloatField(verbose_name=u"Вес", blank=True, null=True)
    body_mass_index = models.FloatField(verbose_name=u"Индекс массы тела", blank=True, null=True)

    class Meta:
        verbose_name = "метрика"
        verbose_name_plural = "метрики"


# Расширяем модель пользователя
class Profile( models.Model ):
   user = models.OneToOneField(User, on_delete=models.CASCADE)
   middle_name = models.CharField(max_length=30, null=True, blank=True, verbose_name=u"Отчество")
   birthday = models.DateField( blank = True, null = True )
   created_at = models.DateTimeField( auto_now_add = True )
   updated_at = models.DateTimeField( auto_now = True )
   avatar = ThumbnailImageField(thumb_width=400, blank = True, null = True, storage=MyFileSystemStorage(), upload_to='avatars/')
   
   sex = models.CharField(max_length=10, choices=SEX_CHOICES, null=True, blank=True, verbose_name=u"Пол")
   
   is_activate = models.BooleanField(default=True)
   activation_url = models.CharField(max_length=150, default="", blank=True)
   
   city = models.ForeignKey( City, null = True, blank = True, verbose_name=u"Город" )
   postcode = models.CharField(max_length=15, default="", blank=True, verbose_name=u"Индекс" )
   region = models.CharField(max_length=50, default="", blank=True, verbose_name=u"Регион" )
   street = models.CharField(max_length=50, default="", blank=True, verbose_name=u"Улица" )
   housing = models.CharField(max_length=50, default="", blank=True, verbose_name=u"Корпус" )
   structure = models.CharField(max_length=50, default="", blank=True, verbose_name=u"Строение" )
   house = models.CharField(max_length=50, default="", blank=True, verbose_name=u"Дом" )
   apartment = models.CharField(max_length=50, default="", blank=True, verbose_name=u"Квартира" )
   mobile_phone = models.CharField(max_length=50, default="", blank=True, verbose_name=u"Мобильный телефон" )
   home_phone = models.CharField(max_length=50, default="", blank=True, verbose_name=u"Домашний телефон" )
   
   user_type = models.IntegerField(default=0, choices=USER_TYPE_CHOICES, verbose_name=u"Тип пользователя" )
   
   metric = models.ForeignKey( Metric, null = True, blank = True, verbose_name=u"Метрики" )
   
   company = models.CharField(max_length=100, default="", blank=True, verbose_name=u"Место работы" )
   
   profession = models.CharField(max_length=100, default="", blank=True, verbose_name=u"Профессия" )
   
   position = models.CharField(max_length=100, default="", blank=True, verbose_name=u"Должность" )
   
   ehr = models.ForeignKey( 'EHR', null = True, blank = True, verbose_name=u"ЭМК" )
   
   patients = models.ManyToManyField( 'Profile', blank = True, verbose_name=u"Пациенты", related_name="digitmed_user_patients" )
   doctors = models.ManyToManyField( 'Profile', blank = True, verbose_name=u"Доктора", related_name="digitmed_user_doctors" )
   
   insurance_policy = models.CharField(max_length=40, default="", blank=True, verbose_name=u"Страховой полис" )
   SNILS = models.CharField(max_length=40, default="", blank=True, verbose_name=u"СНИЛС" )

   # Инфо для телеграма.
   telegram_id = models.CharField(max_length=40, default="", blank=True, verbose_name=u"id телеграма" )
   telegram_username = models.CharField(max_length=40, default="", blank=True, verbose_name=u"Никнейм телеграма" )
   
   def __unicode__(self):
     return self.user.username
   
   @property
   def get_beauty_mobile_phone(self):
       mobile_phone = self.mobile_phone
       country = mobile_phone[0:2]
       operator = mobile_phone[2:5]
       field1 = mobile_phone[5:8]
       field2 = mobile_phone[8:10]
       field3 = mobile_phone[10:]
       return "%s(%s)%s-%s-%s" % (country, operator, field1, field2, field3)
   
   @property
   def get_heart_rate(self):
       return self.ehr.indicators.filter(type='heart_rate').order_by('-timestamp')[0:1][0].value
   
   @property
   def get_user_name(self):
       return "%s %s %s" % ( self.user.last_name, self.user.first_name, self.middle_name )
   
   @property
   def get_age(self):
       today = date.today()
       age = today - self.birthday
       return age.days / 365
   
   @property
   def get_BMI(self):
       return "%.2f" % ( self.metric.weight / ( ( self.metric.height / 100.0 ) ** 2 ) )
   
   @property
   def get_age_str(self):
     today = date.today()
     age = today - self.birthday
     age = age.days / 365
     suffix = "лет"
     if age == 1:
       suffix = "год"
     elif age == 2 or age == 3 or age == 4:
       suffix = "года"
     elif age / 10 == 1:
       suffix = "лет"
     elif age % 10 == 1:
       suffix = "год"
     elif age % 10 == 2 or age % 10 == 3 or age % 10 == 4:
       suffix = "года"
     elif  5 <= age % 10 == 5 <= 9:
       suffix = "лет"  
     return "%d %s" % (age, suffix)
   
   class Meta:
     verbose_name="профиль"
     verbose_name_plural = "профили"

class Symptom( models.Model ):
    title = models.CharField(max_length=550, null = True, blank=True, verbose_name=u"Название")
    eng_title = models.CharField(max_length=550, null = True, blank=True, verbose_name=u"Название на англ")
    class Meta:
       verbose_name="симптом"
       verbose_name_plural = "симптомы"
    
    def __unicode__(self):
        return self.title

class Desease( models.Model ):
    title = models.CharField(max_length=550, null = True, blank=True, verbose_name=u"Название")
    description = models.TextField(max_length=550, blank = True, null = True, verbose_name=u"Описание заболевания")
    symptoms = models.ManyToManyField( Symptom, blank=True, verbose_name=u"Симптомы" )
    
    def __unicode__(self):
        return self.title
    
    class Meta:
       verbose_name="патология"
       verbose_name_plural = "патологии"

class Scheduler( models.Model ):
    start = models.DateTimeField(null = True, blank=True, verbose_name=u"Начало приёма")
    end = models.DateTimeField(null = True, blank=True, verbose_name=u"Окончание приёма")
    cabinet_number = models.CharField(max_length=550, null = True, blank=True, verbose_name=u"Номер кабинета")
    patient = models.ForeignKey( 'Profile', blank = True, null = True, verbose_name=u"Пациент", related_name="digitmed_schedule_patient" )
    doctor = models.ForeignKey( 'Profile', blank = True, null = True, verbose_name=u"Врач", related_name="digitmed_schedule_doctor" )

class MedFile(models.Model):
    name = models.CharField(max_length=550, null = True, blank=True, verbose_name=u"Заголовок")
    avatar = ThumbnailImageField(thumb_width=400, blank = True, null = True, storage=MyFileSystemStorage(), upload_to='procedures/')
    description = models.CharField(max_length=550, null = True, blank=True, verbose_name=u"Расшифровка")

class MedService(models.Model):
    name = models.CharField(max_length=550, null = True, blank=True, verbose_name=u"Название услуги")
    code = models.CharField(max_length=50, default="", null = True, blank=True,  verbose_name=u"Код услуги" )
    files = models.ManyToManyField( MedFile, blank=True, verbose_name=u"Изображения" )

class Procedure(models.Model):
    timestamp_start = models.DateTimeField(null = True, blank=True, verbose_name=u"Дата и время начала процедуры")
    timestamp_end = models.DateTimeField(null = True, blank=True, verbose_name=u"Дата и время конца процедуры")
    services = models.ManyToManyField( MedService, blank=True, verbose_name=u"Медицинская услуга" )
    

class Research(models.Model):
    timestamp_start = models.DateTimeField(null = True, verbose_name=u"Дата и время начала обследования")
    timestamp_end = models.DateTimeField(null = True, blank = True, verbose_name=u"Дата и время конца обследования")
    complaints = models.TextField(null = True, blank = True, verbose_name=u"Жалобы пациента")
    symptoms = models.TextField(null = True, blank = True, verbose_name=u"Симптомы")
    diagnose = models.TextField(null = True, blank = True, verbose_name=u"Диагноз")
    doctors = models.ManyToManyField( Profile, blank = True )
    notes = models.CharField(max_length=550, blank = True, null = True, verbose_name=u"Заметки врача" )
    procedures = models.ManyToManyField( Procedure, blank=True, verbose_name=u"Услуги" )
    class Meta:
         verbose_name="Исследование"
         verbose_name_plural = "Исследования"


class Vaccination(models.Model):
    timestamp_start = models.DateTimeField(null = True, verbose_name=u"Дата и время прививки")
    dose = models.CharField(max_length=550, blank = True, null = True, verbose_name=u"Доза")
    series = models.CharField(max_length=550, blank = True, null = True, verbose_name=u"Серия")
    drug_name = models.CharField(max_length=550, blank = True, null = True, verbose_name=u"Наименования препарата")
    reaction = models.TextField(blank = True, null = True, verbose_name=u"Реакция")
    
    class Meta:
       verbose_name="прививка"
       verbose_name_plural = "прививки"


class EHR(models.Model):
    blood_type = models.CharField( max_length=5, blank = True, null = True, choices=BLOOD_TYPE_CHOICES, verbose_name=u"Группа крови" )
    rh_factor = models.CharField( max_length=5, blank = True, null = True, choices=RH_FACTOR_CHOICES, verbose_name=u"Резус-фактор" )
    contraindications = models.TextField(max_length=550, blank = True, null = True, verbose_name=u"Противопоказания")
    anamnesis = models.TextField(max_length=550, blank = True, null = True, verbose_name=u"Анамнез")
    address = models.TextField(max_length=550, blank = True, null = True, verbose_name=u"Адрес проживания")
    researchers = models.ManyToManyField( Research, blank = True, verbose_name=u"Исследования" )
    vaccinations = models.ManyToManyField(Vaccination, blank = True, verbose_name=u"Вакцинация" )
    
    class Meta:
       verbose_name="ЭМК"
       verbose_name_plural = "ЭМК"


# Aвтолинкование профиля пользователя к пользователю при его сохранении
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(user=instance)
        ehr = EHR()
        ehr.save()
        profile.ehr = ehr
        profile.save()

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class ProfileAdmin(admin.ModelAdmin):
  list_display = ('user', 'city', 'company',)

class ResearchAdmin(admin.ModelAdmin):
  list_display = ( )

class IndicatorsAdmin(admin.ModelAdmin):
  list_display = ( )

class VaccinationAdmin(admin.ModelAdmin):
  list_display = ()

class EHRAdmin(admin.ModelAdmin):
  list_display = ('id', )
  
  class Meta:
    verbose_name="ЭМК"
    verbose_name_plural = "ЭМК"

class CityAdmin(admin.ModelAdmin):
  #list_display = ('title', 'country', 'year')
  
  class Meta:
    verbose_name="город"
    verbose_name_plural = "города"

class ProcedureAdmin(admin.ModelAdmin):
    list_display = ()

class MedServiceAdmin(admin.ModelAdmin):
    list_display = ()

class SchedulerAdmin(admin.ModelAdmin):
    list_display = ('start', 'end', 'doctor', 'patient', )

class MedFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class SymptomAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')

class DeseaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')

try:
  admin.site.register(Profile, ProfileAdmin)
  admin.site.register(Research, ResearchAdmin)
  admin.site.register(EHR, EHRAdmin)
  admin.site.register(City, CityAdmin)
  admin.site.register(Vaccination, VaccinationAdmin)
  admin.site.register(Procedure, ProcedureAdmin)
  admin.site.register(MedService, MedServiceAdmin)
  admin.site.register(Scheduler, SchedulerAdmin)
  admin.site.register(MedFile, MedFileAdmin)
  admin.site.register(Desease, DeseaseAdmin)
  admin.site.register(Symptom, SymptomAdmin)
except:
  pass

