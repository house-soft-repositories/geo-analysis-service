"""
KML / Shapefile importer.

Lê um arquivo enviado via upload, extrai as feições geométricas usando
GDAL (osgeo.ogr) e retorna uma lista de GEOSGeometry prontas para gravação.

Formatos suportados: KML, KMZ, GeoJSON, Shapefile (zip), GML.
"""
import io
import zipfile
import tempfile
import os
from typing import List

from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon, GeometryCollection
from osgeo import ogr, osr

from core.exceptions import KMLParseError, EmptyGeometryError


# SRID alvo para todos os dados internos
TARGET_SRID = 4326


def _ensure_multipolygon(geom: GEOSGeometry) -> MultiPolygon:
    """Converte Polygon em MultiPolygon; passa MultiPolygon diretamente."""
    if isinstance(geom, Polygon):
        return MultiPolygon(geom, srid=TARGET_SRID)
    if isinstance(geom, MultiPolygon):
        return geom
    raise KMLParseError(f"Geometria do tipo '{geom.geom_type}' não pode ser convertida para MultiPolygon.")


def _ogr_to_geos(ogr_geom) -> GEOSGeometry:
    """Converte osgeo.ogr.Geometry → GEOSGeometry reprojetada para SRID 4326 (sempre 2D)."""
    # Reprojetar para WGS84 se necessário
    wgs84 = osr.SpatialReference()
    wgs84.ImportFromEPSG(TARGET_SRID)
    src_srs = ogr_geom.GetSpatialReference()
    if src_srs and not src_srs.IsSame(wgs84):
        ogr_geom.TransformTo(wgs84)

    # Forçar 2D (remove dimensão Z presente em KMLs com altitude)
    ogr_geom.FlattenTo2D()

    wkt = ogr_geom.ExportToWkt()
    geos = GEOSGeometry(wkt, srid=TARGET_SRID)
    return geos


def _open_datasource(file_content: bytes, filename: str):
    """
    Abre um DataSource OGR a partir de bytes.
    Suporta KML, KMZ, GeoJSON, GML, e Shapefile (zip).
    """
    ext = os.path.splitext(filename)[1].lower()

    # KMZ é um ZIP contendo doc.kml
    if ext == ".kmz":
        with zipfile.ZipFile(io.BytesIO(file_content)) as zf:
            kml_names = [n for n in zf.namelist() if n.endswith(".kml")]
            if not kml_names:
                raise KMLParseError("Arquivo KMZ não contém nenhum arquivo .kml interno.")
            file_content = zf.read(kml_names[0])
            filename = kml_names[0]
            ext = ".kml"

    # Shapefile precisa de diretório temporário
    if ext == ".zip":
        tmpdir = tempfile.mkdtemp()
        with zipfile.ZipFile(io.BytesIO(file_content)) as zf:
            zf.extractall(tmpdir)
        shp_files = [f for f in os.listdir(tmpdir) if f.endswith(".shp")]
        if not shp_files:
            raise KMLParseError("ZIP não contém arquivo .shp.")
        ds = ogr.Open(os.path.join(tmpdir, shp_files[0]))
        if ds is None:
            raise KMLParseError("Não foi possível abrir o Shapefile.")
        return ds

    # Para formatos baseados em texto/xml: salva em arquivo temporário
    suffix = ext if ext in (".kml", ".geojson", ".json", ".gml") else ".kml"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name

    ds = ogr.Open(tmp_path)
    os.unlink(tmp_path)

    if ds is None:
        raise KMLParseError(f"GDAL não conseguiu abrir o arquivo '{filename}'. Verifique o formato.")
    return ds


def extract_geometries(file_content: bytes, filename: str) -> List[GEOSGeometry]:
    """
    Extrai todas as geometrias de um arquivo enviado.

    Retorna lista de GEOSGeometry reprojetadas para SRID 4326.
    Lança KMLParseError se o arquivo for inválido.
    Lança EmptyGeometryError se nenhuma feição for encontrada.
    """
    ds = _open_datasource(file_content, filename)

    geometries: List[GEOSGeometry] = []

    for layer_idx in range(ds.GetLayerCount()):
        layer = ds.GetLayer(layer_idx)
        for feature in layer:
            ogr_geom = feature.GetGeometryRef()
            if ogr_geom is None:
                continue
            geos = _ogr_to_geos(ogr_geom)
            if not geos.empty:
                if not geos.valid:
                    geos = geos.buffer(0)  # corrige geometrias inválidas
                geometries.append(geos)

    if not geometries:
        raise EmptyGeometryError()

    return geometries


def extract_single_geometry(file_content: bytes, filename: str) -> GEOSGeometry:
    """
    Extrai e une todas as geometrias em um único GEOSGeometry.
    Útil para KMLs com múltiplas feições que representam uma única área.
    """
    geoms = extract_geometries(file_content, filename)

    if len(geoms) == 1:
        return geoms[0]

    first = geoms[0]
    for g in geoms[1:]:
        first = first.union(g)

    return first


def extract_multipolygon(file_content: bytes, filename: str) -> MultiPolygon:
    """
    Extrai geometrias e garante retorno como MultiPolygon.
    Ideal para camadas de referência que devem ser polígonos.
    """
    geom = extract_single_geometry(file_content, filename)
    return _ensure_multipolygon(geom)
