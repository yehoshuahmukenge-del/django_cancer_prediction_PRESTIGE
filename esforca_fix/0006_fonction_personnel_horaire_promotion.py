from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [('core', '0005_alter_chrono_horaire_jours_and_more')]

    operations = [
        migrations.AddField(
            model_name='personnel',
            name='fonction',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='personnels',
                to='core.fonction',
            ),
        ),
        migrations.AddField(
            model_name='chrono_horaire',
            name='promotion',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='horaires',
                to='core.promotion',
            ),
        ),
        migrations.RemoveField(
            model_name='chrono_horaire',
            name='fonction',
        ),
        migrations.AddConstraint(
            model_name='chrono_horaire',
            constraint=models.UniqueConstraint(
                fields=('jours', 'heure', 'promotion'),
                name='unique_creneau_promotion',
            ),
        ),
    ]
