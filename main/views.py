from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg, F
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime, timedelta
import random
from collections import defaultdict
from .forms import (RegisterForm, LoginForm, RecipeForm, RecipeIngredientFormSet, 
                   RecipeImageFormSet, RecipeSearchForm, IngredientSearchForm,
                   IngredientForm, TagForm)
from .models import CustomUser, Recipe, RecipeLike, Tag, Ingredient, UserSearchHistory, UserPreference

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.role = 'user'
            user.save()
            return redirect('login')
    else:
        form = RegisterForm()
        # Limpiar mensajes persistentes cuando se carga el formulario de registro
        storage = messages.get_messages(request)
        storage.used = True
    return render(request, 'register.html', {'form': form})

def login_view(request):
    # Crear usuario admin automáticamente si no existe (sin mensajes)
    if not CustomUser.objects.filter(username='admin').exists():
        CustomUser.objects.create_superuser(username='admin', password='admin', role='admin')
    
    # Manejar mensaje de logout solo cuando viene de logout
    if request.method == 'GET' and 'logout' in request.GET:
        return redirect('login')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.role == 'admin':
                return redirect('admin_panel')
            else:
                return redirect('user_panel')
    else:
        form = LoginForm()
        
    return render(request, 'login.html', {'form': form})

@login_required
def user_panel(request):
    if request.user.role != 'user':
        return redirect('admin_panel')
    
    # Obtener las recetas del usuario
    user_recipes = Recipe.objects.filter(author=request.user).order_by('-created_at')[:5]
    
    # Obtener recetas con más likes para mostrar
    popular_recipes = Recipe.objects.annotate(
        total_likes=Count('likes')
    ).order_by('-total_likes')[:5]
    
    context = {
        'user_recipes': user_recipes,
        'popular_recipes': popular_recipes,
    }
    return render(request, 'user_panel.html', context)

@login_required
def admin_panel(request):
    if request.user.role != 'admin':
        return redirect('user_panel')
    
    # Estadísticas para el admin
    total_users = CustomUser.objects.filter(role='user').count()
    total_recipes = Recipe.objects.count()
    total_likes = RecipeLike.objects.count()
    recent_recipes = Recipe.objects.order_by('-created_at')[:10]
    recent_users = CustomUser.objects.filter(role='user').order_by('-date_joined')[:10]
    
    # Estadísticas adicionales
    published_recipes = Recipe.objects.filter(is_published=True).count()
    unpublished_recipes = Recipe.objects.filter(is_published=False).count()
    total_tags = Tag.objects.count()
    total_ingredients = Ingredient.objects.count()
    
    context = {
        'total_users': total_users,
        'total_recipes': total_recipes,
        'total_likes': total_likes,
        'recent_recipes': recent_recipes,
        'recent_users': recent_users,
        'published_recipes': published_recipes,
        'unpublished_recipes': unpublished_recipes,
        'total_tags': total_tags,
        'total_ingredients': total_ingredients,
    }
    return render(request, 'admin_panel.html', context)

@login_required
def admin_users(request):
    """Vista para gestionar usuarios desde el panel de admin"""
    if request.user.role != 'admin':
        return redirect('user_panel')
    
    users = CustomUser.objects.filter(role='user').order_by('-date_joined')
    
    # Búsqueda
    search = request.GET.get('search', '')
    if search:
        users = users.filter(
            Q(username__icontains=search) | 
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
    }
    return render(request, 'admin_users.html', context)

