from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

from .models import Horaire, Promotion


def _roles(user):
    return set(user.roles.values_list('libelle', flat=True))


def _promotions_autorisees(user):
    """Retourne uniquement les promotions que l'utilisateur peut consulter."""
    roles = _roles(user)
    promotions = Promotion.objects.select_related('filiere').none()

    if user.is_superuser or 'Admin' in roles:
        return Promotion.objects.select_related('filiere').all()

    if 'Étudiant' in roles:
        try:
            etudiant = user.etudiant
        except Exception:
            return promotions
        # La promotion est déduite côté serveur : aucun identifiant fourni par
        # le navigateur ne peut donner accès à l'horaire d'une autre promotion.
        return Promotion.objects.select_related('filiere').filter(
            inscriptions__etudiant=etudiant,
            inscriptions__statut='active',
        ).distinct()

    try:
        personnel = user.personnel
    except Exception:
        return promotions

    if 'Chef de filière' in roles:
        return Promotion.objects.select_related('filiere').filter(
            filiere__chef_filiere=personnel,
        ).distinct()

    if 'Enseignant' in roles:
        return Promotion.objects.select_related('filiere').filter(
            horaires__enseignant=personnel,
            horaires__actif=True,
        ).distinct()

    return promotions


@login_required
def emploi_du_temps(request):
    promotions = _promotions_autorisees(request.user).order_by(
        'filiere__codfiliere', '-annee_fin', 'libelle'
    )
    if not promotions.exists():
        return render(request, 'academic/emploi_du_temps.html', {
            'promotion': None,
            'promotions': promotions,
            'grid_rows': [],
            'jours': Horaire.JOURS,
        })

    roles = _roles(request.user)
    if 'Étudiant' in roles and not (request.user.is_superuser or 'Admin' in roles):
        # Un étudiant ne choisit jamais sa promotion par paramètre GET.
        promotion = promotions.order_by('-annee_fin', '-annee_debut').first()
    else:
        promotion_id = request.GET.get('promotion')
        promotion = promotions.filter(pk=promotion_id).first() if promotion_id else promotions.first()
        if promotion is None:
            return HttpResponseForbidden("Vous n'avez pas accès à l'horaire de cette promotion.")

    horaires = list(
        Horaire.objects.filter(promotion=promotion, actif=True)
        .select_related('cours', 'enseignant__utilisateur', 'enseignant__fonction')
        .order_by('heure_debut', 'jour')
    )
    time_slots = sorted({(item.heure_debut, item.heure_fin) for item in horaires})
    by_slot_and_day = {
        (item.heure_debut, item.heure_fin, item.jour): item for item in horaires
    }
    grid_rows = [
        {
            'heure_debut': start,
            'heure_fin': end,
            'cells': [by_slot_and_day.get((start, end, day)) for day, _ in Horaire.JOURS],
        }
        for start, end in time_slots
    ]
    for index, row in enumerate(grid_rows[:-1]):
        next_row = grid_rows[index + 1]
        if row['heure_fin'] < next_row['heure_debut']:
            row['pause_after'] = {
                'debut': row['heure_fin'],
                'fin': next_row['heure_debut'],
            }

    context = {
        'promotion': promotion,
        'promotions': promotions,
        'grid_rows': grid_rows,
        'jours': Horaire.JOURS,
        'can_choose_promotion': not ('Étudiant' in roles and not request.user.is_superuser),
    }
    return render(request, 'academic/emploi_du_temps.html', context)
