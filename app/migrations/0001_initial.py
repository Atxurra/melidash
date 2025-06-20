# Generated by Django 4.2.21 on 2025-06-02 15:11

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProcessedFile',
            fields=[
                ('file_path', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('file_hash', models.CharField(max_length=32)),
                ('last_processed', models.DateTimeField()),
            ],
            options={
                'ordering': ['-last_processed'],
            },
        ),
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('publication_name', models.CharField(max_length=255, unique=True)),
                ('created_at', models.DateField(default=datetime.datetime.now)),
            ],
            options={
                'ordering': ['publication_name'],
            },
        ),
        migrations.CreateModel(
            name='UnassignedPublication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('publication_name', models.CharField(max_length=255, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='Supply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('supply_name', models.CharField(max_length=255, unique=True)),
                ('total_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('units', models.IntegerField(blank=True, null=True)),
                ('purchase_date', models.DateField(blank=True, default=datetime.datetime.now, null=True)),
                ('publication', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='supplies', to='app.publication')),
            ],
            options={
                'ordering': ['-purchase_date'],
            },
        ),
        migrations.CreateModel(
            name='Sale',
            fields=[
                ('sale_id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('buyer', models.CharField(blank=True, max_length=255)),
                ('status', models.CharField(blank=True, max_length=100)),
                ('sale_date', models.DateField(blank=True, null=True)),
                ('dispatch_date', models.DateField(blank=True, null=True)),
                ('delivery_method', models.CharField(blank=True, max_length=100)),
                ('units', models.IntegerField(blank=True, null=True)),
                ('income', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('transaction_costs', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=12, null=True)),
                ('shipping_costs', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=12, null=True)),
                ('refunds', models.DecimalField(blank=True, decimal_places=2, default=0.0, max_digits=12, null=True)),
                ('total', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('source', models.CharField(blank=True, max_length=100)),
                ('previous_units', models.IntegerField(blank=True, null=True)),
                ('previous_status', models.CharField(blank=True, max_length=100, null=True)),
                ('previous_total', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('arrived', models.BooleanField(default=False)),
                ('publication', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sales', to='app.publication')),
            ],
            options={
                'ordering': ['-sale_date'],
            },
        ),
        migrations.CreateModel(
            name='PublicityCost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cost', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('date', models.DateField(blank=True, default=datetime.datetime.now, null=True)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('publication', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='publicity_costs', to='app.publication')),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
    ]
