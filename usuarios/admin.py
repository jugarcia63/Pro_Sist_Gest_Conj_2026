from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('rol', 'debe_cambiar_password')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información adicional', {'fields': ('rol',)}),
    )
    list_display = ['username', 'email', 'rol', 'is_active', 'debe_cambiar_password']
    list_filter = ['rol', 'is_active', 'is_staff']


admin.site.register(Usuario, UsuarioAdmin)
