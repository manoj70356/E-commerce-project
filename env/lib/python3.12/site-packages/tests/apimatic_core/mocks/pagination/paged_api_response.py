from apimatic_core.http.response.http_response import HttpResponse
from tests.apimatic_core.mocks.models.api_response import ApiResponse


class PagedApiResponse(ApiResponse):
    """
    The base class for paged response types.
    """

    def __init__(self, http_response, errors, body, paginated_field_getter):
        """
        Initialize the instance.

        Args:
            http_response: The original HTTP response object.
            errors: Any errors returned by the server.
            body: The paginated response model.
            paginated_field_getter: The value getter for the paginated payload, to provide the iterator on this field.
        """
        super().__init__(http_response, body, errors)
        self._paginated_field_getter = paginated_field_getter

    def items(self):
        """
        Returns an iterator over the items in the paginated response body.
        """
        return iter(self._paginated_field_getter(self.body))

class LinkPagedApiResponse(PagedApiResponse):
    """
    Represents a paginated API response for link based pagination.
    """

    @property
    def next_link(self):
        """
        Returns the next link url using which the current paginated response is fetched.
        """
        return self._next_link

    def __init__(self, http_response, errors, body, paginated_field_getter, next_link):
        """
        Initialize the instance.

        Args:
            http_response: The original HTTP response object.
            errors: Any errors returned by the server.
            body: The paginated response model.
            paginated_field_getter: The value getter for the paginated payload, to provide the iterator on this field.
            next_link: The next link url using which the current paginated response is fetched.
        """
        super().__init__(http_response, body, errors, paginated_field_getter)
        self._next_link = next_link

    def __str__(self):
        """
        Return a string representation of the LinkPagedResponse, including the next_link and body attributes.
        """
        return f"LinkPagedResponse(status_code={self.status_code}, body={self.body}, next_link={self.next_link})"

    @classmethod
    def create(cls, base_api_response, paginated_field_getter=None, next_link=None):
        """
        Create a new instance using the base_api_response and optional pagination parameters.

        Args:
            base_api_response: The base HTTP response object.
            paginated_field_getter: Optional callable to extract paginated field.
            next_link: The next link url using which the current paginated response is fetched.

        Returns:
            An instance of the class.
        """
        return cls(HttpResponse(base_api_response.status_code, base_api_response.reason_phrase,
                                 base_api_response.headers, base_api_response.text, base_api_response.request),
                   base_api_response.body, base_api_response.errors, paginated_field_getter, next_link)

class CursorPagedApiResponse(PagedApiResponse):
    """
    Represents a paginated API response for cursor based pagination.
    """

    @property
    def next_cursor(self):
        """
        Returns the next cursor using which the current paginated response is fetched.
        """
        return self._next_cursor

    def __init__(self, http_response, errors, body, paginated_field_getter, next_cursor):
        """
        Initialize the instance.

        Args:
            http_response: The original HTTP response object.
            errors: Any errors returned by the server.
            body: The paginated response model.
            paginated_field_getter: The value getter for the paginated payload, to provide the iterator on this field.
            next_cursor: The next cursor using which the current paginated response is fetched.
        """
        super().__init__(http_response, body, errors, paginated_field_getter)
        self._next_cursor = next_cursor

    def __str__(self):
        """
        Return a string representation of the CursorPagedResponse, including the next_cursor and body attributes.
        """
        return f"CursorPagedResponse(status_code={self.status_code}, body={self.body}, next_cursor={self.next_cursor})"

    @classmethod
    def create(cls, base_api_response, paginated_field_getter=None, next_cursor=None):
        """
        Create a new instance using the base_api_response and optional pagination parameters.

        Args:
            base_api_response: The base HTTP response object.
            paginated_field_getter: Optional callable to extract paginated field.
            next_cursor: The next cursor using which the current paginated response is fetched.

        Returns:
            An instance of the class.
        """
        return cls(HttpResponse(base_api_response.status_code, base_api_response.reason_phrase,
                                 base_api_response.headers, base_api_response.text, base_api_response.request),
                   base_api_response.body, base_api_response.errors, paginated_field_getter, next_cursor)

class OffsetPagedApiResponse(PagedApiResponse):
    """
    Represents a paginated API response for offset based pagination.
    """

    @property
    def offset(self):
        """
        Returns the offset using which the current paginated response is fetched.
        """
        return self._offset

    def __init__(self, http_response, errors, body, paginated_field_getter, offset):
        """
        Initialize the instance.

        Args:
            http_response: The original HTTP response object.
            errors: Any errors returned by the server.
            body: The paginated response model.
            paginated_field_getter: The value getter for the paginated payload, to provide the iterator on this field.
            offset: The offset using which the current paginated response is fetched.
        """
        super().__init__(http_response, body, errors, paginated_field_getter)
        self._offset = offset

    def __str__(self):
        """
        Return a string representation of the OffsetPagedResponse, including the offset and body attributes.
        """
        return f"OffsetPagedResponse(status_code={self.status_code}, body={self.body}, offset={self.offset})"

    @classmethod
    def create(cls, base_api_response, paginated_field_getter=None, offset=None):
        """
        Create a new instance using the base_api_response and optional pagination parameters.

        Args:
            base_api_response: The base HTTP response object.
            paginated_field_getter: Optional callable to extract paginated field.
            offset: The offset using which the current paginated response is fetched.

        Returns:
            An instance of the class.
        """
        return cls(HttpResponse(base_api_response.status_code, base_api_response.reason_phrase,
                                 base_api_response.headers, base_api_response.text, base_api_response.request),
                   base_api_response.body, base_api_response.errors, paginated_field_getter, offset)

class NumberPagedApiResponse(PagedApiResponse):
    """
    Represents a paginated API response for page number based pagination.
    """

    @property
    def page_number(self):
        """
        Returns the page number using which the current paginated response is fetched.
        """
        return self._page_number

    def __init__(self, http_response, errors, body, paginated_field_getter, page_number):
        """
        Initialize the instance.

        Args:
            http_response: The original HTTP response object.
            errors: Any errors returned by the server.
            body: The paginated response model.
            paginated_field_getter: The value getter for the paginated payload, to provide the iterator on this field.
            page_number: The page number using which the current paginated response is fetched.
        """
        super().__init__(http_response, body, errors, paginated_field_getter)
        self._page_number = page_number

    def __str__(self):
        """
        Return a string representation of the NumberPagedResponse, including the page_number and body attributes.
        """
        return f"NumberPagedResponse(status_code={self.status_code}, body={self.body}, page_number={self.page_number})"

    @classmethod
    def create(cls, base_api_response, paginated_field_getter=None, page_number=None):
        """
        Create a new instance using the base_api_response and optional pagination parameters.

        Args:
            base_api_response: The base HTTP response object.
            paginated_field_getter: Optional callable to extract paginated field.
            page_number: The page number using which the current paginated response is fetched.

        Returns:
            An instance of the class.
        """
        return cls(HttpResponse(base_api_response.status_code, base_api_response.reason_phrase,
                                 base_api_response.headers, base_api_response.text, base_api_response.request),
                   base_api_response.body, base_api_response.errors, paginated_field_getter, page_number)

