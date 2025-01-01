import time
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth import logout, login, authenticate
from setup_app.forms import UserLoginForm, UserRegisterForm
from django.contrib.auth.forms import AuthenticationForm
from setup_app.recommendations import precompute_comic_similarities
from setup_app.scrape_index import create_whoosh_index, scrape, scrape_and_save
from setup_app.models import Estado

# Create your views here.

def index(request):
    """
    View principal para la ruta ''.
    - Si los datos no están cargados, redirige a la página de carga.
    - Si los datos están cargados, redirige a la landing page (index real).
    """
    estado = Estado.objects.first()
    
    if not estado or not estado.datos_cargados:
        return render(request, 'carga.html')
    
    return render(request, 'landing.html')


def cargar_datos(request):
    # Simula un proceso de carga con un retraso
    # time.sleep(3)  # Simula un retraso de 3 segundos
    
    scrape_and_save()
    create_whoosh_index()
    precompute_comic_similarities(k=6)


    # Cambia el estado a "datos cargados"
    estado, created = Estado.objects.get_or_create(id=1)
    estado.datos_cargados = True
    estado.save()

    # Devuelve una respuesta JSON indicando que se completó la carga
    return JsonResponse({'success': True})


def register(request):
    if request.user.is_authenticated:
        # Si el usuario ya está autenticado, redirige al Home
        return redirect('home')  # Cambia 'home' por la vista correspondiente
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user )
            return redirect('home')  
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})



def custom_login(request):
    if request.user.is_authenticated:
        # Si el usuario ya está autenticado, redirige al Home
        return redirect('home')  

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                login(request, user)
                return redirect('home')  # Cambia 'home' por la vista correspondiente
            else:
                form.add_error(None, 'Usuario o contraseña incorrectos')
    else:
        form = UserLoginForm()

    return render(request, 'login.html', {'form': form})


def custom_logout(request):
    logout(request)
    return redirect('/')

