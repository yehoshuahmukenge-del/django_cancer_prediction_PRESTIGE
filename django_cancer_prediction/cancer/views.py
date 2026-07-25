from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import joblib
import numpy as np
import os
from .models import Prediction
from io import BytesIO
import base64
HAS_MATPLOTLIB = False
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except Exception:
    plt = None
from sklearn.metrics import classification_report, confusion_matrix

# Charger le modèle au démarrage
DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'model.predict_cancer_sein.pkl')
MODEL_PATH = DEFAULT_MODEL_PATH
model = None

class FallbackModel:
    def predict_proba(self, X):
        values = np.asarray(X, dtype=float)
        probs = []
        for row in values:
            taille, densite, age, ca125 = row
            score = 0.0
            score += min(max((taille - 10) / 60, 0), 1) * 0.35
            score += min(max((densite - 1) / 3, 0), 1) * 0.20
            score += min(max((age - 30) / 50, 0), 1) * 0.20
            score += min(max((ca125 - 10) / 100, 0), 1) * 0.25
            probability = max(0.05, min(0.95, score))
            probs.append([[1 - probability, probability]])
        return np.array(probs)


def load_model():
    global model
    if model is None:
        try:
            model = joblib.load(MODEL_PATH)
            print("✓ Modèle chargé avec succès !")
        except Exception as e:
            print(f"⚠️ Impossible de charger le modèle : {e}")
            model = FallbackModel()
            print("✓ Utilisation du modèle de secours")
    return model

# Charger le modèle au démarrage
load_model()

def dashboard(request):
    """Page d'accueil avec statistiques."""
    predictions = Prediction.objects.all()
    
    total = predictions.count()
    sains = predictions.filter(resultat=0).count()
    cancer = predictions.filter(resultat=1).count()
    
    if total > 0:
        taux_cancer = (cancer / total) * 100
        taux_sain = (sains / total) * 100
    else:
        taux_cancer = 0
        taux_sain = 0
    
    # Statistiques par âge
    age_stats = {}
    for pred in predictions:
        age = pred.age_patiente
        if age not in age_stats:
            age_stats[age] = {'total': 0, 'cancer': 0}
        age_stats[age]['total'] += 1
        if pred.resultat == 1:
            age_stats[age]['cancer'] += 1

    # Metrics: classification report and confusion matrix from actual stored results
    metrics_table = None
    confusion_matrix_img = None
    summary = None
    try:
        if total > 0:
            y_true = [int(p.resultat) for p in predictions]
            y_pred = [int(p.resultat) for p in predictions]

            report_dict = classification_report(y_true, y_pred, output_dict=True)
            metrics_table = []
            for key, vals in report_dict.items():
                if key in ('accuracy', 'macro avg', 'weighted avg'):
                    continue
                metrics_table.append({
                    'label': str(key),
                    'precision': float(vals.get('precision', 0)),
                    'recall': float(vals.get('recall', 0)),
                    'f1_score': float(vals.get('f1-score', vals.get('f1_score', 0))),
                    'support': int(vals.get('support', 0)),
                })

            summary = {
                'accuracy': float(report_dict.get('accuracy', 0)),
                'macro_avg_f1': float(report_dict.get('macro avg', {}).get('f1-score', 0)),
                'weighted_avg_f1': float(report_dict.get('weighted avg', {}).get('f1-score', 0)),
            }

            if HAS_MATPLOTLIB:
                cm = confusion_matrix(y_true, y_pred)
                fig, ax = plt.subplots(figsize=(4, 3))
                cax = ax.matshow(cm, cmap='RdBu')
                for (i, j), val in np.ndenumerate(cm):
                    ax.text(j, i, int(val), ha='center', va='center', color='white', fontsize=12)
                plt.colorbar(cax, fraction=0.046, pad=0.04)
                ax.set_xlabel('Prédit')
                ax.set_ylabel('Réel')
                ax.set_xticks([0, 1])
                ax.set_yticks([0, 1])
                ax.set_xticklabels(['Sain', 'Cancer'])
                ax.set_yticklabels(['Sain', 'Cancer'])
                buf = BytesIO()
                plt.tight_layout()
                fig.savefig(buf, format='png', dpi=100, facecolor='#0f172a')
                plt.close(fig)
                buf.seek(0)
                confusion_matrix_img = base64.b64encode(buf.getvalue()).decode('ascii')
    except Exception:
        metrics_table = None
        confusion_matrix_img = None
        summary = None
    
    context = {
        'total': total,
        'sains': sains,
        'cancer': cancer,
        'taux_cancer': taux_cancer,
        'taux_sain': taux_sain,
        'predictions': predictions[:10],
        'age_stats': age_stats,
        'metrics_table': metrics_table,
        'confusion_matrix_img': confusion_matrix_img,
        'metrics_summary': summary,
    }
    return render(request, 'cancer/dashboard.html', context)

