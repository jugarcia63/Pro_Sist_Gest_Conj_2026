from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usuarios.urls')),
    path('residentes/', include('residentes.urls')),
    path('vehiculos/', include('vehiculos.urls')),
    path('visitantes/', include('visitantes.urls')),
    path('reservas/', include('reservas.urls')),
    path('pagos/', include('pagos.urls')),
    path('reportes/', include('reportes.urls')),
]