from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import CamadaEstadual, CamadaAmbiental, CamadaGenerica


class CamadaEstadualSerializer(serializers.ModelSerializer):
    class Meta:
        model = CamadaEstadual
        fields = ["id", "nome", "uf", "tipo", "fonte", "criado_em"]


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
        ("ESTADUAL", "Estadual (limites de estado/município)"),
        ("AMBIENTAL", "Ambiental (reserva legal, APP, etc.)"),
        ("GENERICA", "Genérica (qualquer polígono de referência)"),
    ]

    arquivo = serializers.FileField(help_text="Arquivo KML, KMZ, GeoJSON ou Shapefile (ZIP).")
    tipo = serializers.ChoiceField(choices=TIPO_CHOICES, help_text="Tipo da camada a importar.")

    # Campos específicos por tipo
    nome = serializers.CharField(max_length=255, required=False, default="", help_text="Nome da camada (obrigatório para ESTADUAL/AMBIENTAL).")
    uf = serializers.CharField(max_length=2, required=False, default="", help_text="Sigla do estado (ex: SC).")
    slug = serializers.SlugField(max_length=100, required=False, help_text="Slug único (obrigatório para GENERICA).")
    descricao = serializers.CharField(max_length=255, required=False, default="")
    fonte = serializers.CharField(max_length=255, required=False, default="")

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

        if tipo in ("ESTADUAL", "AMBIENTAL") and not data.get("nome"):
            raise serializers.ValidationError({"nome": "Campo obrigatório para camadas do tipo ESTADUAL e AMBIENTAL."})

        if tipo == "GENERICA" and not data.get("slug"):
            raise serializers.ValidationError({"slug": "Campo obrigatório para camadas do tipo GENERICA."})

        if tipo == "ESTADUAL" and not data.get("uf"):
            raise serializers.ValidationError({"uf": "Campo obrigatório para camadas do tipo ESTADUAL."})

        return data
