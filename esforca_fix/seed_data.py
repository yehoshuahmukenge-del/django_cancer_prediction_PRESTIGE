import datetime
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.core.models import (  # noqa: E402
    Chrono_Horaire,
    Cours,
    Etudiant,
    Filiere,
    Fonction,
    Personnel,
    Promotion,
    Role,
    Utilisateur_Role,
)


PASSWORD = "password123"


def seed():
    print("Début du peuplement de la base de données Horaires ESFORCA...")

    roles = {
        name: Role.objects.get_or_create(libelle=name)[0]
        for name in ("Chef de Filière", "Enseignant", "Étudiant", "SG-A")
    }

    # Une fonction décrit la responsabilité du PERSONNEL, jamais le type du cours.
    fonctions = {
        name: Fonction.objects.get_or_create(intitule=name)[0]
        for name in (
            "Chef de filière",
            "Enseignant",
            "Secrétaire Général Académique",
        )
    }

    filiere, _ = Filiere.objects.get_or_create(nom_filiere="Génie Informatique")
    promotions = {
        designation: Promotion.objects.get_or_create(
            designation=designation,
            annee_academique="2025-2026",
            filiere=filiere,
        )[0]
        for designation in ("L1 LMD", "L2 LMD", "L3 INFO A (LMD - GOMBE)")
    }

    def create_personnel(email, nom, post_nom, matricule, grade, fonction, *role_names):
        person = Personnel.objects.filter(email=email).first()
        if not person:
            person = Personnel.objects.create_user(
                email=email,
                nom=nom,
                post_nom=post_nom,
                sexe="M",
                password=PASSWORD,
            )
        matricule_utilise = Personnel.objects.filter(matricule=matricule).exclude(pk=person.pk).exists()
        person.matricule = f"DEMO-{matricule}" if matricule_utilise else matricule
        person.grade = grade
        person.fonction = fonctions[fonction]
        person.save()
        for role_name in role_names:
            Utilisateur_Role.objects.get_or_create(id_util=person, role=roles[role_name])
        return person

    chef = create_personnel(
        "chef@demo.com", "MUKENDI", "Alain", "P001", "Professeur",
        "Chef de filière", "Chef de Filière", "Enseignant",
    )
    sga = create_personnel(
        "sga@demo.com", "KASSONGO", "Bibiche", "P002", "Secrétaire Général",
        "Secrétaire Général Académique", "SG-A",
    )
    sga.is_staff = True
    sga.is_superuser = True
    sga.save(update_fields=("is_staff", "is_superuser"))

    teacher_specs = (
        ("lukele@demo.com", "LUKELE", "Paul", "P010", "Professeur"),
        ("kabisayi@demo.com", "KABISAYI", "Trésor", "P011", "Chef de Travaux"),
        ("babanemi@demo.com", "BABANEMI", "Jean", "P012", "Assistant"),
        ("senda@demo.com", "SENDA", "Marc", "P013", "Assistant"),
        ("tembo@demo.com", "TEMBO", "Alain", "P014", "Chef de Travaux"),
        ("makolo@demo.com", "MAKOLO", "David", "P015", "Assistant"),
        ("kalumbu@demo.com", "KALUMBU", "Patrick", "P016", "Assistant"),
        ("kakafuka@demo.com", "KAKAFUKA", "Joseph", "P017", "Professeur"),
        ("kadima@demo.com", "KADIMA", "Rachel", "P018", "Assistante"),
        ("vumisa@demo.com", "VUMISA", "Eric", "P019", "Chef de Travaux"),
    )
    teachers = [
        create_personnel(email, nom, post_nom, matricule, grade, "Enseignant", "Enseignant")
        for email, nom, post_nom, matricule, grade in teacher_specs
    ]

    def create_student(email, nom, post_nom, matricule, promotion):
        student = Etudiant.objects.filter(email=email).first()
        if not student:
            student = Etudiant.objects.create_user(
                email=email,
                nom=nom,
                post_nom=post_nom,
                sexe="M",
                password=PASSWORD,
            )
        matricule_utilise = Etudiant.objects.filter(num_matric=matricule).exclude(pk=student.pk).exists()
        student.num_matric = f"DEMO-{matricule}" if matricule_utilise else matricule
        student.date_naiss = datetime.date(2003, 1, 1)
        student.promotion = promotion
        student.save()
        Utilisateur_Role.objects.get_or_create(id_util=student, role=roles["Étudiant"])
        return student

    create_student("etudiant@demo.com", "LUMUMBA", "Patrice", "S001", promotions["L3 INFO A (LMD - GOMBE)"])
    create_student("etudiant.l2@demo.com", "ILUNGA", "Sarah", "S002", promotions["L2 LMD"])
    create_student("etudiant.l1@demo.com", "MUTOMBO", "Grâce", "S003", promotions["L1 LMD"])

    course_specs = (
        ("Sécurité", 200),
        ("Mobile", 200),
        ("Cryptographie", 200),
        ("ASP", 200),
        ("Atelier UML", 200),
        ("WINDEV", 200),
        ("Droit Informatique", 200),
        ("Audit Informatique", 200),
        ("Anglais", 200),
        ("Intelligence Artificielle", 200),
        ("Algorithmique", 120),
        ("Base de données", 120),
    )
    courses = {
        title: Cours.objects.update_or_create(titre=title, defaults={"duree": duration})[0]
        for title, duration in course_specs
    }

    # Horaire L3 conforme au document fourni. Chaque ligne porte sa promotion.
    l3_slots = (
        ("Lundi", "08:00", "Sécurité", 0, "PUBLISHED"),
        ("Mardi", "08:00", "Mobile", 1, "PUBLISHED"),
        ("Mercredi", "08:00", "Cryptographie", 2, "PUBLISHED"),
        ("Jeudi", "08:00", "ASP", 3, "PUBLISHED"),
        ("Vendredi", "08:00", "Atelier UML", 4, "PUBLISHED"),
        ("Samedi", "08:00", "WINDEV", 5, "PUBLISHED"),
        ("Mardi", "11:40", "Droit Informatique", 6, "PUBLISHED"),
        ("Mercredi", "11:40", "Audit Informatique", 7, "PUBLISHED"),
        ("Jeudi", "11:40", "Anglais", 8, "PUBLISHED"),
        ("Vendredi", "11:40", "Intelligence Artificielle", 9, "PUBLISHED"),
    )
    for day, start, title, teacher_index, status in l3_slots:
        Chrono_Horaire.objects.update_or_create(
            jours=day,
            heure=datetime.time.fromisoformat(start),
            personnel=teachers[teacher_index],
            defaults={
                "cours": courses[title],
                "promotion": promotions["L3 INFO A (LMD - GOMBE)"],
                "status": status,
            },
        )

    # Promotions L1 et L2 : créneaux distincts pour démontrer l'isolation.
    other_slots = (
        (promotions["L1 LMD"], "Lundi", "13:00", courses["Algorithmique"], teachers[0]),
        (promotions["L1 LMD"], "Mercredi", "13:00", courses["Base de données"], teachers[1]),
        (promotions["L2 LMD"], "Mardi", "15:30", courses["Algorithmique"], teachers[2]),
        (promotions["L2 LMD"], "Jeudi", "15:30", courses["Base de données"], teachers[3]),
    )
    for promotion, day, start, course, teacher in other_slots:
        Chrono_Horaire.objects.update_or_create(
            jours=day,
            heure=datetime.time.fromisoformat(start),
            personnel=teacher,
            defaults={
                "cours": course,
                "promotion": promotion,
                "status": "PUBLISHED",
            },
        )

    # Nettoyage des anciennes catégories erronées si elles ne sont plus utilisées.
    Fonction.objects.filter(
        intitule__in=("Cours Théorique", "Travaux Pratiques")
    ).delete()

    print("Base de données prête.")
    print("- Fonctions liées au personnel : OK")
    print("- Horaires séparés par promotion : OK")
    print("Comptes : chef@demo.com, sga@demo.com, etudiant@demo.com")
    print(f"Mot de passe commun : {PASSWORD}")


if __name__ == "__main__":
    seed()
