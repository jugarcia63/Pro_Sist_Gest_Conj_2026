from django.urls import path
from django.contrib.auth.views import LogoutView, PasswordChangeDoneView
from . import views

urlpatterns = [
    path('login/', views.MiLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('cambiar-password/', views.CambiarPasswordView.as_view(), name='cambiar_password'),
    path('cambiar-password/hecho/', PasswordChangeDoneView.as_view(
        template_name='usuarios/password_cambiada.html'
    ), name='password_change_done'),
]
