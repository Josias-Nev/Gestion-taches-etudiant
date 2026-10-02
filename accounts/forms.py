"""Formulaires d'inscription, connexion et profil."""

from django import forms
from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError

from .models import User


class StudentRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label="Confirmation du mot de passe",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = User
        fields = ["name", "email"]
        labels = {
            "name": "Nom complet",
            "email": "Email",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ex. Josias Nev"}),
            "email": forms.EmailInput(attrs={"placeholder": "nom@example.com", "autocomplete": "email"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} form-control".strip()

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()
        if not name:
            raise ValidationError("Le nom complet est obligatoire.")
        return name

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Un compte existe déjà avec cette adresse email.")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Les mots de passe ne correspondent pas.")
        return password2

    def _post_clean(self):
        super()._post_clean()
        password = self.cleaned_data.get("password1")
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error("password1", error)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = user.email.lower()
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autocomplete": "email", "placeholder": "nom@example.com"}),
    )
    password = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    error_messages = {
        "invalid_login": "Email ou mot de passe incorrect.",
        "inactive": "Ce compte est inactif.",
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} form-control".strip()

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email", "").lower()
        password = cleaned_data.get("password")

        if email and password:
            self.user_cache = authenticate(self.request, username=email, password=password)
            if self.user_cache is None:
                raise ValidationError(self.error_messages["invalid_login"], code="invalid_login")
            if not self.user_cache.is_active:
                raise ValidationError(self.error_messages["inactive"], code="inactive")
        return cleaned_data

    def get_user(self):
        return self.user_cache


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "email"]
        labels = {"name": "Nom complet", "email": "Email"}
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data.get("name", "").strip()
        if not name:
            raise ValidationError("Le nom complet est obligatoire.")
        return name

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        exists = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists()
        if exists:
            raise ValidationError("Cette adresse email est déjà utilisée.")
        return email


class UserCreationAdminForm(StudentRegistrationForm):
    """Formulaire utilisé dans l'administration Django."""


class UserChangeAdminForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label="Mot de passe")

    class Meta:
        model = User
        fields = ["name", "email", "password", "is_active", "is_staff", "is_superuser", "groups", "user_permissions"]
