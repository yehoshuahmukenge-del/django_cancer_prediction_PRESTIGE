from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from academic.views import emploi_du_temps

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('emploi-du-temps/', emploi_du_temps, name='emploi_du_temps'),
]
