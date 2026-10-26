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
- Registro de visitantes
- Parqueadero de visitantes: placa asociada a una unidad, contador de tiempo en vivo y cobro al salir (horas gratis + cada hora iniciada; tarifa editable por el administrador)
- Paquetes en portería: registro por número de guía y destinatario, entrega con hora, quién lo recoge y qué vigilante lo entregó; el residente ve en su panel los paquetes de su unidad
- Reservas de zonas comunes (con validación de horarios y solapamiento)
- Pagos con pasarela simulada
- Reportes de daños

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

### 8. Correr el servidor
```bash
python manage.py runserver
```

Accede en `http://127.0.0.1:8000/login/`

## Notas técnicas

- El sistema usa un modelo de usuario personalizado (`Usuario`, en la app `usuarios`) con un campo `rol` (`residente` / `admin` / `seguridad`), separado del modelo de negocio `Residentes`. Ambos se sincronizan por coincidencia de email.
- No hay registro público: solo el administrador crea cuentas. Al registrar un residente pasa a crearle su cuenta (usuario + contraseña temporal) y el residente debe cambiarla la primera vez que entra. Lo mismo para el personal de seguridad.
- Los pagos usan una pasarela simulada con fines académicos — no procesan transacciones reales ni almacenan datos de tarjetas.
- Requiere MySQL 8.0 (no 8.4+) junto con Django 5.x, ya que Django 6 eleva el requisito mínimo de versión de MySQL.
