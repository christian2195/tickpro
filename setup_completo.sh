#!/bin/bash

echo "🔄 Configurando el sistema de tickets..."
echo "📁 Directorio actual: $(pwd)"

# Activar entorno virtual
if [ -f "venv/bin/activate" ]; then
    echo "✅ Activando entorno virtual..."
    source venv/bin/activate
else
    echo "❌ No se encuentra el entorno virtual"
    exit 1
fi

# Verificar que Django está instalado
python -c "import django" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Django no está instalado. Instalando..."
    pip install django==5.0.6 psycopg2-binary
fi

# 1. Recrear la base de datos desde cero (con tus nombres reales)
echo "🗑️  Eliminando base de datos existente..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS tikectsbd;"
sudo -u postgres psql -c "DROP USER IF EXISTS django_user;"

echo "👤 Creando usuario y base de datos..."
sudo -u postgres psql -c "CREATE USER django_user WITH PASSWORD 'erick2978';"
sudo -u postgres psql -c "CREATE DATABASE tikectsbd OWNER django_user;"

# 2. Dar permisos completos
echo "🔑 Configurando permisos..."
sudo -u postgres psql -d tikectsbd -c "GRANT ALL ON SCHEMA public TO django_user;"
sudo -u postgres psql -d tikectsbd -c "ALTER SCHEMA public OWNER TO django_user;"
sudo -u postgres psql -c "ALTER USER django_user WITH SUPERUSER;"  # Temporal para pruebas

# 3. Verificar conexión
echo "🔍 Verificando conexión a la base de datos..."
python manage.py dbshell << EOF
\dt
\q
EOF

# 4. Eliminar migraciones antiguas (opcional, si quieres empezar fresco)
echo "🧹 Limpiando migraciones antiguas..."
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# 5. Crear nuevas migraciones
echo "📦 Creando migraciones..."
python manage.py makemigrations tikects_app

# 6. Aplicar todas las migraciones
echo "🚀 Aplicando migraciones..."
python manage.py migrate

# 7. Crear superusuario
echo "👤 Creando superusuario..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Superusuario creado')
else:
    print('⚠️  El superusuario ya existe')
"

# 8. Verificar la instalación
echo "✅ Verificando instalación..."
python manage.py check

echo ""
echo "===================================="
echo "✅ CONFIGURACIÓN COMPLETA"
echo "===================================="
echo "🌐 Para iniciar el servidor:"
echo "   cd /var/www/html/tickets"
echo "   source venv/bin/activate"
echo "   python manage.py runserver 0.0.0.0:8000"
echo ""
echo "🔑 Credenciales de acceso:"
echo "   Usuario: admin"
echo "   Contraseña: admin123"
echo "===================================="