from django.shortcuts import render, redirect, get_list_or_404, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .models import Tickets_Colas, Tickets_Servicios, Tickets_Respuestas_Automaticas, Agentes, Cliente, Grupos_Agentes, Agentes_Por_Grupos, Tickets, AsignacionTikects, Grupos_Clientes, ReasignacionTikects, Notificaciones, Direcciones
from django.db.models import Prefetch, Count
from django.http import HttpResponse
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.utils.timezone import localtime
from django.utils import timezone
from datetime import timedelta
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
import pandas as pd
from datetime import datetime
from django.db.models.functions import TruncMonth, TruncWeek
import os
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test

# Create your views here.

# Decorador para verificar si el usuario es superusuario
def superuser_required(view_func):
    decorated_view_func = user_passes_test(
        lambda user: user.is_superuser,  # Verifica si el usuario es superusuario
        login_url='pagina_principal_clientes'  # Redirige a una página si no está autorizado
    )(view_func)
    return decorated_view_func

#Funcion para la pagina de inicio, configuracion y inicio de sesion
def inicio(request):
    if request.method == 'GET':
        return render(request, 'inicio_sesion_admin.html')

    else:
        username = request.POST['username']
        password = request.POST['clave']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if hasattr(user, 'cliente'):
                return redirect('pagina_principal_clientes')  # Redirige a la página principal de clientes
            else:
                return redirect('pagina_principal')  # Redirige a la página principal para otros usuarios
        else:
            return render(request, 'inicio_sesion_admin.html', {
                'error': 'Error usuario o contraseña incorrecta'
            })

@login_required
def cerrar_sesion(request):
    logout(request)
    return redirect('/')

@login_required
def pagina_principal(request):
    if request.method == 'GET':
        user = request.user
        try:
            agente = Agentes.objects.get(usuario=user)
        except Agentes.DoesNotExist:
            agente = None

        notificaciones = Notificaciones.objects.filter(agente=agente, leida=False) if agente else None
        
        return render(request, 'pagina_principal.html', {
            'notificaciones': notificaciones,
            'agente': agente
        })
    else:
        pass

@superuser_required
@login_required
def configuracion(request):
    if request.method == 'GET':
        return render(request, 'configuracion.html')
    else:
        pass

#Funciones para los ver las vistas de los tikects
@superuser_required
@login_required
def tikects_servicios(request):
    if request.method == 'GET':
        servicios = Tickets_Servicios.objects.all()
        return render(request, 'tikects_servicios.html',{
            'servicios': servicios
        })
    else:
        pass

@superuser_required
@login_required
def tikects_colas(request):
    if request.method == 'GET':
        colas = Tickets_Colas.objects.all()
        return render(request, 'tikects_colas.html',{
            'colas': colas
        })
    else:
        pass

@login_required
def tikects_respuestas_automaticas(request):
    if request.method == 'GET':
        respuestas_automaticas = Tickets_Respuestas_Automaticas.objects.all()
        return render(request, 'tikects_respuestas_automaticas.html', {
            'respuestas_automaticas': respuestas_automaticas
        })
    else:
        pass

#Funciones para crear servicios, colas y respuestas automaticas
@superuser_required
@login_required
def tikects_servicios_crear(request):
    if request.method == 'GET':
        return render(request, 'tikects_servicios_crear.html')
    else:
        nombre_servicio = request.POST['servicio']
        descripcion_servicio = request.POST['servicio_descripcion']

        if nombre_servicio and descripcion_servicio:
            servicio = Tickets_Servicios(nombre=nombre_servicio, descripcion=descripcion_servicio)
            servicio.save()
            return redirect('tikects_servicios')

@superuser_required
@login_required
def tikects_colas_crear(request):
    if request.method == 'GET':
        return render(request, 'tikects_colas_crear.html')
    else:
        nombre_colas = request.POST['colas']
        descripcion_colas = request.POST['colas_descripcion']

        if nombre_colas and descripcion_colas:
            colas = Tickets_Colas(nombre=nombre_colas, descripcion=descripcion_colas)
            colas.save()
            return redirect('tikects_colas')

@superuser_required
@login_required
def tikects_respuestas_automaticas_crear(request):
    if request.method == 'GET':
        return render(request, 'tikects_respuestas_automaticas_crear.html')
    else:
        nombre_respuesta = request.POST['respuesta']

        if nombre_respuesta:
            respuesta = Tickets_Respuestas_Automaticas(nombre=nombre_respuesta)
            respuesta.save()
            return redirect('tikects_respuestas_automaticas')
        
#Funcion para la configuracion de usuarios agentes, crear y verlos
@superuser_required
@login_required
def usuarios_agentes(request):
    if request.method == 'GET':
        agentes = Agentes.objects.all()
        return render(request, 'usuarios_agentes.html',{
            'agentes': agentes
        })
    else:
        pass

@superuser_required
@login_required
def usuarios_agentes_crear(request):
    if request.method == 'GET':
        return render(request, 'usuarios_agentes_crear.html')
    else:
        nombre_agente = request.POST['nombre']
        apellido_agente = request.POST['apellido']
        nombre_usuario_agente = request.POST['nombre_usuario']
        email_agente = request.POST['email']
        telefono_agente = request.POST['telefono']
        clave_agente = request.POST['password']

        if nombre_agente and apellido_agente and nombre_usuario_agente and email_agente:

            usuario_nuevo = User.objects.create_user(username=nombre_usuario_agente, email=email_agente, password=clave_agente)
            usuario_nuevo.save()

            agente = Agentes(nombre=nombre_agente, apellido=apellido_agente, nombre_usuario=nombre_usuario_agente, email=email_agente, telefono=telefono_agente, usuario=usuario_nuevo)
            agente.save()
            return redirect('usuarios_agentes')

