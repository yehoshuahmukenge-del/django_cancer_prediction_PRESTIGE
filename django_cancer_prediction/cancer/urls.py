from django.urls import path
from . import views

app_name = 'cancer'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('predict/', views.predict, name='predict'),
    path('history/', views.history, name='history'),
    path('statistics/', views.statistics, name='statistics'),
]
