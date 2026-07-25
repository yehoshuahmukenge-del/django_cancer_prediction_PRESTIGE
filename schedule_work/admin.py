from django.contrib import admin
from .models import Filiere, Promotion, Semestre, Cours, Inscription, Type_evaluation, Cotation, Evaluation, Horaire


@admin.register(Filiere)
class FiliereAdmin(admin.ModelAdmin):
    list_display = ('codfiliere', 'libelle', 'responsable')
    search_fields = ('codfiliere', 'libelle')


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'annee_debut', 'annee_fin', 'filiere')
    search_fields = ('libelle', 'filiere__libelle')
    list_filter = ('annee_debut', 'filiere')


@admin.register(Semestre)
class SemestreAdmin(admin.ModelAdmin):
    list_display = ('libsemestre', 'datedeb', 'datefin')
    search_fields = ('libsemestre',)


@admin.register(Cours)
class CoursAdmin(admin.ModelAdmin):
    list_display = ('codcours', 'libelle', 'filiere', 'semestre', 'coefficient', 'credit')
    search_fields = ('codcours', 'libelle')
    list_filter = ('filiere', 'semestre')


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'cours', 'promotion', 'statut', 'date_inscription')
    search_fields = ('etudiant__utilisateur__username', 'cours__libelle')
    list_filter = ('statut', 'promotion')


@admin.register(Type_evaluation)
class Type_evaluationAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'pourcentage_defaut')
    search_fields = ('libelle',)


@admin.register(Cotation)
class CotationAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'cours', 'type_evaluation', 'note', 'date_saisie')
    search_fields = ('etudiant__utilisateur__username', 'cours__libelle')
    list_filter = ('type_evaluation', 'date_saisie')


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'cours', 'moyenne', 'mention', 'statut')
    search_fields = ('etudiant__utilisateur__username', 'cours__libelle')
    list_filter = ('mention', 'statut')


@admin.register(Horaire)
class HoraireAdmin(admin.ModelAdmin):
    list_display = (
        'promotion', 'jour_libelle', 'heure_debut', 'heure_fin',
        'cours', 'enseignant', 'salle', 'actif',
    )
    list_filter = ('promotion__filiere', 'promotion', 'jour', 'actif')
    search_fields = (
        'promotion__libelle', 'cours__libelle', 'cours__codcours',
        'enseignant__utilisateur__nom', 'enseignant__utilisateur__prenom', 'salle',
    )
    autocomplete_fields = ('promotion', 'cours', 'enseignant')
    ordering = ('promotion', 'jour', 'heure_debut')

    @admin.display(description='Jour', ordering='jour')
    def jour_libelle(self, obj):
        return obj.get_jour_display()
