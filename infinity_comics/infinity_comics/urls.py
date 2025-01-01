from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('setup_app.urls')),
    path('home/', include('home_app.urls')),
]
