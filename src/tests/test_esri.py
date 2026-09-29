import unittest
from unittest.mock import MagicMock, patch, call

from src.stac_utils.esri import query_feature_server

TEST_URL = "https://example.com/arcgis/rest/services/Test/FeatureServer/0/query"


def make_response(features, exceeded_transfer_limit=False, error=None):
    response = MagicMock()
    response.raise_for_status = MagicMock()
    if error:
        response.json.return_value = {"error": error}
    else:
        response.json.return_value = {
            "features": features,
            "exceededTransferLimit": exceeded_transfer_limit,
        }
    return response


class TestQueryFeatureServer(unittest.TestCase):
    @patch("src.stac_utils.esri.requests.get")
    def test_single_page(self, mock_get: MagicMock):
        """Test a single page of results is returned with no extra requests"""

        mock_get.return_value = make_response(
            [
                {"attributes": {"NAME": "Site A"}},
                {"attributes": {"NAME": "Site B"}},
            ]
        )

        rows = query_feature_server(TEST_URL)

        self.assertEqual(
            [{"NAME": "Site A"}, {"NAME": "Site B"}],
            rows,
        )
        mock_get.assert_called_once_with(
            TEST_URL,
            params={
                "where": "1=1",
                "outFields": "*",
                "returnGeometry": False,
                "f": "json",
                "resultRecordCount": 2000,
                "resultOffset": 0,
            },
        )

    @patch("src.stac_utils.esri.requests.get")
    def test_pages_until_transfer_limit_not_exceeded(self, mock_get: MagicMock):
        """Test that it pages through results while exceededTransferLimit is true"""

        mock_get.side_effect = [
            make_response(
                [{"attributes": {"NAME": "Site A"}}], exceeded_transfer_limit=True
            ),
            make_response(
                [{"attributes": {"NAME": "Site B"}}], exceeded_transfer_limit=False
            ),
        ]

        rows = query_feature_server(TEST_URL, page_size=1)

        self.assertEqual([{"NAME": "Site A"}, {"NAME": "Site B"}], rows)
        self.assertEqual(
            [
                call(
                    TEST_URL,
                    params={
                        "where": "1=1",
                        "outFields": "*",
                        "returnGeometry": False,
                        "f": "json",
                        "resultRecordCount": 1,
                        "resultOffset": 0,
                    },
                ),
                call(
                    TEST_URL,
                    params={
                        "where": "1=1",
                        "outFields": "*",
                        "returnGeometry": False,
                        "f": "json",
                        "resultRecordCount": 1,
                        "resultOffset": 1,
                    },
                ),
            ],
            mock_get.call_args_list,
        )

    @patch("src.stac_utils.esri.requests.get")
    def test_stops_on_empty_page_even_if_transfer_limit_flag_is_set(
        self, mock_get: MagicMock
    ):
        """Test it doesn't loop forever if a page comes back empty"""

        mock_get.return_value = make_response([], exceeded_transfer_limit=True)

        rows = query_feature_server(TEST_URL)

        self.assertEqual([], rows)
        mock_get.assert_called_once()

    @patch("src.stac_utils.esri.requests.get")
    def test_return_geometry_adds_lat_lon_and_requests_wgs84(
        self, mock_get: MagicMock
    ):
        """Test geometry is requested in lat/lon and split onto each row"""

        mock_get.return_value = make_response(
            [
                {
                    "attributes": {"NAME": "Site A"},
                    "geometry": {"x": -110.9, "y": 32.2},
                }
            ]
        )

        rows = query_feature_server(TEST_URL, return_geometry=True)

        self.assertEqual(
            [{"NAME": "Site A", "longitude": -110.9, "latitude": 32.2}], rows
        )
        _, kwargs = mock_get.call_args
        self.assertEqual(True, kwargs["params"]["returnGeometry"])
        self.assertEqual(4326, kwargs["params"]["outSR"])

    @patch("src.stac_utils.esri.requests.get")
    def test_raises_on_esri_error_payload(self, mock_get: MagicMock):
        """Test an Esri-style error response (still HTTP 200) raises"""

        mock_get.return_value = make_response(
            [], error={"code": 400, "message": "Invalid where clause"}
        )

        self.assertRaises(RuntimeError, query_feature_server, TEST_URL)

    @patch("src.stac_utils.esri.requests.get")
    def test_raises_on_bad_http_status(self, mock_get: MagicMock):
        """Test that a non-2xx response propagates its raised exception"""

        response = MagicMock()
        response.raise_for_status.side_effect = Exception("500 Server Error")
        mock_get.return_value = response

        self.assertRaises(Exception, query_feature_server, TEST_URL)


if __name__ == "__main__":
    unittest.main()