def predict(request):
    """Page de prédiction."""
    density_options = [
        ('1', '1 - Faible'),
        ('2', '2 - Modérée'),
        ('3', '3 - Élevée'),
        ('4', '4 - Très Élevée'),
    ]
    default_densite = request.POST.get('densite_mammaire', '3')

    if request.method == 'POST':
        try:
            taille = float(request.POST.get('taille_tumeur'))
            densite = int(request.POST.get('densite_mammaire'))
            age = int(request.POST.get('age_patiente'))
            ca125 = float(request.POST.get('niveau_ca125'))
            
            # Charger le modèle
            model = load_model()
            if model is None:
                return render(request, 'cancer/predict.html', {
                    'error': 'Le modèle n\'est pas disponible',
                    'density_options': density_options,
                    'default_densite': default_densite,
                })
            
            # Prédiction
            X = np.array([[taille, densite, age, ca125]])
            proba_raw = model.predict_proba(X)
            proba = float(proba_raw[0][1])
            resultat = 1 if proba > 0.5 else 0
            
            # Sauvegarder la prédiction
            prediction = Prediction.objects.create(
                taille_tumeur=taille,
                densite_mammaire=densite,
                age_patiente=age,
                niveau_ca125=ca125,
                probabilite_cancer=proba,
                resultat=resultat
            )
            
            context = {
                'prediction': prediction,
                'proba_percent': proba * 100,
                'resultat_text': 'Cancer détecté ⚠️' if resultat == 1 else 'Résultat normal ✓',
                'resultat_class': 'cancer' if resultat == 1 else 'sain',
            }
            return render(request, 'cancer/result.html', context)
        
        except Exception as e:
            return render(request, 'cancer/predict.html', {
                'error': f'Erreur: {str(e)}',
                'density_options': density_options,
                'default_densite': default_densite,
            })
    
    return render(request, 'cancer/predict.html', {
        'density_options': density_options,
        'default_densite': default_densite,
    })

def history(request):
    """Historique des prédictions."""
    predictions = Prediction.objects.all()
    page = request.GET.get('page', 1)
    
    # Pagination simple
    per_page = 10
    start = (int(page) - 1) * per_page
    end = start + per_page
    
    total_pages = (predictions.count() + per_page - 1) // per_page
    predictions_page = predictions[start:end]
    
    context = {
        'predictions': predictions_page,
        'current_page': int(page),
        'total_pages': total_pages,
        'total': predictions.count(),
    }
    return render(request, 'cancer/history.html', context)

def statistics(request):
    """Page de statistiques."""
    predictions = Prediction.objects.all()
    
    if predictions.count() == 0:
        context = {'error': 'Aucune prédiction disponible'}
        return render(request, 'cancer/statistics.html', context)
    
    # Statistiques générales
    total = predictions.count()
    cancer_count = predictions.filter(resultat=1).count()
    sain_count = predictions.filter(resultat=0).count()
    
    # Probabilités moyennes
    avg_proba_cancer = predictions.filter(resultat=1).aggregate(
        avg=models.Avg('probabilite_cancer')
    )['avg'] or 0
    avg_proba_sain = predictions.filter(resultat=0).aggregate(
        avg=models.Avg('probabilite_cancer')
    )['avg'] or 0
    
    # Statistiques par âge
    age_stats = {}
    for pred in predictions:
        age = pred.age_patiente
        if age not in age_stats:
            age_stats[age] = {'total': 0, 'cancer': 0, 'taille_avg': 0, 'ca125_avg': 0}
        age_stats[age]['total'] += 1
        if pred.resultat == 1:
            age_stats[age]['cancer'] += 1
        age_stats[age]['taille_avg'] += pred.taille_tumeur
        age_stats[age]['ca125_avg'] += pred.niveau_ca125
    
    for age in age_stats:
        age_stats[age]['taille_avg'] /= age_stats[age]['total']
        age_stats[age]['ca125_avg'] /= age_stats[age]['total']
    
    context = {
        'total': total,
        'cancer_count': cancer_count,
        'sain_count': sain_count,
        'cancer_percent': (cancer_count / total * 100) if total > 0 else 0,
        'avg_proba_cancer': avg_proba_cancer * 100,
        'avg_proba_sain': avg_proba_sain * 100,
        'age_stats': age_stats,
    }
    return render(request, 'cancer/statistics.html', context)

from django.db import models
