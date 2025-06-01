from django.contrib import admin
from .models import WordBank

@admin.register(WordBank)
class WordBankAdmin(admin.ModelAdmin):
    list_display = ('word', 'difficulty')
    list_filter = ('difficulty',)
    search_fields = ('word',)
    actions = ['delete_selected']
