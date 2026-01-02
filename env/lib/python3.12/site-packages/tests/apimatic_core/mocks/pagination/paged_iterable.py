
class PagedIterable:
    """
    An iterable wrapper for paginated data that allows iteration
        over pages or individual items.
    """

    def __init__(self, paginated_data):
        """
        Initialize the instance.

        Args:
            paginated_data: PaginatedData instance containing pages and items.
        """
        self._paginated_data = paginated_data

    def pages(self):
        """
        Retrieve an iterable collection of all pages in the paginated data.

        Returns:
            The Iterable of pages.
        """
        return self._paginated_data.pages()

    def __iter__(self):
        """
        Provides iterator functionality to sequentially access all items across all pages.

        Returns:
            The Iterator of all items in the paginated data.
        """
        return iter(self._paginated_data)
