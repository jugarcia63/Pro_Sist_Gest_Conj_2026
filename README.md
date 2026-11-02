# Sistema de Gestión de Conjuntos Residenciales

Proyecto de Ingeniería de Software desarrollado en Django, para la administración integral de un conjunto residencial: residentes, vehículos, visitantes, reservas de zonas comunes, pagos y reportes de daños.

## Integrantes

- Juan Esteban Vila Aparicio
- Juan David Garcia

## Tecnologías

- Python 3.14
- Django 5.2
- PostGreSQL
- HTML / CSS

## Roles del sistema

| Rol | Accesos |
|---|---|
| **Residente** | Sus pagos, sus reservas, sus reportes, sus vehículos, los paquetes de su unidad |
| **Administrador** | Gestión completa: residentes, vehículos, zonas comunes, reportes, estado de pagos, tarifa del parqueadero |
| **Seguridad** | Registro de visitantes, parqueadero de visitantes, paquetes, consulta de vehículos |

## Módulos

- Gestión de residentes y unidades habitacionales
- Gestión de vehículos (carros y motos, con validación de formato de placa)
- Registro de visitantes: solo nombres, apellidos, cédula, hora de entrada y la unidad que visita (no se registra salida)
- Parqueadero de visitantes: placa asociada a una unidad, contador de tiempo en vivo y cobro al salir (horas gratis + cada hora iniciada; tarifa editable por el administrador)
- Paquetes en portería: registro por número de guía y destinatario, entrega con hora, quién lo recoge y qué vigilante lo entregó; el residente ve en su panel los paquetes de su unidad
- Reservas de zonas comunes (con validación de horarios y solapamiento)
  - Cobro por hora en las zonas que lo ameritan (cada hora iniciada se cobra completa, sin horas gratis) y servicio de limpieza opcional; la factura se genera al aprobar la reserva
  - Inventario de implementos por zona; al terminar, portería recibe la zona, revisa faltantes, daños y aseo, y se genera la multa automáticamente
  - Página de inventario (administración y portería): total, disponibles y en reparación por implemento, con historial. Lo perdido sale del inventario y lo dañado queda en reparación (no se presta) hasta que el administrador lo marca como reparado, lo da de baja o registra una compra
  - Las reservas pendientes que nadie aprobó antes de su horario pasan solas a *Vencida*; las aprobadas que portería no recibió en 3 días se cierran solas
  - Comprobante de la reserva descargable en PDF
  - Calendario de disponibilidad por zona (próximos 7 días); un clic en una hora libre abre la reserva
- Pagos con pasarela simulada
  - Reporte de recaudo por mes y concepto (administración, reservas, multas, parqueadero), descargable en Excel (CSV) y PDF
- Avisos dentro de la app (campana): paquete en portería, reserva aprobada o rechazada, multa y factura nueva
- Correos de aviso opcionales con la API de Brevo (Render gratis bloquea SMTP): se activan con las variables `BREVO_API_KEY` y `CORREO_REMITENTE`; al crear la cuenta de un residente se le puede enviar su usuario y contraseña temporal
- Reportes de daños

## Valores y tarifas

Estos son los valores con los que arranca el sistema. Los que dicen *editable* los cambia el administrador desde la página; un cambio no afecta lo que ya se cobró o reservó (la tarifa se copia en el momento del ingreso o de la reserva).

### Zonas comunes

Se cobran las **horas reservadas** y cada hora iniciada cuenta completa (2 h 10 min = 3 horas), sin horas gratis. La factura se genera cuando el administrador aprueba la reserva.

| Zona | Capacidad | Valor por hora | Servicio de limpieza (opcional) |
|---|---|---|---|
| Salón social | 60 personas | $25.000 | $40.000 |
| Zona BBQ | 20 personas | $15.000 | $30.000 |
| Piscina | 30 personas | Gratis | No aplica |
| Gimnasio | 12 personas | Gratis | No aplica |
| Cancha múltiple | 14 personas | Gratis | No aplica |
| Parque infantil | 25 personas | Gratis | No aplica |
| Salón de juegos | 15 personas | Gratis | No aplica |

*Editable en Zonas comunes → Editar.* Una reserva dura como máximo **12 horas** y no puede cruzarse con otra de la misma zona.

**Ejemplo:** Zona BBQ de 12:00 a 16:00 con limpieza = 4 × $15.000 + $30.000 = **$90.000**.

### Inventario y multas por la entrega

Al terminar la reserva, portería recibe la zona y cuenta los implementos. Lo que falte o llegue dañado se cobra por su **valor de reposición**. Si el residente no tomó el servicio de limpieza y deja la zona sucia, se le cobra el valor de la limpieza. La multa se genera sola y vence a los **15 días**.

