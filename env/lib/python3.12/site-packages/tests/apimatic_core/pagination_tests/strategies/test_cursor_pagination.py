import pytest

from apimatic_core.pagination.pagination_strategy import PaginationStrategy
from apimatic_core.utilities.api_helper import ApiHelper
from apimatic_core.request_builder import RequestBuilder
from apimatic_core.pagination.strategies.cursor_pagination import CursorPagination


class TestCursorPagination:

    @pytest.fixture
    def mock_metadata_wrapper(self, mocker):
        return mocker.Mock(name="metadata_wrapper_mock")

    @pytest.fixture
    def mock_request_builder(self, mocker):
        rb = mocker.Mock(spec=RequestBuilder)
        rb.template_params = {
            "cursor": { "value": "initial_path_cursor", "encode": True}
        }
        rb.query_params = {"cursor": "initial_query_cursor"}
        rb.header_params = {"cursor": "initial_header_cursor"}
        return rb

    @pytest.fixture
    def mock_request_builder_with_body_param(self, mocker):
        rb = mocker.Mock(spec=RequestBuilder)
        rb.template_params = {
            "cursor": {"value": "initial_path_cursor", "encode": True}
        }
        rb.query_params = {"cursor": "initial_query_cursor"}
        rb.header_params = {"cursor": "initial_header_cursor"}
        rb.body_params = {"cursor": "initial_body_cursor"}
        rb.form_params = {"cursor": "initial_form_cursor"}
        return rb

    @pytest.fixture
    def mock_request_builder_with_form_params(self, mocker):
        rb = mocker.Mock(spec=RequestBuilder)
        rb.template_params = {
            "cursor": {"value": "initial_path_cursor", "encode": True}
        }
        rb.query_params = {"cursor": "initial_query_cursor"}
        rb.header_params = {"cursor": "initial_header_cursor"}
        rb.form_params = {"cursor": "initial_form_cursor"}
        return rb

    @pytest.fixture
    def mock_last_response(self, mocker):
        response = mocker.Mock()
        response.text = '{"data": [{"id": 1}], "next_cursor": "next_page_cursor"}'
        response.headers = {'Content-Type': 'application/json'}
        return response

    @pytest.fixture
    def mock_paginated_data(self, mocker, mock_request_builder, mock_last_response):
        paginated_data = mocker.Mock()
        paginated_data.request_builder = mock_request_builder
        paginated_data.last_response = mock_last_response
        return paginated_data

    # Test __init__
    def test_init_success(self, mock_metadata_wrapper):
        cp = CursorPagination(output="$response.body#/next_cursor", input_="$request.query#/cursor", metadata_wrapper=mock_metadata_wrapper)
        assert cp._output == "$response.body#/next_cursor"
        assert cp._input == "$request.query#/cursor"
        assert cp._metadata_wrapper == mock_metadata_wrapper
        assert cp._cursor_value is None

    def test_init_input_none_raises_error(self, mock_metadata_wrapper):
        with pytest.raises(ValueError, match="Input pointer for cursor based pagination cannot be None"):
            CursorPagination(output="$response.body#/next_cursor", input_=None, metadata_wrapper=mock_metadata_wrapper)

    def test_init_metadata_wrapper_none_raises_error(self, mock_metadata_wrapper):
        with pytest.raises(ValueError, match="Metadata wrapper for the pagination cannot be None"):
            CursorPagination(output=None, input_=None, metadata_wrapper=None)

    def test_init_output_none_raises_error(self, mock_metadata_wrapper):
        with pytest.raises(ValueError, match="Output pointer for cursor based pagination cannot be None"):
            CursorPagination(output=None, input_="$request.query#/cursor", metadata_wrapper=mock_metadata_wrapper)

    # Test apply
    def test_apply_initial_call(self, mocker, mock_request_builder, mock_metadata_wrapper):
        paginated_data = mocker.Mock()
        paginated_data.last_response = None
        paginated_data.request_builder = mock_request_builder

        # Mock _get_initial_cursor_value
        mock_get_initial_cursor_value = mocker.patch.object(
            CursorPagination,
            '_get_initial_cursor_value',
            return_value='initial_cursor'
        )

        cp = CursorPagination(
            input_="$request.query#/cursor",
            output="$response.body#/next_cursor",
            metadata_wrapper=mock_metadata_wrapper
        )

        result = cp.apply(paginated_data)

        mock_get_initial_cursor_value.assert_called_once_with(mock_request_builder, "$request.query#/cursor")
        assert cp._cursor_value == "initial_cursor"
        assert result == mock_request_builder

    def test_apply_subsequent_call_with_cursor(self, mocker, mock_paginated_data,
                                               mock_request_builder, mock_last_response, mock_metadata_wrapper):
        # Patch ApiHelper.resolve_response_pointer
        mock_resolve_response_pointer = mocker.patch.object(ApiHelper, 'resolve_response_pointer',
                                                            return_value="next_page_cursor_from_response")

        mock_get_updated_request_builder = mocker.patch.object(CursorPagination, 'get_updated_request_builder',
                                                               return_value=mock_request_builder)

        cp = CursorPagination(
            input_="$request.query#/cursor",
            output="$response.body#/next_cursor",
            metadata_wrapper=mock_metadata_wrapper
        )

        result = cp.apply(mock_paginated_data)

        mock_resolve_response_pointer.assert_called_once_with(
            "$response.body#/next_cursor",
            mock_last_response.text,
            mock_last_response.headers
        )

        mock_get_updated_request_builder.assert_called_once_with(
            mock_request_builder, "$request.query#/cursor", "next_page_cursor_from_response"
        )

        assert cp._cursor_value == "next_page_cursor_from_response"
        assert result == mock_request_builder

    def test_apply_subsequent_call_no_cursor_found(self, mocker, mock_paginated_data, mock_metadata_wrapper):
        # Patch ApiHelper.resolve_response_pointer to return None
        mock_resolve_response_pointer = mocker.patch.object(ApiHelper, 'resolve_response_pointer', return_value=None)
        # Ensure get_updated_request_builder is NOT called
        spy_get_updated_request_builder = mocker.spy(PaginationStrategy, 'get_updated_request_builder')

        cp = CursorPagination(
            input_="$request.query#/cursor",
            output="$response.body#/next_cursor",
            metadata_wrapper=mock_metadata_wrapper
        )

        result = cp.apply(mock_paginated_data)

        mock_resolve_response_pointer.assert_called_once_with(
            "$response.body#/next_cursor",
            mock_paginated_data.last_response.text,
            mock_paginated_data.last_response.headers
        )
        assert cp._cursor_value is None
        spy_get_updated_request_builder.assert_not_called()
        assert result is None

    # Test apply_metadata_wrapper
    def test_apply_metadata_wrapper(self, mock_metadata_wrapper, mocker):
        mock_metadata_wrapper.return_value = "wrapped_response"

        cp = CursorPagination(
            input_="$request.query#/cursor",
            output="$response.body#/next_cursor",
            metadata_wrapper=mock_metadata_wrapper
        )
        cp._cursor_value = "some_cursor_value"  # Set a cursor value for the test
        mock_paged_response = mocker.Mock()

        result = cp.apply_metadata_wrapper(mock_paged_response)

        mock_metadata_wrapper.assert_called_once_with(mock_paged_response, "some_cursor_value")
        assert result == "wrapped_response"


    def test_is_applicable_for_none_response(self, mock_metadata_wrapper):
        cp = CursorPagination(
            input_="$request.query#/cursor",
            output="$response.body#/next_cursor",
            metadata_wrapper=mock_metadata_wrapper
        )
        result = cp.is_applicable(None)
        assert result == True

    # Test _get_initial_cursor_value
    def test_get_initial_cursor_value_path(self, mocker, mock_request_builder):
        mock_split_into_parts = mocker.patch.object(
            ApiHelper, 'split_into_parts', return_value=(PaginationStrategy.PATH_PARAMS_IDENTIFIER, "/path_cursor"))
        mock_get_value_by_json_pointer = mocker.patch.object(
            ApiHelper, 'get_value_by_json_pointer', return_value="initial_path_cursor")

        result = CursorPagination._get_initial_cursor_value(
            mock_request_builder, "$request.path#/cursor")
        mock_split_into_parts.assert_called_once_with("$request.path#/cursor")
        mock_get_value_by_json_pointer.assert_called_once_with(
            mock_request_builder.template_params, "/path_cursor/value")
        assert result == "initial_path_cursor"

    def test_get_initial_cursor_value_query(self, mocker, mock_request_builder):
        mock_split_into_parts = mocker.patch.object(ApiHelper, 'split_into_parts', return_value=(PaginationStrategy.QUERY_PARAMS_IDENTIFIER, "/cursor"))
        mock_get_value_by_json_pointer = mocker.patch.object(ApiHelper, 'get_value_by_json_pointer', return_value="initial_query_cursor")

        result = CursorPagination._get_initial_cursor_value(mock_request_builder, "$request.query#/cursor")
        mock_split_into_parts.assert_called_once_with("$request.query#/cursor")
        mock_get_value_by_json_pointer.assert_called_once_with(mock_request_builder.query_params, "/cursor")
        assert result == "initial_query_cursor"

    def test_get_initial_cursor_value_json_body(self, mocker, mock_request_builder_with_body_param):
        mock_split_into_parts = mocker.patch.object(
            ApiHelper, 'split_into_parts', return_value=(PaginationStrategy.BODY_PARAM_IDENTIFIER, "/cursor"))
        mock_get_value_by_json_pointer = mocker.patch.object(
            ApiHelper, 'get_value_by_json_pointer', return_value="initial_body_cursor")

        result = CursorPagination._get_initial_cursor_value(
            mock_request_builder_with_body_param, "$request.body#/cursor")
        mock_split_into_parts.assert_called_once_with("$request.body#/cursor")
        mock_get_value_by_json_pointer.assert_called_once_with(
            mock_request_builder_with_body_param.body_params, "/cursor")
        assert result == "initial_body_cursor"

    def test_get_initial_cursor_value_form_body(self, mocker, mock_request_builder_with_form_params):
        mock_request_builder_with_form_params.body_params = None
        mock_split_into_parts = mocker.patch.object(
            ApiHelper, 'split_into_parts', return_value=(PaginationStrategy.BODY_PARAM_IDENTIFIER, "/cursor"))
        mock_get_value_by_json_pointer = mocker.patch.object(
            ApiHelper, 'get_value_by_json_pointer', return_value="initial_form_cursor")

        result = CursorPagination._get_initial_cursor_value(
            mock_request_builder_with_form_params, "$request.body#/cursor")
        mock_split_into_parts.assert_called_once_with("$request.body#/cursor")
        mock_get_value_by_json_pointer.assert_called_once_with(
            mock_request_builder_with_form_params.form_params, "/cursor")
        assert result == "initial_form_cursor"

    def test_get_initial_cursor_value_headers(self, mocker, mock_request_builder):
        mock_split_into_parts = mocker.patch.object(ApiHelper, 'split_into_parts', return_value=(PaginationStrategy.HEADER_PARAMS_IDENTIFIER, "/cursor"))
        mock_get_value_by_json_pointer = mocker.patch.object(ApiHelper, 'get_value_by_json_pointer', return_value="initial_header_cursor")

        result = CursorPagination._get_initial_cursor_value(mock_request_builder, "$request.headers#/cursor")
        mock_split_into_parts.assert_called_once_with("$request.headers#/cursor")
        mock_get_value_by_json_pointer.assert_called_once_with(mock_request_builder.header_params, "/cursor")
        assert result == "initial_header_cursor"

    def test_get_initial_cursor_value_invalid_prefix(self, mocker, mock_request_builder):
        mock_split_into_parts = mocker.patch.object(ApiHelper, 'split_into_parts', return_value=("invalid_prefix", "some_field"))
        # Ensure get_value_by_json_pointer is not called for invalid prefixes
        mock_get_value_by_json_pointer = mocker.patch.object(ApiHelper, 'get_value_by_json_pointer')

        result = CursorPagination._get_initial_cursor_value(mock_request_builder, "invalid_prefix.some_field")
        mock_split_into_parts.assert_called_once_with("invalid_prefix.some_field")
        mock_get_value_by_json_pointer.assert_not_called()
        assert result is None
