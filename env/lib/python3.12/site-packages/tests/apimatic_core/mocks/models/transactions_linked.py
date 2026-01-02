from apimatic_core.utilities.api_helper import ApiHelper
from tests.apimatic_core.mocks.models.links import Links
from tests.apimatic_core.mocks.models.transaction import Transaction


class TransactionsLinked(object):

    """Implementation of the 'TransactionsLinked' model.

    Attributes:
        data (List[Transaction]): The model property of type List[Transaction].
        links (Links): The model property of type Links.

    """

    # Create a mapping from Model property names to API property names
    _names = {
        "data": 'data',
        "links": 'links'
    }

    _optionals = [
        'data',
        'links',
    ]

    def __init__(self,
                 data=ApiHelper.SKIP,
                 links=ApiHelper.SKIP):
        """Constructor for the TransactionsLinked class"""

        # Initialize members of the class
        if data is not ApiHelper.SKIP:
            self.data = data 
        if links is not ApiHelper.SKIP:
            self.links = links 

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
        links = Links.from_dictionary(dictionary.get('links')) if 'links' in dictionary.keys() else ApiHelper.SKIP
        # Return an object of this model
        return cls(data,
                   links)

    def __repr__(self):
        return (f'{self.__class__.__name__}('
                f'data={(self.data if hasattr(self, "data") else None)!r}, '
                f'links={(self.links if hasattr(self, "links") else None)!r})')

    def __str__(self):
        return (f'{self.__class__.__name__}('
                f'data={(self.data if hasattr(self, "data") else None)!s}, '
                f'links={(self.links if hasattr(self, "links") else None)!s})')
