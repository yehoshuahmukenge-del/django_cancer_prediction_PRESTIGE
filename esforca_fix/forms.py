from django import forms

from .models import (Chrono_Horaire, Cours, Disponibilite, Etudiant, Filiere,
                     Fonction, Personnel, Promotion, Role, Utilisateur_Role)


class ChronoHoraireForm(forms.ModelForm):
    class Meta:
        model = Chrono_Horaire
        fields = ("promotion", "jours", "heure", "cours", "personnel")
        widgets = {"heure": forms.TimeInput(attrs={"type": "time"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["personnel"].queryset = Personnel.objects.filter(
            roles_associes__role__libelle="Enseignant"
        ).distinct().order_by("nom", "post_nom")
        for field in self.fields.values():
            field.widget.attrs["class"] = "w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 focus:ring-2 focus:ring-primary-500 outline-none"


class PersonnelForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    role = forms.ModelChoiceField(queryset=Role.objects.none())

    class Meta:
        model = Personnel
        fields = ("nom", "post_nom", "sexe", "email", "matricule", "grade", "fonction")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = Role.objects.all().order_by("libelle")
        if self.instance.pk:
            association = self.instance.roles_associes.select_related("role").first()
            if association:
                self.fields["role"].initial = association.role
        for field in self.fields.values():
            field.widget.attrs["class"] = "w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3"

    def save(self, commit=True):
        personnel = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            personnel.set_password(password)
        elif not personnel.pk:
            personnel.set_unusable_password()
        if commit:
            personnel.save()
            Utilisateur_Role.objects.update_or_create(
                id_util=personnel,
                role=self.cleaned_data["role"],
            )
        return personnel


class DisponibiliteForm(forms.ModelForm):
    class Meta:
        model = Disponibilite
        fields = ("jour", "heure_debut", "heure_fin", "note")

    def clean(self):
        cleaned = super().clean()
        debut, fin = cleaned.get("heure_debut"), cleaned.get("heure_fin")
        if debut and fin and debut >= fin:
            raise forms.ValidationError("L'heure de fin doit être postérieure à l'heure de début.")
        return cleaned


class FiliereForm(forms.ModelForm):
    class Meta:
        model = Filiere
        fields = ('nom_filiere',)


class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = ('designation', 'annee_academique', 'filiere')


class CoursForm(forms.ModelForm):
    class Meta:
        model = Cours
        fields = ('titre', 'duree')


class FonctionForm(forms.ModelForm):
    class Meta:
        model = Fonction
        fields = ('intitule',)


class EtudiantForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = Etudiant
        fields = ('nom', 'post_nom', 'sexe', 'email', 'num_matric', 'date_naiss', 'promotion')
        widgets = {'date_naiss': forms.DateInput(attrs={'type': 'date'})}

    def save(self, commit=True):
        etudiant = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            etudiant.set_password(password)
        elif not etudiant.pk:
            etudiant.set_unusable_password()
        if commit:
            etudiant.save()
            role, _ = Role.objects.get_or_create(libelle='Étudiant')
            Utilisateur_Role.objects.get_or_create(id_util=etudiant, role=role)
        return etudiant
