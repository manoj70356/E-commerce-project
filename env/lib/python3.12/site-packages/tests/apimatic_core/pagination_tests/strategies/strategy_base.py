from apimatic_core.pagination.pagination_strategy import PaginationStrategy
from apimatic_core.utilities.api_helper import ApiHelper


class StrategyBase:

    @staticmethod
    def assert_initial_param_extraction(
        mocker,
        mock_request_builder,
        mock_metadata_wrapper,
        input_pointer,
        initial_params,
        expected_value,
        json_pointer_return_value,
        default_value,
        pagination_instance_creator
    ):
        # Set request builder params
        if PaginationStrategy.PATH_PARAMS_IDENTIFIER in input_pointer:
            mock_request_builder._template_params = initial_params
        elif PaginationStrategy.QUERY_PARAMS_IDENTIFIER in input_pointer:
            mock_request_builder._query_params = initial_params
        elif PaginationStrategy.HEADER_PARAMS_IDENTIFIER in input_pointer:
            mock_request_builder._header_params = initial_params
        elif PaginationStrategy.BODY_PARAM_IDENTIFIER in input_pointer:
            mock_request_builder._body_param = initial_params

        # Mock helper methods
        mock_split = mocker.patch.object(ApiHelper, 'split_into_parts',
                                         return_value=(input_pointer.split('#')[0], input_pointer.split('#')[1]))
        mock_json_pointer = mocker.patch.object(ApiHelper, 'get_value_by_json_pointer',
                                                return_value=json_pointer_return_value)

        # Run
        pagination_instance = pagination_instance_creator(input_pointer, mock_metadata_wrapper)
        result = pagination_instance._get_initial_request_param_value(
            mock_request_builder, input_pointer, default_value
        ) if default_value is not None else pagination_instance._get_initial_request_param_value(
            mock_request_builder, input_pointer)

        # Assert
        mock_split.assert_called_once_with(input_pointer)

        if input_pointer.startswith((
            PaginationStrategy.PATH_PARAMS_IDENTIFIER,
            PaginationStrategy.QUERY_PARAMS_IDENTIFIER,
            PaginationStrategy.HEADER_PARAMS_IDENTIFIER,
            PaginationStrategy.BODY_PARAM_IDENTIFIER
        )):
            if PaginationStrategy.PATH_PARAMS_IDENTIFIER in input_pointer:
                accessed = mock_request_builder.template_params
                mock_json_pointer.assert_called_once_with(accessed, f"{input_pointer.split('#')[1]}/value")
            elif PaginationStrategy.QUERY_PARAMS_IDENTIFIER in input_pointer:
                accessed = mock_request_builder.query_params
                mock_json_pointer.assert_called_once_with(accessed, input_pointer.split('#')[1])
            elif PaginationStrategy.HEADER_PARAMS_IDENTIFIER in input_pointer:
                accessed = mock_request_builder.header_params
                mock_json_pointer.assert_called_once_with(accessed, input_pointer.split('#')[1])
            elif PaginationStrategy.BODY_PARAM_IDENTIFIER in input_pointer:
                accessed = mock_request_builder.body_params
                mock_json_pointer.assert_called_once_with(accessed, input_pointer.split('#')[1])
        else:
            mock_json_pointer.assert_not_called()

        assert result == expected_value