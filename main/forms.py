from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import inlineformset_factory
from .models import CustomUser, Recipe, RecipeIngredient, RecipeImage, Ingredient, Tag

class RegisterForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        label="Nombre de usuario",
        help_text='',  # Elimina el help_text por defecto
    )
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['username', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

class LoginForm(AuthenticationForm):
    pass

class RecipeForm(forms.ModelForm):
    """Formulario principal para crear/editar recetas"""
    
    class Meta:
        model = Recipe
        fields = ['title', 'description', 'instructions', 'prep_time', 'cook_time', 
                 'servings', 'difficulty', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de tu receta'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe brevemente tu receta'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Escribe paso a paso cómo preparar la receta'
            }),
            'prep_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Minutos'
            }),
            'cook_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Minutos'
            }),
            'servings': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'difficulty': forms.Select(attrs={
                'class': 'form-control'
            }),
            'tags': forms.CheckboxSelectMultiple()
        }
        labels = {
            'title': 'Título de la receta',
            'description': 'Descripción',
            'instructions': 'Instrucciones de preparación',
            'prep_time': 'Tiempo de preparación (minutos)',
            'cook_time': 'Tiempo de cocción (minutos)',
            'servings': 'Porciones',
            'difficulty': 'Dificultad',
            'tags': 'Etiquetas'
        }

class RecipeIngredientForm(forms.ModelForm):
    """Formulario para ingredientes de la receta"""
    
    ingredient = forms.ModelChoiceField(
        queryset=Ingredient.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control ingredient-select',
            'data-live-search': 'true',
            'data-size': '8',
            'title': 'Buscar ingrediente...'
        }),
        empty_label="Selecciona un ingrediente"
    )
    quantity = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 2 tazas, 500g, al gusto'
        }),
        label="Cantidad"
    )
    
    class Meta:
        model = RecipeIngredient
        fields = ['ingredient', 'quantity']

class RecipeImageForm(forms.ModelForm):
    """Formulario para imágenes de la receta"""
    
    class Meta:
        model = RecipeImage
        fields = ['image', 'caption', 'is_main']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción de la imagen (opcional)'
            }),
            'is_main': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'image': 'Imagen',
            'caption': 'Descripción',
            'is_main': '¿Imagen principal?'
        }

# Formsets para manejar múltiples ingredientes e imágenes
RecipeIngredientFormSet = inlineformset_factory(
    Recipe,
    RecipeIngredient,
    form=RecipeIngredientForm,
    extra=1,            # 1 formulario vacío por defecto
    can_delete=True
)

RecipeImageFormSet = inlineformset_factory(
    Recipe,
    RecipeImage,
    form=RecipeImageForm,
    extra=1,  # Mostrar 1 formulario de imagen por defecto
    can_delete=True
)

class IngredientSearchForm(forms.Form):
    """Formulario para búsqueda por ingredientes (H06)"""
    ingredients = forms.ModelMultipleChoiceField(
        queryset=Ingredient.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label="Ingredientes disponibles"
    )

class RecipeSearchForm(forms.Form):
    """Formulario de búsqueda general de recetas"""
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar recetas...'
        }),
        label="Búsqueda"
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label="Filtrar por etiquetas"
    )
    difficulty = forms.ChoiceField(
        choices=[('', 'Cualquier dificultad')] + Recipe._meta.get_field('difficulty').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Dificultad"
    )

class IngredientForm(forms.ModelForm):
    """Formulario para crear/editar ingredientes desde el panel de admin"""
    
    class Meta:
        model = Ingredient
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del ingrediente (ej: Tomate, Queso mozzarella, Harina)',
                'maxlength': 100
            })
        }
        labels = {
            'name': 'Nombre del Ingrediente'
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip().title()  # Capitaliza la primera letra de cada palabra
            
            # Verificar si ya existe (excluyendo la instancia actual si estamos editando)
            existing = Ingredient.objects.filter(name__iexact=name)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError(f'El ingrediente "{name}" ya existe.')
        
        return name

class TagForm(forms.ModelForm):
    """Formulario para crear/editar etiquetas desde el panel de admin"""
    
    class Meta:
        model = Tag
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la etiqueta (ej: Vegetariana, Rápida, Sin Gluten)',
                'maxlength': 50
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'style': 'width: 60px; height: 40px;'
            })
        }
        labels = {
            'name': 'Nombre de la Etiqueta',
            'color': 'Color'
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip().title()
            
            # Verificar si ya existe (excluyendo la instancia actual si estamos editando)
            existing = Tag.objects.filter(name__iexact=name)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError(f'La etiqueta "{name}" ya existe.')
        
        return name
