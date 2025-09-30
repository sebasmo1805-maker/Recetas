from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from PIL import Image
import os

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    
    def __str__(self):
        return self.username

class Tag(models.Model):
    """Etiquetas para categorizar recetas (vegetariana, rápida, sin gluten, etc.)"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Nombre")
    color = models.CharField(max_length=7, default="#007bff", verbose_name="Color")  # Color hex para mostrar la etiqueta
    
    class Meta:
        verbose_name = "Etiqueta"
        verbose_name_plural = "Etiquetas"
    
    def __str__(self):
        return self.name

class Ingredient(models.Model):
    """Ingredientes que pueden usarse en las recetas"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    
    class Meta:
        verbose_name = "Ingrediente"
        verbose_name_plural = "Ingredientes"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Recipe(models.Model):
    """Modelo principal para las recetas"""
    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.TextField(verbose_name="Descripción", blank=True)
    instructions = models.TextField(verbose_name="Instrucciones de preparación")
    
    # Información adicional
    prep_time = models.PositiveIntegerField(verbose_name="Tiempo de preparación (minutos)", null=True, blank=True)
    cook_time = models.PositiveIntegerField(verbose_name="Tiempo de cocción (minutos)", null=True, blank=True)
    servings = models.PositiveIntegerField(verbose_name="Porciones", default=1)
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ('facil', 'Fácil'),
            ('intermedio', 'Intermedio'),
            ('dificil', 'Difícil')
        ],
        default='facil',
        verbose_name="Dificultad"
    )
    
    # Relaciones
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="Autor")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="Etiquetas")
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient', verbose_name="Ingredientes")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")
    is_published = models.BooleanField(default=True, verbose_name="Publicada")
    
    class Meta:
        verbose_name = "Receta"
        verbose_name_plural = "Recetas"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def total_time(self):
        """Tiempo total de preparación + cocción"""
        prep = self.prep_time or 0
        cook = self.cook_time or 0
        return prep + cook
    
    @property
    def likes_count(self):
        """Número total de me gusta"""
        return self.likes.count()

class RecipeIngredient(models.Model):
    """Tabla intermedia para ingredientes con cantidades"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="recipe_ingredients")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.CharField(max_length=100, verbose_name="Cantidad")  # Ej: "2 tazas", "500g", "al gusto"
    
    class Meta:
        unique_together = ['recipe', 'ingredient']
        verbose_name = "Ingrediente de receta"
        verbose_name_plural = "Ingredientes de receta"
    
    def __str__(self):
        return f"{self.quantity} de {self.ingredient.name}"

class RecipeImage(models.Model):
    """Imágenes de las recetas"""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to='recipes/', verbose_name="Imagen")
    is_main = models.BooleanField(default=False, verbose_name="Imagen principal")
    caption = models.CharField(max_length=200, blank=True, verbose_name="Descripción")
    
    class Meta:
        verbose_name = "Imagen de receta"
        verbose_name_plural = "Imágenes de receta"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Redimensionar imagen si es muy grande
        if self.image:
            img = Image.open(self.image.path)
            if img.height > 800 or img.width > 800:
                img.thumbnail((800, 800))
                img.save(self.image.path)

class RecipeLike(models.Model):
    """Sistema de me gusta para recetas"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'recipe']  # Un usuario solo puede dar un like por receta
        verbose_name = "Me gusta"
        verbose_name_plural = "Me gusta"
    
    def __str__(self):
        return f"{self.user.username} likes {self.recipe.title}"

class UserSearchHistory(models.Model):
    """Historial de búsquedas para recomendaciones personalizadas"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    search_term = models.CharField(max_length=200, verbose_name="Término de búsqueda")
    ingredients_searched = models.ManyToManyField(Ingredient, blank=True)
    tags_searched = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Historial de búsqueda"
        verbose_name_plural = "Historial de búsquedas"
        ordering = ['-created_at']

class UserPreference(models.Model):
    """Preferencias del usuario para recomendaciones"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="preferences")
    favorite_tags = models.ManyToManyField(Tag, blank=True, verbose_name="Etiquetas favoritas")
    favorite_ingredients = models.ManyToManyField(Ingredient, blank=True, verbose_name="Ingredientes favoritos")
    
    class Meta:
        verbose_name = "Preferencia de usuario"
        verbose_name_plural = "Preferencias de usuario"
    
    def __str__(self):
        return f"Preferencias de {self.user.username}"
