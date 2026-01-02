from apimatic_core.pagination.strategies.cursor_pagination import CursorPagination
from apimatic_core.pagination.strategies.link_pagination import LinkPagination
from apimatic_core.pagination.strategies.offset_pagination import OffsetPagination
from apimatic_core.pagination.strategies.page_pagination import PagePagination
from apimatic_core.request_builder import RequestBuilder
from apimatic_core.response_handler import ResponseHandler
from apimatic_core.types.parameter import Parameter
from apimatic_core.utilities.api_helper import ApiHelper
from apimatic_core_interfaces.types.http_method_enum import HttpMethodEnum
from tests.apimatic_core.base import Base
from tests.apimatic_core.mocks.callables.base_uri_callable import Server
from tests.apimatic_core.mocks.models.transactions_cursored import TransactionsCursored
from tests.apimatic_core.mocks.models.transactions_linked import TransactionsLinked
from tests.apimatic_core.mocks.models.transactions_offset import TransactionsOffset
from tests.apimatic_core.mocks.pagination.paged_iterable import PagedIterable
from tests.apimatic_core.mocks.pagination.paged_api_response import CursorPagedApiResponse, OffsetPagedApiResponse, \
    LinkPagedApiResponse, NumberPagedApiResponse
from tests.apimatic_core.mocks.pagination.paged_response import NumberPagedResponse, OffsetPagedResponse, \
    CursorPagedResponse, LinkPagedResponse


