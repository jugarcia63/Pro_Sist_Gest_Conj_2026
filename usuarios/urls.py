from django.urls import path
from django.contrib.auth.views import LogoutView, PasswordChangeDoneView
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('login/', views.MiLoginView.as_view(), name='login'),
    path('registro/', views.RegistroView.as_view(), name='registro'),
    # LogoutView solo acepta POST: el botón "Cerrar sesión" es un formulario
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('cambiar-password/', views.CambiarPasswordView.as_view(), name='cambiar_password'),
    path('cambiar-password/hecho/', PasswordChangeDoneView.as_view(
        template_name='usuarios/password_cambiada.html'
    ), name='password_change_done'),

    path('seguridad/', views.ListaGuardias.as_view(), name='lista_guardias'),
    path('seguridad/nuevo/', views.CrearGuardia.as_view(), name='crear_guardia'),
    path('seguridad/editar/<int:pk>/', views.EditarGuardia.as_view(), name='editar_guardia'),
    path('seguridad/eliminar/<int:pk>/', views.eliminar_guardia, name='eliminar_guardia'),
    path('cuentas/<int:pk>/contrasena/', views.asignar_password, name='asignar_password'),
]
