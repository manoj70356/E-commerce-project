from apimatic_core.http.http_callback import HttpCallBack


class HttpCallContext(HttpCallBack):

    @property
    def request(self):
        return self._request

    @property
    def response(self):
        return self._response

    def __init__(self):
        self._request = None
        self._response = None

    """An interface for  the callback to be called before and after the
    HTTP call for an endpoint is made.

    This class should not be instantiated but should be used as a base class
    for HttpCallBack classes.

    """

    def on_before_request(self, request):  # pragma: no cover
        """The controller will call this method before making the HttpRequest.

        Args:
            request (HttpRequest): The request object which will be sent
                to the HttpClient to be executed.
        """
        self._request = request

    def on_after_response(self, response):  # pragma: no cover
        """The controller will call this method after making the HttpRequest.

        Args:
            response (HttpResponse): The HttpResponse of the API call.
        """
        self._response = response