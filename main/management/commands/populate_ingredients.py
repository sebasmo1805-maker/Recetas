from django.core.management.base import BaseCommand
from main.models import Ingredient

class Command(BaseCommand):
    help = 'Poblar la base de datos con ingredientes comunes de cocina'

    def handle(self, *args, **options):
        ingredientes = [
            # Carnes y proteínas
            'Pollo', 'Pechuga de pollo', 'Muslo de pollo', 'Carne de res', 'Carne molida', 
            'Bistec', 'Costillas', 'Cerdo', 'Chuleta de cerdo', 'Jamón', 'Tocino', 
            'Chorizo', 'Salchicha', 'Pavo', 'Pescado', 'Salmón', 'Atún', 'Camarones', 
            'Langostinos', 'Pulpo', 'Calamar', 'Sardinas', 'Bacalao',
            
            # Huevos y lácteos
            'Huevos', 'Leche', 'Leche evaporada', 'Leche condensada', 'Crema de leche', 
            'Mantequilla', 'Margarina', 'Queso', 'Queso fresco', 'Queso mozzarella', 
            'Queso parmesano', 'Queso cheddar', 'Queso crema', 'Ricotta', 'Yogur', 
            'Yogur griego', 'Queso cottage', 'Suero de leche',
            
            # Vegetales y verduras
            'Cebolla', 'Cebolla blanca', 'Cebolla morada', 'Cebollín', 'Ajo', 'Ajos porro', 
            'Tomate', 'Tomate cherry', 'Pimiento', 'Pimiento rojo', 'Pimiento verde', 
            'Pimiento amarillo', 'Ají', 'Jalapeño', 'Zanahoria', 'Apio', 'Papa', 
            'Papa dulce', 'Yuca', 'Calabaza', 'Calabacín', 'Berenjena', 'Pepino', 
            'Lechuga', 'Espinaca', 'Acelga', 'Col', 'Repollo', 'Coliflor', 'Brócoli', 
            'Rábano', 'Remolacha', 'Nabo', 'Chayote', 'Okra', 'Ejotes', 'Habichuelas',
            
            # Frutas
            'Limón', 'Lima', 'Naranja', 'Mandarina', 'Toronja', 'Manzana', 'Pera', 
            'Plátano', 'Plátano verde', 'Fresa', 'Mora', 'Frambuesa', 'Arándanos', 
            'Uva', 'Mango', 'Piña', 'Papaya', 'Melón', 'Sandía', 'Kiwi', 'Durazno', 
            'Ciruela', 'Cereza', 'Coco', 'Aguacate', 'Maracuyá', 'Guayaba',
            
            # Granos y cereales
            'Arroz', 'Arroz integral', 'Quinoa', 'Avena', 'Cebada', 'Trigo', 'Centeno', 
            'Amaranto', 'Mijo', 'Arroz salvaje', 'Bulgur', 'Cuscús',
            
            # Legumbres
            'Frijoles', 'Frijoles negros', 'Frijoles rojos', 'Frijoles blancos', 
            'Lentejas', 'Garbanzos', 'Arvejas', 'Habas', 'Soja', 'Frijol mungo',
            
            # Pastas y harinas
            'Pasta', 'Espagueti', 'Macarrones', 'Penne', 'Fusilli', 'Lasaña', 
            'Ravioli', 'Ñoquis', 'Harina de trigo', 'Harina integral', 'Harina de maíz', 
            'Harina de arroz', 'Harina de avena', 'Harina de almendra', 'Maicena', 
            'Fécula de papa',
            
            # Frutos secos y semillas
            'Almendras', 'Nueces', 'Avellanas', 'Pistachos', 'Cacahuates', 'Piñones', 
            'Semillas de girasol', 'Semillas de calabaza', 'Chía', 'Linaza', 
            'Semillas de sésamo', 'Nuez de Brasil', 'Anacardos', 'Pecanas',
            
            # Aceites y grasas
            'Aceite de oliva', 'Aceite de girasol', 'Aceite de canola', 'Aceite de coco', 
            'Aceite de sésamo', 'Aceite de aguacate', 'Manteca', 'Ghee',
            
            # Especias y condimentos
            'Sal', 'Pimienta negra', 'Pimienta blanca', 'Pimentón', 'Comino', 'Orégano', 
            'Tomillo', 'Romero', 'Albahaca', 'Perejil', 'Cilantro', 'Eneldo', 'Menta', 
            'Salvia', 'Laurel', 'Canela', 'Clavo de olor', 'Nuez moscada', 'Jengibre', 
            'Cúrcuma', 'Curry en polvo', 'Garam masala', 'Paprika', 'Cayena', 
            'Ajo en polvo', 'Cebolla en polvo', 'Mostaza en polvo', 'Anís', 'Cardamomo',
            
            # Hierbas frescas
            'Albahaca fresca', 'Perejil fresco', 'Cilantro fresco', 'Menta fresca', 
            'Romero fresco', 'Tomillo fresco', 'Orégano fresco', 'Eneldo fresco',
            
            # Condimentos líquidos
            'Vinagre', 'Vinagre de manzana', 'Vinagre balsámico', 'Salsa de soja', 
            'Salsa inglesa', 'Salsa de pescado', 'Mirin', 'Sake', 'Vino blanco', 
            'Vino tinto', 'Brandy', 'Ron', 'Licor',
            
            # Endulzantes
            'Azúcar', 'Azúcar morena', 'Azúcar glass', 'Miel', 'Jarabe de maple', 
            'Melaza', 'Stevia', 'Panela', 'Piloncillo',
            
            # Productos de panadería
            'Pan', 'Pan integral', 'Pan pita', 'Tortillas', 'Galletas', 'Pan rallado', 
            'Levadura', 'Polvo de hornear', 'Bicarbonato de sodio',
            
            # Conservas y enlatados
            'Tomate en lata', 'Pasta de tomate', 'Salsa de tomate', 'Atún enlatado', 
            'Sardinas enlatadas', 'Maíz enlatado', 'Frijoles enlatados', 'Aceitunas', 
            'Aceitunas negras', 'Alcaparras', 'Pepinillos',
            
            # Otros ingredientes
            'Chocolate', 'Chocolate negro', 'Cacao en polvo', 'Vainilla', 'Extracto de vainilla', 
            'Café', 'Té', 'Gelatina sin sabor', 'Agar agar', 'Levadura nutricional', 
            'Tempeh', 'Tofu', 'Seitan', 'Proteína de soja texturizada',
            
            # Ingredientes internacionales
            'Miso', 'Tahini', 'Hummus', 'Wasabi', 'Nori', 'Wakame', 'Kimchi', 
            'Sriracha', 'Harissa', 'Chimichurri', 'Pesto', 'Tapenade'
        ]
        
        created_count = 0
        existing_count = 0
        
        for nombre in ingredientes:
            ingredient, created = Ingredient.objects.get_or_create(name=nombre)
            if created:
                created_count += 1
                self.stdout.write(f'✓ Creado: {nombre}')
            else:
                existing_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n¡Proceso completado!\n'
                f'Ingredientes creados: {created_count}\n'
                f'Ingredientes que ya existían: {existing_count}\n'
                f'Total de ingredientes en la base de datos: {Ingredient.objects.count()}'
            )
        )