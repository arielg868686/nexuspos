# NexusPOS - Sistema de Gestión Comercial

Sistema integral de gestión comercial desarrollado con Flask y SQLite.

## Características

- Gestión de inventario
- Control de ventas
- Gestión de usuarios
- Reportes y estadísticas
- Interfaz moderna y responsiva

## Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Git

## Instalación Local

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/nexuspos.git
cd nexuspos
```

2. Crear un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Iniciar el servidor:
```bash
python server.py
```

5. Acceder a la aplicación:
```
http://localhost:5000
```

## Credenciales de Demo

- Usuario: `demo`
- Contraseña: `demo123`

## Despliegue en la Nube

### Heroku

1. Crear una cuenta en [Heroku](https://heroku.com)
2. Instalar [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
3. Login en Heroku:
```bash
heroku login
```

4. Crear una nueva aplicación:
```bash
heroku create nexuspos-app
```

5. Configurar variables de entorno:
```bash
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=tu-clave-secreta
```

6. Desplegar la aplicación:
```bash
git push heroku main
```

### Otras Plataformas

El sistema también puede ser desplegado en:
- Google Cloud Platform
- AWS
- DigitalOcean
- Azure

## Estructura del Proyecto

```
nexuspos/
├── server.py              # Servidor principal
├── database.py           # Gestión de base de datos
├── inventario.py         # Módulo de inventario
├── pos.py               # Módulo de punto de venta
├── requirements.txt     # Dependencias
├── Procfile            # Configuración para Heroku
├── templates/          # Plantillas HTML
│   ├── index.html
│   ├── login.html
│   ├── demo.html
│   ├── pos.html
│   └── inventario.html
└── static/            # Archivos estáticos
    ├── css/
    ├── js/
    └── img/
```

## Contribuir

1. Fork el repositorio
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Tu Nombre - [@tutwitter](https://twitter.com/tutwitter) - email@ejemplo.com

Link del Proyecto: [https://github.com/tu-usuario/nexuspos](https://github.com/tu-usuario/nexuspos) 