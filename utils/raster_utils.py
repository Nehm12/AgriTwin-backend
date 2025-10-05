# utils/raster_utils.py
import rasterio
from rasterio.warp import transform
import pyproj

def extract_value_from_tiff(tiff_path, lat, lon):
    """
    Retourne la valeur du pixel pour une coordonnée donnée (lat, lon).
    - lat/lon sont en WGS84 (EPSG:4326)
    - conversion automatique si le raster a une projection différente
    """
    try:
        with rasterio.open(tiff_path) as src:
            # Reprojection si nécessaire
            raster_crs = src.crs
            if raster_crs.to_string() != "EPSG:4326":
                x, y = transform(pyproj.CRS("EPSG:4326"), raster_crs, [lon], [lat])
                coords = [(x[0], y[0])]
            else:
                coords = [(lon, lat)]

            values = [val[0] for val in src.sample(coords)]
            if values and values[0] is not None:
                return float(values[0])
            else:
                print(f"⚠️ Aucun pixel trouvé dans {tiff_path} pour ({lat},{lon})")
                return None
    except Exception as e:
        print(f"❌ Erreur lecture TIFF {tiff_path}: {e}")
        return None
