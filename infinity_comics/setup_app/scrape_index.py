import os
from bs4 import BeautifulSoup
import urllib.request
from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in

BASE_URL = "https://comicvine.gamespot.com"
from setup_app.models import Comic, Character, Team, Location, Concept, Object, StoryArc

def scrape():
    comic_links = []
    BASE_URL_SUMAR_i= BASE_URL+"/issues/?issue_filter%5Bletter%5D=&issue_filter%5BsortBy%5D=recent&issue_filter%5BminRating%5D=5&issue_filter%5Bpublishers%5D%5B4010-31%5D=4010-31&issue_filter%5BfromYear%5D=&issue_filter%5BtoYear%5D=&issue_filter%5Bteams%5D%5B4060-3173%5D=4060-3173&page="
    for i in range(1, 4):
        url = BASE_URL_SUMAR_i + str(i)
        html = urllib.request.urlopen(url)
        sopa = BeautifulSoup(html, 'lxml')
        
        lista_comics = sopa.find('ul', class_='editorial cover-grid compact')
        comics = lista_comics.find_all('li')
        
        
        for comic in comics:
            a_tag = comic.find('a', href=True)
            if a_tag:
                comic_links.append(a_tag['href'])
        
    print(comic_links) 
    return comic_links

def get_comic_title(soup):
    # Encuentra el contenedor con clase 'wiki-descriptor'
    descriptor = soup.find('p', class_='wiki-descriptor')
    
    # Busca el 'a' con clase 'wiki-title' dentro de 'wiki-descriptor'
    if descriptor:
        title_tag = descriptor.find('a', class_='wiki-title')
        if title_tag:
            return title_tag.text.strip()
    return None  # Devuelve None si no se encuentra


def scrape_comics_info(comic_links):
    comics_data = []

    for link in comic_links:
        try:
            html = urllib.request.urlopen(BASE_URL + link)
            soup = BeautifulSoup(html, 'lxml')

            # 1. Extraer el título
            title = get_comic_title(soup)

            # 2. Extraer el resumen (summary)
            summary_div = soup.find('div', class_='wiki-item-display js-toc-content')
            paragraphs = summary_div.find_all('p') if summary_div else []
            summary = " ".join([p.get_text(strip=True) for p in paragraphs])
            
            # 3. Extraer la imagen del cómic
            cover_div = soup.find('div', class_='img imgboxart issue-cover')
            comic_image = cover_div.find('img')['src'] if cover_div and cover_div.find('img') else None


            # 4. Extraer entidades relacionadas (Teams, Locations, etc.)
            related_entities = {
                'characters' : [],
                'teams': [],
                'locations': [],
                'concepts': [],
                'objects': [],
                'story arcs': [],
            }

            related_sections = soup.find_all('div', class_='wiki-details-object')
            for section in related_sections:
                h3_tag = section.find('h3')
                if h3_tag:
                    section_name = h3_tag.get_text(strip=True).lower()
                    if section_name in related_entities:  # Filtramos los que nos interesan
                        items = section.find_all('li')
                        for item in items:
                            a_tag = item.find('a', href=True)
                            img_tag = item.find('img', src=True)
                            if a_tag:
                                entity_name = a_tag.get_text(strip=True)
                                entity_image = img_tag['src'] if img_tag else None
                                related_entities[section_name].append({
                                    'name': entity_name,
                                    'image': entity_image
                                })

            # Guardar los datos recolectados
            comics_data.append({
                'title': title,
                'summary': summary,
                'image': comic_image,
                'characters': related_entities['characters'],
                'teams': related_entities['teams'],
                'locations': related_entities['locations'],
                'concepts': related_entities['concepts'],
                'objects': related_entities['objects'],
                'story_arcs': related_entities['story arcs'],
            })
            print(f"Procesado: {title}")

        except Exception as e:
            print(f"Error procesando {link}: {e}")

    #print(comics_data)
    return comics_data


def save_comic_data(comic_data):
    """
    Guarda los datos de un cómic en la base de datos.
    """
    # Crear o actualizar el cómic
    comic, created = Comic.objects.get_or_create(title=comic_data['title'])
    comic.summary = comic_data['summary']
    comic.image = comic_data['image']
    comic.save()

    # Relacionar personajes
    for character_data in comic_data['characters']:
        character, _ = Character.objects.get_or_create(name=character_data['name'])
        character.photo = character_data['image']
        character.save()
        comic.characters.add(character)

    # Relacionar equipos
    for team_data in comic_data['teams']:
        team, _ = Team.objects.get_or_create(name=team_data['name'])
        team.photo = team_data['image']
        team.save()
        comic.teams.add(team)

    # Relacionar localizaciones
    for location_data in comic_data['locations']:
        location, _ = Location.objects.get_or_create(name=location_data['name'])
        location.photo = location_data['image']
        location.save()
        comic.locations.add(location)

    # Relacionar conceptos
    for concept_data in comic_data['concepts']:
        concept, _ = Concept.objects.get_or_create(name=concept_data['name'])
        concept.photo = concept_data['image']
        concept.save()
        comic.concepts.add(concept)

    # Relacionar objetos
    for object_data in comic_data['objects']:
        obj, _ = Object.objects.get_or_create(name=object_data['name'])
        obj.photo = object_data['image']
        obj.save()
        comic.related_objects.add(obj)

    # Relacionar arcos de historia
    for story_arc_data in comic_data['story_arcs']:
        story_arc, _ = StoryArc.objects.get_or_create(name=story_arc_data['name'])
        story_arc.photo = story_arc_data['image']
        story_arc.save()
        comic.story_arcs.add(story_arc)

    print(f"Guardado cómic: {comic.title}")


def scrape_and_save():
    """
    Función principal para scrapear y guardar datos en la base de datos.
    """
    # Paso 1: Obtener los enlaces de los cómics
    comic_links = scrape()  # Usa tu función definida previamente

    # Paso 2: Obtener información detallada de los cómics
    comics_data = scrape_comics_info(comic_links)

    # Paso 3: Guardar en la base de datos
    for comic_data in comics_data:
        save_comic_data(comic_data)

def create_whoosh_index():
    # Directorio donde se guardarán los índices
    index_dir = "whoosh_indexes/comics"

    # Crear el directorio si no existe
    if not os.path.exists(index_dir):
        os.makedirs(index_dir)

    # Definir el esquema del índice simplificado
    schema = Schema(
        id=ID(stored=True),           # ID del cómic
        title=TEXT(stored=True),      # Título del cómic
        summary=TEXT(stored=True),    # Resumen
        characters=TEXT(stored=True), # Personajes (texto plano, separado por comas)
        image=TEXT(stored=True),      # URL de la imagen del cómic
    )

    # Crear o abrir el índice
    ix = create_in(index_dir, schema)

    # Añadir documentos al índice
    writer = ix.writer()

    comics = Comic.objects.prefetch_related('characters')
    for comic in comics:
        writer.add_document(
            id=str(comic.id),
            title=comic.title,
            summary=comic.summary or "",
            characters=", ".join([char.name for char in comic.characters.all()]),
            image=comic.image or "",
        )

    # Guardar los cambios en el índice
    writer.commit()

    print(f"Índice simplificado creado exitosamente en: {index_dir}")








