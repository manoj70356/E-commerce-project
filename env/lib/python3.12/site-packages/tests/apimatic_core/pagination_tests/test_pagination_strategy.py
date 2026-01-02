import pytest

from apimatic_core.pagination.pagination_strategy import PaginationStrategy
from apimatic_core.request_builder import RequestBuilder
from apimatic_core.utilities.api_helper import ApiHelper


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

    @property
    def body_params(self):
        return self._body_param

    @property
    def form_params(self):
        return self._form_params

    def __init__(self, template_params=None, header_params=None, query_params=None, body_param=None, form_params=None):
        super().__init__()
        self._template_params = template_params if template_params is not None else {}
        self._query_params = query_params if query_params is not None else {}
        self._header_params = header_params if header_params is not None else {}
        self._body_param = body_param if body_param is not None else None
        self._form_params = form_params if form_params is not None else {}

    def clone_with(
            self, template_params=None, header_params=None, query_params=None, body_param=None,
            form_params=None
    ):
        body_param = body_param if body_param is not None else self.body_params
        # This mock clone_with will create a new instance with updated params
        new_rb = MockRequestBuilder(
            template_params=template_params if template_params is not None else self.template_params.copy(),
            header_params=header_params if header_params is not None else self.header_params.copy(),
            query_params=query_params if query_params is not None else self.query_params.copy(),
            body_param=body_param.copy() if body_param is not None else None,
            form_params=form_params if form_params is not None else self.form_params.copy(),
        )
        return new_rb

