import requests


def query_feature_server(
    url: str,
    where: str = "1=1",
    out_fields: str = "*",
    return_geometry: bool = False,
    page_size: int = 2000,
) -> list[dict]:
    """
    Query every matching row from an Esri FeatureServer/MapServer layer's
    query endpoint (e.g. ".../FeatureServer/0/query"), paging through
    results as needed.

    Esri servers cap how many rows returned per request regardless of
    what you ask for, and signal there's more with `exceededTransferLimit`,
    so a single request isn't enough for any layer larger than that cap.

    :param url: the layer's query endpoint
    :param where: a SQL where clause, e.g. "ELECTION='2026 General'"
    :param out_fields: comma-separated field names to return, or "*" for all
    :param return_geometry: if True, points are requested in lat/lon
        (wkid 4326) and included in each row as "latitude"/"longitude"
    :param page_size: rows requested per page; actual pages may be smaller
        if the server enforces a lower cap
    :return: each feature's attributes as a dict, combined across all pages
    """
    rows = []
    offset = 0

    while True:
        params = {
            "where": where,
            "outFields": out_fields,
            "returnGeometry": return_geometry,
            "f": "json",
            "resultRecordCount": page_size,
            "resultOffset": offset,
        }
        if return_geometry:
            params["outSR"] = 4326

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise RuntimeError(f"Esri query to {url} failed: {data['error']}")

        features = data.get("features", [])
        for feature in features:
            row = feature["attributes"]
            if return_geometry and feature.get("geometry"):
                row["longitude"] = feature["geometry"].get("x")
                row["latitude"] = feature["geometry"].get("y")
            rows.append(row)

        if not features or not data.get("exceededTransferLimit"):
            break
        offset += len(features)

    return rows
