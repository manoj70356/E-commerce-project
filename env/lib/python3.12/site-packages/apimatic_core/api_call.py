from apimatic_core.configurations.endpoint_configuration import EndpointConfiguration
from apimatic_core.configurations.global_configuration import GlobalConfiguration
from apimatic_core.logger.sdk_logger import LoggerFactory
from apimatic_core.pagination.paginated_data import PaginatedData
from apimatic_core.response_handler import ResponseHandler
import copy

class ApiCall:

    @property
    def new_builder(self):
        return ApiCall(self._global_configuration)

    @property
    def request_builder(self):
        return self._request_builder

    @property
    def get_pagination_strategies(self):
        return self._pagination_strategies

    @property
    def global_configuration(self):
        return self._global_configuration

    def __init__(
            self,
            global_configuration=GlobalConfiguration()
    ):
        self._global_configuration = global_configuration
        self._request_builder = None
        self._response_handler = ResponseHandler()
        self._endpoint_configuration = EndpointConfiguration()
        self._api_logger = LoggerFactory.get_api_logger(self._global_configuration.get_http_client_configuration()
                                                        .logging_configuration)
        self._pagination_strategies = None

    def request(self, request_builder):
        self._request_builder = request_builder
        return self

    def response(self, response_handler):
        self._response_handler = response_handler
        return self

    def pagination_strategies(self, *pagination_strategies):
        self._pagination_strategies = pagination_strategies
        return self

    def endpoint_configuration(self, endpoint_configuration):
        self._endpoint_configuration = endpoint_configuration
        return self

    def execute(self):
        _http_client_configuration = self._global_configuration.get_http_client_configuration()

        if _http_client_configuration.http_client is None:
            raise ValueError("An HTTP client instance is required to execute an Api call.")

        _http_request = self._request_builder.build(self._global_configuration)

        # Logging the request
        self._api_logger.log_request(_http_request)

        _http_callback = _http_client_configuration.http_callback

        # Applying the on before sending HTTP request callback
        if _http_callback is not None:
            _http_callback.on_before_request(_http_request)

        # Executing the HTTP call
        _http_response = _http_client_configuration.http_client.execute(
            _http_request, self._endpoint_configuration)

        # Logging the response
        self._api_logger.log_response(_http_response)

        # Applying the after receiving HTTP response callback
        if _http_callback is not None:
            _http_callback.on_after_response(_http_response)

        return self._response_handler.handle(_http_response, self._global_configuration.get_global_errors())


    def paginate(self, page_iterable_creator, paginated_items_converter):
        return page_iterable_creator(PaginatedData(self, paginated_items_converter))

    def clone(self, global_configuration=None, request_builder=None, response_handler=None,
              endpoint_configuration=None, pagination_strategies=None):
        new_instance = copy.deepcopy(self)
        new_instance._global_configuration = global_configuration or self._global_configuration
        new_instance._request_builder = request_builder or self._request_builder
        new_instance._response_handler = response_handler or self._response_handler
        new_instance._endpoint_configuration = endpoint_configuration or self._endpoint_configuration
        new_instance._pagination_strategies = pagination_strategies or self._pagination_strategies
        return new_instance

    def __deepcopy__(self, memodict={}):
        copy_instance = ApiCall(self._global_configuration)
        copy_instance._request_builder = copy.deepcopy(self._request_builder, memo=memodict)
        copy_instance._response_handler = copy.deepcopy(self._response_handler, memo=memodict)
        copy_instance._endpoint_configuration = copy.deepcopy(self._endpoint_configuration, memo=memodict)
        copy_instance._pagination_strategies = copy.deepcopy(self._pagination_strategies, memo=memodict)
        return copy_instance
