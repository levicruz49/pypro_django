from django.contrib.admin import ModelAdmin, register

from pypro.aperitivos.models import Video


@register(Video)
class VideoAdmin(ModelAdmin):
    list_display = ('titulo', 'slug', 'vimeo_id', 'creation')
    ordering = ('creation',)
    prepopulated_fields = {'slug': ('titulo',)}
