# Generated by Django 3.2.5 on 2021-11-01 18:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Activities',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activity_type', models.CharField(choices=[('Duty', 'Duty'), ('Sleep', 'Sleep')], default='Duty', max_length=100)),
                ('start_date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('end_time', models.TimeField(blank=True, null=True)),
                ('status', models.CharField(blank=True, choices=[('Running', 'Running'), ('Sleeping', 'Sleeping'), ('Stopped', 'Stopped')], default='Running', max_length=100)),
                ('driver', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='driver_activity', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Activity',
                'verbose_name_plural': 'Activities',
            },
        ),
        migrations.CreateModel(
            name='Holidays',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(unique=True)),
                ('title', models.CharField(max_length=200)),
            ],
            options={
                'verbose_name': 'Holiday',
                'verbose_name_plural': 'Holidays',
            },
        ),
        migrations.CreateModel(
            name='Trips',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('duty_start_time', models.TimeField()),
                ('duty_end_time', models.TimeField()),
                ('duty_hour', models.CharField(max_length=20)),
                ('sleep_start_time', models.TimeField()),
                ('sleep_end_time', models.TimeField()),
                ('sleep_hour', models.CharField(max_length=20)),
                ('driver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='driver_trip', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Trip',
                'verbose_name_plural': 'Trips',
            },
        ),
        migrations.CreateModel(
            name='SleepMode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sleep_start_date', models.DateField()),
                ('sleep_start', models.TimeField()),
                ('sleep_end_date', models.DateField(blank=True, null=True)),
                ('sleep_end', models.TimeField(blank=True, null=True)),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sleep_activity', to='core.activities')),
            ],
        ),
        migrations.CreateModel(
            name='Leave',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('leave_type', models.CharField(choices=[('Urlaub', 'Urlaub'), ('Sonderurlaub', 'Sonderurlaub'), ('Krank', 'Krank'), ('Zeitausgleich', 'Zeitausgleich')], default='Urlaub', max_length=200)),
                ('special_leave_reason', models.CharField(blank=True, choices=[('Eheschließung eines Kindes', 'Eheschließung eines Kindes'), ('Umzug innerhalb des Ortes', 'Umzug innerhalb des Ortes'), ('Prüfung im Ausbildungsberuf', 'Prüfung im Ausbildungsberuf'), ('Tod des Ehegatten oder Lebenspartnern', 'Tod des Ehegatten oder Lebenspartnern'), ('Tod des Kindes', 'Tod des Kindes'), ('Tod eines Eltern- oder Stiefelternteils', 'Tod eines Eltern- oder Stiefelternteils'), ('Tod eines Schwiegerelternteils', 'Tod eines Schwiegerelternteils'), ('eigene Eheschließung', 'eigene Eheschließung'), ('Geburt des eigenen Kindes', 'Geburt des eigenen Kindes'), ('Umzug außerhalb des Ortes ', 'Umzug außerhalb des Ortes')], default='Eheschließung eines Kindes', max_length=200)),
                ('from_date', models.DateField()),
                ('to_date', models.DateField()),
                ('message', models.TextField(blank=True)),
                ('leave_status', models.CharField(choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Decline', 'Decline')], default='Pending', max_length=100)),
                ('status_updated_date', models.DateField(auto_now=True)),
                ('driver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='driver_leave', to=settings.AUTH_USER_MODEL)),
                ('status_updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='status_updater', to=settings.AUTH_USER_MODEL, to_field='username')),
            ],
        ),
    ]