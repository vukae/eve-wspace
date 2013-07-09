from Map.models import *
from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.forms import ModelForm
from django import forms

class SystemAdmin(admin.ModelAdmin):
    fields = ['occupied', 'info']

class FCFTWUserAddForm(UserCreationForm):
    username = forms.CharField()


class FCFTWUserAdminForm(UserChangeForm):
    username = forms.CharField()

class FCFTWUserAdmin(UserAdmin):
    form = FCFTWUserAdminForm
    add_form = FCFTWUserAddForm

admin.site.unregister(User)
admin.site.register(User, FCFTWUserAdmin)

admin.site.register(System, SystemAdmin)
admin.site.register(Map)
admin.site.register(MapSystem)
admin.site.register(Signature)
admin.site.register(SignatureType)
admin.site.register(Wormhole)
