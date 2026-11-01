from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Aviso


@login_required
def lista_avisos(request):
    avisos = list(request.user.avisos.all()[:60])
    sin_leer = [a.pk for a in avisos if not a.leido]
    # Se muestran resaltados los nuevos y quedan marcados como leídos
    if sin_leer:
        Aviso.objects.filter(pk__in=sin_leer).update(leido=True)
    return render(request, 'avisos/lista_avisos.html', {'avisos': avisos, 'nuevos': set(sin_leer)})


@login_required
def abrir_aviso(request, id_aviso):
    aviso = get_object_or_404(Aviso, pk=id_aviso, usuario=request.user)
    if not aviso.leido:
        aviso.leido = True
        aviso.save(update_fields=['leido'])
    if aviso.url and url_has_allowed_host_and_scheme(aviso.url, allowed_hosts={request.get_host()}):
        return redirect(aviso.url)
    return redirect('lista_avisos')
