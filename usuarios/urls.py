from django.urls import path
from django.contrib.auth.views import LogoutView, PasswordChangeView, PasswordChangeDoneView
from . import views

urlpatterns = [
    path('login/', views.MiLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('cambiar-password/', PasswordChangeView.as_view(
        template_name='usuarios/cambiar_password.html',
        success_url='/cambiar-password/hecho/'
    ), name='cambiar_password'),
    path('cambiar-password/hecho/', PasswordChangeDoneView.as_view(
        template_name='usuarios/password_cambiada.html'
    ), name='password_change_done'),
]
