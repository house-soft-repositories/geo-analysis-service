from django.contrib.gis import admin
from .models import CamadaEstadual, CamadaAmbiental, CamadaGenerica


@admin.register(CamadaEstadual)
class CamadaEstadualAdmin(admin.GISModelAdmin):
    list_display = ("nome", "uf", "tipo", "fonte", "criado_em")
    list_filter = ("uf", "tipo")
    search_fields = ("nome", "uf")


@admin.register(CamadaAmbiental)
class CamadaAmbientalAdmin(admin.GISModelAdmin):
    list_display = ("nome", "tipo", "codigo", "uf", "fonte", "criado_em")
    list_filter = ("tipo", "uf")
    search_fields = ("nome", "codigo")


@admin.register(CamadaGenerica)
class CamadaGenericaAdmin(admin.GISModelAdmin):
    list_display = ("slug", "descricao", "criado_em", "atualizado_em")
    search_fields = ("slug", "descricao")
