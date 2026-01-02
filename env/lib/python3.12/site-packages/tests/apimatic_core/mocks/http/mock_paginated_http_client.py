from apimatic_core.factories.http_response_factory import HttpResponseFactory
from apimatic_core.http.response.http_response import HttpResponse
from apimatic_core_interfaces.client.http_client import HttpClient

from apimatic_core.utilities.api_helper import ApiHelper


class MockPaginatedHttpClient(HttpClient):
    @property
    def transactions(self):
        return [
            {
                "id": "txn_1",
                "amount": 100.25,
                "timestamp": "Tue, 11 Mar 2025 12:00:00 GMT"
            },
            {
                "id": "txn_2",
                "amount": 200.50,
                "timestamp": "Tue, 11 Mar 2025 12:05:00 GMT"
            },
            {
                "id": "txn_3",
                "amount": 150.75,
                "timestamp": "Tue, 11 Mar 2025 12:10:00 GMT"
            },
            {
                "id": "txn_4",
                "amount": 50.00,
                "timestamp": "Tue, 11 Mar 2025 12:15:00 GMT"
            },
            {
                "id": "txn_5",
                "amount": 500.10,
                "timestamp": "Tue, 11 Mar 2025 12:20:00 GMT"
            },
            {
                "id": "txn_6",
                "amount": 75.25,
                "timestamp": "Tue, 11 Mar 2025 12:25:00 GMT"
            },
            {
                "id": "txn_7",
                "amount": 300.00,
                "timestamp": "Tue, 11 Mar 2025 12:30:00 GMT"
            },
            {
                "id": "txn_8",
                "amount": 400.75,
                "timestamp": "Tue, 11 Mar 2025 12:35:00 GMT"
            },
            {
                "id": "txn_9",
                "amount": 120.90,
                "timestamp": "Tue, 11 Mar 2025 12:40:00 GMT"
            },
            {
                "id": "txn_10",
                "amount": 250.30,
                "timestamp": "Tue, 11 Mar 2025 12:45:00 GMT"
            },
            {
                "id": "txn_11",
                "amount": 99.99,
                "timestamp": "Tue, 11 Mar 2025 12:50:00 GMT"
            },
            {
                "id": "txn_12",
                "amount": 350.40,
                "timestamp": "Tue, 11 Mar 2025 12:55:00 GMT"
            },
            {
                "id": "txn_13",
                "amount": 80.60,
                "timestamp": "Tue, 11 Mar 2025 13:00:00 GMT"
            },
            {
                "id": "txn_14",
                "amount": 60.10,
                "timestamp": "Tue, 11 Mar 2025 13:05:00 GMT"
            },
            {
                "id": "txn_15",
                "amount": 199.99,
                "timestamp": "Tue, 11 Mar 2025 13:10:00 GMT"
            },
            {
                "id": "txn_16",
                "amount": 500.75,
                "timestamp": "Tue, 11 Mar 2025 13:15:00 GMT"
            },
            {
                "id": "txn_17",
                "amount": 650.50,
                "timestamp": "Tue, 11 Mar 2025 13:20:00 GMT"
            },
            {
                "id": "txn_18",
                "amount": 180.90,
                "timestamp": "Tue, 11 Mar 2025 13:25:00 GMT"
            },
            {
                "id": "txn_19",
                "amount": 90.25,
                "timestamp": "Tue, 11 Mar 2025 13:30:00 GMT"
            },
            {
                "id": "txn_20",
                "amount": 320.40,
                "timestamp": "Tue, 11 Mar 2025 13:35:00 GMT"
            }
        ]

    def __init__(self):
        self._current_index = 0
        self._page_number = 1
        self._batch_limit = 5
        self._should_retry = None
        self._contains_binary_response = None
        self.response_factory = HttpResponseFactory()

    def execute(self, request, endpoint_configuration):
        """Execute a given CoreHttpRequest to get a string response back

        Args:
            request (HttpRequest): The given HttpRequest to execute.
            endpoint_configuration (EndpointConfiguration): The endpoint configurations to use.

        Returns:
            HttpResponse: The response of the CoreHttpRequest.

        """
        transaction_batch = self.transactions[self._current_index: self._current_index + 5]
        self._current_index += self._batch_limit
        self._page_number += 1

        if '/transactions/cursor' in request.query_url:
            return self.response_factory.create(
                status_code=200, reason=None, headers=request.headers,
                body=ApiHelper.json_serialize({
                    "data": transaction_batch,
                    "nextCursor": transaction_batch[-1]['id'] if self._current_index < len(self.transactions) else None
                }),
                request=request)

        if '/transactions/offset' in request.query_url:
            return self.response_factory.create(
                status_code=200, reason=None, headers=request.headers,
                body=ApiHelper.json_serialize({
                    "data": transaction_batch
                }),
                request=request)

        if '/transactions/links' in request.query_url:
            return self.response_factory.create(
                status_code=200, reason=None, headers=request.headers,
                body=ApiHelper.json_serialize({
                    "data": transaction_batch,
                    "links": {
                        "next": f"/transactions/links?page=${self._page_number + 1}&size={self._batch_limit}",
                    }
                }),
                request=request)

        if '/transactions/page' in request.query_url:
            return self.response_factory.create(
                status_code=200, reason=None, headers=request.headers,
                body=ApiHelper.json_serialize({
                    "data": transaction_batch,
                }),
                request=request)


    def convert_response(self, response, contains_binary_response, http_request):
        """Converts the Response object of the CoreHttpClient into an
        CoreHttpResponse object.

        Args:
            response (dynamic): The original response object.
            contains_binary_response (bool): The flag to check if the response is of binary type.
            http_request (HttpRequest): The original HttpRequest object.

        Returns:
            CoreHttpResponse: The converted CoreHttpResponse object.

        """
        pass
