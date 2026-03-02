from django.db import models
from django.contrib.gis.db import models as gis_models


class TipoCamadaAmbiental(models.TextChoices):
    RESERVA_LEGAL = "RESERVA_LEGAL", "Reserva Legal"
    APP = "APP", "Área de Preservação Permanente"
    UNIDADE_CONSERVACAO = "UNIDADE_CONSERVACAO", "Unidade de Conservação"
    ASSENTAMENTO = "ASSENTAMENTO", "Assentamento"
    OUTRO = "OUTRO", "Outro"


class CamadaEstadual(models.Model):
    """
    Armazena os limites geográficos de estados brasileiros.
    Utilizada para verificar se uma geometria está dentro do limite estadual.
    """

    nome = models.CharField(max_length=255, help_text="Nome do estado.")
    uf = models.CharField(max_length=2, db_index=True, unique=True, help_text="Sigla do estado (ex: SC).")
    geometry = gis_models.MultiPolygonField(srid=4326, help_text="Geometria do limite (SRID 4326).")
    fonte = models.CharField(max_length=255, blank=True, default="", help_text="Fonte do dado (ex: IBGE 2023).")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Camada Estadual"
        verbose_name_plural = "Camadas Estaduais"
        ordering = ["uf"]
        indexes = [
            models.Index(fields=["uf"]),
        ]

    def __str__(self):
        return f"{self.nome} ({self.uf})"


class CamadaMunicipal(models.Model):
    """
    Armazena os limites geográficos de municípios brasileiros.
    Utilizada para verificar se uma geometria está dentro do limite municipal.
    """

    nome = models.CharField(max_length=255, help_text="Nome do município.")
    uf = models.CharField(max_length=2, db_index=True, help_text="Sigla do estado (ex: SC).")
    codigo_ibge = models.CharField(
        max_length=7,
        db_index=True,
        unique=True,
        help_text="Código IBGE do município com 7 dígitos (ex: 4205407).",
    )
    geometry = gis_models.MultiPolygonField(srid=4326, help_text="Geometria do limite (SRID 4326).")
    fonte = models.CharField(max_length=255, blank=True, default="", help_text="Fonte do dado (ex: IBGE 2023).")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Camada Municipal"
        verbose_name_plural = "Camadas Municipais"
        ordering = ["uf", "nome"]
        indexes = [
            models.Index(fields=["uf"]),
            models.Index(fields=["codigo_ibge"]),
        ]

    def __str__(self):
        return f"{self.nome}/{self.uf} ({self.codigo_ibge})"


class CamadaAmbiental(models.Model):
    """
    Armazena camadas ambientais restritas (Reserva Legal, APP, Unidades de Conservação, etc.).
    Utilizada para verificar sobreposição de geometrias com áreas protegidas.
    """

    nome = models.CharField(max_length=255)
    tipo = models.CharField(max_length=30, choices=TipoCamadaAmbiental.choices, db_index=True)
    codigo = models.CharField(max_length=100, blank=True, default="", help_text="Código identificador externo (ex: CAR, SNUC).")
    geometry = gis_models.MultiPolygonField(srid=4326)
    fonte = models.CharField(max_length=255, blank=True, default="")
    uf = models.CharField(max_length=2, blank=True, default="", db_index=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Camada Ambiental"
        verbose_name_plural = "Camadas Ambientais"
        ordering = ["tipo", "nome"]
        indexes = [
            models.Index(fields=["tipo", "uf"]),
        ]

    def __str__(self):
        return f"[{self.tipo}] {self.nome}"


class CamadaGenerica(models.Model):
    """
    Camada de polígonos de referência de propósito geral.
    Identificada por slug único — permite análise de sobreposição arbitrária.
    """

    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    descricao = models.CharField(max_length=255)
    geometry = gis_models.GeometryCollectionField(srid=4326)
    metadados = models.JSONField(default=dict, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Camada Genérica"
        verbose_name_plural = "Camadas Genéricas"
        ordering = ["slug"]

    def __str__(self):
        return self.slug
