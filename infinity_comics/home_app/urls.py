from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from home_app import views

urlpatterns = [
    path('', views.home, name='home'),
    path('select-heroes/', views.select_favorite_characters, name='select_heroes'),
    path('update-selected-characters/', views.update_selected_characters, name='update_selected_characters'),
    path('comic/<int:comic_id>/', views.comic_detail, name='comic_detail'),
    path('update-user-comic/', views.update_user_comic, name='update_user_comic'),
    path('profile/', views.profile, name='profile'),  # Nueva URL para el perfil del usuario
    path('recommendations/', views.recommendations, name='recommendations'),
    path('search-summary/', views.search_by_summary, name='search_by_summary'),
]