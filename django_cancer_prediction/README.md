# 🏥 Prédiction Cancer du Sein - Django

Une application Django **EXTRÊMEMENT BELLE et PROFESSIONNELLE** pour prédire le cancer du sein avec votre modèle ML !

## ✨ Fonctionnalités

✅ **Tableau de Bord** - Statistiques et KPIs en temps réel  
✅ **Formulaire de Prédiction** - Interface intuitive et prestige  
✅ **Historique Complet** - Toutes les prédictions sauvegardées  
✅ **Statistiques Avancées** - Analyse par âge et probabilités  
✅ **Design Prestige** - Dark mode bleu nuit + cyan électrique + rose  
✅ **Responsive** - Fonctionne sur tous les appareils  

## 🚀 Démarrage Rapide

### 1. Créer l'environnement virtuel

```bash
cd django_cancer_prediction
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Appliquer les migrations

```bash
python manage.py migrate
```

### 4. Créer un super-utilisateur (optionnel)

```bash
python manage.py createsuperuser
```

### 5. Lancer le serveur

```bash
python manage.py runserver
```

L'application s'ouvre à : **http://localhost:8000**

## 📊 Utilisation

### Prédire le Cancer

1. Allez à la page **"🔍 Prédire"**
2. Remplissez les données de la patiente :
   - **Taille Tumeur** (0.5 - 5.0 mm)
   - **Densité Mammaire** (1-4)
   - **Âge** (30-80 ans)
   - **Niveau CA-125** (10-100 U/mL)
3. Cliquez sur **"🔍 Analyser"**
4. Consultez le résultat avec la probabilité

### Consulter l'Historique

- Allez à **"📋 Historique"**
- Consultez toutes les prédictions précédentes
- Pagination automatique

### Voir les Statistiques

- Allez à **"📈 Statistiques"**
- Consultez les statistiques globales
- Analyse par groupe d'âge

## 📍 Placement du Modèle

Votre modèle `.pkl` doit être placé ici :

```
django_cancer_prediction/models/model.predict_cancer_sein.pkl
```

Le modèle se charge **automatiquement** au démarrage de l'application.

## 🎨 Design

- **Palette** : Bleu nuit (#0f172a) + Cyan électrique (#06b6d4) + Rose (#ec4899)
- **Animations** : Fluides et élégantes
- **Responsive** : Mobile-friendly
- **Professionnel** : Prêt pour la présentation ! 🎓

## 📊 Données du Modèle

Votre dataset contient :
- **1000 patients**
- **5 colonnes** : taille_tumeur, densite_mammaire, age_patiente, niveau_ca125, diagnostic
- **50% sains, 50% cancer**

## 🔧 Structure du Projet

```
django_cancer_prediction/
├── manage.py
├── requirements.txt
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── cancer/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── apps.py
├── models/
│   └── model.predict_cancer_sein.pkl
├── templates/cancer/
│   ├── base.html
│   ├── dashboard.html
│   ├── predict.html
│   ├── result.html
│   ├── history.html
│   └── statistics.html
└── static/
    ├── css/
    └── js/
```

## 💡 Conseils

- Les données de test doivent être dans les plages du dataset d'entraînement
- Le modèle utilise une probabilité > 0.5 pour prédire le cancer
- Toutes les prédictions sont sauvegardées en base de données SQLite

## 🎓 Pour la Présentation

Cette application est **prête pour une présentation professionnelle** :
- Interface magnifique et intuitive
- Statistiques complètes
- Historique complet
- Design prestige

**Bonne chance ! 🚀💪**
