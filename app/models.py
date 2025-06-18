from django.db import models
from datetime import datetime
from decimal import Decimal

class Publication(models.Model):
    publication_name = models.CharField(max_length=255, unique=True)
    created_at = models.DateField(default=datetime.now)

    def __str__(self):
        return self.publication_name

    class Meta:
        ordering = ['publication_name']

class Supply(models.Model):
    supply_name = models.CharField(max_length=255, unique=True)
    publication = models.ForeignKey(Publication, on_delete=models.SET_NULL, null=True, blank=True, related_name='supplies')
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    units = models.IntegerField(null=True, blank=True)
    purchase_date = models.DateField(default=datetime.now, null=True, blank=True)
    arrival_date = models.DateField(null=True, blank=True)  # New field for arrival date

    def __str__(self):
        return self.supply_name

    class Meta:
        ordering = ['-purchase_date']

class Sale(models.Model):
    sale_id = models.CharField(max_length=50, primary_key=True)
    publication = models.ForeignKey(Publication, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    publication_name = models.CharField(max_length=255, blank=True)
    buyer = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=100, blank=True)
    sale_date = models.DateField(null=True, blank=True)
    dispatch_date = models.DateField(null=True, blank=True)
    delivery_method = models.CharField(max_length=100, blank=True)
    units = models.IntegerField(null=True, blank=True)
    income = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    transaction_costs = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    shipping_costs = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    refunds = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    source = models.CharField(max_length=100, blank=True)
    previous_units = models.IntegerField(null=True, blank=True)
    previous_status = models.CharField(max_length=100, null=True, blank=True)
    previous_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    arrived = models.BooleanField(default=False)

    def __str__(self):
        return self.sale_id

    class Meta:
        ordering = ['-sale_date']

class PublicityCost(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.SET_NULL, null=True, blank=True, related_name='publicity_costs')
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    date = models.DateField(default=datetime.now, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.publication.publication_name if self.publication else 'Unassigned'} - {self.cost} on {self.date}"

    class Meta:
        ordering = ['-date']

class ProcessedFile(models.Model):
    file_path = models.CharField(max_length=255, primary_key=True)
    file_hash = models.CharField(max_length=32)
    last_processed = models.DateTimeField()

    def __str__(self):
        return self.file_path

    class Meta:
        ordering = ['-last_processed']

class UnassignedPublication(models.Model):
    publication_name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.publication_name

    class Meta:
        ordering = ['created_at']