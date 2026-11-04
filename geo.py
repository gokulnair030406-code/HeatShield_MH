"""Geography helpers: Maharashtra outline, point-in-polygon, IDW interpolation, model-driven risk surface."""
import numpy as np

OUTLINE = [[22.0,72.6],[21.6,73.5],[22.0,74.2],[21.7,75.3],[21.9,76.4],[21.3,77.4],[21.5,78.4],[21.0,80.0],[20.0,80.9],[18.9,80.4],
           [17.8,80.2],[17.1,79.2],[16.0,78.5],[15.7,77.3],[16.3,76.2],[15.8,75.0],[15.9,73.8],[16.4,72.6],[17.6,72.5],[18.5,72.8],
           [19.5,72.6],[20.3,72.7],[21.2,72.5],[22.0,72.6]]
LAT0, LAT1, LON0, LON1 = 15.6, 22.1, 72.4, 81.0
_poly = np.array(OUTLINE)


def inside(lat, lon):
    """Vectorised ray casting."""
    lat, lon = np.asarray(lat, float), np.asarray(lon, float)
    res = np.zeros(lat.shape, bool); n = len(_poly)
    for i in range(n - 1):
        (y1, x1), (y2, x2) = _poly[i], _poly[i + 1]
        cond = ((y1 > lat) != (y2 > lat)) & (lon < (x2 - x1) * (lat - y1) / (y2 - y1 + 1e-12) + x1)
        res ^= cond
    return res


def idw(qlat, qlon, slat, slon, F):
    """Inverse-distance weighting of station feature matrix F (n,7) to query points."""
    qlat, qlon = np.atleast_1d(qlat)[:, None], np.atleast_1d(qlon)[:, None]
    dy = (qlat - slat[None]) * 111.0
    dx = (qlon - slon[None]) * 111.0 * np.cos(np.radians(qlat))
    d2 = dx ** 2 + dy ** 2
    w = (1.0 / (d2 + 200.0)) ** 1.5
    w /= w.sum(1, keepdims=True)
    return w @ F, np.sqrt(d2)


def grid(ny=70, nx=84):
    """Rows are uniform in Web-Mercator y so the overlay lines up on a Leaflet map."""
    ymin, ymax = [np.log(np.tan(np.pi / 4 + np.radians(l) / 2)) for l in (LAT0, LAT1)]
    ys = np.linspace(ymax, ymin, ny)
    lats = np.degrees(2 * np.arctan(np.exp(ys)) - np.pi / 2)
    lons = np.linspace(LON0, LON1, nx)
    return np.meshgrid(lons, lats)  # (ny,nx) each
