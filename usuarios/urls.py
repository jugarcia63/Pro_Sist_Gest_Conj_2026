from django.urls import path 
from django.contrib.auth.views import LogoutView 
from . import views 
 
urlpatterns = [ 
    path('login/', views.MiLoginView.as_view(), name='login'), 
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'), 
    path('dashboard/', views.dashboard, name='dashboard'), 
] 
