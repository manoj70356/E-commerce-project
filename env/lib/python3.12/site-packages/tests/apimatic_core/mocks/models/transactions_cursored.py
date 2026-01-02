from apimatic_core.utilities.api_helper import ApiHelper
from tests.apimatic_core.mocks.models.transaction import Transaction


class TransactionsCursored(object):

    """Implementation of the 'TransactionsCursored' model.

    Attributes:
        data (List[Transaction]): The model property of type List[Transaction].
        next_cursor (str): Cursor for the next page of results.

    """

    # Create a mapping from Model property names to API property names
    _names = {
        "data": 'data',
        "next_cursor": 'nextCursor'
    }

    _optionals = [
        'data',
        'next_cursor',
    ]

    _nullables = [
        'next_cursor',
    ]

    def __init__(self,
                 data=ApiHelper.SKIP,
                 next_cursor=ApiHelper.SKIP):
        """Constructor for the TransactionsCursored class"""

        # Initialize members of the class
        if data is not ApiHelper.SKIP:
            self.data = data 
        if next_cursor is not ApiHelper.SKIP:
            self.next_cursor = next_cursor 

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
        data = None
        if dictionary.get('data') is not None:
            data = [Transaction.from_dictionary(x) for x in dictionary.get('data')]
        else:
            data = ApiHelper.SKIP
        next_cursor = dictionary.get("nextCursor") if "nextCursor" in dictionary.keys() else ApiHelper.SKIP
        # Return an object of this model
        return cls(data,
                   next_cursor)

    def __repr__(self):
        return (f'{self.__class__.__name__}('
                f'data={(self.data if hasattr(self, "data") else None)!r}, '
                f'next_cursor={(self.next_cursor if hasattr(self, "next_cursor") else None)!r})')

    def __str__(self):
        return (f'{self.__class__.__name__}('
                f'data={(self.data if hasattr(self, "data") else None)!s}, '
                f'next_cursor={(self.next_cursor if hasattr(self, "next_cursor") else None)!s})')
