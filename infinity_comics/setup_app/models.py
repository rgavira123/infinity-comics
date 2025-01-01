from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class User(AbstractUser):
    favorite_characters = models.ManyToManyField('Character', blank=True, related_name='fans')
    read_comics = models.ManyToManyField('Comic', through='UserComic', related_name='readers')
    recommended_comics = models.ManyToManyField('Comic', related_name='recommended_to_users', blank=True)

    def __str__(self):
        return self.username

class Estado(models.Model):
    datos_cargados = models.BooleanField(default=False)  # Flag para indicar si los datos están cargados
    ultima_actualizacion = models.DateTimeField(auto_now=True)  # Fecha de la última actualización
    
class Comic(models.Model):
    title = models.CharField(max_length=255)
    summary = models.TextField()  # Resumen o sinopsis del cómic
    image = models.URLField(null=True, blank=True)  # URL de la imagen del cómic
    characters = models.ManyToManyField('Character', related_name='comics')
    teams = models.ManyToManyField('Team', related_name='comics')
    locations = models.ManyToManyField('Location', related_name='comics')
    concepts = models.ManyToManyField('Concept', related_name='comics')
    related_objects = models.ManyToManyField('Object', related_name='comics')
    story_arcs = models.ManyToManyField('StoryArc', related_name='comics')
    
    similar_comics = models.ManyToManyField(
        'self',
        through='ComicSimilarity',
        symmetrical=False,
        related_name='related_comics'
    )

    def __str__(self):
        return self.title

class UserComic(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comic = models.ForeignKey(Comic, on_delete=models.CASCADE)
    read = models.BooleanField(default=False)
    liked = models.BooleanField(default=False)
    disliked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'comic')

class ComicSimilarity(models.Model):
    comic = models.ForeignKey(Comic, on_delete=models.CASCADE, related_name='similarity_base')
    similar_comic = models.ForeignKey(Comic, on_delete=models.CASCADE, related_name='similarity_related')
    similarity_score = models.FloatField()  # Guardamos el valor de la similitud

    class Meta:
        unique_together = ('comic', 'similar_comic')
    
    
class RelatedEntity(models.Model):
    name = models.CharField(max_length=255, unique=True)
    photo = models.URLField(null=True, blank=True)

    class Meta:
        abstract = True  # Este modelo no se crea en la base de datos

    def __str__(self):
        return self.name
    
    
class Character(RelatedEntity):
    pass  


class Team(RelatedEntity):
    pass  


class Location(RelatedEntity):
    pass  


class Concept(RelatedEntity):
    pass  


class Object(RelatedEntity):
    pass  


class StoryArc(RelatedEntity):
    pass  




