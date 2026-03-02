import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("layers", "0001_initial"),
    ]

    operations = [
        # Remove o campo 'tipo' de CamadaEstadual (que antes distinguia ESTADO/MUNICIPIO)
        migrations.RemoveField(
            model_name="camadaestadual",
            name="tipo",
        ),
        # Torna 'uf' único em CamadaEstadual (um registro por estado)
        migrations.AlterField(
            model_name="camadaestadual",
            name="uf",
            field=models.CharField(
                db_index=True,
                help_text="Sigla do estado (ex: SC).",
                max_length=2,
                unique=True,
            ),
        ),
        # Atualiza help_text e ordering de CamadaEstadual
        migrations.AlterField(
            model_name="camadaestadual",
            name="nome",
            field=models.CharField(help_text="Nome do estado.", max_length=255),
        ),
        migrations.AlterModelOptions(
            name="camadaestadual",
            options={
                "ordering": ["uf"],
                "verbose_name": "Camada Estadual",
                "verbose_name_plural": "Camadas Estaduais",
            },
        ),
        # Cria o novo modelo CamadaMunicipal
        migrations.CreateModel(
            name="CamadaMunicipal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(help_text="Nome do município.", max_length=255)),
                ("uf", models.CharField(db_index=True, help_text="Sigla do estado (ex: SC).", max_length=2)),
                (
                    "codigo_ibge",
                    models.CharField(
                        db_index=True,
                        help_text="Código IBGE do município com 7 dígitos (ex: 4205407).",
                        max_length=7,
                        unique=True,
                    ),
                ),
                (
                    "geometry",
                    django.contrib.gis.db.models.fields.MultiPolygonField(
                        help_text="Geometria do limite (SRID 4326).", srid=4326
                    ),
                ),
                ("fonte", models.CharField(blank=True, default="", help_text="Fonte do dado (ex: IBGE 2023).", max_length=255)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Camada Municipal",
                "verbose_name_plural": "Camadas Municipais",
                "ordering": ["uf", "nome"],
                "indexes": [
                    models.Index(fields=["uf"], name="layers_mun_uf_idx"),
                    models.Index(fields=["codigo_ibge"], name="layers_mun_ibge_idx"),
                ],
            },
        ),
    ]
