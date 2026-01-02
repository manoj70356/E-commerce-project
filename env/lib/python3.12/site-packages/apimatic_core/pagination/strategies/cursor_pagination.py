from apimatic_core.pagination.pagination_strategy import PaginationStrategy
from apimatic_core.utilities.api_helper import ApiHelper


class CursorPagination(PaginationStrategy):
    """
    Implements a cursor-based pagination strategy for API responses.

    This class manages the extraction and injection of cursor values between API requests and responses,
    enabling seamless traversal of paginated data. It validates required pointers, updates the request builder
    with the appropriate cursor, and applies a metadata wrapper to paged responses.
    """

    def __init__(self, output, input_, metadata_wrapper):
        """
        Initializes a CursorPagination instance with the specified output and input pointers and a metadata wrapper.

        Validates that both input and output pointers are provided,
         and sets up internal state for cursor-based pagination.

        Args:
            output: JSON pointer to extract the cursor from the API response.
            input_: JSON pointer indicating where to set the cursor in the request.
            metadata_wrapper: Function to wrap paged responses with additional metadata.

        Raises:
            ValueError: If either input_ or output is None.
        """
        super().__init__(metadata_wrapper)

        if input_ is None:
            raise ValueError("Input pointer for cursor based pagination cannot be None")
        if output is None:
            raise ValueError("Output pointer for cursor based pagination cannot be None")

        self._output = output
        self._input = input_
        self._cursor_value = None

    def is_applicable(self, response):
        """
        Checks whether the cursor pagination strategy is a valid candidate based on the given HTTP response.

        Args:
            response: The response from the previous API call.

        Returns:
            bool: True if this strategy is valid based on the given HTTP response..
        """
        if response is None:
            return True

        self._cursor_value = ApiHelper.resolve_response_pointer(
            self._output,
            response.text,
            response.headers
        )

        return self._cursor_value is not None

    def apply(self, paginated_data):
        """
        Advances the pagination by updating the request builder with the next cursor value.

        If there is no previous response, initializes the cursor from the request builder.
        Otherwise, extracts the cursor from the last response using the configured output pointer,
        and updates the request builder for the next page. Returns None if no further pages are available.

        Args:
            paginated_data: An object containing the last response and the current request builder.

        Returns:
            A new request builder for the next page, or None if pagination is complete.
        """
        last_response = paginated_data.last_response
        request_builder = paginated_data.request_builder
        self._cursor_value = self._get_initial_cursor_value(request_builder, self._input)

        # The last response is none which means this is going to be the 1st page
        if last_response is None:
            return request_builder

        self._cursor_value = ApiHelper.resolve_response_pointer(
            self._output,
            last_response.text,
            last_response.headers
        )

        if self._cursor_value is None:
            return None

        return self.get_updated_request_builder(request_builder, self._input, self._cursor_value)

    def apply_metadata_wrapper(self, paged_response):
        """
        Applies the configured metadata wrapper to the paged response, including the current cursor value.

        Args:
            paged_response: The response object from the current page.

        Returns:
            The result of the metadata wrapper applied to the paged response and cursor value.
        """
        return self._metadata_wrapper(paged_response, self._cursor_value)

    @staticmethod
    def _get_initial_cursor_value(request_builder, input_pointer):
        """
        Retrieves the initial cursor value from the request builder using the specified input pointer.

        Args:
            request_builder: The request builder containing request parameters.
            input_pointer (str): The JSON pointer indicating the location of the cursor value.

        Returns:
            The initial cursor value if found, otherwise None.
        """
        path_prefix, field_path = ApiHelper.split_into_parts(input_pointer)

        if path_prefix == PaginationStrategy.PATH_PARAMS_IDENTIFIER:
            value = ApiHelper.get_value_by_json_pointer(
                request_builder.template_params, f"{field_path}/value")
            return value if value is not None else None
        elif path_prefix == PaginationStrategy.QUERY_PARAMS_IDENTIFIER:
            return ApiHelper.get_value_by_json_pointer(request_builder.query_params, field_path)
        elif path_prefix == PaginationStrategy.HEADER_PARAMS_IDENTIFIER:
            return ApiHelper.get_value_by_json_pointer(request_builder.header_params, field_path)
        elif path_prefix == PaginationStrategy.BODY_PARAM_IDENTIFIER:
            return ApiHelper.get_value_by_json_pointer(
                request_builder.body_params or request_builder.form_params, field_path)

        return None
