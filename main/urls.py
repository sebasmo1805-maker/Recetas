from django.urls import path
from . import views

urlpatterns = [
    # Autenticación
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Paneles de usuario
    path('panel/', views.user_panel, name='user_panel'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    
    # H11 - Panel de administración
    path('admin-panel/usuarios/', views.admin_users, name='admin_users'),
    path('admin-panel/recetas/', views.admin_recipes, name='admin_recipes'),
    path('admin-panel/usuario/<int:user_id>/toggle-status/', views.admin_toggle_user_status, name='admin_toggle_user_status'),
    path('admin-panel/receta/<int:recipe_id>/toggle-status/', views.admin_toggle_recipe_status, name='admin_toggle_recipe_status'),
    path('admin-panel/usuario/<int:user_id>/eliminar/', views.admin_delete_user, name='admin_delete_user'),
    path('admin-panel/receta/<int:recipe_id>/eliminar/', views.admin_delete_recipe, name='admin_delete_recipe'),
    
    # Gestión de ingredientes y etiquetas
    path('admin-panel/ingredientes/', views.admin_ingredients, name='admin_ingredients'),
    path('admin-panel/ingredientes/crear/', views.admin_ingredient_create, name='admin_ingredient_create'),
    path('admin-panel/ingredientes/<int:ingredient_id>/editar/', views.admin_ingredient_edit, name='admin_ingredient_edit'),
    path('admin-panel/ingredientes/<int:ingredient_id>/eliminar/', views.admin_ingredient_delete, name='admin_ingredient_delete'),
    path('admin-panel/etiquetas/', views.admin_tags, name='admin_tags'),
    path('admin-panel/etiquetas/crear/', views.admin_tag_create, name='admin_tag_create'),
    path('admin-panel/etiquetas/<int:tag_id>/editar/', views.admin_tag_edit, name='admin_tag_edit'),
    path('admin-panel/etiquetas/<int:tag_id>/eliminar/', views.admin_tag_delete, name='admin_tag_delete'),
    
    # H03 - Explorar recetas
    path('', views.recipe_list, name='recipe_list'),  # Página principal
    path('recetas/', views.recipe_list, name='recipe_list_alt'),
    path('receta/<int:recipe_id>/', views.recipe_detail, name='recipe_detail'),
    
    # H02 - Crear y gestionar recetas
    path('crear-receta/', views.recipe_create, name='recipe_create'),
    path('mis-recetas/', views.my_recipes, name='my_recipes'),
    
    # H07 - Editar/eliminar recetas propias
    path('receta/<int:recipe_id>/editar/', views.recipe_edit, name='recipe_edit'),
    path('receta/<int:recipe_id>/eliminar/', views.recipe_delete, name='recipe_delete'),
    
    # H04 - Me gusta
    path('receta/<int:recipe_id>/like/', views.toggle_like, name='toggle_like'),
    
    # H06 - Búsqueda por ingredientes
    path('buscar-por-ingredientes/', views.search_by_ingredients, name='search_by_ingredients'),
    
    # H05 - Recomendaciones personalizadas
    path('recomendaciones/', views.recommendations, name='recommendations'),
    path('preferencias/', views.update_preferences, name='update_preferences'),
    
    # H10 - Recomendaciones inteligentes (IA)
    path('recomendaciones-ia/', views.smart_recommendations, name='smart_recommendations'),
    
    # API endpoints
    path('api/search-ingredients/', views.search_ingredients_api, name='search_ingredients_api'),
]
