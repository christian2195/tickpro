#!/bin/bash

echo "===================================="
echo "🔄 REINSTALACIÓN COMPLETA DE DJANGO"
echo "===================================="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_message() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    print_error "No se encuentra manage.py en el directorio actual"
    print_error "Por favor, ejecuta este script desde /var/www/html/tickets/"
    exit 1
fi

print_message "📁 Directorio actual: $(pwd)"

# 1. Desactivar entorno virtual si está activo
print_message "🔌 Desactivando entorno virtual..."
deactivate 2>/dev/null || true

# 2. Eliminar entorno virtual existente
print_message "🗑️  Eliminando entorno virtual antiguo..."
rm -rf venv

# 3. Verificar versión de Python
print_message "🔍 Verificando versión de Python..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
print_message "Python detectado: $python_version"

# 4. Crear nuevo entorno virtual
print_message "🆕 Creando nuevo entorno virtual..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    print_error "Error al crear el entorno virtual"
    exit 1
fi

# 5. Activar entorno virtual
print_message "✅ Activando entorno virtual..."
source venv/bin/activate

# 6. Actualizar pip y herramientas básicas
print_message "📦 Actualizando pip y herramientas básicas..."
pip install --upgrade pip setuptools wheel
if [ $? -ne 0 ]; then
    print_error "Error al actualizar pip"
    exit 1
fi

# 7. Instalar dependencias en orden específico
print_message "📚 Instalando dependencias..."

# Lista de dependencias en orden
deps=(
    "asgiref==3.8.1"
    "sqlparse==0.5.3"
    "django==5.0.6"
    "chardet==5.2.0"
    "et_xmlfile==2.0.0"
    "gunicorn==23.0.0"
    "numpy==2.2.4"
    "openpyxl==3.1.5"
    "packaging==24.2"
    "pandas==2.2.3"
    "pillow==11.1.0"
    "psycopg2-binary==2.9.11"
    "PyMySQL==1.1.1"
    "python-dateutil==2.9.0.post0"
    "pytz==2025.1"
    "reportlab==4.3.1"
    "six==1.17.0"
    "tzdata==2025.1"
)

total=${#deps[@]}
count=0

for dep in "${deps[@]}"; do
    count=$((count + 1))
    print_message "   [$count/$total] Instalando $dep..."
    pip install $dep > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        print_error "Error al instalar $dep"
        exit 1
    fi
done

# 8. Verificar instalación de Django
print_message "🔍 Verificando instalación de Django..."
python -c "
import django
import os
print(f'✓ Django {django.__version__} instalado correctamente')
migration_path = os.path.join(os.path.dirname(django.__file__), 'db', 'migrations', 'migration.py')
print(f'✓ Migration.py existe: {os.path.exists(migration_path)}')
" 2>/dev/null

if [ $? -ne 0 ]; then
    print_error "Error en la verificación de Django"
    exit 1
fi

# 9. Verificar importaciones específicas
print_message "🧪 Verificando importaciones específicas..."
python -c "
from django.db import migrations
from django.db.migrations import migration
print('✓ Todas las importaciones funcionan correctamente')
" 2>/dev/null

if [ $? -ne 0 ]; then
    print_error "Error en las importaciones de Django"
    exit 1
fi

# 10. Limpiar caché y archivos temporales
print_message "🧹 Limpiando archivos temporales..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# 11. Verificar que todo está listo
print_message "✅ Todo listo. Versiones instaladas:"
pip list | grep -E "Django|pandas|numpy|openpyxl|reportlab|psycopg2"

# 12. Ofrecer ejecutar migraciones
echo ""
print_warning "¿Quieres ejecutar las migraciones ahora? (s/n)"
read -r run_migrations

if [ "$run_migrations" = "s" ] || [ "$run_migrations" = "S" ]; then
    print_message "🚀 Ejecutando migraciones..."
    
    # Verificar que el script setup_completo.sh existe
    if [ -f "setup_completo.sh" ]; then
        print_message "📝 Ejecutando setup_completo.sh..."
        chmod +x setup_completo.sh
        ./setup_completo.sh
    else
        print_message "📝 No se encuentra setup_completo.sh, ejecutando migraciones básicas..."
        python manage.py makemigrations
        python manage.py migrate
    fi
fi

# 13. Instrucciones finales
echo ""
echo "===================================="
echo -e "${GREEN}✅ REINSTALACIÓN COMPLETADA${NC}"
echo "===================================="
echo ""
echo "📋 Para iniciar el servidor:"
echo "   cd /var/www/html/tickets"
echo "   source venv/bin/activate"
echo "   python manage.py runserver 0.0.0.0:8000"
echo ""
echo "🔧 Si encuentras algún error, puedes ejecutar:"
echo "   ./reinstall.sh  # Para reinstalar todo"
echo "   python manage.py check  # Para verificar el proyecto"
echo "===================================="

# Mantener el script ejecutable
chmod +x "$0"