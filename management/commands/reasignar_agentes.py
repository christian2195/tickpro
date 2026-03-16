# tikects_app/management/commands/reasignar_agentes.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tikects_app.models import AsignacionTikects

class Command(BaseCommand):
    help = 'Reasigna agentes según el tiempo configurado'

    def handle(self, *args, **options):
        ahora = timezone.now()
        asignaciones = AsignacionTikects.objects.filter(
            tiempo_reasignacion__isnull=False,
            agente_reasignacion__isnull=False
        )
        
        for asignacion in asignaciones:
            # Aquí deberías tener lógica para determinar cuándo reasignar
            # Por ejemplo, basado en la fecha de creación o última actividad
            self.stdout.write(
                self.style.SUCCESS(f'Reasignando servicio {asignacion.servicio.nombre}')
            )