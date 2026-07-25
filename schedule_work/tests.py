from datetime import date, time

from django.test import TestCase
from django.urls import reverse

from users.models import Etudiant, Fonction, Personnel, Role, Utilisateur, UtilisateurRole
from .models import Cours, Filiere, Horaire, Inscription, Promotion, Semestre


class EmploiDuTempsAccessTests(TestCase):
    def setUp(self):
        self.role_etudiant = Role.objects.create(libelle='Étudiant')
        self.fonction = Fonction.objects.create(libelle='Professeur')
        prof_user = Utilisateur.objects.create_user(
            username='prof', email='prof@example.com', nom='Prof', prenom='Test'
        )
        self.prof = Personnel.objects.create(
            utilisateur=prof_user,
            grade='Professeur',
            fonction=self.fonction,
            date_embauche=date(2020, 1, 1),
        )
        self.filiere = Filiere.objects.create(
            codfiliere='INFO', libelle='Informatique', responsable=self.prof
        )
        self.promotion_a = Promotion.objects.create(
            libelle='L3 A', annee_debut=2025, annee_fin=2026, filiere=self.filiere
        )
        self.promotion_b = Promotion.objects.create(
            libelle='L2 B', annee_debut=2025, annee_fin=2026, filiere=self.filiere
        )
        semestre = Semestre.objects.create(
            libsemestre='Second semestre', datedeb=date(2026, 2, 1), datefin=date(2026, 7, 1)
        )
        self.cours_a = Cours.objects.create(
            codcours='SEC', libelle='Sécurité', filiere=self.filiere,
            semestre=semestre, enseignant=self.prof,
        )
        self.cours_b = Cours.objects.create(
            codcours='WEB', libelle='Développement Web', filiere=self.filiere,
            semestre=semestre, enseignant=self.prof,
        )
        Horaire.objects.create(
            promotion=self.promotion_a, cours=self.cours_a, enseignant=self.prof,
            jour=1, heure_debut=time(8), heure_fin=time(11, 20), salle='A1',
        )
        Horaire.objects.create(
            promotion=self.promotion_b, cours=self.cours_b, enseignant=self.prof,
            jour=2, heure_debut=time(12), heure_fin=time(15), salle='B2',
        )
        self.user = Utilisateur.objects.create_user(
            username='student', email='student@example.com', nom='Student', prenom='One'
        )
        UtilisateurRole.objects.create(utilisateur=self.user, role=self.role_etudiant)
        student = Etudiant.objects.create(utilisateur=self.user, matricule='ET-001')
        Inscription.objects.create(
            etudiant=student, cours=self.cours_a, promotion=self.promotion_a, statut='active'
        )

    def test_student_cannot_force_another_promotion_in_query_string(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse('emploi_du_temps'), {'promotion': self.promotion_b.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['promotion'], self.promotion_a)
        self.assertContains(response, 'Sécurité')
        self.assertNotContains(response, 'Développement Web')

    def test_fonction_is_attached_to_personnel_not_course(self):
        self.assertEqual(self.prof.fonction, self.fonction)
        self.assertFalse(any(field.name == 'fonction' for field in Cours._meta.get_fields()))
