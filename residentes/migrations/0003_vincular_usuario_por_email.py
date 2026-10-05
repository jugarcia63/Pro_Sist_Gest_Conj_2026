from django.db import migrations


def vincular_por_email(apps, schema_editor):
    Residentes = apps.get_model('residentes', 'Residentes')
    Usuario = apps.get_model('usuarios', 'Usuario')

    for residente in Residentes.objects.exclude(email__isnull=True).exclude(email=''):
        usuario = Usuario.objects.filter(email__iexact=residente.email).first()
        if usuario:
            residente.usuario_id = usuario.id
            residente.save(update_fields=['usuario'])


def revertir(apps, schema_editor):
    Residentes = apps.get_model('residentes', 'Residentes')
    Residentes.objects.update(usuario_id=None)


class Migration(migrations.Migration):

    dependencies = [
        ('residentes', '0002_residentes_usuario'),
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(vincular_por_email, revertir),
    ]
