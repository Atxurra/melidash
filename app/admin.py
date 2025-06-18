from django.contrib import admin
from .models import Publication, Supply, Sale, PublicityCost, ProcessedFile, UnassignedPublication

@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('publication_name', 'created_at')
    search_fields = ('publication_name',)
    list_filter = ('created_at',)

@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ('supply_name', 'publication', 'total_cost', 'units', 'purchase_date', 'arrival_date')
    search_fields = ('supply_name', 'publication__publication_name')
    list_filter = ('publication', 'purchase_date')
    autocomplete_fields = ['publication']

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('sale_id', 'publication', 'buyer', 'status', 'sale_date', 'units', 'total', 'source', 'arrived')
    search_fields = ('sale_id', 'buyer', 'publication__publication_name')
    list_filter = ('publication', 'status', 'sale_date', 'source', 'arrived')
    autocomplete_fields = ['publication']
    readonly_fields = ('previous_units', 'previous_status', 'previous_total')

    def save_model(self, request, obj, form, change):
        if change and obj.source == 'External':
            obj.previous_units = obj.units
            obj.previous_status = obj.status
            obj.previous_total = obj.total
            obj.total = (obj.income or 0) - (obj.transaction_costs or 0) - (obj.shipping_costs or 0) - (obj.refunds or 0)
        super().save_model(request, obj, form, change)

@admin.register(PublicityCost)
class PublicityCostAdmin(admin.ModelAdmin):
    list_display = ('publication', 'cost', 'date', 'description')
    search_fields = ('publication__publication_name', 'description')
    list_filter = ('publication', 'date')
    autocomplete_fields = ['publication']
    actions = ['delete_selected']

@admin.register(ProcessedFile)
class ProcessedFileAdmin(admin.ModelAdmin):
    list_display = ('file_path', 'last_processed')
    search_fields = ('file_path',)
    list_filter = ('last_processed',)

@admin.register(UnassignedPublication)
class UnassignedPublicationAdmin(admin.ModelAdmin):
    list_display = ('publication_name', 'created_at')
    search_fields = ('publication_name',)
    list_filter = ('created_at',)
    actions = ['create_publication']

    def create_publication(self, request, queryset):
        for unassigned in queryset:
            Publication.objects.get_or_create(
                publication_name=unassigned.publication_name,
                defaults={'created_at': unassigned.created_at.date()}
            )
            unassigned.delete()
        self.message_user(request, f"Created {queryset.count()} publications.")
    create_publication.short_description = "Create publications from selected unassigned names"