from django.core.management.base import BaseCommand
from main.models import Tag, Ingredient

class Command(BaseCommand):
    help = 'Poblar datos iniciales de etiquetas e ingredientes'

    def handle(self, *args, **options):
        # Crear etiquetas
        tags_data = [
            ('vegetariana', '#28a745'),
            ('vegana', '#20c997'), 
            ('sin gluten', '#ffc107'),
            ('rápida', '#dc3545'),
            ('fácil', '#17a2b8'),
            ('saludable', '#6f42c1'),
            ('postre', '#fd7e14'),
            ('desayuno', '#6610f2'),
            ('almuerzo', '#e83e8c'),
            ('cena', '#343a40'),
            ('aperitivo', '#007bff'),
            ('bebida', '#20c997'),
            ('italiana', '#28a745'),
            ('mexicana', '#dc3545'),
            ('asiática', '#ffc107'),
            ('mediterránea', '#17a2b8')
        ]

        tags_created = 0
        for name, color in tags_data:
            tag, created = Tag.objects.get_or_create(name=name, defaults={'color': color})
            if created:
                tags_created += 1
                self.stdout.write(f'Etiqueta creada: {name}')

        # Crear ingredientes básicos
        ingredients = [
            'Arroz', 'Pollo', 'Carne de res', 'Cerdo', 'Pescado', 'Camarón',
            'Huevos', 'Leche', 'Queso', 'Mantequilla', 'Aceite de oliva',
            'Cebolla', 'Ajo', 'Tomate', 'Pimiento', 'Zanahoria', 'Apio',
            'Papas', 'Lechuga', 'Espinaca', 'Brócoli', 'Coliflor',
            'Frijoles', 'Lentejas', 'Garbanzos', 'Maíz',
            'Harina', 'Azúcar', 'Sal', 'Pimienta', 'Comino', 'Orégano',
            'Perejil', 'Cilantro', 'Limón', 'Naranja', 'Manzana', 'Plátano',
            'Pan', 'Pasta', 'Avena', 'Quinoa', 'Yogur', 'Crema',
            'Vinagre', 'Mostaza', 'Salsa de soja', 'Miel', 'Canela',
            'Albahaca', 'Romero', 'Tomillo', 'Jengibre', 'Chiles',
            'Aguacate', 'Coco', 'Almendras', 'Nueces', 'Café'
        ]

        ingredients_created = 0
        for ingredient_name in ingredients:
            ingredient, created = Ingredient.objects.get_or_create(name=ingredient_name)
            if created:
                ingredients_created += 1
                self.stdout.write(f'Ingrediente creado: {ingredient_name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Datos iniciales creados exitosamente!\n'
                f'Etiquetas creadas: {tags_created}\n'
                f'Ingredientes creados: {ingredients_created}\n'
                f'Total etiquetas: {Tag.objects.count()}\n'
                f'Total ingredientes: {Ingredient.objects.count()}'
            )
        )