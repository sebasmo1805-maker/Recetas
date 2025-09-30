from django.contrib import admin
from .models import CustomUser, Recipe, Ingredient, Tag, RecipeIngredient, RecipeImage, RecipeLike, UserSearchHistory, UserPreference

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'date_joined']
    search_fields = ['username', 'email']

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color']
    search_fields = ['name']

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1

class RecipeImageInline(admin.TabularInline):
    model = RecipeImage
    extra = 1

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'difficulty', 'prep_time', 'cook_time', 'servings', 'is_published', 'created_at']
    list_filter = ['difficulty', 'is_published', 'created_at', 'tags']
    search_fields = ['title', 'description', 'author__username']
    filter_horizontal = ['tags']
    inlines = [RecipeIngredientInline, RecipeImageInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author')

@admin.register(RecipeLike)
class RecipeLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'recipe', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'recipe__title']

@admin.register(UserSearchHistory)
class UserSearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'search_term', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'search_term']

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user']
    filter_horizontal = ['favorite_tags', 'favorite_ingredients']