@login_required
def admin_recipes(request):
    """Vista para gestionar recetas desde el panel de admin"""
    if request.user.role != 'admin':
        return redirect('user_panel')
    
    recipes = Recipe.objects.all().order_by('-created_at')
    
    # Filtros
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    if status == 'published':
        recipes = recipes.filter(is_published=True)
    elif status == 'unpublished':
        recipes = recipes.filter(is_published=False)
        
    if search:
        recipes = recipes.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search) |
            Q(author__username__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(recipes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'status': status,
    }
    return render(request, 'admin_recipes.html', context)

@login_required
@require_POST
def admin_toggle_user_status(request, user_id):
    """Toggle activo/inactivo de un usuario"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    user = get_object_or_404(CustomUser, id=user_id, role='user')
    user.is_active = not user.is_active
    user.save()
    
    return JsonResponse({
        'success': True,
        'is_active': user.is_active,
        'message': f'Usuario {"activado" if user.is_active else "desactivado"} correctamente'
    })

@login_required
@require_POST
def admin_toggle_recipe_status(request, recipe_id):
    """Toggle publicado/no publicado de una receta"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    recipe = get_object_or_404(Recipe, id=recipe_id)
    recipe.is_published = not recipe.is_published
    recipe.save()
    
    return JsonResponse({
        'success': True,
        'is_published': recipe.is_published,
        'message': f'Receta {"publicada" if recipe.is_published else "ocultada"} correctamente'
    })

@login_required
def admin_delete_user(request, user_id):
    """Eliminar un usuario (solo admins)"""
    if request.user.role != 'admin':
        return redirect('user_panel')
    
    user = get_object_or_404(CustomUser, id=user_id, role='user')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        return redirect('admin_users')
    
    context = {
        'user_to_delete': user,
    }
    return render(request, 'admin_confirm_delete_user.html', context)

@login_required
def admin_delete_recipe(request, recipe_id):
    """Eliminar una receta (solo admins)"""
    if request.user.role != 'admin':
        return redirect('user_panel')
    
    recipe = get_object_or_404(Recipe, id=recipe_id)
    
    if request.method == 'POST':
        title = recipe.title
        recipe.delete()
        return redirect('admin_recipes')
    
    context = {
        'recipe_to_delete': recipe,
    }
    return render(request, 'admin_confirm_delete_recipe.html', context)

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect('/login/?logout=1')

# H03 - Explorar recetas
def recipe_list(request):
    """Vista principal para explorar todas las recetas"""
    recipes = Recipe.objects.filter(is_published=True).select_related('author').prefetch_related('tags', 'images')
    
    # Aplicar filtros de búsqueda
    form = RecipeSearchForm(request.GET)
    if form.is_valid():
        query = form.cleaned_data.get('query')
        tags = form.cleaned_data.get('tags')
        difficulty = form.cleaned_data.get('difficulty')
        
        if query:
            recipes = recipes.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) |
                Q(instructions__icontains=query)
            )
            
            # Guardar búsqueda en historial si el usuario está autenticado
            if request.user.is_authenticated:
                UserSearchHistory.objects.create(
                    user=request.user,
                    search_term=query
                )
        
        if tags:
            recipes = recipes.filter(tags__in=tags).distinct()
        
        if difficulty:
            recipes = recipes.filter(difficulty=difficulty)
    
    # Ordenar por likes o fecha
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by == 'likes':
        recipes = recipes.annotate(total_likes=Count('likes')).order_by('-total_likes', '-created_at')
    else:
        recipes = recipes.order_by('-created_at')
    
    # Paginación
    paginator = Paginator(recipes, 12)  # 12 recetas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'sort_by': sort_by,
    }
    return render(request, 'recipe_list.html', context)

def recipe_detail(request, recipe_id):
    """Vista detallada de una receta"""
    recipe = get_object_or_404(Recipe, id=recipe_id, is_published=True)
    
    # Verificar si el usuario ya dio like
    user_liked = False
    if request.user.is_authenticated:
        user_liked = RecipeLike.objects.filter(user=request.user, recipe=recipe).exists()
    
    # Recetas relacionadas (mismas etiquetas)
    related_recipes = Recipe.objects.filter(
        tags__in=recipe.tags.all(),
        is_published=True
    ).exclude(id=recipe.id).distinct()[:4]
    
    context = {
        'recipe': recipe,
        'user_liked': user_liked,
        'related_recipes': related_recipes,
    }
    return render(request, 'recipe_detail.html', context)

# H02 - Crear y publicar recetas
@login_required
def recipe_create(request):
    if request.user.role != 'user':
        messages.error(request, 'Los administradores no pueden crear recetas. Esta función es solo para usuarios.')
        return redirect('admin_panel')
        
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        ingredient_formset = RecipeIngredientFormSet(request.POST, prefix='ingredient_set')
        image_formset      = RecipeImageFormSet(request.POST, request.FILES, prefix='image_set')
        
        if form.is_valid() and ingredient_formset.is_valid() and image_formset.is_valid():
            recipe = form.save(commit=False)
            recipe.author = request.user
            recipe.save()
            form.save_m2m()

            # Ingredientes
            ingredient_formset.instance = recipe
            ingredient_formset.save()

            # Imágenes (solo si se subió archivo)
            image_formset.instance = recipe
            images = image_formset.save(commit=False)
            for img in images:
                if getattr(img, 'image', None):
                    img.recipe = recipe
                    img.save()
            for obj in image_formset.deleted_objects:
                obj.delete()

            return redirect('recipe_detail', recipe_id=recipe.id)
    else:
        form = RecipeForm()
        ingredient_formset = RecipeIngredientFormSet(prefix='ingredient_set')
        image_formset      = RecipeImageFormSet(prefix='image_set')
    
    return render(request, 'recipe_form.html', {
        'form': form,
        'ingredient_formset': ingredient_formset,
        'image_formset': image_formset,
        'title': 'Crear nueva receta'
    })