| Zona | Implemento | Cantidad | Valor de reposición c/u |
|---|---|---|---|
| Salón social | Mesas plegables | 10 | $180.000 |
| | Sillas | 60 | $45.000 |
| | Manteles | 10 | $35.000 |
| | Equipo de sonido con 2 parlantes | 1 | $900.000 |
| | Micrófono inalámbrico | 1 | $150.000 |
| | Cafetera grande | 1 | $250.000 |
| | Video beam con telón | 1 | $1.800.000 |
| | Extensión eléctrica de 10 m | 2 | $45.000 |
| | Vajilla (puesto completo) | 60 | $18.000 |
| Zona BBQ | Parrilla a gas | 1 | $1.500.000 |
| | Pinzas para asar | 2 | $25.000 |
| | Espátulas | 2 | $20.000 |
| | Cepillo para parrilla | 1 | $30.000 |
| | Bandejas | 4 | $20.000 |
| | Mesas | 4 | $180.000 |
| | Sillas | 16 | $45.000 |
| | Pipeta de gas 40 lb | 1 | $220.000 |
| | Extintor | 1 | $120.000 |
| Piscina | Sillas asoleadoras | 8 | $250.000 |
| | Sombrillas | 4 | $180.000 |
| | Flotadores | 6 | $30.000 |
| | Tablas de natación | 6 | $35.000 |
| | Aro salvavidas | 2 | $150.000 |
| Gimnasio | Colchonetas | 8 | $60.000 |
| | Mancuernas (par) | 10 | $80.000 |
| | Balones de pilates | 4 | $70.000 |
| | Bandas elásticas | 6 | $25.000 |
| | Kettlebells | 4 | $120.000 |
| | Lazos de saltar | 6 | $15.000 |
| Cancha múltiple | Balón de microfútbol | 2 | $90.000 |
| | Balón de baloncesto | 2 | $110.000 |
| | Petos | 12 | $15.000 |
| | Balón de voleibol | 1 | $80.000 |
| | Red de voleibol | 1 | $150.000 |
| | Conos de entrenamiento | 10 | $6.000 |
| Parque infantil | Kit de arenero (balde y pala) | 6 | $15.000 |
| | Balones infantiles | 3 | $25.000 |
| Salón de juegos | Tacos de billar | 4 | $70.000 |
| | Juego de bolas de billar | 1 | $250.000 |
| | Raquetas de ping-pong | 4 | $40.000 |
| | Pelotas de ping-pong | 6 | $3.000 |
| | Juegos de mesa | 6 | $80.000 |
| | Ajedrez | 2 | $60.000 |
| | Dominó | 2 | $30.000 |

*Editable en Zonas comunes → Editar → Inventario.* El estado de cada implemento (disponibles, en reparación e historial) se ve en *Inventario*.

**Ejemplo:** en la BBQ falta 1 pinza, llegan 2 sillas dañadas y la zona quedó sucia = $25.000 + 2 × $45.000 + $30.000 = **$145.000**.

### Parqueadero de visitantes

| Concepto | Valor |
|---|---|
| Horas gratis | 2 |
| Valor por hora después de las gratis | $2.000 |
| Forma de cobro | Cada hora iniciada cuenta completa |

*Editable en Parqueadero visitantes → Tarifa.* Se cobra en portería al registrar la salida.

**Ejemplos:** 1 h 30 min = $0 · 2 h 10 min = 1 hora = $2.000 · 3 h 30 min = 2 horas = $4.000.

### Pagos de los residentes (datos de ejemplo)

| Concepto | Valor | Fecha límite |
|---|---|---|
| Cuota de administración, apartamento de más de 60 m² | $340.000 al mes | día 10 de cada mes |
| Cuota de administración, apartamento de 60 m² o menos | $285.000 al mes | día 10 de cada mes |
| Parqueadero de residentes (carro) | $85.000 al mes | según la factura |

Estas facturas las genera el administrador en *Pagos → Generar factura*, con el valor que defina. Los montos de la tabla son los de los datos de ejemplo que carga el sistema.

## Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/jugarcia63/Pro_Sist_Gest_Conj_2026.git
cd Pro_Sist_Gest_Conj_2026
```

### 2. Crear y activar el entorno virtual
```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/Mac
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Crear la base de datos en MySQL
```sql
CREATE DATABASE gestion_residencial_db CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

### 5. Configurar variables de entorno

Copia `.env.example` como `.env` y completa con tus datos reales:
```bash
copy .env.example .env      # Windows
cp .env.example .env        # Linux/Mac
```

Edita `.env`:

### 6. Migrar la base de datos
```bash
python manage.py migrate
```

### 7. Crear un superusuario
```bash
python manage.py createsuperuser
```

### 8. Datos de ejemplo
```bash
python manage.py poblar_datos            # torres, zonas, residentes, vigilantes, pagos, reservas...
python manage.py refrescar_datos --si    # vuelve a crear pagos, reservas, visitas, etc. con fechas de hoy
```
`refrescar_datos` borra pagos, reservas, visitas, paquetes, reportes y avisos (no toca usuarios, residentes, unidades, zonas ni vehículos) y los crea de nuevo alrededor de la fecha actual: así la demo no muestra facturas de hace meses como vencidas ni reportes viejos abiertos. En Render se ejecuta en el deploy si la variable `REFRESCAR_DATOS` vale `1`; después conviene volver a ponerla en `0`.

### 9. Correr el servidor
```bash
python manage.py runserver
```

Accede en `http://127.0.0.1:8000/login/`

## Notas técnicas

- El sistema usa un modelo de usuario personalizado (`Usuario`, en la app `usuarios`) con un campo `rol` (`residente` / `admin` / `seguridad`), separado del modelo de negocio `Residentes`. Ambos se sincronizan por coincidencia de email.
- No hay registro público: solo el administrador crea cuentas. Al registrar un residente pasa a crearle su cuenta (usuario + contraseña temporal) y el residente debe cambiarla la primera vez que entra. Lo mismo para el personal de seguridad.
- Los pagos usan una pasarela simulada con fines académicos — no procesan transacciones reales ni almacenan datos de tarjetas.
- Requiere MySQL 8.0 (no 8.4+) junto con Django 5.x, ya que Django 6 eleva el requisito mínimo de versión de MySQL.
