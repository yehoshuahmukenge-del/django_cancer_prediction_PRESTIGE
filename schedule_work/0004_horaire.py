from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academic', '0003_filiere_chef_filiere'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Horaire',
            fields=[
                ('idhoraire', models.AutoField(primary_key=True, serialize=False)),
                ('jour', models.PositiveSmallIntegerField(choices=[(1, 'Lundi'), (2, 'Mardi'), (3, 'Mercredi'), (4, 'Jeudi'), (5, 'Vendredi'), (6, 'Samedi')])),
                ('heure_debut', models.TimeField()),
                ('heure_fin', models.TimeField()),
                ('salle', models.CharField(blank=True, max_length=100)),
                ('actif', models.BooleanField(default=True)),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('cours', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='horaires', to='academic.cours')),
                ('enseignant', models.ForeignKey(help_text='Personnel chargé de ce cours. La fonction reste portée par le personnel.', on_delete=django.db.models.deletion.PROTECT, related_name='horaires', to='users.personnel')),
                ('promotion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='horaires', to='academic.promotion')),
            ],
            options={
                'verbose_name': 'Horaire',
                'verbose_name_plural': 'Horaires',
                'db_table': 'horaire',
                'ordering': ('jour', 'heure_debut'),
            },
        ),
        migrations.AddConstraint(
            model_name='horaire',
            constraint=models.UniqueConstraint(fields=('promotion', 'jour', 'heure_debut'), name='horaire_promotion_creneau_unique'),
        ),
    ]
