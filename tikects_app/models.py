from django.db import models
from django.contrib.auth.models import User
import datetime
default_date = datetime.datetime.now()

# Create your models here.

#Tablas para los tickets
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

    def __str__(self):
        return self.nombre 

class Tickets(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    creado = models.DateTimeField(auto_now_add=True)
    cerrado = models.BooleanField(default=False)
    cerrado_fecha = models.DateTimeField(null=True, blank=True)
    cola_perteneciente = models.ForeignKey(Tickets_Colas, on_delete=models.CASCADE)
    servicio_perteneciente = models.ForeignKey(Tickets_Servicios, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    Direccion = models.CharField(max_length=200, default=None)
    descripcion_solucion = models.TextField(null=True, blank=True)
    cerrado_por_agente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cerrado_por_agente', null=True, blank=True)

    def __str__(self):
        return self.titulo

#Tablas para los agentes y clientes
class Agentes(models.Model):
    nombre = models.CharField(max_length=200)
    apellido = models.CharField(max_length=200)
    nombre_usuario = models.CharField(max_length=200)
    email = models.EmailField()
    telefono = models.CharField(max_length=200, default=None)
    ultima_conexion = models.DateTimeField(default=datetime.datetime.now)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agente', default=None)

    def __str__(self):
        return self.nombre_usuario
    
class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    apellido = models.CharField(max_length=200)
    nombre_usuario = models.CharField(max_length=200)
    email = models.EmailField(null=True, blank=True)  # Ahora no es obligatorio
    telefono = models.CharField(max_length=200, null=True, blank=True, default=None)  # Ahora no es obligatorio
    Direccion = models.CharField(max_length=200, default=None)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cliente', default=None)

    def __str__(self):
        return self.nombre_usuario
#Tablas para los grupos de agentes y clientes
class Grupos_Agentes(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre
    
class Grupos_Clientes(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre
    
class Agentes_Por_Grupos(models.Model):
    agente = models.ForeignKey(Agentes, on_delete=models.CASCADE)
    grupo = models.ForeignKey(Grupos_Agentes, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.agente.nombre_usuario} - {self.grupo.nombre}"
    

#Tablas para los permisos
class Permisos(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()


    def __str__(self):
        return self.nombre
    
# Tabla para la asignación de tikects a agentes genéricos
class AsignacionTikects(models.Model):
    servicio = models.ForeignKey(Tickets_Servicios, on_delete=models.CASCADE)
    agente_actual = models.ForeignKey(Agentes, on_delete=models.CASCADE, related_name='agente_actual')
    tiempo_reasignacion = models.IntegerField(null=True, blank=True)  # Tiempo en minutos
    agente_reasignacion = models.ForeignKey(Agentes, on_delete=models.CASCADE, related_name='agente_reasignacion', null=True, blank=True)

    def __str__(self):
        return f"Servicio: {self.servicio.nombre}, Agente Actual: {self.agente_actual.nombre_usuario}"
    
#Tabla para los tikects reasignados
class ReasignacionTikects(models.Model):
    tikect = models.ForeignKey(Tickets, on_delete=models.CASCADE)
    agente_anterior = models.ForeignKey(Agentes, on_delete=models.CASCADE, related_name='reasignaciones_anterior')
    agente_nuevo = models.ForeignKey(Agentes, on_delete=models.CASCADE, related_name='reasignaciones_nuevo')
    fecha_reasignacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tikect: {self.tikect.titulo}, Reasignado de: {self.agente_anterior.nombre_usuario} a {self.agente_nuevo.nombre_usuario}"
    
#Tabla para notificaciones
class Notificaciones(models.Model):
    tikect = models.ForeignKey(Tickets, on_delete=models.CASCADE)
    descripcion = models.TextField()
    usuario_creador = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    fecha_notificacion = models.DateTimeField(auto_now_add=True)
    agente = models.ForeignKey(Agentes, on_delete=models.CASCADE)
    leida = models.BooleanField(default=False)

    def __str__(self):
        return self.descripcion
    
#Tabla para Direciones
class Direcciones(models.Model):  # Antes: Gerencias
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre
