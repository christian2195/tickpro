from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Prefetch, Count
from django.db.models.functions import TruncMonth, TruncWeek
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib import messages
from django.conf import settings

from .models import (
    Tickets_Colas, Tickets_Servicios, Tickets_Respuestas_Automaticas,
    Agentes, Cliente, Grupos_Agentes, Agentes_Por_Grupos, Tickets,
    AsignacionTikects, Grupos_Clientes, ReasignacionTikects,
    Notificaciones, Direcciones
)

import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd
from datetime import datetime
import os
import itertools
import operator

# Create your views here.

# ============================================
# DECORADORES PERSONALIZADOS
# ============================================

def superuser_required(view_func):
    """Verifica que el usuario sea superusuario."""
    decorated_view_func = user_passes_test(
        lambda user: user.is_superuser,
        login_url='pagina_principal_clientes'
    )(view_func)
    return decorated_view_func

def agente_or_superuser_required(view_func):
    """Verifica que el usuario sea agente o superusuario."""
    decorated_view_func = user_passes_test(
        lambda user: user.is_superuser or hasattr(user, 'agente'),
        login_url='inicio'
    )(view_func)
    return decorated_view_func

# ============================================
# AUTENTICACIÓN
# ============================================

def inicio(request):
    if request.method == 'GET':
        return render(request, 'inicio_sesion_admin.html')
    else:
        username = request.POST.get('username')
        password = request.POST.get('clave')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if hasattr(user, 'cliente'):
                return redirect('pagina_principal_clientes')
            else:
                return redirect('pagina_principal')
        else:
            return render(request, 'inicio_sesion_admin.html', {
                'error': 'Error usuario o contraseña incorrecta'
            })

@login_required
def cerrar_sesion(request):
    logout(request)
    return redirect('/')

# ============================================
# PÁGINA PRINCIPAL
# ============================================

@login_required
def pagina_principal(request):
    user = request.user
    agente = None
    notificaciones = []
    ultimos_tickets = []

    try:
        if hasattr(user, 'agente'):
            agente = user.agente
        else:
            agente = Agentes.objects.filter(usuario=user).first()
    except:
        agente = None

    if agente:
        try:
            notificaciones = Notificaciones.objects.filter(agente=agente, leida=False)[:5]
        except:
            notificaciones = []

    try:
        if user.is_superuser or agente:
            ultimos_tickets = Tickets.objects.all().order_by('-fecha_creacion')[:5]
        else:
            ultimos_tickets = Tickets.objects.filter(usuario=user).order_by('-fecha_creacion')[:5]
    except:
        ultimos_tickets = []

    try:
        total_tickets = Tickets.objects.count()
        tickets_abiertos = Tickets.objects.exclude(estado='cerrado').count()
        tickets_cerrados = Tickets.objects.filter(estado='cerrado').count()
        total_agentes = Agentes.objects.count()
    except:
        total_tickets = 0
        tickets_abiertos = 0
        tickets_cerrados = 0
        total_agentes = 0

    now = datetime.now()

    return render(request, 'pagina_principal.html', {
        'notificaciones': notificaciones,
        'agente': agente,
        'ultimos_tickets': ultimos_tickets,
        'total_tickets': total_tickets,
        'tickets_abiertos': tickets_abiertos,
        'tickets_cerrados': tickets_cerrados,
        'total_agentes': total_agentes,
        'now': now
    })

@login_required
def pagina_clientes(request):
    """Página principal para clientes."""
    user = request.user
    total_mis_tickets = Tickets.objects.filter(usuario=user).count()
    mis_tickets_abiertos = Tickets.objects.filter(usuario=user).exclude(estado='cerrado').count()
    mis_tickets_cerrados = Tickets.objects.filter(usuario=user, estado='cerrado').count()
    ultimos_tickets = Tickets.objects.filter(usuario=user).order_by('-fecha_creacion')[:5]

    return render(request, 'pagina_principal_clientes.html', {
        'total_mis_tickets': total_mis_tickets,
        'mis_tickets_abiertos': mis_tickets_abiertos,
        'mis_tickets_cerrados': mis_tickets_cerrados,
        'ultimos_tickets': ultimos_tickets,
        'now': datetime.now()
    })

# ============================================
# CONFIGURACIÓN
# ============================================

@superuser_required
@login_required
def configuracion(request):
    return render(request, 'configuracion.html')

# ============================================
# SERVICIOS, COLAS Y RESPUESTAS AUTOMÁTICAS
# ============================================

@superuser_required
@login_required
def tikects_servicios(request):
    servicios = Tickets_Servicios.objects.all()
    return render(request, 'tikects_servicios.html', {'servicios': servicios})

@superuser_required
@login_required
def tikects_colas(request):
    colas = Tickets_Colas.objects.all()
    return render(request, 'tikects_colas.html', {'colas': colas})

@login_required
def tikects_respuestas_automaticas(request):
    respuestas_automaticas = Tickets_Respuestas_Automaticas.objects.all()
    return render(request, 'tikects_respuestas_automaticas.html', {
        'respuestas_automaticas': respuestas_automaticas
    })

@superuser_required
@login_required
def tikects_servicios_crear(request):
    if request.method == 'POST':
        nombre = request.POST.get('servicio')
        descripcion = request.POST.get('servicio_descripcion')
        if nombre and descripcion:
            Tickets_Servicios.objects.create(nombre=nombre, descripcion=descripcion)
            return redirect('tikects_servicios')
    return render(request, 'tikects_servicios_crear.html')

@superuser_required
@login_required
def tikects_colas_crear(request):
    if request.method == 'POST':
        nombre = request.POST.get('colas')
        descripcion = request.POST.get('colas_descripcion')
        if nombre and descripcion:
            Tickets_Colas.objects.create(nombre=nombre, descripcion=descripcion)
            return redirect('tikects_colas')
    return render(request, 'tikects_colas_crear.html')

@superuser_required
@login_required
def tikects_respuestas_automaticas_crear(request):
    if request.method == 'POST':
        nombre = request.POST.get('respuesta')
        if nombre:
            Tickets_Respuestas_Automaticas.objects.create(nombre=nombre)
            return redirect('tikects_respuestas_automaticas')
    return render(request, 'tikects_respuestas_automaticas_crear.html')

@superuser_required
@login_required
def eliminar_servicio(request, servicio_id):
    servicio = get_object_or_404(Tickets_Servicios, id=servicio_id)
    if request.method == 'POST':
        servicio.delete()
    return redirect('tikects_servicios')

@superuser_required
@login_required
def eliminar_cola(request, cola_id):
    cola = get_object_or_404(Tickets_Colas, id=cola_id)
    if request.method == 'POST':
        cola.delete()
    return redirect('tikects_colas')

@superuser_required
@login_required
def eliminar_respuesta_automatica(request, respuesta_id):
    respuesta = get_object_or_404(Tickets_Respuestas_Automaticas, id=respuesta_id)
    if request.method == 'POST':
        respuesta.delete()
    return redirect('tikects_respuestas_automaticas')

@superuser_required
@login_required
def editar_servicios(request, servicio_id):
    servicio = get_object_or_404(Tickets_Servicios, id=servicio_id)
    if request.method == 'POST':
        servicio.nombre = request.POST.get('nombre')
        servicio.descripcion = request.POST.get('descripcion')
        servicio.save()
        return redirect('tikects_servicios')
    return render(request, 'tikects_servicios_editar.html', {'servicio': servicio})

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

# ============================================
# AGENTES Y GRUPOS
# ============================================

@superuser_required
@login_required
def usuarios_agentes(request):
    agentes = Agentes.objects.all()
    return render(request, 'usuarios_agentes.html', {'agentes': agentes})

@superuser_required
@login_required
def usuarios_agentes_crear(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        username = request.POST.get('nombre_usuario')
        email = request.POST.get('email')
        password = request.POST.get('password')
        telefono = request.POST.get('telefono')

        if nombre and apellido and username and email and password:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=nombre,
                last_name=apellido
            )
            Agentes.objects.create(
                usuario=user,
                nombre_usuario=username,
                correo=email,
                # Los campos extra como nombre, apellido, telefono podrían añadirse si existen en el modelo Agentes
                # Según el modelo actual, Agentes tiene: usuario, nombre_usuario, correo, fecha_creacion
                # Si se requieren nombre/apellido/telefono, habría que ajustar el modelo.
                # Por ahora, asumimos que el modelo Agentes solo tiene esos campos básicos.
            )
            return redirect('usuarios_agentes')
    return render(request, 'usuarios_agentes_crear.html')

@superuser_required
@login_required
def editar_agente(request, agente_id):
    agente = get_object_or_404(Agentes, id=agente_id)
    usuario = agente.usuario

    if request.method == 'POST':
        nueva_password = request.POST.get('password')
        if nueva_password and len(nueva_password) < 8:
            messages.error(request, "La contraseña debe tener al menos 8 caracteres.")
            return render(request, 'agentes_editar.html', {'agente': agente})

        # Actualizar campos del agente (depende del modelo)
        # Si el modelo Agentes tiene estos campos, actualizarlos.
        # Por ahora, solo actualizamos el usuario asociado.
        usuario.first_name = request.POST.get('nombre', usuario.first_name)
        usuario.last_name = request.POST.get('apellido', usuario.last_name)
        usuario.email = request.POST.get('email', usuario.email)
        if nueva_password:
            usuario.set_password(nueva_password)
        usuario.save()

        # Si Agentes tiene campos extra, actualizarlos aquí
        # agente.nombre_usuario = request.POST.get('nombre_usuario') ...

        messages.success(request, "Agente actualizado exitosamente.")
        return redirect('usuarios_agentes')

    return render(request, 'agentes_editar.html', {'agente': agente})

@login_required
def ver_agentes(request):
    agentes = Agentes.objects.all().order_by('nombre_usuario')
    return render(request, 'usuarios_agentes.html', {'agentes': agentes})

@superuser_required
@login_required
def usuarios_grupos_agentes(request):
    grupos_agentes = Grupos_Agentes.objects.all()
    return render(request, 'usuarios_grupos_agentes.html', {'grupos_agentes': grupos_agentes})

@superuser_required
@login_required
def usuarios_grupos_agentes_crear(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre_grupo')
        descripcion = request.POST.get('descripcion_grupo')
        if nombre:
            Grupos_Agentes.objects.create(nombre=nombre, descripcion=descripcion)
            return redirect('usuarios_grupos_agentes')
    return render(request, 'usuarios_grupos_agentes_crear.html')

@superuser_required
@login_required
def usuariops_grupo_agentes_eliminar(request, grupo_id):
    grupo = get_object_or_404(Grupos_Agentes, id=grupo_id)
    if request.method == 'POST':
        grupo.delete()
    return redirect('usuarios_grupos_agentes')

@superuser_required
@login_required
def editar_grupo(request, grupo_id):
    grupo = get_object_or_404(Grupos_Agentes, id=grupo_id)
    if request.method == 'POST':
        grupo.nombre = request.POST.get('nombre')
        grupo.descripcion = request.POST.get('descripcion')
        grupo.save()
        return redirect('usuarios_grupos_agentes')
    return render(request, 'grupos_editar.html', {'grupo': grupo})

@superuser_required
@login_required
def usuarios_por_grupos_agentes(request):
    grupos = Grupos_Agentes.objects.prefetch_related(
        Prefetch('agentes_por_grupos_set', queryset=Agentes_Por_Grupos.objects.select_related('agente'))
    ).all()
    return render(request, 'usuarios_por_grupos_agentes.html', {'grupos': grupos})

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
        agente_id = request.POST.get('agente')
        grupo_id = request.POST.get('grupo')
        if agente_id and grupo_id:
            agente = get_object_or_404(Agentes, id=agente_id)
            grupo = get_object_or_404(Grupos_Agentes, id=grupo_id)
            if Agentes_Por_Grupos.objects.filter(agente=agente, grupo=grupo).exists():
                return render(request, 'usuarios_grupos_agentes_agregar.html', {
                    'agentes': Agentes.objects.all(),
                    'grupos': Grupos_Agentes.objects.all(),
                    'error': 'El agente ya pertenece a este grupo.'
                })
            Agentes_Por_Grupos.objects.create(agente=agente, grupo=grupo)
            return redirect('usuarios_por_grupos_agentes')
        return redirect('usuarios_grupos_agentes_agregar')

@superuser_required
@login_required
def eliminar_agente_de_grupo(request, grupo_agente_id):
    grupo_agente = get_object_or_404(Agentes_Por_Grupos, id=grupo_agente_id)
    if request.method == 'POST':
        grupo_agente.delete()
    return redirect('usuarios_por_grupos_agentes')

# ============================================
# CLIENTES Y DIRECCIONES
# ============================================

@superuser_required
@login_required
def clientes(request):
    clientes_list = Cliente.objects.all()
    paginator = Paginator(clientes_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'usuarios_clientes.html', {'page_obj': page_obj})

@superuser_required
@login_required
def crear_clientes(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        username = request.POST.get('username')
        email = request.POST.get('email') or None
        telefono = request.POST.get('telefono') or None
        password = request.POST.get('password')
        direccion = request.POST.get('direccion')

        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=nombre,
                last_name=apellido,
                email=email
            )
            Cliente.objects.create(
                nombre=nombre,
                apellido=apellido,
                nombre_usuario=username,
                email=email,
                telefono=telefono,
                direccion=direccion,
                usuario=user
            )
            return redirect('ver_cliente')
        except Exception as e:
            return render(request, 'usuarios_clientes_crear.html', {'error': str(e)})
    return render(request, 'usuarios_clientes_crear.html')

@superuser_required
@login_required
def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        cliente.nombre = request.POST.get('nombre')
        cliente.apellido = request.POST.get('apellido')
        cliente.nombre_usuario = request.POST.get('nombre_usuario')
        cliente.email = request.POST.get('email') or None
        cliente.direccion = request.POST.get('direccion')
        password = request.POST.get('password')
        if password:
            cliente.usuario.set_password(password)
            cliente.usuario.save()
        cliente.save()
        return redirect('ver_cliente')
    return render(request, 'usuarios_editar_cliente.html', {'cliente': cliente})

@superuser_required
@login_required
def eliminar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    if request.method == 'POST':
        cliente.delete()
    return redirect('ver_cliente')

@superuser_required
@login_required
def usuarios_clientes_grupos(request):
    grupos_clientes = Grupos_Clientes.objects.all()
    return render(request, 'usuarios_clientes_grupos.html', {'grupos_clientes': grupos_clientes})

@superuser_required
@login_required
def usuarios_clientes_grupos_crear(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        if nombre and descripcion:
            Grupos_Clientes.objects.create(nombre=nombre, descripcion=descripcion)
            return redirect('usuarios_clientes_grupos')
    return render(request, 'usuarios_clientes_grupos_crear.html')

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
            messages.success(request, 'Dirección creada con éxito.')
            return redirect('ver_direcciones')
        else:
            messages.error(request, 'Todos los campos son obligatorios.')
    return render(request, 'direccion_crear.html')

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
            messages.success(request, 'Dirección actualizada.')
            return redirect('ver_direcciones')
        else:
            messages.error(request, 'Todos los campos son obligatorios.')
    return render(request, 'editar_direccion.html', {'direccion': direccion})

@superuser_required
@login_required
def eliminar_direccion(request, direccion_id):
    direccion = get_object_or_404(Direcciones, id=direccion_id)
    if request.method == 'POST':
        direccion.delete()
        messages.success(request, 'Dirección eliminada.')
    return redirect('ver_direcciones')

# ============================================
# TICKETS - VISTAS PRINCIPALES
# ============================================

@login_required
def ver_tikects(request):
    tikects = Tickets.objects.all().order_by('-fecha_creacion')
    reasignaciones_dict = {}
    try:
        for r in ReasignacionTikects.objects.all():
            if r.agente_nuevo and r.agente_nuevo.usuario:
                reasignaciones_dict[r.tikect.id] = r.agente_nuevo.usuario.username
    except:
        pass
    paginator = Paginator(tikects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'tikects_ver_todos.html', {
        'tikects': page_obj,
        'reasignaciones_dict': reasignaciones_dict
    })

@login_required
def ver_tikects_cerrados(request):
    tikects = Tickets.objects.filter(estado='cerrado').order_by('-fecha_creacion')
    reasignaciones_dict = {}
    try:
        for r in ReasignacionTikects.objects.all():
            if r.agente_nuevo and r.agente_nuevo.usuario:
                reasignaciones_dict[r.tikect.id] = r.agente_nuevo.usuario.username
    except:
        pass
    paginator = Paginator(tikects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'tikects_ver_todos.html', {
        'tikects': page_obj,
        'reasignaciones_dict': reasignaciones_dict
    })

@login_required
def ver_tikects_abiertos(request):
    tikects = Tickets.objects.exclude(estado='cerrado').order_by('-fecha_creacion')
    reasignaciones_dict = {}
    try:
        for r in ReasignacionTikects.objects.all():
            if r.agente_nuevo and r.agente_nuevo.usuario:
                reasignaciones_dict[r.tikect.id] = r.agente_nuevo.usuario.username
    except:
        pass
    paginator = Paginator(tikects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'tikects_ver_todos.html', {
        'tikects': page_obj,
        'reasignaciones_dict': reasignaciones_dict
    })

@login_required
def detalle_tikect(request, tikect_id):
    tikect = get_object_or_404(Tickets, id=tikect_id)
    try:
        Notificaciones.objects.filter(tikect=tikect, agente__usuario=request.user).update(leida=True)
    except:
        pass

    if request.method == 'POST':
        tikect.estado = 'cerrado'
        tikect.save()
        if hasattr(request.user, 'agente'):
            return redirect('ver_tikects_asignados_agentes')
        else:
            return redirect('ver_tikects')

    reasignaciones = ReasignacionTikects.objects.filter(tikect=tikect)
    reasignado = False
    if reasignaciones.exists():
        agente_nuevo = reasignaciones.first().agente_nuevo
        if hasattr(request.user, 'agente') and agente_nuevo == request.user.agente:
            reasignado = True

    return render(request, 'detalle_tikect.html', {
        'tikect': tikect,
        'reasignado': reasignado
    })

@login_required
def cerrar_tikect(request, tikect_id):
    tikect = get_object_or_404(Tickets, id=tikect_id)
    if request.method == 'POST':
        descripcion_solucion = request.POST.get('descripcion_solucion')
        tikect.estado = 'cerrado'
        tikect.fecha_cierre = timezone.now()
        tikect.descripcion_solucion = descripcion_solucion
        tikect.cerrado_por_agente = request.user
        tikect.save()
        if hasattr(request.user, 'agente'):
            return redirect('ver_tikects_asignados_agentes')
        else:
            return redirect('ver_tikects')
    return redirect('detalle_tikect', tikect_id=tikect.id)

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
            'error': 'Este ticket ya ha sido reasignado.'
        })

    grupo_agente_actual = Agentes_Por_Grupos.objects.filter(agente=agente_actual).first()
    if not grupo_agente_actual:
        return redirect('detalle_tikect', tikect_id=tikect.id)

    agentes_grupo = Agentes.objects.filter(
        agentes_por_grupos__grupo=grupo_agente_actual.grupo
    ).exclude(id=agente_actual.id)

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
            descripcion=f"Ticket reasignado desde {agente_actual.nombre_usuario}"
        )
        return redirect('ver_tikects_asignados_agentes')

    return render(request, 'reasignar_tikects.html', {
        'tikect': tikect,
        'agentes_grupo': agentes_grupo
    })

# ============================================
# TICKETS - VISTAS PARA CLIENTES
# ============================================

@login_required
def ver_mis_tikects(request):
    tikects = Tickets.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    paginator = Paginator(tikects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'tikects_vista_lista_cliente.html', {'page_obj': page_obj})

@login_required
def ver_mis_tikects_cerrados(request):
    tikects = Tickets.objects.filter(usuario=request.user, estado='cerrado').order_by('-fecha_creacion')
    paginator = Paginator(tikects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'tikects_vista_lista_cliente.html', {'page_obj': page_obj})

@login_required
def ver_mis_tikects_abiertos(request):
    tikects = Tickets.objects.filter(usuario=request.user).exclude(estado='cerrado').order_by('-fecha_creacion')
    paginator = Paginator(tikects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'tikects_vista_lista_cliente.html', {'page_obj': page_obj})

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
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        cola_id = request.POST.get('cola')
        servicio_id = request.POST.get('servicio')
        direccion = request.POST.get('direccion')
        usuario = request.user

        cola = get_object_or_404(Tickets_Colas, id=cola_id)
        servicio = get_object_or_404(Tickets_Servicios, id=servicio_id)

        nuevo_tikect = Tickets.objects.create(
            titulo=titulo,
            descripcion=descripcion,
            cola_perteneciente=cola,
            servicio=servicio,
            direccion=direccion,
            usuario=usuario
        )

        try:
            asignacion = AsignacionTikects.objects.get(servicio=servicio)
            if asignacion.agente_actual:
                Notificaciones.objects.create(
                    tikect=nuevo_tikect,
                    descripcion=f"Nuevo ticket '{titulo}'",
                    usuario_creador=usuario,
                    agente=asignacion.agente_actual
                )
        except AsignacionTikects.DoesNotExist:
            pass

        return redirect('ver_mis_tikects')
    return redirect('crear_tikects_clientes')

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
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        cola_id = request.POST.get('cola')
        servicio_id = request.POST.get('servicio')
        direccion = request.POST.get('direccion')
        usuario = request.user

        cola = get_object_or_404(Tickets_Colas, id=cola_id)
        servicio = get_object_or_404(Tickets_Servicios, id=servicio_id)

        nuevo_tikect = Tickets.objects.create(
            titulo=titulo,
            descripcion=descripcion,
            cola_perteneciente=cola,
            servicio=servicio,
            direccion=direccion,
            usuario=usuario
        )

        try:
            asignacion = AsignacionTikects.objects.get(servicio=servicio)
            if asignacion.agente_actual:
                Notificaciones.objects.create(
                    tikect=nuevo_tikect,
                    descripcion=f"Nuevo ticket '{titulo}'",
                    usuario_creador=usuario,
                    agente=asignacion.agente_actual
                )
        except AsignacionTikects.DoesNotExist:
            pass

        return redirect('ver_tikects')
    return redirect('crear_tikects')

