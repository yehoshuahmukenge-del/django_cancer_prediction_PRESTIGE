from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UtilisateurManager(BaseUserManager):
    def create_user(self, email, nom, post_nom, sexe, password=None):
        if not email:
            raise ValueError("L'utilisateur doit avoir une adresse email")
        user = self.model(
            email=self.normalize_email(email),
            nom=nom,
            post_nom=post_nom,
            sexe=sexe,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nom, post_nom, sexe, password=None):
        user = self.create_user(email, nom, post_nom, sexe, password)
        user.is_admin = True
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user

class Utilisateur(AbstractBaseUser, PermissionsMixin):
    SEXE_CHOICES = [('M', 'Masculin'), ('F', 'Féminin')]
    id_user = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100)
    post_nom = models.CharField(max_length=100)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = UtilisateurManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom', 'post_nom', 'sexe']

    def __str__(self):
        return f"{self.nom} {self.post_nom}"

    def a_role(self, libelle):
        """Point unique de contrôle des rôles définis par le diagramme UML."""
        return self.roles_associes.filter(role__libelle=libelle).exists()

class Personnel(Utilisateur):
    matricule = models.CharField(max_length=50, unique=True, null=True)
    grade = models.CharField(max_length=100, null=True)
    fonction = models.ForeignKey(
        'Fonction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='personnels',
    )
    
    class Meta:
        verbose_name = "Personnel"
        verbose_name_plural = "Personnels"

class Role(models.Model):
    id_role = models.AutoField(primary_key=True)
    libelle = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.libelle

class Utilisateur_Role(models.Model):
    id_util = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='roles_associes')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    class Meta:
        unique_together = ('id_util', 'role')

class Filiere(models.Model):
    id_filiere = models.AutoField(primary_key=True)
    nom_filiere = models.CharField(max_length=200, unique=True)
    def __str__(self): return self.nom_filiere

class Promotion(models.Model):
    id_prom = models.AutoField(primary_key=True)
    designation = models.CharField(max_length=200)
    annee_academique = models.CharField(max_length=20)
    filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name='promotions')
    def __str__(self): return f"{self.designation} ({self.annee_academique})"

    class Meta:
        constraints = [models.UniqueConstraint(fields=('designation', 'annee_academique', 'filiere'), name='unique_promotion_filiere_annee')]

class Etudiant(Utilisateur):
    num_matric = models.CharField(max_length=50, unique=True, null=True)
    date_naiss = models.DateField(null=True)
    promotion = models.ForeignKey(Promotion, on_delete=models.SET_NULL, null=True, related_name='etudiants')
    
    class Meta:
        verbose_name = "Etudiant"
        verbose_name_plural = "Etudiants"

class Cours(models.Model):
    id_cours = models.AutoField(primary_key=True)
    titre = models.CharField(max_length=200)
    duree = models.PositiveIntegerField(help_text="Durée en minutes")
    def __str__(self): return self.titre

class Fonction(models.Model):
    id_fonction = models.AutoField(primary_key=True)
    intitule = models.CharField(max_length=100)
    def __str__(self): return self.intitule

class Chrono_Horaire(models.Model):
    JOURS_CHOICES = [(jour, jour) for jour in ('Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi')]
    STATUS_CHOICES = [
        ('DRAFT', 'Brouillon'),
        ('PROPOSED', 'Proposé (Chef Filière)'),
        ('CONFIRMED', 'Confirmé (SGA)'),
        ('PUBLISHED', 'Publié'),
    ]
    id_chrono = models.AutoField(primary_key=True)
    heure = models.TimeField()
    jours = models.CharField(max_length=20, choices=JOURS_CHOICES)
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE, related_name='horaires')
    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='dispense_cours')
    promotion = models.ForeignKey(
        Promotion,
        on_delete=models.CASCADE,
        related_name='horaires',
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    annotations = models.TextField(blank=True, null=True, help_text="Annotations ou demandes de modification de l'enseignant")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('jours', 'heure', 'personnel'), name='unique_creneau_personnel'),
            models.UniqueConstraint(fields=('jours', 'heure', 'promotion'), name='unique_creneau_promotion'),
        ]
    
    def __str__(self):
        return f"{self.jours} {self.heure} - {self.cours.titre}"

    def peut_transitionner_vers(self, nouvel_etat):
        transitions = {
            'DRAFT': {'PROPOSED'},
            'PROPOSED': {'DRAFT', 'CONFIRMED'},
            'CONFIRMED': {'PUBLISHED'},
            'PUBLISHED': set(),
        }
        return nouvel_etat in transitions.get(self.status, set())

    def transitionner(self, nouvel_etat):
        if not self.peut_transitionner_vers(nouvel_etat):
            raise ValueError(f"Transition interdite : {self.status} vers {nouvel_etat}")
        self.status = nouvel_etat
        self.save(update_fields=['status'])

class Disponibilite(models.Model):
    enseignant = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='disponibilites')
    jour = models.CharField(max_length=20)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    note = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Disponibilité"
        verbose_name_plural = "Disponibilités"
        constraints = [models.CheckConstraint(check=models.Q(heure_fin__gt=models.F('heure_debut')), name='disponibilite_fin_apres_debut')]
