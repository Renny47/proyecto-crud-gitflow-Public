# Sistema de Gestión de Registro

## Descripción
Sistema web para gestionar clientes, categorías y proveedores desarrollado con Flask.

## Instalación y Ejecución

1. Instalar Python 3.11 o superior
2. Instalar dependencias:
   pip install flask flask-sqlalchemy gunicorn psycopg2-binary email-validator

3. Ejecutar la aplicación:
   python main.py

4. Abrir en el navegador:
   http://localhost:5000

## Características
- Gestión completa de clientes (nombre, correo, teléfono)
- Gestión de categorías
- Gestión de proveedores (nombre, contacto)
- Interfaz web responsive con Bootstrap 5
- Validación de formularios

## Estructura del Proyecto
- app.py: Aplicación principal Flask
- main.py: Punto de entrada
- templates/: Plantillas HTML
- static/: Archivos CSS y JavaScript

## Tecnologías Utilizadas
- Backend: Flask (Python)
- Frontend: HTML, CSS, JavaScript
- Framework CSS: Bootstrap 5
- Iconos: Font Awesome
