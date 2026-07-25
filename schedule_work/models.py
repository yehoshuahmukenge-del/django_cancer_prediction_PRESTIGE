from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from users.models import Personnel, Etudiant


class Filiere(models.Model):
    """Filière d'études"""
    idfiliere = models.AutoField(primary_key=True)
    codfiliere = models.CharField(max_length=50, unique=True)
    libelle = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    responsable = models.ForeignKey(Personnel, on_delete=models.SET_NULL, null=True, blank=True, related_name='filieres_responsable')
    chef_filiere = models.ForeignKey(Personnel, on_delete=models.SET_NULL, null=True, blank=True, related_name='filieres_chef', help_text='Chef de filière (Personnel avec rôle Chef de filière)')
    
    class Meta:
        db_table = 'filiere'
        verbose_name = 'Filière'
        verbose_name_plural = 'Filières'
    
    def __str__(self):
        return f"{self.codfiliere} - {self.libelle}"
    
    def get_chef_filiere(self):
        """Retourne le chef de filière"""
        return self.chef_filiere


class Promotion(models.Model):
    """Promotion d'étudiants"""
    idpromotion = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=100)
    annee_debut = models.IntegerField()
    annee_fin = models.IntegerField()
    filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name='promotions')
    
    class Meta:
        db_table = 'promotion'
        verbose_name = 'Promotion'
        verbose_name_plural = 'Promotions'
        unique_together = ('libelle', 'filiere')
    
    def __str__(self):
        return f"{self.libelle} - {self.filiere}"


class Semestre(models.Model):
    """Semestre académique"""
    idsemestre = models.AutoField(primary_key=True)
    libsemestre = models.CharField(max_length=100)
    datedeb = models.DateField()
    datefin = models.DateField()
    
    class Meta:
        db_table = 'semestre'
        verbose_name = 'Semestre'
        verbose_name_plural = 'Semestres'
    
    def __str__(self):
        return self.libsemestre


class Cours(models.Model):
    """Cours/Matière"""
    idcours = models.AutoField(primary_key=True)
    codcours = models.CharField(max_length=50, unique=True)
    libelle = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    coefficient = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    credit = models.IntegerField(default=3, validators=[MinValueValidator(1)])
    filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name='cours')
    semestre = models.ForeignKey(Semestre, on_delete=models.CASCADE, related_name='cours')
    enseignant = models.ForeignKey(Personnel, on_delete=models.SET_NULL, null=True, blank=True, related_name='cours_enseignes')
    
    class Meta:
        db_table = 'cours'
        verbose_name = 'Cours'
        verbose_name_plural = 'Cours'
        unique_together = ('codcours', 'filiere')
    
    def __str__(self):
        return f"{self.codcours} - {self.libelle}"


class Inscription(models.Model):
    """Inscription d'un étudiant à un cours"""
    idinscription = models.AutoField(primary_key=True)
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='inscriptions')
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='inscriptions')
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='inscriptions')
    date_inscription = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(
        max_length=20,
        choices=[('active', 'Active'), ('suspendue', 'Suspendue'), ('terminee', 'Terminée')],
        default='active'
    )
    
    class Meta:
        db_table = 'inscription'
        verbose_name = 'Inscription'
        verbose_name_plural = 'Inscriptions'
        unique_together = ('etudiant', 'cours', 'promotion')
    
    def __str__(self):
        return f"{self.etudiant} - {self.cours}"


class Type_evaluation(models.Model):
    """Type d'évaluation (Contrôle continu, Examen, etc.)"""
    idtype = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    pourcentage_defaut = models.IntegerField(default=100, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    class Meta:
        db_table = 'type_evaluation'
        verbose_name = 'Type d\'évaluation'
        verbose_name_plural = 'Types d\'évaluation'
    
    def __str__(self):
        return self.libelle


class Cotation(models.Model):
    """Cotation/Note pour une évaluation"""
    idcotation = models.AutoField(primary_key=True)
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='cotations')
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='cotations')
    type_evaluation = models.ForeignKey(Type_evaluation, on_delete=models.CASCADE, related_name='cotations')
    note = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    date_saisie = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    saisie_par = models.ForeignKey(Personnel, on_delete=models.SET_NULL, null=True, related_name='cotations_saisies')
    
    class Meta:
        db_table = 'cotation'
        verbose_name = 'Cotation'
        verbose_name_plural = 'Cotations'
        unique_together = ('etudiant', 'cours', 'type_evaluation')
    
    def __str__(self):
        return f"{self.etudiant} - {self.cours} - {self.note}/20"


