from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from setup_app import views

urlpatterns = [
    path('', views.index, name='index'),
    path('cargar_datos/', views.cargar_datos, name='cargar_datos'),
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
]