#Funcion para crear grupos para los agentes
@superuser_required
@login_required
def usuarios_grupos_agentes(request):
    if request.method == 'GET':
        grupos_agentes= Grupos_Agentes.objects.all()
        return render(request, 'usuarios_grupos_agentes.html',{
            'grupos_agentes': grupos_agentes
        })
    else:
        pass

@superuser_required
@login_required
def usuarios_grupos_agentes_crear(request):
    if request.method == 'GET':
        return render(request, 'usuarios_grupos_agentes_crear.html')
    else:
        nombre_grupo = request.POST['nombre_grupo']
        descripcion_grupo = request.POST['descripcion_grupo']

        if nombre_grupo:
            grupo = Grupos_Agentes(nombre=nombre_grupo, descripcion=descripcion_grupo)
            grupo.save()
            return redirect('usuarios_grupos_agentes')

@superuser_required
@login_required
def usuariops_grupo_agentes_eliminar(request, grupo_id):
    grupo = get_object_or_404(Grupos_Agentes, id=grupo_id)
    if request.method == 'POST':
        grupo.delete()
        return redirect('usuarios_grupos_agentes')  # Redirige a la lista de grupos después de eliminar
    return render(request, 'usuarios_grupos_agentes.html', {'grupo': grupo})

#Funcion para ver los usuarios por grupos de agentes y agregarlos
@superuser_required
@login_required
def usuarios_por_grupos_agentes(request):
    if request.method == 'GET':
        # Obtenemos los datos de la relación agentes y grupos
        grupos = Grupos_Agentes.objects.prefetch_related(
            Prefetch('agentes_por_grupos_set', queryset=Agentes_Por_Grupos.objects.select_related('agente'))
        ).all()
        return render(request, 'usuarios_por_grupos_agentes.html', {
            'grupos': grupos  # Contexto que envía los datos a la plantilla
        })
    else:
        pass

@superuser_required
@login_required
def usuarios_grupos_agentes_agregar(request):
    if request.method == 'GET':
        agentes = Agentes.objects.all()
        grupos = Grupos_Agentes.objects.all()
        return render(request, 'usuarios_grupos_agentes_agregar.html', {
            'agentes': agentes,
            'grupos': grupos
        })
    else:
        agente_id = request.POST['agente']
        grupo_id = request.POST['grupo']
        
        if agente_id and grupo_id:
            agente = Agentes.objects.get(id=agente_id)
            grupo = Grupos_Agentes.objects.get(id=grupo_id)

            # Verificar si la relación ya existe
            if Agentes_Por_Grupos.objects.filter(agente=agente, grupo=grupo).exists():
                agentes = Agentes.objects.all()
                grupos = Grupos_Agentes.objects.all()
                return render(request, 'usuarios_grupos_agentes_agregar.html', {
                    'agentes': agentes,
                    'grupos': grupos,
                    'error': 'El agente ya pertenece a este grupo. Por favor, elija otro grupo.'
                })

            agente_por_grupo = Agentes_Por_Grupos(agente=agente, grupo=grupo)
            agente_por_grupo.save()
            return redirect('usuarios_por_grupos_agentes')
        
#Funcion para los permisos
@superuser_required
@login_required
def permisos(request):
    if request.method == 'GET':
        agentes = Agentes.objects.all()
        grupos = Grupos_Agentes.objects.all()
        return render(request, 'permisos.html',{
            'agentes': agentes,
            'grupos': grupos
        })
    else:
        pass

#Funcion para ver la pagina principal de los clientes
@login_required
def pagina_clientes(request):
    if request.method == 'GET':
        return render(request, 'pagina_principal_clientes.html')
    else:
        pass

#Funcion para crear los clientes y verlos
@superuser_required
@login_required
def clientes(request):
    if request.method == 'GET':
        clientes = Cliente.objects.all()  # Obtener todos los clientes
        paginator = Paginator(clientes, 10)  # Mostrar 10 clientes por página

        # Obtener el número de página actual desde los parámetros GET
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)  # Obtener los clientes de la página actual

        return render(request, 'usuarios_clientes.html', {'page_obj': page_obj})

@superuser_required
@login_required
def crear_clientes(request):
    if request.method == 'GET':
        return render(request, 'usuarios_clientes_crear.html')

    elif request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        username = request.POST.get('username')
        email = request.POST.get('email') or None  # Manejar email opcional
        telefono = request.POST.get('telefono') or None  # Manejar teléfono opcional
        password = request.POST.get('password')
        direccion = request.POST.get('direccion')

        try:
            # Crear usuario
            nuevo_usuario = User.objects.create_user(
                username=username,
                password=password,
                first_name=nombre,
                last_name=apellido
            )
            nuevo_usuario.save()

            # Crear cliente
            Cliente.objects.create(
                nombre=nombre,
                apellido=apellido,
                nombre_usuario=username,
                email=email,
                telefono=telefono,
                direccion=direccion,
                usuario=nuevo_usuario
            )

            return redirect('ver_cliente')  # Redirige a la lista de clientes
        except Exception as e:
            return render(request, 'usuarios_clientes_crear.html', {
                'error': f'Error al crear el cliente: {str(e)}'
            })

    return HttpResponse(status=405)
        
#Funcion para ver y crear los tickets (administrador)
@login_required
def ver_tikects(request):
    if request.method == 'GET':
        tikects = Tickets.objects.all().order_by('-creado')  # Ordenar por fecha de creación en orden descendente
        reasignaciones_dict = {reasignacion.tikect.id: reasignacion.agente_nuevo.usuario.username for reasignacion in ReasignacionTikects.objects.all()}
        paginator = Paginator(tikects, 10)  # Mostrar 10 tikects por página
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'tikects_ver_todos.html', {'tikects': page_obj, 'reasignaciones_dict': reasignaciones_dict})
    else:
        pass