class TestPaginationStrategy:
    @pytest.fixture
    def mock_request_builder(self):
        rb = MockRequestBuilder(
            template_params={"id": "user123"},
            query_params={"page": 1, "limit": 10},
            header_params={"X-Api-Key": "abc"},
        )
        return rb

    @pytest.fixture
    def mock_request_builder_with_json_body(self):
        rb = MockRequestBuilder(
            template_params={"id": "user123"},
            query_params={"page": 1, "limit": 10},
            header_params={"X-Api-Key": "abc"},
            body_param={"data": "value"}
        )
        return rb

    @pytest.fixture
    def mock_request_builder_with_form_body(self):
        rb = MockRequestBuilder(
            template_params={"id": "user123"},
            query_params={"page": 1, "limit": 10},
            header_params={"X-Api-Key": "abc"},
            form_params={"data": "value"}
        )
        return rb


    # Test updating path parameters
    def test_update_request_builder_path_param(self, mocker, mock_request_builder):
        input_pointer = "$request.path#/id"
        offset = "user456"

        # Mock ApiHelper.split_into_parts
        mock_split_into_parts = mocker.patch.object(
            ApiHelper, 'split_into_parts', return_value=(PaginationStrategy.PATH_PARAMS_IDENTIFIER, "/id"))
        # Mock ApiHelper.update_entry_by_json_pointer
        mock_update_entry_by_json_pointer = mocker.patch.object(
            ApiHelper, 'update_entry_by_json_pointer',
            side_effect=lambda data, path, value, inplace: {**data, 'id': value})

        updated_rb = PaginationStrategy.get_updated_request_builder(mock_request_builder, input_pointer, offset)

        mock_split_into_parts.assert_called_once_with(input_pointer)
        mock_update_entry_by_json_pointer.assert_called_once_with(
            mock_request_builder.template_params.copy(), "/id/value", offset, inplace=True
        )

        assert updated_rb is not mock_request_builder  # Should return a cloned instance
        assert updated_rb.template_params == {"id": "user456"}
        assert updated_rb.query_params == {"page": 1, "limit": 10}  # Should remain unchanged
        assert updated_rb.header_params == {"X-Api-Key": "abc"}  # Should remain unchanged

    # Test updating query parameters
    def test_update_request_builder_query_param(self, mocker, mock_request_builder):
        input_pointer = "$request.query#/page"
        offset = 5

        mock_split_into_parts = mocker.patch.object(
            ApiHelper, 'split_into_parts', return_value=(PaginationStrategy.QUERY_PARAMS_IDENTIFIER, "/page"))
        mock_update_entry_by_json_pointer = mocker.patch.object(
            ApiHelper, 'update_entry_by_json_pointer',
            side_effect=lambda data, path, value, inplace: {**data, 'page': value})

        updated_rb = PaginationStrategy.get_updated_request_builder(mock_request_builder, input_pointer, offset)

        mock_split_into_parts.assert_called_once_with(input_pointer)
        mock_update_entry_by_json_pointer.assert_called_once_with(
            mock_request_builder.query_params.copy(), "/page", offset, inplace=True
        )

        assert updated_rb is not mock_request_builder
        assert updated_rb.template_params == {"id": "user123"}
        assert updated_rb.query_params == {"page": 5, "limit": 10}
        assert updated_rb.header_params == {"X-Api-Key": "abc"}


    # Test updating header parameters
    def test_update_request_builder_header_param(self, mocker, mock_request_builder):
        input_pointer = "$request.headers#/X-Api-Key"
        offset = "xyz"

        mock_split_into_parts = mocker.patch.object(
            ApiHelper, 'split_into_parts', return_value=(PaginationStrategy.HEADER_PARAMS_IDENTIFIER, "/X-Api-Key"))
        mock_update_entry_by_json_pointer = mocker.patch.object(
            ApiHelper, 'update_entry_by_json_pointer',
            side_effect=lambda data, path, value, inplace: {**data, 'X-Api-Key': value})

        updated_rb = PaginationStrategy.get_updated_request_builder(mock_request_builder, input_pointer, offset)

        mock_split_into_parts.assert_called_once_with(input_pointer)
        mock_update_entry_by_json_pointer.assert_called_once_with(
            mock_request_builder.header_params.copy(), "/X-Api-Key", offset, inplace=True
        )

        assert updated_rb is not mock_request_builder
        assert updated_rb.template_params == {"id": "user123"}
        assert updated_rb.query_params == {"page": 1, "limit": 10}
        assert updated_rb.header_params == {"X-Api-Key": "xyz"}

    def test_update_request_builder_json_body_param(self, mocker, mock_request_builder_with_json_body):
        input_pointer = "$request.body#/data"
        updated_value = "changed_value"

        mock_split_into_parts = mocker.patch.object(
            ApiHelper, 'split_into_parts', return_value=(PaginationStrategy.BODY_PARAM_IDENTIFIER, "/data"))
        mock_update_entry_by_json_pointer = mocker.patch.object(
            ApiHelper, 'update_entry_by_json_pointer',
            side_effect=lambda data, path, value, inplace: {**data, 'data': value})

        updated_rb = PaginationStrategy.get_updated_request_builder(mock_request_builder_with_json_body, input_pointer, updated_value)

        mock_split_into_parts.assert_called_once_with(input_pointer)
        mock_update_entry_by_json_pointer.assert_called_once_with(
            mock_request_builder_with_json_body.body_params.copy(), "/data", updated_value, inplace=True
        )

        assert updated_rb is not mock_request_builder_with_json_body
        assert updated_rb.template_params == {"id": "user123"}
        assert updated_rb.query_params == {"page": 1, "limit": 10}
        assert updated_rb.header_params == {"X-Api-Key": "abc"}
        assert updated_rb.body_params == {"data": "changed_value"}

    def test_update_request_builder_form_body_param(self, mocker, mock_request_builder_with_form_body):
        input_pointer = "$request.body#/data"
        updated_value = "changed_value"

        mock_split_into_parts = mocker.patch.object(
            ApiHelper, 'split_into_parts', return_value=(PaginationStrategy.BODY_PARAM_IDENTIFIER, "/data"))
        mock_update_entry_by_json_pointer = mocker.patch.object(
            ApiHelper, 'update_entry_by_json_pointer',
            side_effect=lambda data, path, value, inplace: {**data, 'data': value})

        updated_rb = PaginationStrategy.get_updated_request_builder(
            mock_request_builder_with_form_body, input_pointer, updated_value)

        mock_split_into_parts.assert_called_once_with(input_pointer)
        mock_update_entry_by_json_pointer.assert_called_once_with(
            mock_request_builder_with_form_body.form_params.copy(), "/data", updated_value, inplace=True
        )

        assert updated_rb is not mock_request_builder_with_form_body
        assert updated_rb.template_params == {"id": "user123"}
        assert updated_rb.query_params == {"page": 1, "limit": 10}
        assert updated_rb.header_params == {"X-Api-Key": "abc"}
        assert updated_rb.form_params == {"data": "changed_value"}


    # Test with an invalid input pointer prefix
    def test_update_request_builder_invalid_prefix(self, mocker, mock_request_builder):
        input_pointer = "invalid.prefix#/some_field"
        offset = "new_value"

        mock_split_into_parts = mocker.patch.object(ApiHelper, 'split_into_parts', return_value=("invalid.prefix", "/some_field"))
        # Ensure update_entry_by_json_pointer is NOT called
        spy_update_entry_by_json_pointer = mocker.spy(ApiHelper, 'update_entry_by_json_pointer')

        updated_rb = PaginationStrategy.get_updated_request_builder(mock_request_builder, input_pointer, offset)

        mock_split_into_parts.assert_called_once_with(input_pointer)
        spy_update_entry_by_json_pointer.assert_not_called()

        assert updated_rb is not mock_request_builder  # Still returns a cloned instance
        # Original parameters should be passed to clone_with, effectively returning an unchanged copy
        assert updated_rb.template_params == mock_request_builder.template_params
        assert updated_rb.query_params == mock_request_builder.query_params
        assert updated_rb.header_params == mock_request_builder.header_params
        assert updated_rb.body_params == mock_request_builder.body_params
        assert updated_rb.form_params == mock_request_builder.form_params


    # Test when the original parameter dict is empty
    def test_update_request_builder_empty_params(self, mocker):
        mock_rb_empty = mocker.Mock(spec=RequestBuilder)
        mock_rb_empty.template_params = {}
        mock_rb_empty.query_params = {}
        mock_rb_empty.header_params = {}
        mock_rb_empty.body_params = {}
        mock_rb_empty.form_params = {}
        # Make mock_rb_empty's clone_with method behave like our custom mock
        mock_rb_empty.clone_with.side_effect = \
            lambda template_params=None, query_params=None, header_params=None, body_param=None, form_params=None:\
                MockRequestBuilder(
                    template_params=template_params if template_params is not None else {},
                    query_params=query_params if query_params is not None else {},
                    header_params=header_params if header_params is not None else {},
                    body_param=body_param if body_param is not None else None,
                    form_params=form_params if form_params is not None else {}
                )

        input_pointer = "$request.query#/offset"
        offset = 0

        mock_split_into_parts = mocker.patch.object(
            ApiHelper, 'split_into_parts', return_value=(PaginationStrategy.QUERY_PARAMS_IDENTIFIER, "/offset"))
        mock_update_entry_by_json_pointer = mocker.patch.object(ApiHelper, 'update_entry_by_json_pointer',
                            side_effect=lambda data, path, value, inplace: {**data, 'offset': value})

        updated_rb = PaginationStrategy.get_updated_request_builder(mock_rb_empty, input_pointer, offset)

        mock_split_into_parts.assert_called_once_with(input_pointer)
        mock_update_entry_by_json_pointer.assert_called_once_with(
            {}, "/offset", offset, inplace=True  # Should be an empty dict passed initially
        )

        assert updated_rb.query_params == {"offset": 0}
        assert updated_rb.template_params == {}
        assert updated_rb.header_params == {}
        assert updated_rb.body_params == {}
        assert updated_rb.form_params == {}