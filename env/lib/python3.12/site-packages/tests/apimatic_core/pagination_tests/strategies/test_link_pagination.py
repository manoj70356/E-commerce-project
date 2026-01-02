import pytest

from apimatic_core.utilities.api_helper import ApiHelper
from apimatic_core.request_builder import RequestBuilder
from apimatic_core.pagination.strategies.link_pagination import LinkPagination


class TestLinkPagination:

    @pytest.fixture
    def mock_metadata_wrapper(self, mocker):
        return mocker.Mock(name="metadata_wrapper_mock")

    @pytest.fixture
    def mock_request_builder(self, mocker):
        # A simple mock for RequestBuilder that can be cloned
        class MockRequestBuilder(RequestBuilder):

            @property
            def query_params(self):
                return self._query_params

            def __init__(self, query_params=None):
                super().__init__()
                self._query_params = query_params if query_params is not None else {}

            def clone_with(self, **kwargs):
                new_rb = MockRequestBuilder()
                # Copy existing attributes
                new_rb._query_params = self.query_params.copy()

                # Apply updates from kwargs
                if 'query_params' in kwargs:
                    new_rb._query_params = kwargs['query_params']
                return new_rb

        rb = MockRequestBuilder(query_params={"initial_param": "initial_value"})
        return rb

    @pytest.fixture
    def mock_last_response_with_link(self, mocker):
        response = mocker.Mock()
        response.text = '{"data": [{"id": 1}], "links": {"next": "https://api.example.com/data?page=2&limit=10"}}'
        response.headers = {'Content-Type': 'application/json'}
        return response

    @pytest.fixture
    def mock_last_response_no_link(self, mocker):
        response = mocker.Mock()
        response.text = '{"data": [{"id": 1}]}'  # No 'next' link
        response.headers = {'Content-Type': 'application/json'}
        return response

    @pytest.fixture
    def mock_paginated_data_with_link(self, mocker, mock_request_builder, mock_last_response_with_link):
        paginated_data = mocker.Mock()
        paginated_data.request_builder = mock_request_builder
        paginated_data.last_response = mock_last_response_with_link
        return paginated_data

    @pytest.fixture
    def mock_paginated_data_no_link(self, mocker, mock_request_builder, mock_last_response_no_link):
        paginated_data = mocker.Mock()
        paginated_data.request_builder = mock_request_builder
        paginated_data.last_response = mock_last_response_no_link
        return paginated_data

    @pytest.fixture
    def mock_paginated_data_initial_call(self, mocker, mock_request_builder):
        paginated_data = mocker.Mock()
        paginated_data.request_builder = mock_request_builder
        paginated_data.last_response = None  # Simulates the first call
        return paginated_data

    # Test __init__
    def test_init_success(self, mock_metadata_wrapper):
        lp = LinkPagination(next_link_pointer="$response.body#/links/next", metadata_wrapper=mock_metadata_wrapper)
        assert lp._next_link_pointer == "$response.body#/links/next"
        assert lp._metadata_wrapper == mock_metadata_wrapper
        assert lp._next_link is None

    def test_init_next_link_pointer_none_raises_error(self, mock_metadata_wrapper):
        with pytest.raises(ValueError, match="Next link pointer for cursor based pagination cannot be None"):
            LinkPagination(next_link_pointer=None, metadata_wrapper=mock_metadata_wrapper)

    def test_init_metadata_wrapper_none_raises_error(self, mock_metadata_wrapper):
        with pytest.raises(ValueError, match="Metadata wrapper for the pagination cannot be None"):
            LinkPagination(next_link_pointer=None, metadata_wrapper=None)

    # Test apply
    def test_apply_initial_call_returns_original_request_builder(
            self, mock_paginated_data_initial_call, mock_metadata_wrapper):
        lp = LinkPagination(next_link_pointer="$response.body#/links/next", metadata_wrapper=mock_metadata_wrapper)
        result = lp.apply(mock_paginated_data_initial_call)
        assert result == mock_paginated_data_initial_call.request_builder
        assert lp._next_link is None

    def test_apply_with_next_link_found(self, mocker, mock_paginated_data_with_link, mock_request_builder):
        # Patch ApiHelper.resolve_response_pointer and ApiHelper.get_query_parameters
        mock_resolve_response_pointer = mocker.patch.object(
            ApiHelper, 'resolve_response_pointer',
            return_value="https://api.example.com/data?page=2&limit=10"
        )
        mock_get_query_parameters = mocker.patch.object(
            ApiHelper, 'get_query_parameters',
            return_value={"page": "2", "limit": "10"}
        )

        lp = LinkPagination(next_link_pointer="$response.body#/links/next", metadata_wrapper=mocker.Mock())
        result_rb = lp.apply(mock_paginated_data_with_link)

        mock_resolve_response_pointer.assert_called_once_with(
            "$response.body#/links/next",
            mock_paginated_data_with_link.last_response.text,
            mock_paginated_data_with_link.last_response.headers
        )
        mock_get_query_parameters.assert_called_once_with("https://api.example.com/data?page=2&limit=10")

        assert lp._next_link == "https://api.example.com/data?page=2&limit=10"
        assert result_rb is not mock_request_builder  # Should be a cloned instance
        assert result_rb.query_params == {"initial_param": "initial_value", "page": "2", "limit": "10"}

    def test_apply_no_next_link_found_in_response(self, mocker, mock_paginated_data_no_link, mock_metadata_wrapper):
        # Patch ApiHelper.resolve_response_pointer to return None
        mock_resolve_response_pointer = mocker.patch.object(ApiHelper, 'resolve_response_pointer', return_value=None)
        # Ensure get_query_parameters is NOT called
        spy_get_query_parameters = mocker.spy(ApiHelper, 'get_query_parameters')

        lp = LinkPagination(next_link_pointer="$response.body#/links/next", metadata_wrapper=mock_metadata_wrapper)
        result = lp.apply(mock_paginated_data_no_link)

        mock_resolve_response_pointer.assert_called_once_with(
            "$response.body#/links/next",
            mock_paginated_data_no_link.last_response.text,
            mock_paginated_data_no_link.last_response.headers
        )
        assert lp._next_link is None
        spy_get_query_parameters.assert_not_called()
        assert result is None

    # Test apply_metadata_wrapper
    def test_apply_metadata_wrapper(self, mock_metadata_wrapper, mocker):
        mock_metadata_wrapper.return_value = "wrapped_response_with_link"

        lp = LinkPagination(
            next_link_pointer="$response.body#/links/next",
            metadata_wrapper=mock_metadata_wrapper
        )
        lp._next_link = "https://api.example.com/data?page=2"  # Set a next link for the test
        mock_paged_response = mocker.Mock()

        result = lp.apply_metadata_wrapper(mock_paged_response)

        mock_metadata_wrapper.assert_called_once_with(mock_paged_response, "https://api.example.com/data?page=2")
        assert result == "wrapped_response_with_link"

    def test_is_applicable_for_none_response(self, mock_metadata_wrapper):
        lp = LinkPagination(
            next_link_pointer="$response.body#/next_cursor",
            metadata_wrapper=mock_metadata_wrapper
        )
        result = lp.is_applicable(None)
        assert result == True