# H07 - Editar o eliminar recetas propias
@login_required
def recipe_edit(request, recipe_id):
    if request.user.role != 'user':
        messages.error(request, 'Los administradores no pueden editar recetas desde esta interfaz. Use el panel administrativo para gestionar recetas.')
        return redirect('admin_panel')
        
    recipe = get_object_or_404(Recipe, id=recipe_id, author=request.user)
    
    if request.method == 'POST':
        form = RecipeForm(request.POST, instance=recipe)
        ingredient_formset = RecipeIngredientFormSet(request.POST, instance=recipe, prefix='ingredient_set')
        image_formset      = RecipeImageFormSet(request.POST, request.FILES, instance=recipe, prefix='image_set')
        
        if form.is_valid() and ingredient_formset.is_valid() and image_formset.is_valid():
            recipe = form.save()
            ingredient_formset.save()

            # Mantener imágenes si no se sube nada; crear solo si hay archivo
            images = image_formset.save(commit=False)
            for img in images:
                # si no se cambió el file, Django mantiene el anterior automáticamente
                img.recipe = recipe
                img.save()
            for obj in image_formset.deleted_objects:
                obj.delete()

            return redirect('recipe_detail', recipe_id=recipe.id)
    else:
        form = RecipeForm(instance=recipe)
        ingredient_formset = RecipeIngredientFormSet(instance=recipe, prefix='ingredient_set')
        image_formset      = RecipeImageFormSet(instance=recipe, prefix='image_set')
    
    return render(request, 'recipe_form.html', {
        'form': form,
        'ingredient_formset': ingredient_formset,
        'image_formset': image_formset,
        'recipe': recipe,
        'title': 'Editar receta'
    })
@login_required
def recipe_delete(request, recipe_id):
    """Vista para eliminar receta propia - Solo usuarios normales"""
    if request.user.role != 'user':
        messages.error(request, 'Los administradores no pueden eliminar recetas desde esta interfaz. Use el panel administrativo para gestionar recetas.')
        return redirect('admin_panel')
        
    recipe = get_object_or_404(Recipe, id=recipe_id, author=request.user)
    
    if request.method == 'POST':
        recipe.delete()
        return redirect('my_recipes')
    
    return render(request, 'recipe_confirm_delete.html', {'recipe': recipe})

@login_required
def my_recipes(request):
    """Vista para mostrar las recetas del usuario - Solo usuarios normales"""
    if request.user.role != 'user':
        messages.error(request, 'Los administradores no tienen recetas propias. Pueden gestionar todas las recetas desde el panel administrativo.')
        return redirect('admin_panel')
        
    recipes = Recipe.objects.filter(author=request.user).order_by('-created_at')
    
    paginator = Paginator(recipes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'my_recipes.html', {'page_obj': page_obj})

# H04 - Dar "me gusta" a recetas
@login_required
@require_POST
def toggle_like(request, recipe_id):
    """Vista AJAX para dar/quitar like a una receta - Solo usuarios normales"""
    if request.user.role != 'user':
        return JsonResponse({
            'error': 'Los administradores no pueden dar "me gusta" a recetas. Esta función es exclusiva para usuarios.',
            'liked': False,
            'likes_count': 0
        }, status=403)
        
    recipe = get_object_or_404(Recipe, id=recipe_id)
    
    like, created = RecipeLike.objects.get_or_create(
        user=request.user,
        recipe=recipe
    )
    
    if not created:
        # Si ya existía, lo eliminamos (quitar like)
        like.delete()
        liked = False
    else:
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'likes_count': recipe.likes_count
    })

# H06 - Búsqueda por ingredientes
def search_by_ingredients(request):
    """Vista para buscar recetas por ingredientes disponibles"""
    form = IngredientSearchForm(request.GET)
    recipes = None
    
    if form.is_valid() and form.cleaned_data.get('ingredients'):
        selected_ingredients = form.cleaned_data['ingredients']
        
        # Buscar recetas que contengan AL MENOS UNO de los ingredientes seleccionados
        recipes = Recipe.objects.filter(
            ingredients__in=selected_ingredients,
            is_published=True
        ).distinct().annotate(
            matching_ingredients=Count('ingredients', filter=Q(ingredients__in=selected_ingredients))
        ).order_by('-matching_ingredients', '-created_at')
        
        # Guardar búsqueda en historial
        if request.user.is_authenticated:
            search_history = UserSearchHistory.objects.create(
                user=request.user,
                search_term=f"Búsqueda por ingredientes: {', '.join([i.name for i in selected_ingredients])}"
            )
            search_history.ingredients_searched.set(selected_ingredients)
    
    context = {
        'form': form,
        'recipes': recipes,
    }
    return render(request, 'search_by_ingredients.html', context)

