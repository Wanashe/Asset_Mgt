from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    path('', views.home, name='home'),
    path('asset-tables/', views.asset_sync_workspace, name='asset_sync_workspace'),
    path('asset-tables/add/', views.asset_add, name='asset_add'),
    path('asset-tables/edit/<int:asset_id>/', views.asset_edit, name='asset_edit'),
    path('asset-tables/delete/<int:asset_id>/', views.asset_delete, name='asset_delete'),
    
    # Asset Movement Routes
    path('asset-tables/transfer/', views.asset_transfer, name='asset_transfer'),
    path('asset-tables/transfer/<int:asset_id>/', views.asset_transfer, name='asset_transfer_item'),
    
    # Asset CSV & PDF Export Routes
    path('asset-tables/export/', views.asset_export_csv, name='asset_export_csv'),
    path('reports/export-pdf/', views.generate_pdf_report, name='generate_pdf_report'),
    
    # Reports Hub & History Logs
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    path('reports/transfer/', views.transfer_history_report, name='transfer_history_report'),
   
    # Active Transfer & Inventory Export Routes
    path('export/transfers/csv/', views.transfer_export_csv, name='transfer_export_csv'),
    path('export/transfers/pdf/', views.generate_pdf_report, name='transfer_export_pdf'), 
]