from apimatic_core.pagination.pagination_strategy import PaginationStrategy
from apimatic_core.types.parameter import Parameter
from apimatic_core.utilities.api_helper import ApiHelper


class LinkPagination(PaginationStrategy):
    """
    Implements a pagination strategy that extracts the next page link from API responses using a JSON pointer.

    This class updates the request builder with query parameters from the next page link and applies a metadata
     wrapper to the paged response.
    """

    def __init__(self, next_link_pointer, metadata_wrapper):
        """
        Initializes a LinkPagination instance with the given next link pointer and metadata wrapper.

        Args:
            next_link_pointer: JSON pointer to extract the next page link from the API response.
            metadata_wrapper: Callable to wrap the paged response metadata.

        Raises:
            ValueError: If next_link_pointer is None.
        """
        super().__init__(metadata_wrapper)

        if next_link_pointer is None:
            raise ValueError("Next link pointer for cursor based pagination cannot be None")

        self._next_link_pointer = next_link_pointer
        self._next_link = None

    def is_applicable(self, response):
        """
        Checks whether the link pagination strategy is a valid candidate based on the given HTTP response.

        Args:
            response: The response from the previous API call.

        Returns:
            bool: True if this strategy is valid based on the given HTTP response..
        """
        if response is None:
            return True

        self._next_link = ApiHelper.resolve_response_pointer(
            self._next_link_pointer,
            response.text,
            response.headers
        )

        return self._next_link is not None

    def apply(self, paginated_data):
        """
        Updates the request builder with query parameters from the next page
         link extracted from the last API response.

        Args:
            paginated_data: An object containing the last API response and the current request builder.

        Returns:
            A new request builder instance with updated query parameters for the next page,
             or None if no next link is found.
        """
        last_response = paginated_data.last_response
        request_builder = paginated_data.request_builder

        # The last response is none which means this is going to be the 1st page
        if last_response is None:
            return request_builder

        self._next_link = ApiHelper.resolve_response_pointer(
            self._next_link_pointer,
            last_response.text,
            last_response.headers
        )

        if self._next_link is None:
            return None

        query_params = ApiHelper.get_query_parameters(self._next_link)
        updated_query_params = request_builder.query_params.copy()
        updated_query_params.update(query_params)

        return request_builder.clone_with(query_params=updated_query_params)

    def apply_metadata_wrapper(self, paged_response):
        """
        Applies the metadata wrapper to the paged response, including the next page link.

        Args:
            paged_response: The API response object for the current page.

        Returns:
            The result of the metadata wrapper, typically containing the response and next link information.
        """
        return self._metadata_wrapper(paged_response, self._next_link)