class Evaluation(models.Model):
    """Résultat d'évaluation d'un étudiant"""
    idevaluation = models.AutoField(primary_key=True)
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='evaluations')
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='evaluations')
    moyenne = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        null=True,
        blank=True
    )
    mention = models.CharField(
        max_length=50,
        choices=[
            ('excellent', 'Excellent'),
            ('bien', 'Bien'),
            ('assez_bien', 'Assez bien'),
            ('passable', 'Passable'),
            ('faible', 'Faible'),
        ],
        null=True,
        blank=True
    )
    statut = models.CharField(
        max_length=50,
        choices=[
            ('admis', 'Admis'),
            ('ajourné', 'Ajourné'),
            ('redoublant', 'Redoublant'),
        ],
        null=True,
        blank=True
    )
    date_calcul = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'evaluation'
        verbose_name = 'Évaluation'
        verbose_name_plural = 'Évaluations'
        unique_together = ('etudiant', 'cours')
    
    def __str__(self):
        return f"{self.etudiant} - {self.cours} - {self.moyenne}/20"
    
    def calculate_average(self):
        """Calcule la moyenne pondérée des cotations"""
        cotations = self.etudiant.cotations.filter(cours=self.cours)
        if not cotations.exists():
            return None
        
        total_note = sum(float(c.note) for c in cotations)
        return round(total_note / cotations.count(), 2)
    
    def get_mention(self):
        """Détermine la mention basée sur la moyenne"""
        if self.moyenne is None:
            return None
        
        moyenne = float(self.moyenne)
        if moyenne >= 16:
            return 'excellent'
        elif moyenne >= 14:
            return 'bien'
        elif moyenne >= 12:
            return 'assez_bien'
        elif moyenne >= 10:
            return 'passable'
        else:
            return 'faible'
    
    def get_statut(self):
        """Détermine le statut basé sur la moyenne"""
        if self.moyenne is None:
            return None
        
        moyenne = float(self.moyenne)
        if moyenne >= 10:
            return 'admis'
        elif moyenne >= 8:
            return 'redoublant'
        else:
            return 'ajourné'


class Horaire(models.Model):
    """Créneau de cours propre à une promotion."""

    JOURS = [
        (1, 'Lundi'),
        (2, 'Mardi'),
        (3, 'Mercredi'),
        (4, 'Jeudi'),
        (5, 'Vendredi'),
        (6, 'Samedi'),
    ]

    idhoraire = models.AutoField(primary_key=True)
    promotion = models.ForeignKey(
        Promotion,
        on_delete=models.CASCADE,
        related_name='horaires',
    )
    cours = models.ForeignKey(
        Cours,
        on_delete=models.PROTECT,
        related_name='horaires',
    )
    enseignant = models.ForeignKey(
        Personnel,
        on_delete=models.PROTECT,
        related_name='horaires',
        help_text="Personnel chargé de ce cours. La fonction reste portée par le personnel.",
    )
    jour = models.PositiveSmallIntegerField(choices=JOURS)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    salle = models.CharField(max_length=100, blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'horaire'
        verbose_name = 'Horaire'
        verbose_name_plural = 'Horaires'
        ordering = ('jour', 'heure_debut')
        constraints = [
            models.UniqueConstraint(
                fields=('promotion', 'jour', 'heure_debut'),
                name='horaire_promotion_creneau_unique',
            ),
        ]

    def __str__(self):
        return (
            f"{self.promotion} - {self.get_jour_display()} "
            f"{self.heure_debut:%H:%M} - {self.cours.libelle}"
        )

    def clean(self):
        errors = {}
        if self.heure_debut and self.heure_fin and self.heure_debut >= self.heure_fin:
            errors['heure_fin'] = "L'heure de fin doit être postérieure à l'heure de début."

        if self.promotion_id and self.cours_id:
            if self.promotion.filiere_id != self.cours.filiere_id:
                errors['cours'] = "Le cours doit appartenir à la filière de la promotion."

        if self.jour and self.heure_debut and self.heure_fin:
            overlaps = Horaire.objects.filter(
                jour=self.jour,
                heure_debut__lt=self.heure_fin,
                heure_fin__gt=self.heure_debut,
                actif=True,
            ).exclude(pk=self.pk)
            if self.promotion_id and overlaps.filter(promotion_id=self.promotion_id).exists():
                errors['heure_debut'] = "Cette promotion possède déjà un cours pendant ce créneau."
            if self.enseignant_id and overlaps.filter(enseignant_id=self.enseignant_id).exists():
                errors['enseignant'] = "Cet enseignant est déjà occupé pendant ce créneau."
            if self.salle and overlaps.filter(salle__iexact=self.salle).exists():
                errors['salle'] = "Cette salle est déjà occupée pendant ce créneau."

        if errors:
            raise ValidationError(errors)
