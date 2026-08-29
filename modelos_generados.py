# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AdjuntosReporte(models.Model):
    id_adjunto = models.IntegerField(db_column='Id_Adjunto')  # Field name made lowercase.
    id_reporte_fk = models.IntegerField(db_column='Id_Reporte_FK', blank=True, null=True)  # Field name made lowercase.
    nombre_archivo = models.CharField(db_column='Nombre_Archivo', max_length=150, blank=True, null=True)  # Field name made lowercase.
    url_archivo = models.CharField(db_column='Url_Archivo', max_length=255, blank=True, null=True)  # Field name made lowercase.
    tipo_archivo = models.CharField(db_column='Tipo_Archivo', max_length=50, blank=True, null=True)  # Field name made lowercase.
    fecha_subida = models.DateTimeField(db_column='Fecha_Subida', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'adjuntos_reporte'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('UsuariosUsuario', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Pagos(models.Model):
    id_pago = models.IntegerField(db_column='Id_Pago')  # Field name made lowercase.
    id_residente_fk = models.IntegerField(db_column='Id_Residente_FK', blank=True, null=True)  # Field name made lowercase.
    tipo_pago = models.CharField(db_column='Tipo_Pago', max_length=20, blank=True, null=True)  # Field name made lowercase.
    id_reserva_fk = models.IntegerField(db_column='Id_Reserva_FK', blank=True, null=True)  # Field name made lowercase.
    mes_año = models.DateTimeField(db_column='Mes_Año', blank=True, null=True)  # Field name made lowercase.
    valor = models.DecimalField(db_column='Valor', max_digits=12, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    fecha_vencimiento = models.DateField(db_column='Fecha_Vencimiento', blank=True, null=True)  # Field name made lowercase.
    fecha_pago = models.DateField(db_column='Fecha_Pago', blank=True, null=True)  # Field name made lowercase.
    metodo_pago = models.CharField(db_column='Metodo_Pago', max_length=30, blank=True, null=True)  # Field name made lowercase.
    comprobante_url = models.CharField(db_column='Comprobante_Url', max_length=255, blank=True, null=True)  # Field name made lowercase.
    estado = models.CharField(db_column='Estado', max_length=20, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'pagos'


class Reportes(models.Model):
    id_reportes = models.IntegerField(db_column='Id_Reportes')  # Field name made lowercase.
    id_residente_fk = models.IntegerField(db_column='Id_Residente_FK', blank=True, null=True)  # Field name made lowercase.
    categoria = models.CharField(db_column='Categoria', max_length=50, blank=True, null=True)  # Field name made lowercase.
    descripcion = models.TextField(db_column='Descripcion', blank=True, null=True)  # Field name made lowercase.
    fecha_reporte = models.DateTimeField(db_column='Fecha_Reporte', blank=True, null=True)  # Field name made lowercase.
    estado = models.CharField(db_column='Estado', max_length=20, blank=True, null=True)  # Field name made lowercase.
    asignado_a_fk = models.IntegerField(db_column='Asignado_a_FK', blank=True, null=True)  # Field name made lowercase.
    fecha_resolucion = models.DateTimeField(db_column='Fecha_Resolucion', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'reportes'


class Reservas(models.Model):
    id_reservas = models.IntegerField(db_column='Id_Reservas')  # Field name made lowercase.
    id_zona_fk = models.IntegerField(db_column='Id_Zona_FK', blank=True, null=True)  # Field name made lowercase.
    id_unidad_fk = models.IntegerField(db_column='Id_Unidad_FK', blank=True, null=True)  # Field name made lowercase.
    fecha_reserva = models.DateTimeField(db_column='Fecha_Reserva', blank=True, null=True)  # Field name made lowercase.
    fecha_inicio = models.DateTimeField(db_column='Fecha_Inicio', blank=True, null=True)  # Field name made lowercase.
    fecha_fin = models.DateTimeField(db_column='Fecha_Fin', blank=True, null=True)  # Field name made lowercase.
    estado = models.CharField(db_column='Estado', max_length=20, blank=True, null=True)  # Field name made lowercase.
    observaciones = models.TextField(db_column='Observaciones', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'reservas'


class Residentes(models.Model):
    id_residente = models.IntegerField(db_column='Id_Residente')  # Field name made lowercase.
    tipo_documento = models.CharField(db_column='Tipo_Documento', max_length=100, blank=True, null=True)  # Field name made lowercase.
    num_documento = models.CharField(db_column='Num_Documento', max_length=100, blank=True, null=True)  # Field name made lowercase.
    nombres = models.CharField(db_column='Nombres', max_length=255, blank=True, null=True)  # Field name made lowercase.
    apellidos = models.CharField(db_column='Apellidos', max_length=255, blank=True, null=True)  # Field name made lowercase.
    telefono = models.CharField(db_column='Telefono', max_length=255, blank=True, null=True)  # Field name made lowercase.
    email = models.CharField(db_column='Email', max_length=255, blank=True, null=True)  # Field name made lowercase.
    fecha_registro = models.DateTimeField(db_column='Fecha_Registro', blank=True, null=True)  # Field name made lowercase.
    estado = models.IntegerField(db_column='Estado', blank=True, null=True)  # Field name made lowercase.
    id_unidad_fk = models.IntegerField(db_column='Id_Unidad_FK', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'residentes'


class Roles(models.Model):
    id_rol = models.IntegerField(db_column='Id_Rol')  # Field name made lowercase.
    nombre = models.CharField(db_column='Nombre', max_length=100, blank=True, null=True)  # Field name made lowercase.
    descripcion = models.CharField(db_column='Descripcion', max_length=255, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'roles'


class Unidades(models.Model):
    id_unidad = models.IntegerField(db_column='Id_Unidad')  # Field name made lowercase.
    torre = models.CharField(db_column='Torre', max_length=10, blank=True, null=True)  # Field name made lowercase.
    apto = models.CharField(db_column='Apto', max_length=10, blank=True, null=True)  # Field name made lowercase.
    piso = models.IntegerField(db_column='Piso', blank=True, null=True)  # Field name made lowercase.
    area = models.DecimalField(db_column='Area', max_digits=8, decimal_places=2, blank=True, null=True)  # Field name made lowercase.
    id_residente_fk = models.IntegerField(db_column='Id_Residente_FK', blank=True, null=True)  # Field name made lowercase.
    estado = models.IntegerField(db_column='Estado', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'unidades'


class Usuario(models.Model):
    id_usuario = models.IntegerField(db_column='Id_Usuario')  # Field name made lowercase.
    nombre = models.CharField(db_column='Nombre', max_length=100, blank=True, null=True)  # Field name made lowercase.
    email = models.CharField(db_column='Email', max_length=100, blank=True, null=True)  # Field name made lowercase.
    contraseña = models.CharField(db_column='Contraseña', max_length=255, blank=True, null=True)  # Field name made lowercase.
    id_rol_fk = models.IntegerField(db_column='Id_Rol_FK', blank=True, null=True)  # Field name made lowercase.
    id_residente_fk = models.IntegerField(db_column='Id_Residente_FK', blank=True, null=True)  # Field name made lowercase.
    estado = models.IntegerField(db_column='Estado', blank=True, null=True)  # Field name made lowercase.
    fecha_creacion = models.DateTimeField(db_column='Fecha_creacion', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'usuario'


class UsuariosUsuario(models.Model):
    id = models.BigAutoField(primary_key=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()
    rol = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'usuarios_usuario'


class UsuariosUsuarioGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(UsuariosUsuario, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'usuarios_usuario_groups'
        unique_together = (('usuario', 'group'),)


class UsuariosUsuarioUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(UsuariosUsuario, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'usuarios_usuario_user_permissions'
        unique_together = (('usuario', 'permission'),)


class Vehiculos(models.Model):
    id_vehiculo = models.IntegerField(db_column='Id_Vehiculo')  # Field name made lowercase.
    placa = models.CharField(db_column='Placa', max_length=10, blank=True, null=True)  # Field name made lowercase.
    marca = models.CharField(db_column='Marca', max_length=50, blank=True, null=True)  # Field name made lowercase.
    modelo = models.CharField(db_column='Modelo', max_length=50, blank=True, null=True)  # Field name made lowercase.
    color = models.CharField(db_column='Color', max_length=30, blank=True, null=True)  # Field name made lowercase.
    id_residente_fk = models.IntegerField(db_column='Id_Residente_FK', blank=True, null=True)  # Field name made lowercase.
    tipo_vehiculo = models.CharField(db_column='Tipo_Vehiculo', max_length=20, blank=True, null=True)  # Field name made lowercase.
    estado = models.CharField(db_column='Estado', max_length=20, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'vehiculos'