class TestPaginatedApiCall(Base):

    def setup_test(self, global_config):
        self.global_config = global_config
        self.http_response_catcher = self.global_config.get_http_client_configuration().http_callback
        self.http_client = self.global_config.get_http_client_configuration().http_client
        self.api_call_builder = self.new_api_call_builder(self.global_config)

    def _make_paginated_call(
            self, path, query_params, pagination_strategy, deserialize_into_model, is_api_response_enabled,
            body_params=None, form_params=None
    ):
        """
        Helper method to build and execute a paginated API call.
        """

        if body_params is None:
            body_params = {}

        if form_params is None:
            form_params = {}

        response_handler = ResponseHandler() \
            .deserializer(ApiHelper.json_deserialize) \
            .deserialize_into(deserialize_into_model)

        if is_api_response_enabled:
            response_handler.is_api_response(True)

        request_builder = RequestBuilder() \
            .server(Server.DEFAULT) \
            .path(path) \
            .http_method(HttpMethodEnum.GET) \
            .header_param(Parameter().key('accept').value('application/json'))

        for key, value in query_params.items():
            request_builder.query_param(Parameter().key(key).value(value))

        for key, value in body_params.items():
            request_builder.body_param(Parameter().key(key).value(value))

        for key, value in form_params.items():
            request_builder.form_param(Parameter().key(key).value(value))

        return self.api_call_builder.new_builder.request(request_builder) \
            .response(response_handler) \
            .pagination_strategies(pagination_strategy) \
            .paginate(
                lambda _paginated_data: PagedIterable(_paginated_data),
                lambda _response: _response.data
            )

    def _assert_paginated_results(self, result):
        """
        Helper method to assert the common pagination results.
        """
        assert isinstance(result, PagedIterable)
        paginated_data = []
        for item in result:
            paginated_data.append(item)

        assert len(paginated_data) == 20

        for page in result.pages():
            assert len(page.items()) == 5

    # --- Tests with API Response Enabled ---

    def test_link_paginated_call_with_api_response_enabled(self):
        self.setup_test(self.paginated_global_configuration)
        size = 5
        result = self._make_paginated_call(
            path='/transactions/links',
            query_params={'page': 1, 'size': size},
            pagination_strategy=LinkPagination(
                '$response.body#/links/next',
                lambda _response, _link: LinkPagedApiResponse.create(
                    _response, lambda _obj: _obj.data, _link)
            ),
            deserialize_into_model=TransactionsLinked.from_dictionary,
            is_api_response_enabled=True
        )
        self._assert_paginated_results(result)

    def test_cursor_paginated_call_with_api_response_enabled(self):
        self.setup_test(self.paginated_global_configuration)
        limit = 5
        result = self._make_paginated_call(
            path='/transactions/cursor',
            query_params={'cursor': 'initial cursor', 'limit': limit},
            pagination_strategy=CursorPagination(
                '$response.body#/nextCursor',
                '$request.query#/cursor',
                lambda _response, _cursor: CursorPagedApiResponse.create(
                    _response, lambda _obj: _obj.data, _cursor)
            ),
            deserialize_into_model=TransactionsCursored.from_dictionary,
            is_api_response_enabled=True
        )
        self._assert_paginated_results(result)

    def test_offset_paginated_call_with_api_response_enabled(self):
        self.setup_test(self.paginated_global_configuration)
        limit = 5
        result = self._make_paginated_call(
            path='/transactions/offset',
            query_params={'offset': 0, 'limit': limit},
            pagination_strategy=OffsetPagination(
                '$request.query#/offset',
                lambda _response, _offset: OffsetPagedApiResponse.create(
                    _response, lambda _obj: _obj.data, _offset)
            ),
            deserialize_into_model=TransactionsOffset.from_dictionary,
            is_api_response_enabled=True
        )
        self._assert_paginated_results(result)

    def test_page_paginated_call_with_api_response_enabled(self):
        self.setup_test(self.paginated_global_configuration)
        size = 5
        result = self._make_paginated_call(
            path='/transactions/page',
            query_params={'page': 1, 'size': size},
            pagination_strategy=PagePagination(
                '$request.query#/page',
                lambda _response, _page_no: NumberPagedApiResponse.create(
                    _response, lambda _obj: _obj.data, _page_no)
            ),
            deserialize_into_model=TransactionsLinked.from_dictionary,
            is_api_response_enabled=True
        )
        self._assert_paginated_results(result)

    # --- Tests with API Response Disabled ---

    def test_link_paginated_call_with_api_response_disabled(self):
        self.setup_test(self.paginated_global_configuration)
        size = 5
        result = self._make_paginated_call(
            path='/transactions/links',
            query_params={'page': 1, 'size': size},
            pagination_strategy=LinkPagination(
                '$response.body#/links/next',
                lambda _response, _link: LinkPagedResponse(
                    _response, lambda _obj: _obj.data, _link)
            ),
            deserialize_into_model=TransactionsLinked.from_dictionary,
            is_api_response_enabled=False
        )
        self._assert_paginated_results(result)

    def test_cursor_paginated_call_with_api_response_disabled(self):
        self.setup_test(self.paginated_global_configuration)
        limit = 5
        result = self._make_paginated_call(
            path='/transactions/cursor',
            query_params={'cursor': 'initial cursor', 'limit': limit},
            pagination_strategy=CursorPagination(
                '$response.body#/nextCursor',
                '$request.query#/cursor',
                lambda _response, _cursor: CursorPagedResponse(
                    _response, lambda _obj: _obj.data, _cursor)
            ),
            deserialize_into_model=TransactionsCursored.from_dictionary,
            is_api_response_enabled=False
        )
        self._assert_paginated_results(result)

    def test_offset_paginated_call_with_api_response_disabled(self):
        self.setup_test(self.paginated_global_configuration)
        limit = 5
        result = self._make_paginated_call(
            path='/transactions/offset',
            query_params={'offset': 0, 'limit': limit},
            pagination_strategy=OffsetPagination(
                '$request.query#/offset',
                lambda _response, _offset: OffsetPagedResponse(
                    _response, lambda _obj: _obj.data, _offset)
            ),
            deserialize_into_model=TransactionsOffset.from_dictionary,
            is_api_response_enabled=False
        )
        self._assert_paginated_results(result)

    def test_page_paginated_call_with_api_response_disabled(self):
        self.setup_test(self.paginated_global_configuration)
        size = 5
        result = self._make_paginated_call(
            path='/transactions/page',
            query_params={'page': 1, 'size': size},
            pagination_strategy=PagePagination(
                '$request.query#/page',
                lambda _response, _page_no: NumberPagedResponse(
                    _response, lambda _obj: _obj.data, _page_no)
            ),
            deserialize_into_model=TransactionsLinked.from_dictionary,
            is_api_response_enabled=False
        )
        self._assert_paginated_results(result)

    def test_page_paginated_json_body_call(self):
        self.setup_test(self.paginated_global_configuration)
        limit = 5
        result = self._make_paginated_call(
            path='/transactions/cursor',
            query_params={},
            body_params={'cursor': 'initial cursor', 'limit': limit},
            pagination_strategy=CursorPagination(
                '$response.body#/nextCursor',
                '$request.body#/cursor',
                lambda _response, _cursor: CursorPagedResponse(
                    _response, lambda _obj: _obj.data, _cursor)
            ),
            deserialize_into_model=TransactionsLinked.from_dictionary,
            is_api_response_enabled=False
        )
        self._assert_paginated_results(result)

    def test_page_paginated_form_body_call(self):
        self.setup_test(self.paginated_global_configuration)
        limit = 5
        result = self._make_paginated_call(
            path='/transactions/cursor',
            query_params={},
            form_params={'cursor': 'initial cursor', 'limit': limit},
            pagination_strategy=CursorPagination(
                '$response.body#/nextCursor',
                '$request.body#/cursor',
                lambda _response, _cursor: CursorPagedResponse(
                    _response, lambda _obj: _obj.data, _cursor)
            ),
            deserialize_into_model=TransactionsLinked.from_dictionary,
            is_api_response_enabled=False
        )
        self._assert_paginated_results(result)