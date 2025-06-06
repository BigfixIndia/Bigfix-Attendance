# Generated by Django 5.2 on 2025-04-22 04:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0010_attendance_log'),
    ]

    operations = [
        migrations.CreateModel(
            name='Holiday',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('date', models.DateField()),
            ],
            options={
                'db_table': 'Holiday',
            },
        ),
        migrations.AlterUniqueTogether(
            name='attendance_attendance_data',
            unique_together=set(),
        ),
        migrations.AlterModelTable(
            name='attendance_log',
            table='attendance_log',
        ),
    ]
