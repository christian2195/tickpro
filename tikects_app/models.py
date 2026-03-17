from django.db import models
from django.contrib.auth.models import User
import datetime

# ============================================
# OPCIONES PARA LOS CAMPOS
# ============================================
TIPO_TICKET = [
    ('bug', 'Bug/Error'),
    ('feature', 'Nueva Funcionalidad'),
    ('support', 'Soporte General'),
    ('consulta', 'Consulta'),
    ('incidente', 'Incidente'),
]

PRIORIDAD = [
    ('baja', 'Baja'),
    ('media', 'Media'),
    ('alta', 'Alta'),
    ('urgente', 'Urgente'),
    ('critica', 'Crítica'),
]

ESTADO_TICKET = [
    ('nuevo', 'Nuevo (Sin revisar)'),
    ('triaje', 'En Triaje'),
    ('asignado', 'Asignado'),
    ('en_proceso', 'En Proceso'),
    ('pendiente', 'Pendiente de Información'),
    ('resuelto', 'Resuelto'),
    ('cerrado', 'Cerrado'),
    ('rechazado', 'Rechazado'),
]

# ============================================
# TABLAS DE CONFIGURACIÓN
# ============================================

class Tickets_Colas(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre

class Tickets_Servicios(models.Model): 
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre

class Tickets_Respuestas_Automaticas(models.Model):
    nombre = models.CharField(max_length=200)
    asunto = models.CharField(max_length=200)
    cuerpo = models.TextField()

    def __str__(self):
        return self.nombre

# ============================================
# USUARIOS Y AGENTES
# ============================================

class Grupos_Agentes(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre

class Agentes(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre_usuario = models.CharField(max_length=200)
    correo = models.EmailField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre_usuario

class Agentes_Por_Grupos(models.Model):
    agente = models.ForeignKey(Agentes, on_delete=models.CASCADE)
    grupo = models.ForeignKey(Grupos_Agentes, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.agente.nombre_usuario} - {self.grupo.nombre}"

# ============================================
# CLIENTES
# ============================================

class Direcciones(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

class Grupos_Clientes(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre

class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    correo = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.ForeignKey(Direcciones, on_delete=models.SET_NULL, null=True)
    grupo = models.ForeignKey(Grupos_Clientes, on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

# ============================================
# TABLA PRINCIPAL: TICKETS
# ============================================

class Tickets(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    
    # --- CAMPO CORREGIDO ---
    tipo = models.CharField(max_length=20, choices=TIPO_TICKET, default='support')
    # -----------------------
    
    prioridad = models.CharField(max_length=20, choices=PRIORIDAD, default='media')
    estado = models.CharField(max_length=20, choices=ESTADO_TICKET, default='nuevo')
    estado_triage = models.CharField(max_length=20, choices=ESTADO_TICKET, default='nuevo')
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets_creados')
    agente_asignado = models.ForeignKey(Agentes, on_delete=models.SET_NULL, null=True, blank=True)
    
    cola = models.ForeignKey(Tickets_Colas, on_delete=models.SET_NULL, null=True, blank=True)
    servicio = models.ForeignKey(Tickets_Servicios, on_delete=models.SET_NULL, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, null=True, blank=True)

    # Campos para cierre
    cerrado_por_agente = models.ForeignKey(Agentes, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_cerrados')
    fecha_cierre = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"#{self.id} - {self.titulo}"

# ============================================
# SEGUIMIENTO Y NOTIFICACIONES
# ============================================

class AsignacionTikects(models.Model):
    tikect = models.ForeignKey(Tickets, on_delete=models.CASCADE)
    agente = models.ForeignKey(Agentes, on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

class ReasignacionTikects(models.Model):
    tikect = models.ForeignKey(Tickets, on_delete=models.CASCADE)
    agente_anterior = models.ForeignKey(Agentes, on_delete=models.CASCADE, related_name='reasignaciones_anterior')
    agente_nuevo = models.ForeignKey(Agentes, on_delete=models.CASCADE, related_name='reasignaciones_nuevo')
    fecha_reasignacion = models.DateTimeField(auto_now_add=True)

class Notificaciones(models.Model):
    tikect = models.ForeignKey(Tickets, on_delete=models.CASCADE)
    descripcion = models.TextField()
    usuario_creador = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    fecha_notificacion = models.DateTimeField(auto_now_add=True)
    agente = models.ForeignKey(Agentes, on_delete=models.CASCADE)
    leida = models.BooleanField(default=False)

    def __str__(self):
        return self.descripcion