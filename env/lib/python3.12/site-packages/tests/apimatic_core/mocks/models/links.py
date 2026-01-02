from apimatic_core.utilities.api_helper import ApiHelper


class Links(object):

    """Implementation of the 'Links' model.

    Attributes:
        first (str): The model property of type str.
        last (str): The model property of type str.
        prev (str): The model property of type str.
        next (str): The model property of type str.

    """

    # Create a mapping from Model property names to API property names
    _names = {
        "first": 'first',
        "last": 'last',
        "prev": 'prev',
        "_next": 'next'
    }

    _optionals = [
        'first',
        'last',
        'prev',
        '_next',
    ]

    def __init__(self,
                 first=ApiHelper.SKIP,
                 last=ApiHelper.SKIP,
                 prev=ApiHelper.SKIP,
                 _next=ApiHelper.SKIP):
        """Constructor for the Links class"""

        # Initialize members of the class
        if first is not ApiHelper.SKIP:
            self.first = first 
        if last is not ApiHelper.SKIP:
            self.last = last 
        if prev is not ApiHelper.SKIP:
            self.prev = prev 
        if _next is not ApiHelper.SKIP:
            self._next = _next

    @classmethod
    def from_dictionary(cls,
                        dictionary):
        """Creates an instance of this model from a dictionary

        Args:
            dictionary (dictionary): A dictionary representation of the object
            as obtained from the deserialization of the server's response. The
            keys MUST match property names in the API description.

        Returns:
            object: An instance of this structure class.

        """

        if not isinstance(dictionary, dict) or dictionary is None:
            return None

        # Extract variables from the dictionary
        first = dictionary.get("first") if dictionary.get("first") else ApiHelper.SKIP
        last = dictionary.get("last") if dictionary.get("last") else ApiHelper.SKIP
        prev = dictionary.get("prev") if dictionary.get("prev") else ApiHelper.SKIP
        _next = dictionary.get("next") if dictionary.get("next") else ApiHelper.SKIP
        # Return an object of this model
        return cls(first,
                   last,
                   prev,
                   _next)

    def __repr__(self):
        return (f'{self.__class__.__name__}('
                f'first={(self.first if hasattr(self, "first") else None)!r}, '
                f'last={(self.last if hasattr(self, "last") else None)!r}, '
                f'prev={(self.prev if hasattr(self, "prev") else None)!r}, '
                f'next={(self._next if hasattr(self, "_next") else None)!r})')

    def __str__(self):
        return (f'{self.__class__.__name__}('
                f'first={(self.first if hasattr(self, "first") else None)!s}, '
                f'last={(self.last if hasattr(self, "last") else None)!s}, '
                f'prev={(self.prev if hasattr(self, "prev") else None)!s}, '
                f'next={(self._next if hasattr(self, "_next") else None)!s})')
