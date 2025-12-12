from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('crop-suggestion/', views.crop_suggestion, name='crop_suggestion'),
    path('market-data/', views.market_data, name='market_data'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/download-insights.csv', views.download_insights_csv, name='download_insights_csv'),
    path('contact/', views.contact, name='contact'),
    path('schemes/', views.schemes, name='schemes'),
]
