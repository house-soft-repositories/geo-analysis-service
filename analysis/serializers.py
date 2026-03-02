from rest_framework import serializers
from .services.overlap_service import ALL_CHECKS


class AnaliseOverlapSerializer(serializers.Serializer):
    """
    Serializador para a requisição de análise de sobreposição.

    Body: multipart/form-data
    """

    kml_area = serializers.FileField(
        help_text="Arquivo KML/KMZ/GeoJSON/Shapefile(ZIP) da área de intervenção. Obrigatório.",
    )
    kml_imovel = serializers.FileField(
        required=False,
        help_text="Arquivo KML do imóvel. Necessário para o check de contenção.",
    )
    uf = serializers.CharField(
        max_length=2,
        required=False,
        default="",
        help_text="Sigla do estado para verificação de limite (ex: SC).",
    )
    checks = serializers.MultipleChoiceField(
        choices=ALL_CHECKS,
        required=False,
        help_text="Lista de checks a executar. Padrão: todos.",
    )
    slugs_camadas = serializers.ListField(
        child=serializers.SlugField(),
        required=False,
        default=list,
        help_text="Lista de slugs de CamadasGenericas a verificar.",
    )
    tipos_ambientais = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text="Lista de tipos ambientais para verificação (APP, UNIDADE_CONSERVACAO, etc.).",
    )

    def validate_checks(self, value):
        if not value:
            return ALL_CHECKS
        return list(value)

    def validate_uf(self, value):
        if value:
            return value.upper()
        return value