# H05 - Recomendaciones personalizadas
@login_required
def recommendations(request):
    """Vista para mostrar recomendaciones personalizadas - Solo usuarios normales"""
    if request.user.role != 'user':
        messages.error(request, 'Los administradores no reciben recomendaciones personalizadas. Su función es gestionar la plataforma.')
        return redirect('admin_panel')
        
    user = request.user
    recommended_recipes = []
    
    # Obtener preferencias del usuario (crear si no existen)
    preferences, created = UserPreference.objects.get_or_create(user=user)
    
    # 1. Recomendaciones basadas en recetas que le han gustado
    liked_recipes = Recipe.objects.filter(
        likes__user=user,
        is_published=True
    ).prefetch_related('tags')
    
    if liked_recipes.exists():
        # Obtener etiquetas de recetas que le gustaron
        liked_tags = Tag.objects.filter(recipe__in=liked_recipes).distinct()
        
        # Recomendar recetas con etiquetas similares que no haya dado like
        tag_based_recommendations = Recipe.objects.filter(
            tags__in=liked_tags,
            is_published=True
        ).exclude(
            id__in=liked_recipes.values_list('id', flat=True)
        ).exclude(
            author=user  # No recomendar sus propias recetas
        ).annotate(
            tag_matches=Count('tags', filter=Q(tags__in=liked_tags))
        ).order_by('-tag_matches', '-created_at')[:10]
        
        recommended_recipes.extend(tag_based_recommendations)
    
    # 2. Recomendaciones basadas en historial de búsquedas
    search_history = UserSearchHistory.objects.filter(user=user).order_by('-created_at')[:10]
    
    if search_history.exists():
        # Obtener ingredientes y etiquetas búsquedas recientes
        searched_ingredients = Ingredient.objects.filter(
            usersearchhistory__in=search_history
        ).distinct()
        
        searched_tags = Tag.objects.filter(
            usersearchhistory__in=search_history
        ).distinct()
        
        # Recomendar recetas con ingredientes o etiquetas búsquedas
        search_based_recommendations = Recipe.objects.filter(
            Q(ingredients__in=searched_ingredients) | Q(tags__in=searched_tags),
            is_published=True
        ).exclude(
            id__in=[r.id for r in recommended_recipes]
        ).exclude(
            author=user
        ).exclude(
            likes__user=user  # No recomendar recetas ya liked
        ).distinct().annotate(
            relevance_score=Count('ingredients', filter=Q(ingredients__in=searched_ingredients)) +
                          Count('tags', filter=Q(tags__in=searched_tags))
        ).order_by('-relevance_score', '-created_at')[:10]
        
        recommended_recipes.extend(search_based_recommendations)
    
    # 3. Recomendaciones basadas en preferencias del usuario
    if preferences.favorite_tags.exists() or preferences.favorite_ingredients.exists():
        preference_recommendations = Recipe.objects.filter(
            Q(tags__in=preferences.favorite_tags.all()) |
            Q(ingredients__in=preferences.favorite_ingredients.all()),
            is_published=True
        ).exclude(
            id__in=[r.id for r in recommended_recipes]
        ).exclude(
            author=user
        ).exclude(
            likes__user=user
        ).distinct().annotate(
            preference_score=Count('tags', filter=Q(tags__in=preferences.favorite_tags.all())) +
                           Count('ingredients', filter=Q(ingredients__in=preferences.favorite_ingredients.all()))
        ).order_by('-preference_score', '-created_at')[:10]
        
        recommended_recipes.extend(preference_recommendations)
    
    # 4. Si no hay suficientes recomendaciones, agregar recetas populares
    if len(recommended_recipes) < 12:
        popular_recipes = Recipe.objects.filter(
            is_published=True
        ).exclude(
            id__in=[r.id for r in recommended_recipes]
        ).exclude(
            author=user
        ).exclude(
            likes__user=user
        ).annotate(
            total_likes=Count('likes')
        ).order_by('-total_likes', '-created_at')[:12 - len(recommended_recipes)]
        
        recommended_recipes.extend(popular_recipes)
    
    # Eliminar duplicados y limitar a 12 recetas
    seen_ids = set()
    unique_recommendations = []
    for recipe in recommended_recipes:
        if recipe.id not in seen_ids:
            unique_recommendations.append(recipe)
            seen_ids.add(recipe.id)
        if len(unique_recommendations) >= 12:
            break
    
    # Estadísticas para mostrar al usuario
    stats = {
        'total_likes': liked_recipes.count(),
        'total_searches': search_history.count(),
        'favorite_tags': preferences.favorite_tags.count(),
        'favorite_ingredients': preferences.favorite_ingredients.count(),
    }
    
    context = {
        'recommended_recipes': unique_recommendations,
        'stats': stats,
        'preferences': preferences,
    }
    return render(request, 'recommendations.html', context)

