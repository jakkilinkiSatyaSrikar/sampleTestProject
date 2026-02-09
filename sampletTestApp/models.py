from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50) # e.g., Electronics, Clothing
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class Sale(models.Model):
    # This Foreign Key is the "relationship" the AI needs to understand
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    region = models.CharField(max_length=100) # e.g., North, South
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    sale_date = models.DateField() # Essential for "This month vs last month" queries

    def __str__(self):
        return f"{self.product.name} - {self.region}"

# Create your models here.
