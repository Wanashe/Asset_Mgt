from django.contrib import admin
from .models import Asset, Ticket, Location, AssetTransfer

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'floor', 'building')

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'asset_tag', 'category', 'assigned_to', 'current_location', 'condition')
    list_filter = ('category', 'condition', 'current_location')
    search_fields = ('name', 'asset_tag', 'assigned_to')

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('asset', 'priority', 'status', 'reported_at')
    list_filter = ('status', 'priority')

@admin.register(AssetTransfer)
class AssetTransferAdmin(admin.ModelAdmin):
    list_display = ('asset', 'from_person', 'to_person', 'from_location', 'to_location', 'transferred_at')
    list_filter = ('transferred_at',)
    search_fields = ('asset__name', 'asset__asset_tag', 'from_person', 'to_person')