@login_required
def ver_tikects_cerrados(request):
    tikects = Tickets.objects.filter(cerrado=True).order_by('-creado')  # Ordenar por fecha de creación en orden descendente
    reasignaciones_dict = {reasignacion.tikect.id: reasignacion.agente_nuevo.usuario.username for reasignacion in ReasignacionTikects.objects.all()}
    paginator = Paginator(tikects, 10)  # Mostrar 10 tikects por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'tikects_ver_todos.html', {'tikects': page_obj, 'reasignaciones_dict': reasignaciones_dict})

@login_required
def ver_tikects_abiertos(request):
    tikects = Tickets.objects.filter(cerrado=False).order_by('-creado')  # Ordenar por fecha de creación en orden descendente
    reasignaciones_dict = {reasignacion.tikect.id: reasignacion.agente_nuevo.usuario.username for reasignacion in ReasignacionTikects.objects.all()}
    paginator = Paginator(tikects, 10)  # Mostrar 10 tikects por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'tikects_ver_todos.html', {'tikects': page_obj, 'reasignaciones_dict': reasignaciones_dict})

#Funcion para crear los tikects clientes
@login_required
def crear_tikects_clientes(request):
    if request.method == 'GET':
        servicios = Tickets_Servicios.objects.all()
        colas = Tickets_Colas.objects.all()
        direcciones = Direcciones.objects.all()
        return render(request, 'tikects_crear.html', {
            'servicios': servicios,
            'colas': colas,
            'direcciones': direcciones,
        })
    elif request.method == 'POST':
        titulo = request.POST['titulo']
        descripcion = request.POST['descripcion']
        cola_id = request.POST['cola']
        servicio_id = request.POST['servicio']
        direccion = request.POST['direccion']
        usuario = request.user

        cola = Tickets_Colas.objects.get(id=cola_id)
        servicio = Tickets_Servicios.objects.get(id=servicio_id)

        nuevo_tikect = Tickets.objects.create(
            titulo=titulo,
            descripcion=descripcion,
            cola_perteneciente=cola,
            servicio_perteneciente=servicio,
            direccion=direccion,
            usuario=usuario
        )

        # Obtener la asignación del servicio
        try:
            asignacion = AsignacionTikects.objects.get(servicio=servicio)
            agente_asignado = asignacion.agente_actual
        except AsignacionTikects.DoesNotExist:
            agente_asignado = None

        # Crear notificación para el agente asignado
        if agente_asignado:
            Notificaciones.objects.create(
                tikect=nuevo_tikect,
                descripcion=f"Nuevo ticket '{titulo}'",
                usuario_creador=usuario,
                agente=agente_asignado
            )

        return redirect('ver_mis_tikects')

#Funcion para crear los tikects administrador y agentes
@login_required
def crear_tikects(request):
    if request.method == 'GET':
        servicios = Tickets_Servicios.objects.all()
        colas = Tickets_Colas.objects.all()
        direcciones = Direcciones.objects.all()
        return render(request, 'tikects_crear.html', {
            'servicios': servicios,
            'colas': colas,
            'direcciones': direcciones
        })
    elif request.method == 'POST':
        titulo = request.POST['titulo']
        descripcion = request.POST['descripcion']
        cola_id = request.POST['cola']
        servicio_id = request.POST['servicio']
        direccion = request.POST['direccion']
        usuario = request.user

        cola = Tickets_Colas.objects.get(id=cola_id)
        servicio = Tickets_Servicios.objects.get(id=servicio_id)

        nuevo_tikect = Tickets.objects.create(
            titulo=titulo,
            descripcion=descripcion,
            cola_perteneciente=cola,
            servicio_perteneciente=servicio,
            direccion=direccion,
            usuario=usuario
        )

        # Obtener la asignación del servicio
        try:
            asignacion = AsignacionTikects.objects.get(servicio=servicio)
            agente_asignado = asignacion.agente_actual
        except AsignacionTikects.DoesNotExist:
            agente_asignado = None

        # Crear notificación para el agente asignado
        if agente_asignado:
            Notificaciones.objects.create(
                tikect=nuevo_tikect,
                descripcion=f"Nuevo ticket '{titulo}'",
                usuario_creador=usuario,
                agente=agente_asignado
            )

        return redirect('ver_tikects')
    
#Funcion para ver los tikects de los agentes genericos y la reasignacion
@superuser_required
@login_required
def agente_generico(request):
    if request.method == 'GET':
        # Excluir servicios que ya tienen un agente genérico asignado
        servicios = Tickets_Servicios.objects.exclude(id__in=AsignacionTikects.objects.values_list('servicio', flat=True))
        # Excluir agentes que ya están asignados como agentes genéricos
        agentes = Agentes.objects.exclude(id__in=AsignacionTikects.objects.values_list('agente_actual', flat=True))
        return render(request, 'agente_generico.html', {
            'servicios': servicios,
            'agentes': agentes
        })
    else:
        servicio_id = request.POST['servicio']
        agente_actual_id = request.POST['agente_actual']
        tiempo_reasignacion = request.POST.get('tiempo_reasignacion')
        agente_reasignacion_id = request.POST.get('agente_reasignacion')

        servicio = Tickets_Servicios.objects.get(id=servicio_id)
        agente_actual = Agentes.objects.get(id=agente_actual_id)
        agente_reasignacion = Agentes.objects.get(id=agente_reasignacion_id) if agente_reasignacion_id else None

        # Convertir tiempo_reasignacion a entero si no está vacío, de lo contrario, establecerlo en None
        tiempo_reasignacion = int(tiempo_reasignacion) if tiempo_reasignacion else None

        nueva_asignacion = AsignacionTikects(
            servicio=servicio,
            agente_actual=agente_actual,
            tiempo_reasignacion=tiempo_reasignacion,
            agente_reasignacion=agente_reasignacion
        )
        nueva_asignacion.save()

        # Programar la reasignación si se especificó un tiempo de reasignación y un agente de reasignación
        if tiempo_reasignacion and agente_reasignacion:
            reasignar_agente(nueva_asignacion.id, tiempo_reasignacion)

        return redirect('ver_agentes_genericos')

