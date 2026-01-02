
class PagedResponse:
    """
    The base class for paged response types.
    """

    @property
    def body(self):
        """
        Returns the content associated with the Page instance.
        """
        return self._body

    def __init__(self, body, paginated_field_getter):
        """
        Initialize the instance.

        Args:
            body: The paginated response model.
            paginated_field_getter: The value getter for the paginated payload, to provide the iterator on this field.
        """
        self._body = body
        self._paginated_field_getter = paginated_field_getter

    def items(self):
        """
        Returns an iterator over the items in the paginated response body.
        """
        return iter(self._paginated_field_getter(self.body))

class LinkPagedResponse(PagedResponse):
    """
    Represents a paginated API response for link based pagination.
    """

    @property
    def next_link(self):
        """
        Returns the next link url using which the current paginated response is fetched.
        """
        return self._next_link

    def __init__(self, body, paginated_field_getter, next_link):
        """
        Initialize the instance.

        Args:
            body: The paginated response model.
            paginated_field_getter: The value getter for the paginated payload, to provide the iterator on this field.
            next_link: The next link url using which the current paginated response is fetched.
        """
        super().__init__(body, paginated_field_getter)
        self._next_link = next_link

    def __str__(self):
        """
        Return a string representation of the LinkPagedResponse, including the next_link and body attributes.
        """
        return f"LinkPagedResponse(body={self.body}, next_link={self.next_link})"

class CursorPagedResponse(PagedResponse):
    """
    Represents a paginated API response for cursor based pagination.
    """

    @property
    def next_cursor(self):
        """
        Returns the next cursor using which the current paginated response is fetched.
        """
        return self._next_cursor

    def __init__(self, body, paginated_field_getter, next_cursor):
        """
        Initialize the instance.

        Args:
            body: The paginated response model.
            paginated_field_getter: The value getter for the paginated payload, to provide the iterator on this field.
            next_cursor: The next cursor using which the current paginated response is fetched.
        """
        super().__init__(body, paginated_field_getter)
        self._next_cursor = next_cursor

    def __str__(self):
        """
        Return a string representation of the CursorPagedResponse, including the next_cursor and body attributes.
        """
        return f"CursorPagedResponse(body={self.body}, next_cursor={self.next_cursor})"

class OffsetPagedResponse(PagedResponse):
    """
    Represents a paginated API response for offset based pagination.
    """

    @property
    def offset(self):
        """
        Returns the offset using which the current paginated response is fetched.
        """
        return self._offset

    def __init__(self, body, paginated_field_getter, offset):
        """
        Initialize the instance.

        Args:
            body: The paginated response model.
            paginated_field_getter: The value getter for the paginated payload, to provide the iterator on this field.
            offset: The offset using which the current paginated response is fetched.
        """
        super().__init__(body, paginated_field_getter)
        self._offset = offset

    def __str__(self):
        """
        Return a string representation of the OffsetPagedResponse, including the offset and body attributes.
        """
        return f"OffsetPagedResponse(body={self.body}, offset={self.offset})"

class NumberPagedResponse(PagedResponse):
    """
    Represents a paginated API response for page number based pagination.
    """

    @property
    def page_number(self):
        """
        Returns the page number using which the current paginated response is fetched.
        """
        return self._page_number

    def __init__(self, body, paginated_field_getter, page_number):
        """
        Initialize the instance.

        Args:
            body: The paginated response model.
            paginated_field_getter: The value getter for the paginated payload, to provide the iterator on this field.
            page_number: The page number using which the current paginated response is fetched.
        """
        super().__init__(body, paginated_field_getter)
        self._page_number = page_number

    def __str__(self):
        """
        Return a string representation of the NumberPagedResponse, including the page_number and body attributes.
        """
        return f"NumberPagedResponse(body={self.body}, page_number={self.page_number})"

