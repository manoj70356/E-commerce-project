from apimatic_core.utilities.api_helper import ApiHelper
from tests.apimatic_core.mocks.models.transaction import Transaction


class TransactionsOffset(object):

    """Implementation of the 'TransactionsOffset' model.

    Attributes:
        data (List[Transaction]): The model property of type List[Transaction].

    """

    # Create a mapping from Model property names to API property names
    _names = {
        "data": 'data'
    }

    _optionals = [
        'data',
    ]

    def __init__(self,
                 data=ApiHelper.SKIP):
        """Constructor for the TransactionsOffset class"""

        # Initialize members of the class
        if data is not ApiHelper.SKIP:
            self.data = data 

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
        # Return an object of this model
        return cls(data)

    def __repr__(self):
        return (f'{self.__class__.__name__}('
                f'data={(self.data if hasattr(self, "data") else None)!r})')

    def __str__(self):
        return (f'{self.__class__.__name__}('
                f'data={(self.data if hasattr(self, "data") else None)!s})')