@login_required
def update_preferences(request):
    """Vista para actualizar preferencias del usuario - Solo usuarios normales"""
    if request.user.role != 'user':
        messages.error(request, 'Los administradores no tienen preferencias personales. Esta función es exclusiva para usuarios.')
        return redirect('admin_panel')
        
    preferences, created = UserPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Actualizar etiquetas favoritas
        favorite_tags = request.POST.getlist('favorite_tags')
        if favorite_tags:
            preferences.favorite_tags.set(Tag.objects.filter(id__in=favorite_tags))
        else:
            preferences.favorite_tags.clear()
        
        # Actualizar ingredientes favoritos
        favorite_ingredients = request.POST.getlist('favorite_ingredients')
        if favorite_ingredients:
            preferences.favorite_ingredients.set(Ingredient.objects.filter(id__in=favorite_ingredients))
        else:
            preferences.favorite_ingredients.clear()
        
        return redirect('recommendations')
    
    context = {
        'preferences': preferences,
        'all_tags': Tag.objects.all(),
        'all_ingredients': Ingredient.objects.all(),
    }
    return render(request, 'update_preferences.html', context)

# H10 - Recomendaciones inteligentes (IA)
@login_required
def smart_recommendations(request):
    """Vista para recomendaciones inteligentes que mejoran con el tiempo"""
    user = request.user
    
    # Algoritmo de recomendaciones inteligente
    recommendations = get_smart_recommendations(user)
    
    context = {
        'recommended_recipes': recommendations[:12],  # Limitar a 12 recetas
        'algorithm_info': {
            'version': '2.0',
            'last_updated': timezone.now(),
            'total_analyzed': Recipe.objects.filter(is_published=True).count(),
        }
    }
    return render(request, 'smart_recommendations.html', context)

def get_smart_recommendations(user):
    """
    Algoritmo inteligente de recomendaciones que utiliza múltiples factores:
    1. Análisis de comportamiento del usuario
    2. Similitud con otros usuarios (Collaborative Filtering)
    3. Análisis de contenido (Content-Based Filtering)
    4. Factores temporales y de popularidad
    5. Machine Learning básico para scoring
    """
    
    # 1. Análisis del perfil del usuario
    user_profile = analyze_user_profile(user)
    
    # 2. Encontrar usuarios similares (Collaborative Filtering)
    similar_users = find_similar_users(user, user_profile)
    
    # 3. Obtener todas las recetas candidatas
    candidate_recipes = Recipe.objects.filter(
        is_published=True
    ).exclude(
        author=user
    ).exclude(
        likes__user=user
    ).select_related('author').prefetch_related('tags', 'ingredients', 'likes')
    
    # 4. Calcular score inteligente para cada receta
    scored_recipes = []
    for recipe in candidate_recipes:
        score = calculate_smart_score(recipe, user, user_profile, similar_users)
        if score > 0:  # Solo incluir recetas con score positivo
            recipe.ai_score = score
            scored_recipes.append(recipe)
    
    # 5. Ordenar por score y aplicar diversidad
    scored_recipes.sort(key=lambda x: x.ai_score, reverse=True)
    
    # 6. Aplicar diversidad para evitar recomendaciones repetitivas
    diverse_recommendations = apply_diversity_filter(scored_recipes, user_profile)
    
    return diverse_recommendations