@superuser_required
@login_required
def reasignar_agente(asignacion_id, tiempo_reasignacion):
    # Esta función debe ser ejecutada después del tiempo de reasignación
    asignacion = AsignacionTikects.objects.get(id=asignacion_id)
    if asignacion.agente_reasignacion:
        asignacion.agente_actual = asignacion.agente_reasignacion
        asignacion.agente_reasignacion = None
        asignacion.tiempo_reasignacion = None
        asignacion.save()

@superuser_required    
@login_required
def ver_agentes_genericos(request):
    asignaciones = AsignacionTikects.objects.all()
    return render(request, 'agentes_genericos_ver.html', {
        'asignaciones': asignaciones
    })

@superuser_required
@login_required
def eliminar_asignacion(request, asignacion_id):
    asignacion = get_object_or_404(AsignacionTikects, id=asignacion_id)
    asignacion.delete()
    return redirect('ver_agentes_genericos')

#Funcion para ver los clientes vean sus tikects
@login_required
def ver_mis_tikects(request):
    # Obtener los tickets del usuario actual
    tikects = Tickets.objects.filter(usuario=request.user).order_by('-creado')
    paginator = Paginator(tikects, 10)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'tikects_vista_lista_cliente.html', {'page_obj': page_obj})

@login_required
def ver_mis_tikects_cerrados(request):
    tikects = Tickets.objects.filter(usuario=request.user, cerrado=True).order_by('-creado')
    paginator = Paginator(tikects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'tikects_vista_lista_cliente.html', {'page_obj': page_obj})

@login_required
def ver_mis_tikects_abiertos(request):
    tikects = Tickets.objects.filter(usuario=request.user, cerrado=False).order_by('-creado')
    paginator = Paginator(tikects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'tikects_vista_lista_cliente.html', {'page_obj': page_obj})

