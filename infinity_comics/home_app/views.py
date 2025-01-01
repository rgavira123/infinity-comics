from django.core.paginator import Paginator
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from whoosh.index import open_dir
from whoosh.qparser import QueryParser

from setup_app.recommendations import calculate_user_recommendations
from setup_app.models import Character, Comic, UserComic

# Create your views here.

@login_required
def home(request):
    """
    Vista para mostrar todos los cómics.
    """
    user = request.user
    if not user.favorite_characters.exists():
        return redirect('select_heroes')
    
    # Manejo de búsqueda
    search_query = request.GET.get('search', '')
    comics = Comic.objects.filter(title__icontains=search_query).order_by('title')

    # Paginación
    paginator = Paginator(comics, 12)  # 12 cómics por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'home.html', {
        'comics': page_obj,
        'search_query': search_query,
    })

@login_required
def comic_detail(request, comic_id):
    """
    Vista para mostrar los detalles de un cómic.
    """
    comic = get_object_or_404(Comic, id=comic_id)
    similar_comics = comic.similar_comics.all()
    favorite_characters = request.user.favorite_characters.all()
    user_comic, created = UserComic.objects.get_or_create(user=request.user, comic=comic)
    return render(request, 'comic_detail.html', {
        'comic': comic,
        'similar_comics': similar_comics,
        'favorite_characters': favorite_characters,
        'user_comic': user_comic,
    })

@login_required
def update_user_comic(request):
    """
    Vista para actualizar las preferencias del usuario sobre un cómic.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            comic_id = data.get('comic_id')
            action = data.get('action')
            comic = get_object_or_404(Comic, id=comic_id)
            user_comic, created = UserComic.objects.get_or_create(user=request.user, comic=comic)

            if action == 'read':
                user_comic.read = not user_comic.read
            elif action == 'like':
                user_comic.liked = not user_comic.liked
                if user_comic.liked:
                    user_comic.disliked = False
            elif action == 'dislike':
                user_comic.disliked = not user_comic.disliked
                if user_comic.disliked:
                    user_comic.liked = False

            user_comic.save()
            return JsonResponse({'status': 'success'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
def select_favorite_characters(request):
    """
    Vista para que los usuarios seleccionen sus personajes favoritos.
    """
    user = request.user

    # Inicializa la sesión para personajes seleccionados si no existe
    if 'selected_characters' not in request.session:
        request.session['selected_characters'] = []

    # Manejo de búsqueda
    search_query = request.GET.get('search', '')
    characters = Character.objects.filter(name__icontains=search_query).order_by('name')

    # Paginación
    paginator = Paginator(characters, 24)  # 24 personajes por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Recupera los IDs seleccionados para marcarlos como `checked`
    selected_ids = request.session['selected_characters']

    # Si el usuario confirma la selección
    if request.method == 'POST' and 'confirm' in request.POST:
        for char_id in selected_ids:
            character = Character.objects.get(id=char_id)
            user.favorite_characters.add(character)
        request.session.pop('selected_characters')  # Limpia la selección en sesión
        return redirect('home')

    return render(request, 'select_heroes.html', {
        'characters': page_obj,
        'search_query': search_query,
        'selected_ids': selected_ids,
    })

@login_required
def update_selected_characters(request):
    """
    Vista para actualizar la selección de personajes en la sesión.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            char_id = data.get('char_id')
            action = data.get('action')
            stored_ids = request.session.get('selected_characters', [])

            if action == 'add' and char_id not in stored_ids:
                stored_ids.append(char_id)
            elif action == 'remove' and char_id in stored_ids:
                stored_ids.remove(char_id)

            request.session['selected_characters'] = stored_ids
            return JsonResponse({'status': 'success'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

@login_required
def profile(request):
    """
    Vista para mostrar el perfil del usuario.
    """
    user = request.user
    favorite_characters = user.favorite_characters.all()
    read_comics = user.read_comics.filter(usercomic__read=True)
    liked_comics = user.read_comics.filter(usercomic__liked=True)
    disliked_comics = user.read_comics.filter(usercomic__disliked=True)

    return render(request, 'profile.html', {
        'favorite_characters': favorite_characters,
        'read_comics': read_comics,
        'liked_comics': liked_comics,
        'disliked_comics': disliked_comics,
    })

@login_required
def recommendations(request):
    """
    Vista para mostrar las recomendaciones de cómics al usuario.
    """
    user = request.user
    calculate_user_recommendations(user)
    recommended_comics = user.recommended_comics.all()

    return render(request, 'recommendations.html', {
        'recommended_comics': recommended_comics,
    })

def search_comics(query_str, field="title"):
    """
    Busca cómics en el índice de Whoosh utilizando el título o el resumen.
    
    :param query_str: Término de búsqueda
    :param field: Campo en el que buscar (por defecto, "title")
    :return: Lista de resultados con títulos, resúmenes y personajes
    """
    index_dir = "././whoosh_indexes/comics"  # Directorio del índice de Whoosh
    index = open_dir(index_dir)

    with index.searcher() as searcher:
        query = QueryParser(field, index.schema).parse(query_str)
        results = searcher.search(query, limit=10)  # Limita a los 10 primeros resultados

        # Construir una lista de resultados
        return [
            {
                "id": result.get("id"),
                "title": result.get("title", "No title"),
                "summary": result.get("summary", "No summary available"),
                "characters": result.get("characters", "No characters listed"),
                "image": result.get("image", ""),
            }
            for result in results
        ]

@login_required
def search_by_summary(request):
    """
    Vista para buscar cómics por el contenido del resumen.
    """
    query = request.GET.get('query', '')
    results = search_comics(query, field="summary") if query else []
    return render(request, 'search_results.html', {
        'query': query,
        'results': results,
    })

