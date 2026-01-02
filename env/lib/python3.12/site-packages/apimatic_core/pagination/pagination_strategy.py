# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod

from apimatic_core.utilities.api_helper import ApiHelper


class PaginationStrategy(ABC):
    """
    Abstract base class for implementing pagination strategies.

    Provides methods to initialize with pagination metadata, apply pagination logic to request builders,
    and update request builders with new pagination parameters based on JSON pointers.
    """

    PATH_PARAMS_IDENTIFIER = "$request.path"
    QUERY_PARAMS_IDENTIFIER = "$request.query"
    HEADER_PARAMS_IDENTIFIER = "$request.headers"
    BODY_PARAM_IDENTIFIER = "$request.body"

    def __init__(self, metadata_wrapper):
        """
        Initializes the PaginationStrategy with the provided metadata wrapper.

        Args:
            metadata_wrapper: An object containing pagination metadata. Must not be None.

        Raises:
            ValueError: If metadata_wrapper is None.
        """
        if metadata_wrapper is None:
            raise ValueError("Metadata wrapper for the pagination cannot be None")

        self._metadata_wrapper = metadata_wrapper

    @abstractmethod
    def is_applicable(self, response):
        """
        Checks whether the pagination strategy is a valid candidate based on the given HTTP response.

        Args:
            response: The response from the previous API call.

        Returns:
            bool: True if this strategy is valid based on the given HTTP response..
        """
        ...

    @abstractmethod
    def apply(self, paginated_data):
        """
        Modifies the request builder to fetch the next page of results based on the provided paginated data.

        Args:
            paginated_data: The response data from the previous API call.

        Returns:
            RequestBuilder: An updated request builder configured for the next page request.
        """
        ...

    @abstractmethod
    def apply_metadata_wrapper(self, paged_response):
        """
        Processes the paged API response using the metadata wrapper.

        Args:
            paged_response: The response object containing paginated data.

        Returns:
            The processed response with applied pagination metadata.
        """
        ...

    @staticmethod
    def get_updated_request_builder(request_builder, input_pointer, offset):
        """
        Updates the given request builder by modifying its path, query,
         or header parameters based on the specified JSON pointer and offset.

        Args:
            request_builder: The request builder instance to update.
            input_pointer (str): JSON pointer indicating which parameter to update.
            offset: The value to set at the specified parameter location.

        Returns:
            The updated request builder with the modified parameter.
        """
        path_prefix, field_path = ApiHelper.split_into_parts(input_pointer)
        template_params = request_builder.template_params
        query_params = request_builder.query_params
        header_params = request_builder.header_params
        body_params = request_builder.body_params
        form_params = request_builder.form_params

        if path_prefix == PaginationStrategy.PATH_PARAMS_IDENTIFIER:
            template_params = ApiHelper.update_entry_by_json_pointer(
                template_params.copy(), f"{field_path}/value", offset, inplace=True)
        elif path_prefix == PaginationStrategy.QUERY_PARAMS_IDENTIFIER:
            query_params = ApiHelper.update_entry_by_json_pointer(
                query_params.copy(), field_path, offset, inplace=True)
        elif path_prefix == PaginationStrategy.HEADER_PARAMS_IDENTIFIER:
            header_params = ApiHelper.update_entry_by_json_pointer(
                header_params.copy(), field_path, offset, inplace=True)
        elif path_prefix == PaginationStrategy.BODY_PARAM_IDENTIFIER:
            if body_params is not None:
                body_params = ApiHelper.update_entry_by_json_pointer(
                    body_params.copy(), field_path, offset, inplace=True)
            else:
                form_params = ApiHelper.update_entry_by_json_pointer(
                    form_params.copy(), field_path, offset, inplace=True)

        return request_builder.clone_with(
            template_params=template_params, query_params=query_params, header_params=header_params,
            body_param=body_params, form_params=form_params
        )

    @staticmethod
    def _get_initial_request_param_value(request_builder, input_pointer, default=0):
        """
        Extracts the initial pagination offset value from the request builder using the specified JSON pointer.

        Args:
            request_builder: The request builder containing path, query, and header parameters.
            input_pointer (str): JSON pointer indicating which parameter to extract.
            default (int, optional): The value to return if the parameter is not found. Defaults to 0.

        Returns:
            int: The initial offset value from the specified parameter, or default if not found.
        """
        path_prefix, field_path = ApiHelper.split_into_parts(input_pointer)

        if path_prefix == PaginationStrategy.PATH_PARAMS_IDENTIFIER:
            value = ApiHelper.get_value_by_json_pointer(
                request_builder.template_params, f"{field_path}/value")
            return int(value) if value is not None else default
        elif path_prefix == PaginationStrategy.QUERY_PARAMS_IDENTIFIER:
            value = ApiHelper.get_value_by_json_pointer(request_builder.query_params, field_path)
            return int(value) if value is not None else default
        elif path_prefix == PaginationStrategy.HEADER_PARAMS_IDENTIFIER:
            value = ApiHelper.get_value_by_json_pointer(request_builder.header_params, field_path)
            return int(value) if value is not None else default
        elif path_prefix == PaginationStrategy.BODY_PARAM_IDENTIFIER:
            value = ApiHelper.get_value_by_json_pointer(
                request_builder.body_params or request_builder.form_params, field_path)
            return int(value) if value is not None else default

        return default