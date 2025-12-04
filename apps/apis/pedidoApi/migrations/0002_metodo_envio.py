from __future__ import annotations

import decimal

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('pedidoApi', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MetodoEnvio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255, unique=True)),
                ('tipo_transporte', models.CharField(max_length=50, unique=True)),
                ('descripcion', models.TextField(blank=True)),
                ('costo', models.DecimalField(decimal_places=2, default=decimal.Decimal('0.00'), max_digits=12, validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.00'))])),
                ('dias_estimados', models.CharField(default='3-5', max_length=50)),
                ('activo', models.BooleanField(default=True)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Método de Envío',
                'verbose_name_plural': 'Métodos de Envío',
                'ordering': ['nombre'],
            },
        ),
    ]