def analyze_user_profile(user):
    """Analiza el perfil completo del usuario para crear un modelo de preferencias"""
    profile = {
        'liked_tags': defaultdict(int),
        'liked_ingredients': defaultdict(int),
        'searched_terms': [],
        'activity_score': 0,
        'preference_vector': {},
        'time_preferences': defaultdict(int),
        'difficulty_preference': defaultdict(int)
    }
    
    # Analizar recetas que le han gustado
    liked_recipes = Recipe.objects.filter(likes__user=user).prefetch_related('tags', 'ingredients')
    
    for recipe in liked_recipes:
        # Analizar etiquetas
        for tag in recipe.tags.all():
            profile['liked_tags'][tag.name] += 1
        
        # Analizar ingredientes
        for ingredient in recipe.ingredients.all():
            profile['liked_ingredients'][ingredient.name] += 1
        
        # Analizar tiempo de preparación
        if recipe.total_time <= 30:
            profile['time_preferences']['rápida'] += 1
        elif recipe.total_time <= 60:
            profile['time_preferences']['media'] += 1
        else:
            profile['time_preferences']['larga'] += 1
        
        # Analizar dificultad
        profile['difficulty_preference'][recipe.difficulty] += 1
    
    # Analizar historial de búsquedas
    recent_searches = UserSearchHistory.objects.filter(
        user=user,
        created_at__gte=timezone.now() - timedelta(days=30)
    ).order_by('-created_at')[:20]
    
    for search in recent_searches:
        profile['searched_terms'].append(search.search_term.lower())
    
    # Calcular score de actividad
    profile['activity_score'] = (
        liked_recipes.count() * 3 +
        recent_searches.count() * 1 +
        Recipe.objects.filter(author=user).count() * 5
    )
    
    return profile

def find_similar_users(user, user_profile):
    """Encuentra usuarios con gustos similares usando Collaborative Filtering"""
    similar_users = []
    
    # Obtener usuarios que han dado like a recetas similares
    user_liked_recipes = Recipe.objects.filter(likes__user=user)
    
    if user_liked_recipes.exists():
        # Encontrar otros usuarios que también han dado like a esas recetas
        potential_similar_users = CustomUser.objects.filter(
            likes__recipe__in=user_liked_recipes
        ).exclude(id=user.id).annotate(
            common_likes=Count('likes', filter=Q(likes__recipe__in=user_liked_recipes))
        ).filter(common_likes__gt=0).order_by('-common_likes')[:10]
        
        for similar_user in potential_similar_users:
            similarity_score = calculate_user_similarity(user, similar_user, user_profile)
            if similarity_score > 0.3:  # Umbral de similitud
                similar_users.append({
                    'user': similar_user,
                    'similarity': similarity_score
                })
    
    return sorted(similar_users, key=lambda x: x['similarity'], reverse=True)[:5]

def calculate_user_similarity(user1, user2, user1_profile):
    """Calcula la similitud entre dos usuarios"""
    # Obtener recetas que le gustaron al usuario 2
    user2_liked_recipes = Recipe.objects.filter(likes__user=user2).prefetch_related('tags', 'ingredients')
    
    if not user2_liked_recipes.exists():
        return 0
    
    # Crear perfil básico del usuario 2
    user2_tags = defaultdict(int)
    user2_ingredients = defaultdict(int)
    
    for recipe in user2_liked_recipes:
        for tag in recipe.tags.all():
            user2_tags[tag.name] += 1
        for ingredient in recipe.ingredients.all():
            user2_ingredients[ingredient.name] += 1
    
    # Calcular similitud usando intersección de gustos
    tag_similarity = calculate_similarity_score(user1_profile['liked_tags'], user2_tags)
    ingredient_similarity = calculate_similarity_score(user1_profile['liked_ingredients'], user2_ingredients)
    
    # Promedio ponderado
    total_similarity = (tag_similarity * 0.6 + ingredient_similarity * 0.4)
    
    return min(total_similarity, 1.0)  # Limitar a 1.0

def calculate_similarity_score(dict1, dict2):
    """Calcula la similitud entre dos diccionarios usando cosine similarity simplificado"""
    if not dict1 or not dict2:
        return 0
    
    # Encontrar elementos comunes
    common_items = set(dict1.keys()) & set(dict2.keys())
    
    if not common_items:
        return 0
    
    # Calcular similitud basada en elementos comunes
    similarity = len(common_items) / max(len(dict1), len(dict2))
    
    return similarity

