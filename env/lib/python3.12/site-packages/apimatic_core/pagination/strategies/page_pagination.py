from apimatic_core.pagination.pagination_strategy import PaginationStrategy
from apimatic_core.utilities.api_helper import ApiHelper

class PagePagination(PaginationStrategy):
    """
    Implements a page-based pagination strategy for API requests.

    This class manages pagination by updating the request builder with the appropriate page number,
    using a JSON pointer to identify the pagination parameter. It also applies a metadata wrapper
    to each paged response, including the current page number.
    """

    def __init__(self, input_, metadata_wrapper):
        """
        Initializes a PagePagination instance with the given input pointer and metadata wrapper.

        Args:
            input_: The JSON pointer indicating the pagination parameter in the request.
            metadata_wrapper: A callable for wrapping pagination metadata.

        Raises:
            ValueError: If input_ is None.
        """
        super().__init__(metadata_wrapper)

        if input_ is None:
            raise ValueError("Input pointer for page based pagination cannot be None")

        self._input = input_
        self._page_number = 1

    def is_applicable(self, response):
        """
        Checks whether the offset pagination strategy is a valid candidate based on the given HTTP response.

        Args:
            response: The response from the previous API call.

        Returns:
            bool: True if this strategy is valid based on the given HTTP response..
        """
        return True

    def apply(self, paginated_data):
        """
        Updates the request builder to fetch the next page of results based on the current paginated data.

        Args:
            paginated_data: An object containing the last response, request builder, and page size.

        Returns:
            The updated request builder configured for the next page request.
        """
        last_response = paginated_data.last_response
        request_builder = paginated_data.request_builder
        self._page_number = self._get_initial_request_param_value(request_builder, self._input, 1)

        # The last response is none which means this is going to be the 1st page
        if last_response is None:
            return request_builder

        self._page_number += 1 if paginated_data.page_size > 0 else 0

        return self.get_updated_request_builder(request_builder, self._input, self._page_number)

    def apply_metadata_wrapper(self, paged_response):
        """
        Applies the metadata wrapper to the paged response, including the current page number.

        Args:
            paged_response: The response object for the current page.

        Returns:
            The result of the metadata wrapper with the paged response and current page number.
        """
        return self._metadata_wrapper(paged_response, self._page_number)
