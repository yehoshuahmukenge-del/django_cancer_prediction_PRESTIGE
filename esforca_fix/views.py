from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (ChronoHoraireForm, CoursForm, DisponibiliteForm,
                    EtudiantForm, FiliereForm, FonctionForm, PersonnelForm,
                    PromotionForm)
from .models import (Chrono_Horaire, Cours, Disponibilite, Etudiant, Filiere,
                     Fonction, Personnel, Promotion)

CHEF, ENSEIGNANT, ETUDIANT, SGA = "Chef de Filière", "Enseignant", "Étudiant", "SG-A"


def _roles(user):
    return set(user.roles_associes.values_list("role__libelle", flat=True))


def role_required(*allowed_roles):
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not (_roles(request.user) & set(allowed_roles)):
                messages.error(request, "Accès refusé.")
                return redirect("dashboard")
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        user = authenticate(request, email=request.POST.get("email"), password=request.POST.get("password"))
        if user:
            login(request, user)
            next_url = request.POST.get("next") or request.GET.get("next")
            if next_url and next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)
            return redirect("dashboard")
        messages.error(request, "Email ou mot de passe incorrect.")
    return render(request, "registration/login.html")


@login_required
def logout_view(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    roles = _roles(request.user)
    context = {"user_roles": roles, "horaires": Chrono_Horaire.objects.none()}
    related = Chrono_Horaire.objects.select_related("cours", "personnel__fonction", "promotion__filiere")
    if SGA in roles:
        context.update(is_sga=True, horaires=related, personnels=Personnel.objects.all())
    elif CHEF in roles:
        context.update(is_chef=True, horaires=related)
    elif ENSEIGNANT in roles and hasattr(request.user, "personnel"):
        context.update(is_enseignant=True, horaires=related.filter(personnel=request.user.personnel))
    elif ETUDIANT in roles and hasattr(request.user, "etudiant"):
        context.update(
            is_etudiant=True,
            horaires=related.filter(
                status="PUBLISHED",
                promotion=request.user.etudiant.promotion,
            ),
        )
    context["published_count"] = context["horaires"].filter(status="PUBLISHED").count()
    context["pending_count"] = context["horaires"].filter(status__in=("PROPOSED", "CONFIRMED")).count()
    return render(request, "core/dashboard.html", context)


@login_required
def schedule_list(request):
    roles = _roles(request.user)
    horaires = Chrono_Horaire.objects.select_related("cours", "personnel__fonction", "promotion__filiere")
    context = {"user_roles": roles}
    if SGA in roles:
        context["is_sga"] = True
    elif CHEF in roles:
        context["is_chef"] = True
    elif ENSEIGNANT in roles and hasattr(request.user, "personnel"):
        context["is_enseignant"] = True
        horaires = horaires.filter(personnel=request.user.personnel)
    elif ETUDIANT in roles and hasattr(request.user, "etudiant"):
        context["is_etudiant"] = True
        horaires = horaires.filter(
            status="PUBLISHED",
            promotion=request.user.etudiant.promotion,
        )
    else:
        horaires = horaires.none()
    status = request.GET.get("status", "")
    search = request.GET.get("q", "").strip()
    if status in dict(Chrono_Horaire.STATUS_CHOICES):
        horaires = horaires.filter(status=status)
    if search:
        horaires = horaires.filter(cours__titre__icontains=search) | horaires.filter(personnel__nom__icontains=search) | horaires.filter(personnel__post_nom__icontains=search)
    context.update(horaires=horaires.distinct(), active_status=status, search=search)
    return render(request, "core/schedule_list.html", context)


@role_required(CHEF)
def edit_schedule(request, pk=None):
    horaire = get_object_or_404(Chrono_Horaire, pk=pk) if pk else None
    if horaire and horaire.status not in ("DRAFT", "PROPOSED"):
        messages.error(request, "Un horaire confirmé ou publié ne peut plus être modifié.")
        return redirect("dashboard")
    form = ChronoHoraireForm(request.POST or None, instance=horaire)
    if request.method == "POST" and form.is_valid():
        instance = form.save(commit=False)
        status = request.POST.get("status")
        instance.status = status if status in ("DRAFT", "PROPOSED") else "DRAFT"
        instance.save()
        messages.success(request, "Horaire enregistré.")
        return redirect("dashboard")
    return render(request, "core/edit_schedule.html", {"horaire": horaire, "form": form})


@role_required(CHEF)
def publish_schedule(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    horaire = get_object_or_404(Chrono_Horaire, pk=pk)
    if horaire.status != "CONFIRMED":
        messages.error(request, "Seul un horaire confirmé par le SGA peut être publié.")
    else:
        horaire.transitionner("PUBLISHED")
        messages.success(request, "Horaire publié officiellement.")
    return redirect("dashboard")


@role_required(SGA)
def confirm_schedule(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    horaire = get_object_or_404(Chrono_Horaire, pk=pk)
    if horaire.status != "PROPOSED":
        messages.error(request, "Seul un horaire proposé peut être confirmé.")
    else:
        horaire.transitionner("CONFIRMED")
        messages.success(request, "Charge horaire confirmée par le SGA.")
    return redirect("dashboard")


@role_required(ENSEIGNANT)
def submit_availability(request):
    if not hasattr(request.user, "personnel"):
        messages.error(request, "Aucun profil personnel associé.")
        return redirect("dashboard")
    if request.method == "POST":
        rows = zip(request.POST.getlist("jour[]"), request.POST.getlist("debut[]"), request.POST.getlist("fin[]"), request.POST.getlist("note[]"))
        forms = [DisponibiliteForm({"jour": j, "heure_debut": d, "heure_fin": f, "note": n}) for j, d, f, n in rows]
        if forms and all(form.is_valid() for form in forms):
            with transaction.atomic():
                for form in forms:
                    item = form.save(commit=False)
                    item.enseignant = request.user.personnel
                    item.save()
            messages.success(request, "Disponibilités soumises.")
            return redirect("dashboard")
        messages.error(request, "Corrigez les créneaux invalides.")
    return render(request, "core/availability.html", {"disponibilites": Disponibilite.objects.filter(enseignant=request.user.personnel)})


@role_required(ENSEIGNANT)
def annotate_schedule(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not hasattr(request.user, "personnel"):
        messages.error(request, "Aucun profil personnel associé.")
        return redirect("dashboard")
    horaire = get_object_or_404(Chrono_Horaire, pk=pk, personnel=request.user.personnel)
    horaire.annotations = request.POST.get("annotations", "").strip()
    horaire.save(update_fields=["annotations"])
    messages.success(request, "Annotation enregistrée.")
    return redirect("dashboard")


@role_required(SGA)
def manage_personnel(request, pk=None):
    personnel = get_object_or_404(Personnel, pk=pk) if pk else None
    form = PersonnelForm(request.POST or None, instance=personnel)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Personnel mis à jour." if personnel else "Personnel ajouté.")
        return redirect("manage_personnel")
    return render(request, "core/personnel.html", {"form": form, "personnel": personnel, "personnels": Personnel.objects.all()})


@role_required(SGA)
def delete_personnel(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    personnel = get_object_or_404(Personnel, pk=pk)
    if personnel.pk == request.user.pk:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
    else:
        personnel.delete()
        messages.success(request, "Personnel supprimé.")
    return redirect("manage_personnel")


REFERENTIELS = {
    'filieres': (Filiere, FiliereForm, 'Filières', 'nom_filiere'),
    'promotions': (Promotion, PromotionForm, 'Promotions', 'designation'),
    'cours': (Cours, CoursForm, 'Cours', 'titre'),
    'fonctions': (Fonction, FonctionForm, 'Fonctions', 'intitule'),
}


@role_required(SGA, CHEF)
def manage_referentiel(request, type_objet, pk=None):
    if type_objet not in REFERENTIELS:
        return redirect('dashboard')
    model, form_class, titre, champ_nom = REFERENTIELS[type_objet]
    objet = get_object_or_404(model, pk=pk) if pk else None
    form = form_class(request.POST or None, instance=objet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"{titre.rstrip('s')} enregistré(e).")
        return redirect('manage_referentiel', type_objet=type_objet)
    return render(request, 'core/referentiel.html', {
        'form': form, 'objet': objet, 'objets': model.objects.all(),
        'titre': titre, 'type_objet': type_objet, 'champ_nom': champ_nom,
        'user_roles': _roles(request.user),
    })


@role_required(SGA, CHEF)
def delete_referentiel(request, type_objet, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    if type_objet not in REFERENTIELS:
        return redirect('dashboard')
    model, _, titre, _ = REFERENTIELS[type_objet]
    objet = get_object_or_404(model, pk=pk)
    try:
        objet.delete()
        messages.success(request, f"{titre.rstrip('s')} supprimé(e).")
    except Exception:
        messages.error(request, "Suppression impossible : cet élément est encore utilisé.")
    return redirect('manage_referentiel', type_objet=type_objet)


@role_required(SGA)
def manage_students(request, pk=None):
    etudiant = get_object_or_404(Etudiant, pk=pk) if pk else None
    form = EtudiantForm(request.POST or None, instance=etudiant)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Étudiant enregistré.")
        return redirect('manage_students')
    return render(request, 'core/students.html', {
        'form': form, 'etudiant': etudiant,
        'etudiants': Etudiant.objects.select_related('promotion__filiere'),
        'user_roles': _roles(request.user), 'is_sga': True,
    })


@role_required(SGA)
def delete_student(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    get_object_or_404(Etudiant, pk=pk).delete()
    messages.success(request, "Étudiant supprimé.")
    return redirect('manage_students')
