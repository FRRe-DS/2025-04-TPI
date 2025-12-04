"""
Management command para inicializar métodos de envío en la base de datos.

Uso:
    python manage.py init_metodos_envio
    
Este comando:
1. Crea los métodos de envío estándar si no existen.
2. Se ejecuta de forma segura incluso si algunos ya existen.
3. Puede ejecutarse múltiples veces sin causar errores.

Métodos creados:
- Envío estándar (road): Entrega a domicilio, costo 0, 2-5 días
- Envío express (air): Entrega aérea, costo 0, 1-3 días  
- Envío marítimo (sea): Entrega marítima, costo 0, 5-7 días
- Envío por tren (rail): Entrega por ferrocarril, costo 0, 3-5 días
- Retiro en sucursal (retiro_sucursal): Retiro en sucursal, costo 0, 1-2 días
- Demo con seguimiento (demo_tracking): Seguimiento de demo, costo 0, 1 día
"""

from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import logging

from apps.apis.pedidoApi.models import MetodoEnvio

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Inicializa los métodos de envío en la base de datos.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Elimina todos los métodos de envío existentes y los recrea.',
        )

    def handle(self, *args, **options):
        reset = options.get('reset', False)
        
        if reset:
            self.stdout.write(self.style.WARNING('Eliminando métodos de envío existentes...'))
            MetodoEnvio.objects.all().delete()
            logger.info("Se eliminaron todos los métodos de envío existentes.")

        # Definir métodos de envío estándar
        metodos_estandar = [
            {
                'nombre': 'Envío estándar',
                'tipo_transporte': 'road',
                'descripcion': 'Entrega a domicilio por transporte terrestre (2-5 días hábiles)',
                'costo': Decimal('0.00'),
                'dias_estimados': '2-5',
                'activo': True,
            },
            {
                'nombre': 'Envío express',
                'tipo_transporte': 'air',
                'descripcion': 'Entrega urgente por transporte aéreo (1-3 días hábiles)',
                'costo': Decimal('0.00'),
                'dias_estimados': '1-3',
                'activo': True,
            },
            {
                'nombre': 'Envío marítimo',
                'tipo_transporte': 'sea',
                'descripcion': 'Entrega por transporte marítimo (5-7 días hábiles)',
                'costo': Decimal('0.00'),
                'dias_estimados': '5-7',
                'activo': True,
            },
            {
                'nombre': 'Envío por tren',
                'tipo_transporte': 'rail',
                'descripcion': 'Entrega por transporte ferroviario (3-5 días hábiles)',
                'costo': Decimal('0.00'),
                'dias_estimados': '3-5',
                'activo': True,
            },
            {
                'nombre': 'Retiro en sucursal',
                'tipo_transporte': 'retiro_sucursal',
                'descripcion': 'Retiro en sucursal (1-2 días hábiles)',
                'costo': Decimal('0.00'),
                'dias_estimados': '1-2',
                'activo': True,
            },
            {
                'nombre': 'Demo con seguimiento',
                'tipo_transporte': 'demo_tracking',
                'descripcion': 'Envío de demostración con seguimiento integrado (1 día)',
                'costo': Decimal('0.00'),
                'dias_estimados': '1',
                'activo': True,
            },
            {
                'nombre': 'Envío a domicilio',
                'tipo_transporte': 'domicilio',
                'descripcion': 'Envío estándar a domicilio (2-5 días hábiles)',
                'costo': Decimal('0.00'),
                'dias_estimados': '2-5',
                'activo': True,
            },
        ]

        created_count = 0
        updated_count = 0
        
        try:
            with transaction.atomic():
                for metodo_data in metodos_estandar:
                    tipo_transporte = metodo_data['tipo_transporte']
                    metodo, created = MetodoEnvio.objects.get_or_create(
                        tipo_transporte=tipo_transporte,
                        defaults=metodo_data
                    )
                    
                    if created:
                        created_count += 1
                        logger.info(f"Método de envío creado: {metodo.nombre}")
                        self.stdout.write(
                            self.style.SUCCESS(f"✓ Creado: {metodo.nombre} ({tipo_transporte})")
                        )
                    else:
                        # Actualizar si es necesario (en caso de que reset=True)
                        if reset or not metodo.nombre or not metodo.descripcion:
                            for key, value in metodo_data.items():
                                setattr(metodo, key, value)
                            metodo.save()
                            updated_count += 1
                            logger.info(f"Método de envío actualizado: {metodo.nombre}")
                            self.stdout.write(
                                self.style.WARNING(f"↻ Actualizado: {metodo.nombre} ({tipo_transporte})")
                            )
                        else:
                            self.stdout.write(
                                self.style.SUCCESS(f"✓ Ya existe: {metodo.nombre} ({tipo_transporte})")
                            )

        except Exception as e:
            logger.exception(f"Error inicializando métodos de envío: {e}")
            raise CommandError(f"Error al inicializar métodos de envío: {e}")

        # Resumen final
        total_metodos = MetodoEnvio.objects.count()
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS(f'Inicialización completada exitosamente'))
        self.stdout.write(self.style.SUCCESS(f'  - Métodos creados: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'  - Métodos actualizados: {updated_count}'))
        self.stdout.write(self.style.SUCCESS(f'  - Total de métodos en BD: {total_metodos}'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        logger.info(
            f"Inicialización de métodos de envío completada: "
            f"{created_count} creados, {updated_count} actualizados, "
            f"{total_metodos} total"
        )
