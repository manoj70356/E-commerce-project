import pytest

from apimatic_core.configurations.global_configuration import GlobalConfiguration
from apimatic_core.http.configurations.http_client_configuration import HttpClientConfiguration
from apimatic_core.pagination.paginated_data import PaginatedData
from apimatic_core.pagination.pagination_strategy import PaginationStrategy
from apimatic_core.request_builder import RequestBuilder


class TestPaginatedData:

    @pytest.fixture
    def mock_api_call(self, mocker):
        mock_api_call_instance = mocker.Mock()
        mock_api_call_instance.get_pagination_strategies = []
        mock_api_call_instance.request_builder = mocker.Mock(spec=RequestBuilder)
        mock_api_call_instance.request_builder.query_params = {"initial": "value"}  # Example

        # Mock GlobalConfiguration and HttpClientConfiguration for deepcopy
        mock_http_client_config = mocker.Mock(spec=HttpClientConfiguration)
        mock_http_client_config.http_callback = None  # Default
        mock_http_client_config.clone.return_value = mock_http_client_config  # Return self on clone

        mock_global_config = mocker.Mock(spec=GlobalConfiguration)
        mock_global_config.get_http_client_configuration.return_value = mock_http_client_config
        mock_global_config.clone_with.return_value = mock_global_config  # Return self on clone

        mock_api_call_instance.global_configuration = mock_global_config

        # Mock the clone method of ApiCall
        mock_api_call_instance.clone.return_value = mock_api_call_instance
        return mock_api_call_instance

    @pytest.fixture
    def mock_paginated_items_converter(self, mocker):
        # A simple converter that returns a list of items from a mock body
        def converter(body):
            if body and 'items' in body:
                return body['items']
            return []

        return mocker.Mock(side_effect=converter)

    @pytest.fixture
    def mock_paginated_data_instance(self, mock_api_call, mock_paginated_items_converter):
        # We need to create a real instance for public method tests
        # We will mock internal dependencies within the tests as needed.
        return PaginatedData(mock_api_call, mock_paginated_items_converter)

    @pytest.fixture
    def mock_pagination_strategy(self, mocker):
        strategy = mocker.Mock(spec=PaginationStrategy)
        # Default behavior: apply returns a request builder, apply_metadata_wrapper returns the response
        strategy.apply.return_value = mocker.Mock(spec=RequestBuilder)
        strategy.apply_metadata_wrapper.side_effect = lambda response: response
        return strategy

    @pytest.fixture
    def mock_http_response(self, mocker):
        response = mocker.Mock()
        response.body = {"items": [{"id": 1, "name": "Item 1"}]}
        return response

    @pytest.fixture
    def mock_http_response_empty_items(self, mocker):
        response = mocker.Mock()
        response.body = {"items": []}
        return response

    def test_init_paginated_items_converter_none_raises_error(self, mock_api_call):
        with pytest.raises(ValueError, match="paginated_items_converter cannot be None"):
            PaginatedData(api_call=mock_api_call, paginated_items_converter=None)

    # Test __next__
    def test_next_iterates_current_items(self, mock_paginated_data_instance):
        mock_paginated_data_instance._items = ["item1", "item2"]
        mock_paginated_data_instance._page_size = 2
        mock_paginated_data_instance._current_index = 0

        assert next(mock_paginated_data_instance) == "item1"
        assert mock_paginated_data_instance._current_index == 1
        assert next(mock_paginated_data_instance) == "item2"
        assert mock_paginated_data_instance._current_index == 2

    def test_next_fetches_next_page_when_current_exhausted(self, mocker, mock_paginated_data_instance,
                                                           mock_http_response):
        mock_paginated_data_instance._items = ["old_item"]
        mock_paginated_data_instance._page_size = 1
        mock_paginated_data_instance._current_index = 1  # Simulate exhausted

        # Mock _fetch_next_page (private method)
        mock_fetch_next_page = mocker.patch.object(PaginatedData, '_fetch_next_page', return_value=mock_http_response)

        # First call to next should trigger fetch_next_page
        first_new_item = next(mock_paginated_data_instance)

        mock_fetch_next_page.assert_called_once()
        mock_paginated_data_instance._paginated_items_converter.assert_called_once_with(mock_http_response.body)
        assert first_new_item == {"id": 1, "name": "Item 1"}
        assert mock_paginated_data_instance._page_size == 1
        assert mock_paginated_data_instance._current_index == 1
        assert mock_paginated_data_instance._items == [{"id": 1, "name": "Item 1"}]

    def test_next_raises_stopiteration_when_no_more_items(self, mocker, mock_paginated_data_instance,
                                                          mock_http_response_empty_items):
        mock_paginated_data_instance._items = []
        mock_paginated_data_instance._page_size = 0
        mock_paginated_data_instance._current_index = 0

        # Mock _fetch_next_page (private method) to return a response with empty items
        mocker.patch.object(PaginatedData, '_fetch_next_page', return_value=mock_http_response_empty_items)

        with pytest.raises(StopIteration):
            next(mock_paginated_data_instance)

        # Also check when _fetch_next_page returns an empty list (simulating no more strategies)
        mocker.patch.object(PaginatedData, '_fetch_next_page',
                            return_value=[])  # _fetch_next_page returns [] if no strategy applies
        mock_paginated_data_instance._items = []
        mock_paginated_data_instance._page_size = 0
        mock_paginated_data_instance._current_index = 0
        with pytest.raises(StopIteration):
            next(mock_paginated_data_instance)

    # Test pages
    def test_pages_yields_paginated_responses(self, mocker, mock_paginated_data_instance, mock_pagination_strategy,
                                              mock_http_response, mock_http_response_empty_items):
        # Mock _get_new_self_instance (private method)
        # Create a new mock instance for the independent iterator used by pages()
        pages_internal_paginated_data = mocker.Mock(spec=PaginatedData)
        mocker.patch.object(PaginatedData, 'clone', return_value=pages_internal_paginated_data)

        # Configure the *internal* mock instance's _fetch_next_page
        pages_internal_paginated_data._fetch_next_page = mocker.Mock(
            side_effect=[
                mock_http_response,  # First page
                mocker.Mock(body={"items": [{"id": 2, "name": "Item 2"}]}),  # Second page
                mock_http_response_empty_items  # Signal end of pages
            ]
        )
        # Configure the *internal* mock instance's paginated_items_converter
        pages_internal_paginated_data._paginated_items_converter = mocker.Mock(
            side_effect=[
                mock_http_response.body['items'],
                [{"id": 2, "name": "Item 2"}],
                []  # For the empty response
            ]
        )
        # Ensure _page_size is updated by the private method
        pages_internal_paginated_data._page_size = 0  # Initial state for internal
        pages_internal_paginated_data.last_response = None  # Initial state for internal

        pages_generator = mock_paginated_data_instance.pages()

        # First page
        page1 = next(pages_generator)
        assert page1.body['items'] == [{"id": 1, "name": "Item 1"}]

        # Second page
        page2 = next(pages_generator)
        assert page2.body['items'] == [{"id": 2, "name": "Item 2"}]

        # Attempt to get third page should raise StopIteration
        with pytest.raises(StopIteration):
            next(pages_generator)

        assert pages_internal_paginated_data._fetch_next_page.call_count == 3

    def test_pages_returns_empty_generator_if_no_initial_items(self, mocker, mock_paginated_data_instance,
                                                               mock_http_response_empty_items):
        # Mock _get_new_self_instance (private method)
        pages_internal_paginated_data = mocker.Mock(spec=PaginatedData)
        mocker.patch.object(PaginatedData, 'clone', return_value=pages_internal_paginated_data)

        # Configure the *internal* mock instance's _fetch_next_page to return an empty items response immediately
        pages_internal_paginated_data._fetch_next_page = mocker.Mock(return_value=mock_http_response_empty_items)
        pages_internal_paginated_data._paginated_items_converter = mocker.Mock(return_value=[])
        pages_internal_paginated_data._page_size = 0
        pages_internal_paginated_data.last_response = None

        pages_generator = mock_paginated_data_instance.pages()
        with pytest.raises(StopIteration):
            next(pages_generator)

    def test_fetch_next_page_with_locked_strategy(self, mock_api_call, mocker):
        paginated_data = PaginatedData(mock_api_call, paginated_items_converter=mocker.Mock())
        strategy = mocker.Mock()
        strategy.apply.return_value = mocker.Mock()
        strategy.apply_metadata_wrapper.return_value = mocker.Mock()

        paginated_data._locked_strategy = strategy

        result = paginated_data._fetch_next_page()

        strategy.apply.assert_called_once()
        strategy.apply_metadata_wrapper.assert_called_once()
        assert result == strategy.apply_metadata_wrapper.return_value

    def test_fetch_next_page_first_strategy_successful(self, mock_api_call, mocker):
        paginated_data = PaginatedData(mock_api_call, paginated_items_converter=mocker.Mock())

        strategy = mocker.Mock()
        strategy.apply.return_value = mocker.Mock()
        strategy.apply_metadata_wrapper.return_value = mocker.Mock()
        strategy.is_applicable.return_value = True

        paginated_data._pagination_strategies = [strategy]

        mocker.patch.object(paginated_data, "_get_locked_strategy", return_value=strategy)

        result = paginated_data._fetch_next_page()

        strategy.apply.assert_called_once()
        strategy.apply_metadata_wrapper.assert_called_once()
        assert result == strategy.apply_metadata_wrapper.return_value
        assert paginated_data._locked_strategy == strategy

    def test_fetch_next_page_all_strategies_none(self, mock_api_call, mocker):
        paginated_data = PaginatedData(mock_api_call, paginated_items_converter=mocker.Mock())

        strategy1 = mocker.Mock()
        strategy1.apply.return_value = None

        strategy2 = mocker.Mock()
        strategy2.apply.return_value = None

        paginated_data._pagination_strategies = [strategy1, strategy2]

        result = paginated_data._fetch_next_page()

        strategy1.apply.assert_called_once()
        strategy2.apply.assert_called_once()
        assert result is None
        assert paginated_data._locked_strategy is None