#Funcion para que los agentes vean los tikects que estan asignados a ellos
@login_required
def ver_tikects_asignados_agentes(request):
    agente_actual = get_object_or_404(Agentes, usuario=request.user)
    
    # Obtener los tikects asignados directamente al agente
    tikects_directos = Tickets.objects.filter(usuario=agente_actual.usuario).order_by('-creado')
    
    # Obtener los tikects reasignados al agente
    reasignaciones = ReasignacionTikects.objects.filter(agente_nuevo=agente_actual)
    tikects_reasignados = Tickets.objects.filter(id__in=[reasignacion.tikect.id for reasignacion in reasignaciones]).order_by('-creado')
    
    # Obtener los tikects relacionados con los servicios asignados al agente
    asignaciones_servicios = AsignacionTikects.objects.filter(agente_actual=agente_actual)
    tikects_servicios = Tickets.objects.filter(servicio_perteneciente__in=[asignacion.servicio for asignacion in asignaciones_servicios]).order_by('-creado')
    
    # Combinar todas las listas de tikects
    tikects = tikects_directos | tikects_reasignados | tikects_servicios

    # Aplicar paginación
    paginator = Paginator(tikects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Obtener las reasignaciones para mostrar en la tabla
    reasignaciones_dict = {reasignacion.tikect.id: reasignacion.agente_nuevo.usuario.username for reasignacion in ReasignacionTikects.objects.all()}
    
    return render(request, 'tikects_asignados_agentes.html', {
        'tikects': page_obj,
        'reasignaciones_dict': reasignaciones_dict
    })

@login_required
def ver_tikects_asignados_agentes_cerrados(request):
    agente_actual = get_object_or_404(Agentes, usuario=request.user)
    
    tikects_directos = Tickets.objects.filter(usuario=agente_actual.usuario, cerrado=True).order_by('-creado')
    reasignaciones = ReasignacionTikects.objects.filter(agente_nuevo=agente_actual)
    tikects_reasignados = Tickets.objects.filter(id__in=[reasignacion.tikect.id for reasignacion in reasignaciones], cerrado=True).order_by('-creado')
    asignaciones_servicios = AsignacionTikects.objects.filter(agente_actual=agente_actual)
    tikects_servicios = Tickets.objects.filter(servicio_perteneciente__in=[asignacion.servicio for asignacion in asignaciones_servicios], cerrado=True).order_by('-creado')
    
    tikects = tikects_directos | tikects_reasignados | tikects_servicios

    paginator = Paginator(tikects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    reasignaciones_dict = {reasignacion.tikect.id: reasignacion.agente_nuevo.usuario.username for reasignacion in ReasignacionTikects.objects.all()}
    
    return render(request, 'tikects_asignados_agentes.html', {
        'tikects': page_obj,
        'reasignaciones_dict': reasignaciones_dict
    })

@login_required
def ver_tikects_asignados_agentes_abiertos(request):
    agente_actual = get_object_or_404(Agentes, usuario=request.user)
    
    tikects_directos = Tickets.objects.filter(usuario=agente_actual.usuario, cerrado=False).order_by('-creado')
    reasignaciones = ReasignacionTikects.objects.filter(agente_nuevo=agente_actual)
    tikects_reasignados = Tickets.objects.filter(id__in=[reasignacion.tikect.id for reasignacion in reasignaciones], cerrado=False).order_by('-creado')
    asignaciones_servicios = AsignacionTikects.objects.filter(agente_actual=agente_actual)
    tikects_servicios = Tickets.objects.filter(servicio_perteneciente__in=[asignacion.servicio for asignacion in asignaciones_servicios], cerrado=False).order_by('-creado')
    
    tikects = tikects_directos | tikects_reasignados | tikects_servicios

    paginator = Paginator(tikects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    reasignaciones_dict = {reasignacion.tikect.id: reasignacion.agente_nuevo.usuario.username for reasignacion in ReasignacionTikects.objects.all()}
    
    return render(request, 'tikects_asignados_agentes.html', {
        'tikects': page_obj,
        'reasignaciones_dict': reasignaciones_dict
    })

#Funcion para ver los detalles de los tikects
@login_required
def detalle_tikect(request, tikect_id):
    tikect = get_object_or_404(Tickets, id=tikect_id)

    # Marcar las notificaciones relacionadas como leídas
    Notificaciones.objects.filter(tikect=tikect, agente__usuario=request.user).update(leida=True)

    if request.method == 'POST':
        tikect.cerrado = True
        tikect.save()
        return redirect('ver_tikects')
    
    reasignaciones = ReasignacionTikects.objects.filter(tikect=tikect)
    if reasignaciones.exists():
        agente_nuevo = reasignaciones.first().agente_nuevo
        if hasattr(request.user, 'agente') and agente_nuevo == request.user.agente:
            return render(request, 'detalle_tikect.html', {
                'tikect': tikect,
                'reasignado': True
            })

    return render(request, 'detalle_tikect.html', {
        'tikect': tikect
    })

@login_required
def cerrar_tikect(request, tikect_id):
    tikect = get_object_or_404(Tickets, id=tikect_id)
    if request.method == 'POST':
        descripcion_solucion = request.POST.get('descripcion_solucion')
        tikect.cerrado = True
        tikect.cerrado_fecha = timezone.now()
        tikect.descripcion_solucion = descripcion_solucion
        tikect.cerrado_por_agente = request.user
        tikect.save()
        if hasattr(request.user, 'agente'):
            return redirect('ver_tikects_asignados_agentes')
        else:
            return redirect('ver_tikects')
    return render(request, 'detalle_tikect.html', {
        'tikect': tikect
    })

#Funcion para ver las estadisticas
@superuser_required
@login_required
def tikects_estadisticas(request):
    total_tikects = Tickets.objects.count()
    tikects_cerrados = Tickets.objects.filter(cerrado=True).count()
    tikects_abiertos = Tickets.objects.filter(cerrado=False).count()
    servicios = Tickets.objects.values('servicio_perteneciente__nombre').annotate(count=Count('servicio_perteneciente'))

    porcentaje_abiertos = (tikects_abiertos / total_tikects * 100) if total_tikects > 0 else 0
    porcentaje_cerrados = (tikects_cerrados / total_tikects * 100) if total_tikects > 0 else 0

    tikects_por_dia_cerrados = Tickets.objects.filter(cerrado=True).values('cerrado_fecha__date').annotate(count=Count('id')).order_by('cerrado_fecha__date')
    tikects_por_mes_cerrados = Tickets.objects.filter(cerrado=True).annotate(month=TruncMonth('cerrado_fecha')).values('month').annotate(count=Count('id')).order_by('month')
    tikects_por_semana_cerrados = Tickets.objects.filter(cerrado=True).annotate(week=TruncWeek('cerrado_fecha')).values('week').annotate(count=Count('id')).order_by('week')
    tikects_por_agente = Tickets.objects.filter(cerrado=True).values(
        'cerrado_por_agente__username',
        'cerrado_por_agente__agente__nombre',
        'cerrado_por_agente__agente__apellido'
    ).annotate(count=Count('id')).order_by('-count')

    context = {
        'total_tikects': total_tikects,
        'tikects_cerrados': tikects_cerrados,
        'tikects_abiertos': tikects_abiertos,
        'porcentaje_abiertos': porcentaje_abiertos,
        'porcentaje_cerrados': porcentaje_cerrados,
        'servicios': list(servicios),
        'tikects_por_dia_cerrados': list(tikects_por_dia_cerrados),
        'tikects_por_mes_cerrados': list(tikects_por_mes_cerrados),
        'tikects_por_semana_cerrados': list(tikects_por_semana_cerrados),
        'tikects_por_agente': list(tikects_por_agente),
    }
    return render(request, 'estadisticas.html', context)

#Funcion para exportar las estadisticas a excel
@superuser_required
@login_required
def exportar_tikects_excel(request):
    servicio_seleccionado = request.GET.get('servicio')

    if servicio_seleccionado == "Todo":
        tikects = Tickets.objects.filter(cerrado=True)
    else:
        tikects = Tickets.objects.filter(cerrado=True, servicio_perteneciente__nombre=servicio_seleccionado)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Tikects"

    headers = ['ID', 'Título', 'Descripción', 'Usuario', 'Servicio', 'Estado', 'Fecha de Creación', "Fecha de Cierre", "Descripción de la solución", "Agente que cerró el ticket", "Dirección"]
    ws.append(headers)

    for tikect in tikects:
        estado = 'Cerrado' if tikect.cerrado else 'Abierto'
        fecha_creacion = tikect.creado
        agente_cierre = tikect.cerrado_por_agente.username if tikect.cerrado_por_agente else "N/A"
        direccion = tikect.direccion if tikect.direccion else "N/A"

        ws.append([
            tikect.id,
            tikect.titulo,
            tikect.descripcion,
            tikect.usuario.username,
            tikect.servicio_perteneciente.nombre,
            estado,
            fecha_creacion,
            tikect.cerrado_fecha,
            tikect.descripcion_solucion,
            agente_cierre,
            direccion
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=tikects_cerrados_{servicio_seleccionado}.xlsx'
    wb.save(response)
    return response

#Funcion para exportar las estadisticas a pdf
@superuser_required
@login_required
def exportar_tikects_pdf(request):
    servicio_seleccionado = request.GET.get('servicio')

    if servicio_seleccionado == "Todo":
        tikects = Tickets.objects.filter(cerrado=True)
    else:
        tikects = Tickets.objects.filter(cerrado=True, servicio_perteneciente__nombre=servicio_seleccionado)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=tikects_cerrados_{servicio_seleccionado}.pdf'

    c = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    margen_x = 30
    margen_y = height - 40
    espaciado_vertical = 15
    ancho_columna = [30, 100, 100, 60, 80, 80, 90, 70, 100]

    c.setFont("Helvetica-Bold", 10)
    c.drawString(margen_x, margen_y, "ID")
    c.drawString(margen_x + ancho_columna[0], margen_y, "Título")
    c.drawString(margen_x + sum(ancho_columna[:2]), margen_y, "Descripción")
    c.drawString(margen_x + sum(ancho_columna[:3]), margen_y, "Usuario")
    c.drawString(margen_x + sum(ancho_columna[:4]), margen_y, "Servicio")
    c.drawString(margen_x + sum(ancho_columna[:5]), margen_y, "Estado")
    c.drawString(margen_x + sum(ancho_columna[:6]), margen_y, "Fecha Cierre")
    c.drawString(margen_x + sum(ancho_columna[:7]), margen_y, "Agente")
    c.drawString(margen_x + sum(ancho_columna[:8]), margen_y, "Dirección")
    c.line(margen_x, margen_y - 5, width - margen_x, margen_y - 5)

    c.setFont("Helvetica", 9)
    y = margen_y - espaciado_vertical * 2
    for tikect in tikects:
        estado = 'Cerrado' if tikect.cerrado else 'Abierto'
        fecha_cierre = tikect.cerrado_fecha.strftime('%Y-%m-%d %H:%M:%S') if tikect.cerrado_fecha else "N/A"
        agente = tikect.cerrado_por_agente.username if tikect.cerrado_por_agente else "N/A"
        direccion = tikect.direccion if tikect.direccion else "N/A"

        c.drawString(margen_x, y, str(tikect.id))
        c.drawString(margen_x + ancho_columna[0], y, tikect.titulo[:15])
        c.drawString(margen_x + sum(ancho_columna[:2]), y, tikect.descripcion[:20])
        c.drawString(margen_x + sum(ancho_columna[:3]), y, tikect.usuario.username)
        c.drawString(margen_x + sum(ancho_columna[:4]), y, tikect.servicio_perteneciente.nombre)
        c.drawString(margen_x + sum(ancho_columna[:5]), y, estado)
        c.drawString(margen_x + sum(ancho_columna[:6]), y, fecha_cierre)
        c.drawString(margen_x + sum(ancho_columna[:7]), y, agente)
        c.drawString(margen_x + sum(ancho_columna[:8]), y, direccion)

        y -= espaciado_vertical

        if y < 40:
            c.showPage()
            y = height - 40
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margen_x, y, "ID")
            c.drawString(margen_x + ancho_columna[0], y, "Título")
            c.drawString(margen_x + sum(ancho_columna[:2]), y, "Descripción")
            c.drawString(margen_x + sum(ancho_columna[:3]), y, "Usuario")
            c.drawString(margen_x + sum(ancho_columna[:4]), y, "Servicio")
            c.drawString(margen_x + sum(ancho_columna[:5]), y, "Estado")
            c.drawString(margen_x + sum(ancho_columna[:6]), y, "Fecha Cierre")
            c.drawString(margen_x + sum(ancho_columna[:7]), y, "Agente")
            c.drawString(margen_x + sum(ancho_columna[:8]), y, "Dirección")
            c.line(margen_x, y - 5, width - margen_x, y - 5)

            y -= espaciado_vertical * 2

    c.showPage()
    c.save()
    return response

#Funcion para eliminar los servicios, colas y respuestas automaticas
@superuser_required
@login_required
def eliminar_servicio(request, servicio_id):
    servicio = get_object_or_404(Tickets_Servicios, id=servicio_id)
    if request.method == 'POST':
        servicio.delete()
        return redirect('tikects_servicios')
    return render(request, 'tikects_servicios.html', {'servicio': servicio})

@superuser_required
@login_required
def eliminar_cola(request, cola_id):
    cola = get_object_or_404(Tickets_Colas, id=cola_id)
    if request.method == 'POST':
        cola.delete()
        return redirect('tikects_colas')
    return render(request, 'tikects_colas.html', {'cola': cola})

@superuser_required
@login_required
def eliminar_respuesta_automatica(request, respuesta_id):
    respuesta = get_object_or_404(Tickets_Respuestas_Automaticas, id=respuesta_id)
    if request.method == 'POST':
        respuesta.delete()
        return redirect('tikects_respuestas_automaticas')
    return render(request, 'tikects_respuestas_automaticas.html', {'respuesta': respuesta})

#Funcion para los grupos de clientes, ver y crear
@superuser_required
@login_required
def usuarios_clientes_grupos(request):
    if request.method == 'GET':
        grupos_clientes = Grupos_Clientes.objects.all()
        return render(request, 'usuarios_clientes_grupos.html', {
            'grupos_clientes': grupos_clientes
        })
    else:
        pass

@superuser_required
@login_required
def usuarios_clientes_grupos_crear(request):
    if request.method == 'GET':
        return render(request, 'usuarios_clientes_grupos_crear.html')
    else:
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        if nombre and descripcion:
            Grupos_Clientes.objects.create(nombre=nombre, descripcion=descripcion)
            return redirect('ver_grupos')
    
#Funcion para poder eliminar los agentes de los grupos
@superuser_required
@login_required
def eliminar_agente_de_grupo(request, grupo_agente_id):
    grupo_agente = get_object_or_404(Agentes_Por_Grupos, id=grupo_agente_id)
    grupo_agente.delete()
    return redirect('usuarios_por_grupos_agentes')

#Funcion para eliminar los clientes y editar
@superuser_required
@login_required
def eliminar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    cliente.delete()
    return redirect('ver_cliente')

@superuser_required
@login_required
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == 'GET':
        return render(request, 'usuarios_editar_cliente.html', {'cliente': cliente})

    elif request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        nombre_usuario = request.POST.get('nombre_usuario')
        email = request.POST.get('email', '').strip()
        email = email if email else None
        password = request.POST.get('password')
        direccion = request.POST.get('direccion')

        cliente.nombre = nombre
        cliente.apellido = apellido
        cliente.nombre_usuario = nombre_usuario
        cliente.email = email
        cliente.direccion = direccion

        if password:
            cliente.usuario.set_password(password)
            cliente.usuario.save()

        cliente.save()
        return redirect('ver_cliente')

#Funcion para reasignar los tikects manualmente
@login_required
def reasignar_tikect(request, tikect_id):
    tikect = get_object_or_404(Tickets, id=tikect_id)
    try:
        agente_actual = Agentes.objects.get(usuario=request.user)
    except Agentes.DoesNotExist:
        return redirect('detalle_tikect', tikect_id=tikect.id)

    if ReasignacionTikects.objects.filter(tikect=tikect, agente_nuevo=agente_actual).exists():
        return render(request, 'reasignar_tikects.html', {
            'tikect': tikect,
            'error': 'Este tikect ya ha sido reasignado.'
        })

    grupo_agente_actual = Agentes_Por_Grupos.objects.filter(agente=agente_actual).first()
    if not grupo_agente_actual:
        return redirect('detalle_tikect', tikect_id=tikect.id)

    agentes_por_grupo = Agentes_Por_Grupos.objects.filter(grupo=grupo_agente_actual.grupo).exclude(agente=agente_actual)
    agentes_grupo = [agente_por_grupo.agente for agente_por_grupo in agentes_por_grupo]

    if request.method == 'POST':
        nuevo_agente_id = request.POST.get('nuevo_agente')
        nuevo_agente = get_object_or_404(Agentes, id=nuevo_agente_id)

        ReasignacionTikects.objects.create(
            tikect=tikect,
            agente_anterior=agente_actual,
            agente_nuevo=nuevo_agente
        )

        Notificaciones.objects.create(
            tikect=tikect,
            agente=nuevo_agente,
            descripcion="Tikect reasignado"
        )

        return redirect('ver_tikects_asignados_agentes')

    return render(request, 'reasignar_tikects.html', {
        'tikect': tikect,
        'agentes_grupo': agentes_grupo
    })

#Chekear notificaciones
def check_notifications(request):
    if request.user.is_authenticated:
        agente = getattr(request.user, 'agente', None)
        if agente:
            nuevas_notificaciones = Notificaciones.objects.filter(agente=agente, leida=False)
            notificaciones = [
                {'tikect_id': n.tikect.id, 'descripcion': n.descripcion}
                for n in nuevas_notificaciones
            ]
            return JsonResponse({'new_notifications': nuevas_notificaciones.exists(), 'notifications': notificaciones})
    return JsonResponse({'new_notifications': False, 'notifications': []})

#Editar servicios de tikects
@superuser_required
@login_required
def editar_servicios(request, servicio_id):
    servicio = get_object_or_404(Tickets_Servicios, id=servicio_id)

    if request.method == 'GET':
        return render(request, 'tikects_servicios_editar.html', {'servicio': servicio})
    else:
        servicio.nombre = request.POST.get('nombre')
        servicio.descripcion = request.POST.get('descripcion')
        servicio.save()
        return redirect('tikects_servicios')

#Editar cola de los tikects
@superuser_required
@login_required
def editar_cola(request, cola_id):
    cola = get_object_or_404(Tickets_Colas, id=cola_id)

    if request.method == 'POST':
        cola.nombre = request.POST.get('nombre')
        cola.descripcion = request.POST.get('descripcion')
        cola.save()
        return redirect('tikects_colas')

    return render(request, 'tikects_colas_editar.html', {'cola': cola})

#Editar agentes
@superuser_required
@login_required
def editar_agente(request, agente_id):
    try:
        agente = get_object_or_404(Agentes, id=agente_id)
        usuario = agente.usuario

        if request.method == 'POST':
            nueva_contrasena = request.POST.get('password')
            
            if nueva_contrasena and len(nueva_contrasena) < 8:
                messages.error(request, "La contraseña debe tener al menos 8 caracteres.")
                return render(request, 'agentes_editar.html', {'agente': agente})

            agente.nombre = request.POST.get('nombre', agente.nombre)
            agente.apellido = request.POST.get('apellido', agente.apellido)
            agente.nombre_usuario = request.POST.get('nombre_usuario', agente.nombre_usuario)
            agente.email = request.POST.get('email', agente.email)
            agente.telefono = request.POST.get('telefono', agente.telefono)

            if nueva_contrasena:
                usuario.set_password(nueva_contrasena)

            agente.save()
            usuario.save()

            messages.success(request, "Agente actualizado exitosamente.")
            return redirect('ver_agentes')

        return render(request, 'agentes_editar.html', {'agente': agente})

    except Exception as e:
        messages.error(request, f"Error inesperado: {e}")
        return redirect('usuarios_agentes')

#Editar grupos
@superuser_required
@login_required
def editar_grupo(request, grupo_id):
    grupo = get_object_or_404(Grupos_Agentes, id=grupo_id)

    if request.method == 'POST':
        grupo.nombre = request.POST.get('nombre')
        grupo.descripcion = request.POST.get('descripcion')
        grupo.save()
        return redirect('ver_grupos')

    return render(request, 'grupos_editar.html', {'grupo': grupo})

# Funciones para direcciones
@superuser_required
@login_required
def ver_direcciones(request):
    direcciones = Direcciones.objects.all()
    return render(request, 'direcciones.html', {'direcciones': direcciones})

@superuser_required
@login_required
def crear_direccion(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')

        if nombre and descripcion:
            Direcciones.objects.create(nombre=nombre, descripcion=descripcion)
            messages.success(request, 'La dirección se ha creado con éxito.')
            return redirect('ver_direcciones')
        else:
            messages.error(request, 'Todos los campos son obligatorios.')

    return render(request, 'direccion_crear.html')

@superuser_required
@login_required
def eliminar_direccion(request, direccion_id):
    direccion = get_object_or_404(Direcciones, id=direccion_id)
    if request.method == 'POST':
        direccion.delete()
        messages.success(request, 'La dirección ha sido eliminada con éxito.')
        return redirect('ver_direcciones')
    return redirect('ver_direcciones')

@superuser_required
@login_required
def editar_direccion(request, direccion_id):
    direccion = get_object_or_404(Direcciones, id=direccion_id)
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        if nombre and descripcion:
            direccion.nombre = nombre
            direccion.descripcion = descripcion
            direccion.save()
            messages.success(request, 'La dirección ha sido actualizada con éxito.')
            return redirect('ver_direcciones')
        else:
            messages.error(request, 'Todos los campos son obligatorios.')
    return render(request, 'editar_direccion.html', {'direccion': direccion})

@superuser_required
@login_required
def registrar_usuarios(request):
    ruta_archivo = os.path.join(settings.BASE_DIR, 'usuarios_nuevos.xlsx')
    error = None

    if request.method == 'POST':
        try:
            datos = pd.read_excel(ruta_archivo)
            
            if datos.isnull().values.any():
                raise ValueError("El archivo Excel contiene valores nulos. Verifica las columnas.")

            columnas_requeridas = ['Nombre', 'Apellido', 'usuario', 'Clave', 'Direccion', 'Correo']
            if not all(col in datos.columns for col in columnas_requeridas):
                raise ValueError("El archivo Excel no contiene las columnas necesarias: 'Nombre', 'Apellido', 'usuario', 'Clave', 'Direccion', 'Correo'")

            for _, fila in datos.iterrows():
                try:
                    nombre = fila['Nombre']
                    apellido = fila['Apellido']
                    nombre_usuario = fila['usuario']
                    clave = fila['Clave']
                    direccion = fila['Direccion']
                    email = fila['Correo']
                    telefono = "000-000-0000"

                    if not User.objects.filter(username=nombre_usuario).exists():
                        usuario = User.objects.create_user(username=nombre_usuario, email=email, password=clave)
                        usuario.save()

                        cliente = Cliente(
                            nombre=nombre,
                            apellido=apellido,
                            nombre_usuario=nombre_usuario,
                            email=email,
                            telefono=telefono,
                            direccion=direccion,
                            usuario=usuario
                        )
                        cliente.save()
                    else:
                        print(f"Usuario {nombre_usuario} ya existe, se omite su registro.")
                except Exception as error_individual:
                    print(f"Error al registrar el usuario {fila['usuario']}: {error_individual}")
                    continue

            print(f"Total de usuarios procesados: {datos.shape[0]}")
            return redirect('ver_cliente')

        except Exception as e:
            error = str(e)

    return render(request, 'registrar_usuarios.html', {'error': error})

#Funcion para ver los agentes para el servidor
def ver_agentes(request):
    agentes = Agentes.objects.all().order_by('nombre_usuario')
    return render(request, 'usuarios_agentes.html', {'agentes': agentes})

#Funcion para registrar los tickets
@superuser_required
@login_required
def registrar_tickets_excel(request):
    ruta_archivo = os.path.join(settings.BASE_DIR, 'LISTA DE TICKETS CERRADOS.xlsx')

    if request.method == 'POST':
        try:
            df = pd.read_excel(ruta_archivo)

            for index, row in df.iterrows():
                try:
                    try:
                        cliente = Cliente.objects.get(email=row['IDdelcliente'])
                        usuario = cliente.usuario
                    except Cliente.DoesNotExist:
                        messages.warning(request, f"Cliente con email '{row['IDdelcliente']}' no encontrado. Saltando registro.")
                        continue

                    cola = Tickets_Colas.objects.get(nombre=row['Cola'])
                    servicio = Tickets_Servicios.objects.get(nombre=row['Servicio'])

                    creado_fecha = None
                    cerrado_fecha = None

                    if not pd.isnull(row['Creado']):
                        creado_str = row['Creado'].split('(')[0].strip()
                        if len(creado_str) == 19:
                            creado_fecha = datetime.strptime(creado_str, '%Y-%m-%d %H:%M:%S')
                        else:
                            creado_str = creado_str[:10] + ' ' + creado_str[10:]
                            creado_fecha = datetime.strptime(creado_str, '%Y-%m-%d %H:%M:%S')

                    if not pd.isnull(row['Fechadecierre']):
                        cerrado_str = row['Fechadecierre'].split('(')[0].strip()
                        if len(cerrado_str) == 19:
                            cerrado_fecha = datetime.strptime(cerrado_str, '%Y-%m-%d %H:%M:%S')
                        else:
                            cerrado_str = cerrado_str[:10] + ' ' + cerrado_str[10:]
                            cerrado_fecha = datetime.strptime(cerrado_str, '%Y-%m-%d %H:%M:%S')

                    ticket = Tickets(
                        titulo=row['Título'],
                        descripcion="Descripción no proporcionada",
                        creado=creado_fecha,
                        cerrado=(row['Estado'].lower() == 'cerrado'),
                        cerrado_fecha=cerrado_fecha,
                        cola_perteneciente=cola,
                        servicio_perteneciente=servicio,
                        usuario=usuario,
                        direccion=cliente.direccion,
                        descripcion_solucion="Solución no proporcionada"
                    )
                    ticket.save()

                except Tickets_Colas.DoesNotExist:
                    messages.warning(request, f"Cola '{row['Cola']}' no encontrada. Saltando registro.")
                except Tickets_Servicios.DoesNotExist:
                    messages.warning(request, f"Servicio '{row['Servicio']}' no encontrado. Saltando registro.")
                except Exception as e:
                    messages.error(request, f"Error al registrar el ticket en la fila {index}: {e}")

            messages.success(request, "Tickets registrados exitosamente.")
            return redirect('ver_tikects')

        except Exception as e:
            messages.error(request, f"Error al procesar el archivo: {e}")

    return render(request, 'registrar_tickets_excel.html')