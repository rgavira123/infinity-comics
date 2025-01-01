from collections import defaultdict
from setup_app.models import Comic, ComicSimilarity


def calculate_jaccard_similarity(set_a, set_b):
    """
    Calcula la similaridad de Jaccard entre dos conjuntos.
    """
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0


def precompute_comic_similarities(k=5):
    """
    Preprocesa y guarda los k vecinos más cercanos para cada cómic en la base de datos.
    """
    # Paso 1: Obtener todos los cómics y construir conjuntos
    comics = Comic.objects.prefetch_related('characters', 'teams', 'locations', 'concepts', 'related_objects')
    comic_sets = {}

    for comic in comics:
        comic_sets[comic.id] = {
            'characters': set(comic.characters.values_list('id', flat=True)),
            'teams': set(comic.teams.values_list('id', flat=True)),
            'locations': set(comic.locations.values_list('id', flat=True)),
            'concepts': set(comic.concepts.values_list('id', flat=True)),
            'related_objects': set(comic.related_objects.values_list('id', flat=True)),
        }

    # Paso 2: Calcular similitudes y almacenar los k vecinos más cercanos
    ComicSimilarity.objects.all().delete()  # Limpia datos previos para evitar duplicados

    for comic_a_id, set_a in comic_sets.items():
        similarities = []

        for comic_b_id, set_b in comic_sets.items():
            if comic_a_id == comic_b_id:
                continue  # Ignorar comparaciones consigo mismo

            # Combinar los conjuntos para calcular similitud
            full_set_a = set_a['characters'] | set_a['teams'] | set_a['locations'] | set_a['concepts'] | set_a['related_objects']
            full_set_b = set_b['characters'] | set_b['teams'] | set_b['locations'] | set_b['concepts'] | set_b['related_objects']

            similarity = calculate_jaccard_similarity(full_set_a, full_set_b)
            similarities.append((comic_b_id, similarity))

        # Ordenar por similitud descendente y obtener los k vecinos más cercanos
        similarities = sorted(similarities, key=lambda x: -x[1])[:k]

        # Guardar en la base de datos
        for similar_comic_id, score in similarities:
            ComicSimilarity.objects.create(
                comic_id=comic_a_id,
                similar_comic_id=similar_comic_id,
                similarity_score=score
            )

    print("Preprocesamiento completado: Similitudes almacenadas exitosamente.")


def calculate_user_recommendations(user, k=4):
    """
    Calcula y guarda las recomendaciones de cómics para un usuario basado en sus cómics favoritos.
    """
    liked_comics = user.read_comics.filter(usercomic__liked=True)
    disliked_comics = set(user.read_comics.filter(usercomic__disliked=True).values_list('id', flat=True))
    favorite_characters = set(user.favorite_characters.values_list('id', flat=True))
    recommendations = defaultdict(float)
    bonus_value = 0.3  # Ajustar el valor del bonus

    for comic in liked_comics:
        similar_comics = ComicSimilarity.objects.filter(comic=comic).order_by('-similarity_score')[:k]
        for sim in similar_comics:
            if sim.similar_comic.id not in disliked_comics and sim.similar_comic not in liked_comics and not user.read_comics.filter(id=sim.similar_comic.id).exists():
                bonus = bonus_value if favorite_characters & set(sim.similar_comic.characters.values_list('id', flat=True)) else 0.0
                recommendations[sim.similar_comic] += sim.similarity_score + bonus

    # Ordenar recomendaciones por puntaje
    sorted_recommendations = sorted(recommendations.items(), key=lambda x: -x[1])[:k]
    user.recommended_comics.clear()
    for comic, score in sorted_recommendations:
        user.recommended_comics.add(comic)

    print(f"Recomendaciones calculadas para el usuario {user.username}")
