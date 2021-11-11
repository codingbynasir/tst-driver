from django.contrib import admin

# Register your models here.
from account.models import Driver, Employee

admin.site.register(Driver)
admin.site.register(Employee)
