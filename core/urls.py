from django.urls import path
from django.contrib import admin
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.summary_view, name='summary'),
    path('upload/', views.excel_processing_view, name='excel_upload'),
    path('assign-publications/', views.assign_publications, name='assign_publications'),
]