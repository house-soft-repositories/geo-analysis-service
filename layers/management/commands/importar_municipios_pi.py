"""
Comando de importação dos municípios do Piauí — IBGE Localidades 2022.

Lê todos os arquivos KML do diretório informado (padrão do Piauí),
extrai as geometrias de localidade (pontos), aplica convex_hull para
gerar o polígono aproximado do município e registra em CamadaMunicipal.

Formato esperado de nome de arquivo:
    {nome_municipio}_{codigo_ibge_7dig}_localidades_{ano}.kml
    ex: acaua_2200053_localidades_2022.kml

Uso:
    python manage.py importar_municipios_pi --diretorio /caminho/para/PI/
    python manage.py importar_municipios_pi --diretorio /caminho/para/PI/ --dry-run
"""
import os
import re
import glob
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon, Point

from layers.models import CamadaMunicipal
from layers.importers.kml_importer import extract_geometries


# Regex para extrair código IBGE e nome do arquivo
# ex: acaua_2200053_localidades_2022.kml
_FILENAME_RE = re.compile(
    r"^(?P<slug>.+?)_(?P<codigo_ibge>\d{7})_localidades_\d{4}\.kml$",
    re.IGNORECASE,
)

UF = "PI"
FONTE = "IBGE Localidades 2022"


def _slug_para_nome(slug: str) -> str:
    """Converte o slug do arquivo em nome legível com acentuação básica."""
    palavras = slug.replace("_", " ").title()
    # Correções comuns de preposições e artigos
    preposicoes = {"Do", "Da", "De", "Dos", "Das", "E", "Do"}
    partes = palavras.split()
    resultado = [
        p.lower() if (p in preposicoes and i > 0) else p
        for i, p in enumerate(partes)
    ]
    return " ".join(resultado)


def _geometrias_para_multipolygon(geoms: list) -> MultiPolygon | None:
    """
    Converte uma lista de GEOSGeometry (geralmente pontos de localidades)
    em um MultiPolygon usando convex_hull.

    - 1 ponto  → buffer de 0.01 grau (~1 km) convertido em MultiPolygon
    - N pontos → union + convex_hull → Polygon → MultiPolygon
    - Polygon/MultiPolygon diretamente → normaliza para MultiPolygon
    """
    if not geoms:
        return None

    # Se já são polígonos, usa direto
    if all(g.geom_type in ("Polygon", "MultiPolygon") for g in geoms):
        uniao = geoms[0]
        for g in geoms[1:]:
            uniao = uniao.union(g)
        if uniao.geom_type == "Polygon":
            return MultiPolygon(uniao, srid=4326)
        if uniao.geom_type == "MultiPolygon":
            return uniao

    # Caso pontos/linhas: une tudo e aplica convex_hull
    uniao = geoms[0]
    for g in geoms[1:]:
        uniao = uniao.union(g)

    hull = uniao.convex_hull

    if hull.geom_type == "Point":
        # Único ponto: buffer ~0.01 grau ≈ 1 km
        buffered = hull.buffer(0.01)
        if buffered.geom_type == "Polygon":
            return MultiPolygon(buffered, srid=4326)
        return None

    if hull.geom_type == "LineString":
        # Dois pontos colineares: buffer fino
        buffered = hull.buffer(0.005)
        if buffered.geom_type == "Polygon":
            return MultiPolygon(buffered, srid=4326)
        return None

    if hull.geom_type == "Polygon":
        return MultiPolygon(hull, srid=4326)

    if hull.geom_type == "MultiPolygon":
        return hull

    return None


class Command(BaseCommand):
    help = "Importa municípios do Piauí a partir dos KMLs de localidades do IBGE 2022."

    def add_arguments(self, parser):
        parser.add_argument(
            "--diretorio",
            required=True,
            help="Caminho para o diretório com os arquivos KML do Piauí.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Apenas lê e valida os arquivos, sem gravar no banco.",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="Exibe detalhes de cada município processado.",
        )

    def handle(self, *args, **options):
        diretorio = Path(options["diretorio"])
        dry_run = options["dry_run"]
        verbose = options["verbose"]

        if not diretorio.exists():
            raise CommandError(f"Diretório não encontrado: {diretorio}")

        arquivos = sorted(diretorio.glob("*.kml"))

        if not arquivos:
            raise CommandError(f"Nenhum arquivo .kml encontrado em: {diretorio}")

        self.stdout.write(
            self.style.NOTICE(
                f"{'[DRY-RUN] ' if dry_run else ''}Encontrados {len(arquivos)} arquivo(s) KML em {diretorio}"
            )
        )

        criados = 0
        atualizados = 0
        erros = 0
        ignorados = 0

        for arquivo in arquivos:
            match = _FILENAME_RE.match(arquivo.name)
            if not match:
                self.stdout.write(
                    self.style.WARNING(f"  [IGNORADO] Nome não reconhecido: {arquivo.name}")
                )
                ignorados += 1
                continue

            slug = match.group("slug")
            codigo_ibge = match.group("codigo_ibge")
            nome = _slug_para_nome(slug)

            try:
                file_content = arquivo.read_bytes()
                geoms = extract_geometries(file_content, arquivo.name)
                multipolygon = _geometrias_para_multipolygon(geoms)

                if multipolygon is None:
                    self.stdout.write(
                        self.style.WARNING(f"  [ERRO] Não foi possível gerar polígono: {arquivo.name}")
                    )
                    erros += 1
                    continue

                if verbose:
                    self.stdout.write(
                        f"  {nome} ({codigo_ibge}) — {len(geoms)} ponto(s) → hull {multipolygon.geom_type}"
                    )

                if not dry_run:
                    _, created = CamadaMunicipal.objects.update_or_create(
                        codigo_ibge=codigo_ibge,
                        defaults={
                            "nome": nome,
                            "uf": UF,
                            "geometry": multipolygon,
                            "fonte": FONTE,
                        },
                    )
                    if created:
                        criados += 1
                    else:
                        atualizados += 1
                else:
                    criados += 1  # conta como "seria criado/atualizado"

            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(f"  [ERRO] {arquivo.name}: {exc}")
                )
                erros += 1

        # Resumo final
        self.stdout.write("")
        if dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"[DRY-RUN] Concluído — {criados} seriam importados, {ignorados} ignorados, {erros} erro(s)."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Importação concluída — {criados} criados, {atualizados} atualizados, "
                f"{ignorados} ignorados, {erros} erro(s)."
            ))
