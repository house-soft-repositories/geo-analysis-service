from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import CamadaEstadual, CamadaMunicipal, CamadaAmbiental, CamadaGenerica


class CamadaEstadualSerializer(serializers.ModelSerializer):
    class Meta:
        model = CamadaEstadual
        fields = ["id", "nome", "uf", "fonte", "criado_em"]


class CamadaMunicipalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CamadaMunicipal
        fields = ["id", "nome", "uf", "codigo_ibge", "fonte", "criado_em"]


class CamadaAmbientalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CamadaAmbiental
        fields = ["id", "nome", "tipo", "codigo", "uf", "fonte", "criado_em", "atualizado_em"]


class CamadaGenericaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CamadaGenerica
        fields = ["id", "slug", "descricao", "metadados", "criado_em", "atualizado_em"]


class ImportarCamadaSerializer(serializers.Serializer):
    """Serializador para importação de camadas via upload de arquivo."""

    TIPO_CHOICES = [
        ("ESTADUAL", "Estadual (limites de estado)"),
        ("MUNICIPAL", "Municipal (limites de município)"),
        ("AMBIENTAL", "Ambiental (reserva legal, APP, etc.)"),
        ("GENERICA", "Genérica (qualquer polígono de referência)"),
    ]

    arquivo = serializers.FileField(help_text="Arquivo KML, KMZ, GeoJSON ou Shapefile (ZIP).")
    tipo = serializers.ChoiceField(choices=TIPO_CHOICES, help_text="Tipo da camada a importar.")

    # Campos comuns
    nome = serializers.CharField(max_length=255, required=False, default="", help_text="Nome da camada (obrigatório para ESTADUAL/MUNICIPAL/AMBIENTAL).")
    uf = serializers.CharField(max_length=2, required=False, default="", help_text="Sigla do estado (ex: SC).")
    fonte = serializers.CharField(max_length=255, required=False, default="")

    # Campos específicos por tipo
    slug = serializers.SlugField(max_length=100, required=False, help_text="Slug único (obrigatório para GENERICA).")
    descricao = serializers.CharField(max_length=255, required=False, default="")

    # Para camadas municipais
    codigo_ibge = serializers.CharField(
        max_length=7,
        required=False,
        default="",
        help_text="Código IBGE do município com 7 dígitos (obrigatório para MUNICIPAL).",
    )

    # Para camadas ambientais
    tipo_ambiental = serializers.ChoiceField(
        choices=[(c, c) for c in ["RESERVA_LEGAL", "APP", "UNIDADE_CONSERVACAO", "ASSENTAMENTO", "OUTRO"]],
        required=False,
        default="OUTRO",
        help_text="Subtipo ambiental (somente para tipo=AMBIENTAL).",
    )
    codigo = serializers.CharField(max_length=100, required=False, default="")

    def validate(self, data):
        tipo = data.get("tipo")

        if tipo in ("ESTADUAL", "MUNICIPAL", "AMBIENTAL") and not data.get("nome"):
            raise serializers.ValidationError({"nome": f"Campo obrigatório para camadas do tipo {tipo}."})

        if tipo in ("ESTADUAL", "MUNICIPAL") and not data.get("uf"):
            raise serializers.ValidationError({"uf": f"Campo obrigatório para camadas do tipo {tipo}."})

        if tipo == "MUNICIPAL" and not data.get("codigo_ibge"):
            raise serializers.ValidationError({"codigo_ibge": "Campo obrigatório para camadas do tipo MUNICIPAL."})

        if tipo == "GENERICA" and not data.get("slug"):
            raise serializers.ValidationError({"slug": "Campo obrigatório para camadas do tipo GENERICA."})

        return data
