# Sistema de Gestión de Conjuntos Residenciales

Proyecto de Ingeniería de Software — [ingenieria de software 1/ universidad antonio nariño]

## Integrantes
- juan esteban vila
- juan david garcia

## Tecnologías
- Django 5.2
- MySQL 8.0
- Python 3.14

## Instalación
1. Clonar el repo
2. Crear entorno virtual: `python -m venv venv`
3. Activarlo: `venv\Scripts\activate` (Windows)
4. Instalar dependencias: `pip install -r requirements.txt`
5. Crear la base de datos: `CREATE DATABASE gestion_residencial_db;`
6. Configurar credenciales en `settings.py` (ver sección Configuración)
7. Migrar: `python manage.py migrate`
8. Crear superusuario: `python manage.py createsuperuser`
9. Correr: `python manage.py runserver`

## Configuración
Ajustar en `GestionDeConjuntos/settings.py` según tu entorno local:
- `DATABASES` (usuario, contraseña, host de MySQL)

## Módulos del sistema
- Residentes y unidades
- Vehículos
- Visitantes
- Reservas de zonas comunes
- Pagos (pasarela simulada)
- Reportes de daños

## Roles del sistema
- Residente
- Administrador
- Seguridad
