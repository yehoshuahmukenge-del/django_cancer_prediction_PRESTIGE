from django.db import models

class Prediction(models.Model):
    RESULT_CHOICES = [
        (0, 'Sain'),
        (1, 'Cancer'),
    ]
    
    taille_tumeur = models.FloatField()
    densite_mammaire = models.IntegerField()
    age_patiente = models.IntegerField()
    niveau_ca125 = models.FloatField()
    
    probabilite_cancer = models.FloatField()
    resultat = models.IntegerField(choices=RESULT_CHOICES)
    
    date_prediction = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_prediction']
    
    def __str__(self):
        return f"Prédiction {self.id} - {self.get_resultat_display()}"
