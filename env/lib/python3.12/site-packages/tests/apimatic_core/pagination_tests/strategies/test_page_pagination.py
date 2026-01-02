import pytest

from apimatic_core.pagination.paginated_data import PaginatedData
from apimatic_core.pagination.strategies.page_pagination import PagePagination
from apimatic_core.request_builder import RequestBuilder
from tests.apimatic_core.pagination_tests.strategies.strategy_base import StrategyBase


class TestPagePagination(StrategyBase):

    @pytest.fixture
    def mock_metadata_wrapper(self, mocker):
        return mocker.Mock(name="metadata_wrapper_mock")

    @pytest.fixture
    def mock_request_builder(self, mocker):
        class MockRequestBuilder(RequestBuilder):
            @property
            def template_params(self):
                return self._template_params

            @property
            def query_params(self):
                return self._query_params

            @property
            def header_params(self):
                return self._header_params

            def __init__(self, template_params=None, query_params=None, header_params=None):
                super().__init__()
                self._template_params = template_params if template_params is not None else {}
                self._query_params = query_params if query_params is not None else {}
                self._header_params = header_params if header_params is not None else {}

            def clone_with(self, **kwargs):
                new_rb = MockRequestBuilder()
                new_rb._template_params = self.template_params.copy()
                new_rb._query_params = self.query_params.copy()
                new_rb._header_params = self.header_params.copy()

                if 'template_params' in kwargs:
                    new_rb.template_params.update(kwargs['template_params'])
                if 'query_params' in kwargs:
                    new_rb.query_params.update(kwargs['query_params'])
                if 'header_params' in kwargs:
                    new_rb.header_params.update(kwargs['header_params'])
                return new_rb

        rb = MockRequestBuilder(
            template_params={"page": 1},
            query_params={"page": 2, "limit": 10},
            header_params={"page": 3}
        )
        return rb

    @pytest.fixture
    def mock_last_response(self, mocker):
        response = mocker.Mock()
        response.text = '{"data": [{"id": 1}]}'
        response.headers = {'Content-Type': 'application/json'}
        return response

    @pytest.fixture
    def mock_paginated_data_initial_call(self, mocker, mock_request_builder):
        paginated_data = mocker.Mock(spec=PaginatedData)
        paginated_data.last_response = None
        paginated_data.request_builder = mock_request_builder
        paginated_data.page_size = 0
        return paginated_data

    @pytest.fixture
    def mock_paginated_data_subsequent_call_with_results(self, mocker, mock_request_builder, mock_last_response):
        paginated_data = mocker.Mock(spec=PaginatedData)
        paginated_data.last_response = mock_last_response
        paginated_data.request_builder = mock_request_builder
        paginated_data.page_size = 5
        return paginated_data

    @pytest.fixture
    def mock_paginated_data_subsequent_call_no_results(self, mocker, mock_request_builder, mock_last_response):
        paginated_data = mocker.Mock(spec=PaginatedData)
        paginated_data.last_response = mock_last_response
        paginated_data.request_builder = mock_request_builder
        paginated_data.page_size = 0
        return paginated_data

    def _create_page_pagination_instance(self, input_value, metadata_wrapper):
        return PagePagination(input_=input_value, metadata_wrapper=metadata_wrapper)

    def test_init_success(self, mock_metadata_wrapper):
        pp = self._create_page_pagination_instance("$request.query#/page", mock_metadata_wrapper)
        assert pp._input == "$request.query#/page"
        assert pp._metadata_wrapper == mock_metadata_wrapper
        assert pp._page_number == 1

    def test_init_input_none_raises_error(self, mock_metadata_wrapper):
        with pytest.raises(ValueError, match="Input pointer for page based pagination cannot be None"):
            self._create_page_pagination_instance(None, mock_metadata_wrapper)

    def test_init_metadata_wrapper_none_raises_error(self):
        with pytest.raises(ValueError, match="Metadata wrapper for the pagination cannot be None"):
            self._create_page_pagination_instance("$request.query#/page", None)

    def test_apply_initial_call_with_page_from_query(self, mocker, mock_paginated_data_initial_call,
                                                     mock_request_builder, mock_metadata_wrapper):
        mock_get_initial_request_param_value = mocker.patch.object(PagePagination, '_get_initial_request_param_value', return_value=5)

        pp = self._create_page_pagination_instance("$request.query#/page", mock_metadata_wrapper)
        result_rb = pp.apply(mock_paginated_data_initial_call)

        mock_get_initial_request_param_value.assert_called_once_with(mock_request_builder, "$request.query#/page", 1)
        assert pp._page_number == 5
        assert result_rb == mock_request_builder

    def test_apply_subsequent_call_increments_page_with_results(self, mocker,
                                                                mock_paginated_data_subsequent_call_with_results,
                                                                mock_request_builder):
        pp = self._create_page_pagination_instance("$request.query#/page", mocker.Mock())
        pp._page_number = 2

        mock_get_updated_request_builder = mocker.patch.object(
            PagePagination, 'get_updated_request_builder',
            return_value=mock_request_builder.clone_with(query_params={"page": 3, "limit": 10})
        )

        result_rb = pp.apply(mock_paginated_data_subsequent_call_with_results)

        assert pp._page_number == 3
        mock_get_updated_request_builder.assert_called_once_with(
            mock_request_builder, "$request.query#/page", 3
        )
        assert result_rb.query_params["page"] == 3

    def test_apply_subsequent_call_does_not_increment_page_with_no_results(self, mocker,
                                                                           mock_paginated_data_subsequent_call_no_results,
                                                                           mock_request_builder):
        pp = self._create_page_pagination_instance("$request.query#/page", mocker.Mock())
        pp._page_number = 3

        mock_get_updated_request_builder = mocker.patch.object(
            PagePagination, 'get_updated_request_builder'
        )

        pp.apply(mock_paginated_data_subsequent_call_no_results)

        assert pp._page_number == 2
        mock_get_updated_request_builder.assert_called_once_with(
            mock_request_builder, "$request.query#/page", 2
        )

    def test_apply_metadata_wrapper(self, mock_metadata_wrapper, mocker):
        mock_metadata_wrapper.return_value = "wrapped_response_with_page"

        pp = self._create_page_pagination_instance(
            input_value="$request.query#/page",
            metadata_wrapper=mock_metadata_wrapper
        )
        pp._page_number = 5
        mock_page_response = mocker.Mock()

        result = pp.apply_metadata_wrapper(mock_page_response)

        mock_metadata_wrapper.assert_called_once_with(mock_page_response, 5)
        assert result == "wrapped_response_with_page"

    @pytest.mark.parametrize(
        "input_pointer, initial_params, expected_value, json_pointer_return_value",
        [
            ("$request.path#/page", {"page": {"value": 2, "encoded": True}}, 2, "2"),
            ("$request.query#/page", {"page": 3, "limit": 10}, 3, "3"),
            ("$request.headers#/page", {"page": 4}, 4, "4"),
            ("$request.query#/page", {"limit": 10}, 0, None),
            ("invalid_prefix#/page", {"page": 10}, 0, "10"),
        ]
    )
    def test_get_initial_page_offset_various_scenarios(self, mocker, mock_request_builder, mock_metadata_wrapper,
                                                   input_pointer, initial_params, expected_value, json_pointer_return_value):
        self.assert_initial_param_extraction(
            mocker,
            mock_request_builder,
            mock_metadata_wrapper,
            input_pointer,
            initial_params,
            expected_value,
            json_pointer_return_value,
            default_value=0,
            pagination_instance_creator=self._create_page_pagination_instance
        )