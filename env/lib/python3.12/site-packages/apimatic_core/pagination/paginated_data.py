from apimatic_core.http.http_call_context import HttpCallContext
from collections.abc import Iterator
import copy

class PaginatedData(Iterator):
    """
    Iterator class for handling paginated API responses.

    Provides methods to iterate over items and pages, fetch next pages using defined pagination strategies,
    and access the latest HTTP response and request builder. Supports independent iterators for concurrent traversals.
    """

    @property
    def last_response(self):
        """
        Returns the most recent HTTP response received during pagination.
        """
        return self._http_call_context.response if self._last_request_builder is not None else None

    @property
    def request_builder(self):
        """
        Returns the appropriate request builder for the current pagination state.
        """
        return self._initial_request_builder if self._last_request_builder is None else self._last_request_builder


    @property
    def page_size(self):
        """
        Returns the number of items in the current page of paginated results.
        """
        return self._page_size

    def __init__(self, api_call, paginated_items_converter):
        """
        Initializes a PaginatedData instance with the given API call and item converter.

        Deep copies the API call, sets up pagination strategies, HTTP call context, and global configuration.
        Raises:
            ValueError: If paginated_items_converter is None.

        Args:
            api_call: The API call object to paginate.
            paginated_items_converter: Function to convert paginated response bodies into items.
        """
        if paginated_items_converter is None:
            raise ValueError('paginated_items_converter cannot be None')

        self._api_call = api_call
        self._paginated_items_converter = paginated_items_converter
        self._initial_request_builder = api_call.request_builder
        self._last_request_builder = None
        self._locked_strategy = None
        self._pagination_strategies = self._api_call.get_pagination_strategies
        self._http_call_context =\
            self._api_call.global_configuration.get_http_client_configuration().http_callback or HttpCallContext()
        _http_client_configuration = self._api_call.global_configuration.get_http_client_configuration().clone(
            http_callback=self._http_call_context)
        self._global_configuration = self._api_call.global_configuration.clone_with(
            http_client_configuration=_http_client_configuration)
        self._paged_response = None
        self._items = []
        self._page_size = 0
        self._current_index = 0

    def __iter__(self):
        """
        Returns a new independent iterator instance for paginated data traversal.
        """
        return self.clone()

    def __next__(self):
        """
        Returns the next item in the paginated data sequence.

        Fetches the next page if the current page is exhausted. Raises StopIteration when no more items are available.
        """
        if self._current_index < self.page_size:
            item = self._items[self._current_index]
            self._current_index += 1
            return item

        self._paged_response = self._fetch_next_page()
        self._items = self._paginated_items_converter(
            self._paged_response.body) if self._paged_response else []
        if not self._items:
            raise StopIteration
        self._page_size, self._current_index = len(self._items), 0
        item = self._items[self._current_index]
        self._current_index += 1
        return item

    def pages(self):
        """
        Yields each page of the paginated response as an independent generator.

        Returns:
            Generator yielding HTTP response objects for each page.
        """
        # Create a new instance so the page iteration is independent
        paginated_data = self.clone()

        while True:
            paginated_data._paged_response = paginated_data._fetch_next_page()
            paginated_data._items = self._paginated_items_converter(
                paginated_data._paged_response.body) if paginated_data._paged_response else []
            if not paginated_data._items:
                break
            paginated_data._page_size = len(paginated_data._items)
            yield paginated_data._paged_response

    def _fetch_next_page(self):
        """
        Fetches the next page of paginated data using available pagination strategies.

        Attempts each strategy to build the next request, executes the API call,
         and applies any response metadata wrappers.
        Returns an empty list if no further pages are available.

        Returns:
            The processed response object for the next page, or None if no pagination strategy is applicable.

        Raises:
            Exception: Propagates any exceptions encountered during the API call execution.
        """

        if self._locked_strategy is not None:
            return self._execute_strategy(self._locked_strategy)

        for pagination_strategy in self._pagination_strategies:
            response = self._execute_strategy(pagination_strategy)
            if response is None:
                continue

            if self._locked_strategy is None:
                self._locked_strategy = self._get_locked_strategy()

            return response

        return None

    def _execute_strategy(self, pagination_strategy):
        request_builder = pagination_strategy.apply(self)
        if request_builder is None:
            return None

        self._last_request_builder = request_builder

        response = self._api_call.clone(
            global_configuration=self._global_configuration, request_builder=request_builder
        ).execute()
        return pagination_strategy.apply_metadata_wrapper(response)

    def _get_locked_strategy(self):
        for pagination_strategy in self._pagination_strategies:
            if pagination_strategy.is_applicable(self.last_response):
                return pagination_strategy

    def clone(self):
        """
        Creates and returns a new independent PaginatedData instance
        with a cloned API call that resets to the initial request builder.
        """
        cloned_api_call = self._api_call.clone(request_builder=self._initial_request_builder)
        return PaginatedData(cloned_api_call, self._paginated_items_converter)
