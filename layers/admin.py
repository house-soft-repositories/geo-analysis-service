from django.contrib.gis import admin
from .models import CamadaEstadual, CamadaMunicipal, CamadaAmbiental, CamadaGenerica


@admin.register(CamadaEstadual)
class CamadaEstadualAdmin(admin.GISModelAdmin):
    list_display = ("nome", "uf", "fonte", "criado_em")
    list_filter = ("uf",)
    search_fields = ("nome", "uf")


@admin.register(CamadaMunicipal)
class CamadaMunicipalAdmin(admin.GISModelAdmin):
    list_display = ("nome", "uf", "codigo_ibge", "fonte", "criado_em")
    list_filter = ("uf",)
    search_fields = ("nome", "codigo_ibge")


@admin.register(CamadaAmbiental)
class CamadaAmbientalAdmin(admin.GISModelAdmin):
    list_display = ("nome", "tipo", "codigo", "uf", "fonte", "criado_em")
    list_filter = ("tipo", "uf")
    search_fields = ("nome", "codigo")


@admin.register(CamadaGenerica)
class CamadaGenericaAdmin(admin.GISModelAdmin):
    list_display = ("slug", "descricao", "criado_em", "atualizado_em")
    search_fields = ("slug", "descricao")
