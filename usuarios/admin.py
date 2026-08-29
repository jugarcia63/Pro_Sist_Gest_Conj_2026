from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('rol',)}),
    )
    list_display = ['username', 'email', 'rol', 'is_staff']

admin.site.register(Usuario, UsuarioAdmin)