# ============================================
# TICKETS - VISTAS PARA AGENTES
# ============================================

@login_required
def ver_tikects_asignados_agentes(request):
    agente_actual = get_object_or_404(Agentes, usuario=request.user)

    tikects_directos = Tickets.objects.filter(usuario=agente_actual.usuario).order_by('-fecha_creacion')
    reasignaciones = ReasignacionTikects.objects.filter(agente_nuevo=agente_actual)
    tikects_reasignados = Tickets.objects.filter(id__in=[r.tikect.id for r in reasignaciones]).order_by('-fecha_creacion')
    asignaciones_servicios = AsignacionTikects.objects.filter(agente_actual=agente_actual)
    tikects_servicios = Tickets.objects.filter(servicio__in=[a.servicio for a in asignaciones_servicios]).order_by('-fecha_creacion')

    tikects_list = list(tikects_directos) + list(tikects_reasignados) + list(tikects_servicios)
    tikects_list.sort(key=lambda x: x.fecha_creacion, reverse=True)

    paginator = Paginator(tikects_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    reasignaciones_dict = {}
    try:
        for r in ReasignacionTikects.objects.all():
            if r.agente_nuevo and r.agente_nuevo.usuario:
                reasignaciones_dict[r.tikect.id] = r.agente_nuevo.usuario.username
    except:
        pass

    return render(request, 'tikects_asignados_agentes.html', {
        'tikects': page_obj,
        'reasignaciones_dict': reasignaciones_dict
    })

@login_required
def ver_tikects_asignados_agentes_cerrados(request):
    agente_actual = get_object_or_404(Agentes, usuario=request.user)

    tikects_directos = Tickets.objects.filter(usuario=agente_actual.usuario, estado='cerrado').order_by('-fecha_creacion')
    reasignaciones = ReasignacionTikects.objects.filter(agente_nuevo=agente_actual)
    tikects_reasignados = Tickets.objects.filter(id__in=[r.tikect.id for r in reasignaciones], estado='cerrado').order_by('-fecha_creacion')
    asignaciones_servicios = AsignacionTikects.objects.filter(agente_actual=agente_actual)
    tikects_servicios = Tickets.objects.filter(servicio__in=[a.servicio for a in asignaciones_servicios], estado='cerrado').order_by('-fecha_creacion')

    tikects_list = list(tikects_directos) + list(tikects_reasignados) + list(tikects_servicios)
    tikects_list.sort(key=lambda x: x.fecha_creacion, reverse=True)

    paginator = Paginator(tikects_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    reasignaciones_dict = {}
    try:
        for r in ReasignacionTikects.objects.all():
            if r.agente_nuevo and r.agente_nuevo.usuario:
                reasignaciones_dict[r.tikect.id] = r.agente_nuevo.usuario.username
    except:
        pass

    return render(request, 'tikects_asignados_agentes.html', {
        'tikects': page_obj,
        'reasignaciones_dict': reasignaciones_dict
    })

@login_required
def ver_tikects_asignados_agentes_abiertos(request):
    agente_actual = get_object_or_404(Agentes, usuario=request.user)

    tikects_directos = Tickets.objects.filter(usuario=agente_actual.usuario).exclude(estado='cerrado').order_by('-fecha_creacion')
    reasignaciones = ReasignacionTikects.objects.filter(agente_nuevo=agente_actual)
    tikects_reasignados = Tickets.objects.filter(id__in=[r.tikect.id for r in reasignaciones]).exclude(estado='cerrado').order_by('-fecha_creacion')
    asignaciones_servicios = AsignacionTikects.objects.filter(agente_actual=agente_actual)
    tikects_servicios = Tickets.objects.filter(servicio__in=[a.servicio for a in asignaciones_servicios]).exclude(estado='cerrado').order_by('-fecha_creacion')

    tikects_list = list(tikects_directos) + list(tikects_reasignados) + list(tikects_servicios)
    tikects_list.sort(key=lambda x: x.fecha_creacion, reverse=True)

    paginator = Paginator(tikects_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    reasignaciones_dict = {}
    try:
        for r in ReasignacionTikects.objects.all():
            if r.agente_nuevo and r.agente_nuevo.usuario:
                reasignaciones_dict[r.tikect.id] = r.agente_nuevo.usuario.username
    except:
        pass

    return render(request, 'tikects_asignados_agentes.html', {
        'tikects': page_obj,
        'reasignaciones_dict': reasignaciones_dict
    })

# ============================================
# ESTADÍSTICAS Y EXPORTACIONES
# ============================================

@superuser_required
@login_required
def tikects_estadisticas(request):
    total_tikects = Tickets.objects.count()
    tikects_cerrados = Tickets.objects.filter(estado='cerrado').count()
    tikects_abiertos = Tickets.objects.exclude(estado='cerrado').count()
    servicios = Tickets.objects.values('servicio__nombre').annotate(count=Count('servicio'))

    porcentaje_abiertos = (tikects_abiertos / total_tikects * 100) if total_tikects > 0 else 0
    porcentaje_cerrados = (tikects_cerrados / total_tikects * 100) if total_tikects > 0 else 0

    tikects_por_dia_cerrados = Tickets.objects.filter(estado='cerrado').values('fecha_cierre__date').annotate(count=Count('id')).order_by('fecha_cierre__date')
    tikects_por_mes_cerrados = Tickets.objects.filter(estado='cerrado').annotate(month=TruncMonth('fecha_cierre')).values('month').annotate(count=Count('id')).order_by('month')
    tikects_por_semana_cerrados = Tickets.objects.filter(estado='cerrado').annotate(week=TruncWeek('fecha_cierre')).values('week').annotate(count=Count('id')).order_by('week')

    # Tickets cerrados por agente
    tikects_por_agente = []
    try:
        agentes_ids = Tickets.objects.filter(estado='cerrado').exclude(
            cerrado_por_agente__isnull=True
        ).values_list('cerrado_por_agente', flat=True).distinct()

        for agente_id in agentes_ids:
            try:
                user = User.objects.get(id=agente_id)
                count = Tickets.objects.filter(estado='cerrado', cerrado_por_agente_id=agente_id).count()
                tikects_por_agente.append({
                    'cerrado_por_agente__username': user.username,
                    'cerrado_por_agente__first_name': user.first_name,
                    'cerrado_por_agente__last_name': user.last_name,
                    'count': count
                })
            except User.DoesNotExist:
                pass
        tikects_por_agente = sorted(tikects_por_agente, key=lambda x: x['count'], reverse=True)
    except Exception as e:
        print(f"Error en estadísticas de agentes: {e}")
        tikects_por_agente = []

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

@superuser_required
@login_required
def exportar_tikects_excel(request):
    servicio_seleccionado = request.GET.get('servicio', 'Todo')
    if servicio_seleccionado == 'Todo':
        tikects = Tickets.objects.filter(estado='cerrado')
    else:
        tikects = Tickets.objects.filter(estado='cerrado', servicio__nombre=servicio_seleccionado)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Tikects Cerrados"

    headers = ['ID', 'Título', 'Descripción', 'Usuario', 'Servicio', 'Fecha Creación', 'Fecha Cierre', 'Solución', 'Agente que cerró', 'Dirección']
    ws.append(headers)

    for t in tikects:
        ws.append([
            t.id,
            t.titulo,
            t.descripcion,
            t.usuario.username,
            t.servicio.nombre if t.servicio else '',
            t.fecha_creacion.strftime('%Y-%m-%d %H:%M') if t.fecha_creacion else '',
            t.fecha_cierre.strftime('%Y-%m-%d %H:%M') if t.fecha_cierre else '',
            t.descripcion_solucion or '',
            t.cerrado_por_agente.username if t.cerrado_por_agente else '',
            t.direccion or ''
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=tickets_cerrados_{servicio_seleccionado}.xlsx'
    wb.save(response)
    return response

@superuser_required
@login_required
def exportar_tikects_pdf(request):
    servicio_seleccionado = request.GET.get('servicio', 'Todo')
    if servicio_seleccionado == 'Todo':
        tikects = Tickets.objects.filter(estado='cerrado')
    else:
        tikects = Tickets.objects.filter(estado='cerrado', servicio__nombre=servicio_seleccionado)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=tickets_cerrados_{servicio_seleccionado}.pdf'

    c = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    x = 50
    y = height - 50
    line_height = 14

    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, f"Tickets Cerrados - {servicio_seleccionado}")
    y -= 30

    c.setFont("Helvetica-Bold", 10)
    headers = ['ID', 'Título', 'Usuario', 'Servicio', 'Fecha Cierre']
    col_widths = [40, 200, 100, 100, 80]
    x_pos = x
    for i, h in enumerate(headers):
        c.drawString(x_pos, y, h)
        x_pos += col_widths[i]
    y -= line_height

    c.setFont("Helvetica", 9)
    for t in tikects:
        x_pos = x
        c.drawString(x_pos, y, str(t.id))
        x_pos += col_widths[0]
        c.drawString(x_pos, y, t.titulo[:30])
        x_pos += col_widths[1]
        c.drawString(x_pos, y, t.usuario.username[:15])
        x_pos += col_widths[2]
        c.drawString(x_pos, y, t.servicio.nombre if t.servicio else '')
        x_pos += col_widths[3]
        c.drawString(x_pos, y, t.fecha_cierre.strftime('%Y-%m-%d') if t.fecha_cierre else '')
        y -= line_height
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 9)

    c.save()
    return response

# ============================================
# AGENTES GENÉRICOS (Asignación de servicios)
# ============================================

@superuser_required
@login_required
def agente_generico(request):
    if request.method == 'GET':
        servicios = Tickets_Servicios.objects.exclude(
            id__in=AsignacionTikects.objects.values_list('tikect__servicio', flat=True)
        )
        agentes = Agentes.objects.exclude(
            id__in=AsignacionTikects.objects.values_list('agente', flat=True)
        )
        return render(request, 'agente_generico.html', {
            'servicios': servicios,
            'agentes': agentes
        })
    else:
        servicio_id = request.POST.get('servicio')
        agente_actual_id = request.POST.get('agente')
        tiempo_reasignacion = request.POST.get('tiempo_reasignacion')
        agente_reasignacion_id = request.POST.get('agente_reasignacion')

        servicio = get_object_or_404(Tickets_Servicios, id=servicio_id)
        agente_actual = get_object_or_404(Agentes, id=agente_actual_id)
        agente_reasignacion = Agentes.objects.filter(id=agente_reasignacion_id).first() if agente_reasignacion_id else None
        tiempo = int(tiempo_reasignacion) if tiempo_reasignacion else None

        AsignacionTikects.objects.create(
            servicio=servicio,
            agente_actual=agente_actual,
            tiempo_reasignacion=tiempo,
            agente_reasignacion=agente_reasignacion
        )
        return redirect('ver_agentes_genericos')

@superuser_required
@login_required
def ver_agentes_genericos(request):
    asignaciones = AsignacionTikects.objects.all()
    return render(request, 'agentes_genericos_ver.html', {'asignaciones': asignaciones})

@superuser_required
@login_required
def eliminar_asignacion(request, asignacion_id):
    asignacion = get_object_or_404(AsignacionTikects, id=asignacion_id)
    if request.method == 'POST':
        asignacion.delete()
    return redirect('ver_agentes_genericos')

# ============================================
# PERMISOS
# ============================================

@superuser_required
@login_required
def permisos(request):
    agentes = Agentes.objects.all()
    grupos = Grupos_Agentes.objects.all()
    return render(request, 'permisos.html', {
        'agentes': agentes,
        'grupos': grupos
    })

# ============================================
# NOTIFICACIONES
# ============================================

def check_notifications(request):
    if request.user.is_authenticated:
        agente = getattr(request.user, 'agente', None)
        if agente:
            nuevas = Notificaciones.objects.filter(agente=agente, leida=False)
            notificaciones = [
                {'tikect_id': n.tikect.id, 'descripcion': n.descripcion}
                for n in nuevas
            ]
            return JsonResponse({
                'new_notifications': nuevas.exists(),
                'notifications': notificaciones
            })
    return JsonResponse({'new_notifications': False, 'notifications': []})

# ============================================
# CARGA MASIVA (EXCEL)
# ============================================

@superuser_required
@login_required
def registrar_usuarios(request):
    ruta = os.path.join(settings.BASE_DIR, 'usuarios_nuevos.xlsx')
    error = None
    if request.method == 'POST':
        try:
            df = pd.read_excel(ruta)
            required = ['Nombre', 'Apellido', 'usuario', 'Clave', 'Direccion', 'Correo']
            if not all(col in df.columns for col in required):
                raise ValueError("Columnas incorrectas")
            for _, row in df.iterrows():
                if not User.objects.filter(username=row['usuario']).exists():
                    user = User.objects.create_user(
                        username=row['usuario'],
                        password=row['Clave'],
                        email=row['Correo'],
                        first_name=row['Nombre'],
                        last_name=row['Apellido']
                    )
                    Cliente.objects.create(
                        nombre=row['Nombre'],
                        apellido=row['Apellido'],
                        nombre_usuario=row['usuario'],
                        email=row['Correo'],
                        telefono='000-000-0000',
                        direccion=row['Direccion'],
                        usuario=user
                    )
            return redirect('ver_cliente')
        except Exception as e:
            error = str(e)
    return render(request, 'registrar_usuarios.html', {'error': error})

@superuser_required
@login_required
def registrar_tickets_excel(request):
    ruta = os.path.join(settings.BASE_DIR, 'LISTA DE TICKETS CERRADOS.xlsx')
    if request.method == 'POST':
        try:
            df = pd.read_excel(ruta)
            for _, row in df.iterrows():
                try:
                    cliente = Cliente.objects.get(email=row['IDdelcliente'])
                except Cliente.DoesNotExist:
                    messages.warning(request, f"Cliente {row['IDdelcliente']} no encontrado")
                    continue
                try:
                    cola = Tickets_Colas.objects.get(nombre=row['Cola'])
                    servicio = Tickets_Servicios.objects.get(nombre=row['Servicio'])
                except (Tickets_Colas.DoesNotExist, Tickets_Servicios.DoesNotExist):
                    messages.warning(request, "Cola o servicio no encontrado")
                    continue

                creado = None
                cerrado_fecha = None
                if pd.notnull(row.get('Creado')):
                    try:
                        creado = datetime.strptime(str(row['Creado']).split('(')[0].strip(), '%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                if pd.notnull(row.get('Fechadecierre')):
                    try:
                        cerrado_fecha = datetime.strptime(str(row['Fechadecierre']).split('(')[0].strip(), '%Y-%m-%d %H:%M:%S')
                    except:
                        pass

                estado_bool = str(row.get('Estado', '')).lower() == 'cerrado'
                Tickets.objects.create(
                    titulo=row['Título'],
                    descripcion='',
                    fecha_creacion=creado,
                    cerrado=estado_bool,
                    estado='cerrado' if estado_bool else 'nuevo',
                    fecha_cierre=cerrado_fecha,
                    cola_perteneciente=cola,
                    servicio=servicio,
                    usuario=cliente.usuario,
                    direccion=cliente.direccion,
                    descripcion_solucion=''
                )
            messages.success(request, "Tickets importados correctamente")
            return redirect('ver_tikects')
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, 'registrar_tickets_excel.html')

# ============================================
# TRIAGE
# ============================================

@agente_or_superuser_required
def mesa_triage(request):
    tickets_nuevos = Tickets.objects.filter(
        Q(estado_triage='nuevo') | Q(estado_triage='triaje')
    ).order_by('-fecha_creacion')

    stats = {
        'total_pendientes': Tickets.objects.filter(estado_triage__in=['nuevo', 'triaje']).count(),
        'por_prioridad': {
            'critica': Tickets.objects.filter(prioridad='critica', estado_triage='nuevo').count(),
            'urgente': Tickets.objects.filter(prioridad='urgente', estado_triage='nuevo').count(),
            'alta': Tickets.objects.filter(prioridad='alta', estado_triage='nuevo').count(),
        },
        'por_tipo': list(Tickets.objects.values('tipo').filter(estado_triage='nuevo').annotate(total=Count('id'))),
    }

    prioridad = request.GET.get('prioridad', '')
    tipo = request.GET.get('tipo', '')
    busqueda = request.GET.get('busqueda', '')

    tickets_filtrados = tickets_nuevos
    if prioridad:
        tickets_filtrados = tickets_filtrados.filter(prioridad=prioridad)
    if tipo:
        tickets_filtrados = tickets_filtrados.filter(tipo=tipo)
    if busqueda:
        tickets_filtrados = tickets_filtrados.filter(
            Q(titulo__icontains=busqueda) |
            Q(descripcion__icontains=busqueda) |
            Q(usuario__username__icontains=busqueda)
        )

    paginator = Paginator(tickets_filtrados, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'tickets': page_obj,
        'stats': stats,
        'prioridad_actual': prioridad,
        'tipo_actual': tipo,
        'busqueda': busqueda,
        'prioridades': [('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta'),
                        ('urgente', 'Urgente'), ('critica', 'Crítica')],
        'tipos': [('bug', 'Bug/Error'), ('feature', 'Nueva Funcionalidad'),
                  ('support', 'Soporte'), ('consulta', 'Consulta'),
                  ('incidente', 'Incidente')],
    }
    return render(request, 'mesa_triage.html', context)

@agente_or_superuser_required
def procesar_triage(request, ticket_id):
    ticket = get_object_or_404(Tickets, id=ticket_id)
    if request.method == 'POST':
        ticket.tipo = request.POST.get('tipo')
        ticket.prioridad = request.POST.get('prioridad')
        ticket.estado_triage = request.POST.get('estado_triage', 'asignado')
        ticket.tiempo_resolucion_estimado = request.POST.get('tiempo_estimado')
        ticket.tags = request.POST.get('tags')
        ticket.notas_triage = request.POST.get('notas_triage')
        ticket.fecha_triage = datetime.now()

        if hasattr(request.user, 'agente'):
            ticket.agente_triage = request.user.agente

        agente_id = request.POST.get('agente_asignado')
        if agente_id:
            agente = Agentes.objects.get(id=agente_id)
            ticket.usuario = agente.usuario

        ticket.save()

        if ticket.estado_triage == 'asignado' and ticket.usuario and hasattr(ticket.usuario, 'agente'):
            Notificaciones.objects.create(
                tikect=ticket,
                descripcion="Ticket asignado tras triage",
                agente=ticket.usuario.agente,
                usuario_creador=request.user
            )
        return redirect('mesa_triage')

    agentes = Agentes.objects.all()
    colas = Tickets_Colas.objects.all()
    servicios = Tickets_Servicios.objects.all()
    context = {
        'ticket': ticket,
        'agentes': agentes,
        'colas': colas,
        'servicios': servicios,
        'prioridades': [('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta'),
                        ('urgente', 'Urgente'), ('critica', 'Crítica')],
        'tipos': [('bug', 'Bug/Error'), ('feature', 'Nueva Funcionalidad'),
                  ('support', 'Soporte'), ('consulta', 'Consulta'),
                  ('incidente', 'Incidente')],
        'estados_triage': [('nuevo', 'Nuevo'), ('triaje', 'En Triaje'),
                           ('asignado', 'Asignado'), ('rechazado', 'Rechazado')],
    }
    return render(request, 'procesar_triage.html', context)