def calculate_smart_score(recipe, user, user_profile, similar_users):
    """Calcula un score inteligente para una receta basado en múltiples factores"""
    score = 0.0
    
    # 1. Score basado en tags del usuario (40% del peso)
    tag_score = 0
    recipe_tags = [tag.name for tag in recipe.tags.all()]
    for tag in recipe_tags:
        if tag in user_profile['liked_tags']:
            tag_score += user_profile['liked_tags'][tag] * 0.4
    
    # 2. Score basado en ingredientes del usuario (30% del peso)
    ingredient_score = 0
    recipe_ingredients = [ing.name for ing in recipe.ingredients.all()]
    for ingredient in recipe_ingredients:
        if ingredient in user_profile['liked_ingredients']:
            ingredient_score += user_profile['liked_ingredients'][ingredient] * 0.3
    
    # 3. Score de usuarios similares (20% del peso)
    collaborative_score = 0
    for similar_user_data in similar_users:
        similar_user = similar_user_data['user']
        similarity = similar_user_data['similarity']
        
        # Verificar si el usuario similar le dio like a esta receta
        if RecipeLike.objects.filter(user=similar_user, recipe=recipe).exists():
            collaborative_score += similarity * 0.2
    
    # 4. Score de popularidad y calidad (10% del peso)
    popularity_score = min(recipe.likes_count * 0.1, 1.0)  # Normalizar
    
    # 5. Score temporal - recetas más nuevas tienen ligero bonus
    days_old = (timezone.now() - recipe.created_at).days
    freshness_score = max(0, (30 - days_old) / 30) * 0.1 if days_old <= 30 else 0
    
    # 6. Score de diversidad - penalizar si es muy similar a recetas ya recomendadas
    diversity_bonus = random.uniform(0.05, 0.15)  # Elemento de diversidad aleatoria
    
    # 7. Score basado en preferencias de tiempo y dificultad
    time_score = 0
    if recipe.total_time <= 30 and 'rápida' in user_profile['time_preferences']:
        time_score = 0.1
    elif 30 < recipe.total_time <= 60 and 'media' in user_profile['time_preferences']:
        time_score = 0.1
    elif recipe.total_time > 60 and 'larga' in user_profile['time_preferences']:
        time_score = 0.1
    
    difficulty_score = 0
    if recipe.difficulty in user_profile['difficulty_preference']:
        difficulty_score = user_profile['difficulty_preference'][recipe.difficulty] * 0.05
    
    # Combinar todos los scores
    total_score = (
        tag_score + 
        ingredient_score + 
        collaborative_score + 
        popularity_score + 
        freshness_score + 
        diversity_bonus +
        time_score +
        difficulty_score
    )
    
    return total_score

def apply_diversity_filter(scored_recipes, user_profile):
    """Aplica filtro de diversidad para evitar recomendaciones muy similares"""
    if not scored_recipes:
        return []
    
    diverse_recipes = []
    used_tags = set()
    used_ingredients = set()
    
    # Tomar las mejores recetas pero asegurar diversidad
    for recipe in scored_recipes:
        recipe_tags = set(tag.name for tag in recipe.tags.all())
        recipe_ingredients = set(ing.name for ing in recipe.ingredients.all())
        
        # Verificar si esta receta añade diversidad
        tag_overlap = len(recipe_tags & used_tags) / max(len(recipe_tags), 1)
        ingredient_overlap = len(recipe_ingredients & used_ingredients) / max(len(recipe_ingredients), 1)
        
        # Si hay poca superposición o es una receta muy buena, incluirla
        if tag_overlap < 0.7 or ingredient_overlap < 0.6 or recipe.ai_score > 2.0:
            diverse_recipes.append(recipe)
            used_tags.update(recipe_tags)
            used_ingredients.update(recipe_ingredients)
            
            # Limitar número de recomendaciones
            if len(diverse_recipes) >= 15:
                break
    
    return diverse_recipes

# ===================== GESTIÓN DE INGREDIENTES Y ETIQUETAS (ADMIN) =====================

@login_required
def admin_ingredients(request):
    """Vista para gestionar ingredientes desde el panel de admin"""
    if request.user.role != 'admin':
        return redirect('user_panel')
    
    ingredients = Ingredient.objects.all().order_by('name')
    
    # Búsqueda
    search = request.GET.get('search', '')
    if search:
        ingredients = ingredients.filter(name__icontains=search)
    
    # Paginación
    paginator = Paginator(ingredients, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'total_ingredients': Ingredient.objects.count(),
    }
    return render(request, 'admin_ingredients.html', context)

@login_required
def admin_ingredient_create(request):
    """Vista para crear un nuevo ingrediente"""
    if request.user.role != 'admin':
        return redirect('user_panel')
    
    if request.method == 'POST':
        form = IngredientForm(request.POST)
        if form.is_valid():
            ingredient = form.save()
            return redirect('admin_ingredients')
    else:
        form = IngredientForm()
    
    context = {
        'form': form,
        'action': 'Crear',
    }
    return render(request, 'admin_ingredient_form.html', context)

