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
    echo "❌ Django no está instalado."
    exit 1
fi

# 1. Recrear la base de datos
echo "🗑️  Eliminando base de datos existente..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS tikectsbd;"
sudo -u postgres psql -c "DROP USER IF EXISTS django_user;"

echo "👤 Creando usuario y base de datos..."
sudo -u postgres psql -c "CREATE USER django_user WITH PASSWORD 'erick2978';"
sudo -u postgres psql -c "CREATE DATABASE tikectsbd OWNER django_user;"

# 2. Dar permisos
echo "🔑 Configurando permisos..."
sudo -u postgres psql -d tikectsbd -c "GRANT ALL ON SCHEMA public TO django_user;"
sudo -u postgres psql -d tikectsbd -c "ALTER SCHEMA public OWNER TO django_user;"
sudo -u postgres psql -c "ALTER USER django_user WITH SUPERUSER;"

# 3. Eliminar migraciones antiguas
echo "🧹 Limpiando migraciones antiguas..."
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# 4. Crear migraciones iniciales
echo "📦 Creando migraciones iniciales..."
python manage.py makemigrations tikects_app

# 5. Aplicar migraciones
echo "🚀 Aplicando migraciones..."
python manage.py migrate

# 6. Revocar superuser
echo "🔒 Revocando permisos de superusuario..."
sudo -u postgres psql -c "ALTER USER django_user WITH NOSUPERUSER;"

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
echo "   cd $(pwd)"
echo "   source venv/bin/activate"
echo "   python manage.py runserver 0.0.0.0:8000"
echo ""
echo "🔑 Credenciales de acceso:"
echo "   Usuario: admin"
echo "   Contraseña: admin123"
echo "===================================="