@login_required
def admin_ingredient_edit(request, ingredient_id):
    """Vista para editar un ingrediente existente"""
    if request.user.role != 'admin':
        return redirect('user_panel')
    
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    
    if request.method == 'POST':
        form = IngredientForm(request.POST, instance=ingredient)
        if form.is_valid():
            ingredient = form.save()
            return redirect('admin_ingredients')
    else:
        form = IngredientForm(instance=ingredient)
    
    context = {
        'form': form,
        'ingredient': ingredient,
        'action': 'Editar',
    }
    return render(request, 'admin_ingredient_form.html', context)

@login_required
def admin_ingredient_delete(request, ingredient_id):
    """Vista para eliminar un ingrediente"""
    if request.user.role != 'admin':
        return redirect('user_panel')
    
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    
    if request.method == 'POST':
        name = ingredient.name
        # Verificar si el ingrediente está siendo usado en recetas
        recipes_using = Recipe.objects.filter(ingredients=ingredient).count()
        if recipes_using > 0:
            messages.error(request, f'No se puede eliminar "{name}" porque está siendo usado en {recipes_using} receta(s).')
        else:
            ingredient.delete()
        return redirect('admin_ingredients')
    
    # Contar recetas que usan este ingrediente
    recipes_using = Recipe.objects.filter(ingredients=ingredient)
    
    context = {
        'ingredient': ingredient,
        'recipes_using': recipes_using,
        'recipes_count': recipes_using.count(),
    }
    return render(request, 'admin_confirm_delete_ingredient.html', context)

@login_required
def admin_tags(request):
    """Vista para gestionar etiquetas desde el panel de admin"""
    if request.user.role != 'admin':
        return redirect('user_panel')
    
    tags = Tag.objects.all().order_by('name')
    
    # Búsqueda
    search = request.GET.get('search', '')
    if search:
        tags = tags.filter(name__icontains=search)
    
    # Paginación
    paginator = Paginator(tags, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'total_tags': Tag.objects.count(),
    }
    return render(request, 'admin_tags.html', context)

@login_required
def admin_tag_create(request):
    """Vista para crear una nueva etiqueta"""
    if request.user.role != 'admin':
        return redirect('user_panel')
    
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save()
            return redirect('admin_tags')
    else:
        form = TagForm()
    
    context = {
        'form': form,
        'action': 'Crear',
    }
    return render(request, 'admin_tag_form.html', context)

@login_required
def admin_tag_edit(request, tag_id):
    """Vista para editar una etiqueta existente"""
    if request.user.role != 'admin':
        return redirect('user_panel')
    
    tag = get_object_or_404(Tag, id=tag_id)
    
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            tag = form.save()
            return redirect('admin_tags')
    else:
        form = TagForm(instance=tag)
    
    context = {
        'form': form,
        'tag': tag,
        'action': 'Editar',
    }
    return render(request, 'admin_tag_form.html', context)

@login_required
def admin_tag_delete(request, tag_id):
    """Vista para eliminar una etiqueta"""
    if request.user.role != 'admin':
        return redirect('user_panel')
    
    tag = get_object_or_404(Tag, id=tag_id)
    
    if request.method == 'POST':
        name = tag.name
        # Verificar si la etiqueta está siendo usada en recetas
        recipes_using = Recipe.objects.filter(tags=tag).count()
        if recipes_using > 0:
            messages.error(request, f'No se puede eliminar "{name}" porque está siendo usada en {recipes_using} receta(s).')
        else:
            tag.delete()
        return redirect('admin_tags')
    
    # Contar recetas que usan esta etiqueta
    recipes_using = Recipe.objects.filter(tags=tag)
    
    context = {
        'tag': tag,
        'recipes_using': recipes_using,
        'recipes_count': recipes_using.count(),
    }
    return render(request, 'admin_confirm_delete_tag.html', context)

# Vista API para búsqueda de ingredientes
def search_ingredients_api(request):
    """API para buscar ingredientes en tiempo real"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:  # Solo buscar si hay al menos 2 caracteres
        return JsonResponse({'ingredients': []})
    
    # Buscar ingredientes que contengan la consulta
    ingredients = Ingredient.objects.filter(
        name__icontains=query
    ).order_by('name')[:20]  # Limitar a 20 resultados
    
    ingredients_data = [
        {
            'id': ingredient.id,
            'name': ingredient.name
        }
        for ingredient in ingredients
    ]
    
    return JsonResponse({'ingredients': ingredients_data})
