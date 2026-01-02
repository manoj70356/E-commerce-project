from apimatic_core.types.error_case import ErrorCase
from tests.apimatic_core.mocks.exceptions.global_test_exception import GlobalTestException
from tests.apimatic_core.mocks.exceptions.nested_model_exception import NestedModelException


class GlobalConfiguration:
    def __init__(self, with_template_message = False):
        if with_template_message:
            self._global_errors = {
                '400': ErrorCase()
                .error_message_template('error_code => {$statusCode}, header => {$response.header.accept}, '
                                        'body => {$response.body#/ServerCode} - {$response.body#/ServerMessage}')
                .exception_type(GlobalTestException),
                '412': ErrorCase()
                .error_message_template('global error message -> error_code => {$statusCode}, header => '
                                        '{$response.header.accept}, body => {$response.body#/ServerCode} - '
                                        '{$response.body#/ServerMessage} - {$response.body#/model/name}')
                .exception_type(NestedModelException)
            }
        else:
            self._global_errors = {
                '400': ErrorCase().error_message('400 Global').exception_type(GlobalTestException),
                '412': ErrorCase().error_message('Precondition Failed').exception_type(NestedModelException),
                '3XX': ErrorCase().error_message('3XX Global').exception_type(GlobalTestException),
                'default': ErrorCase().error_message('Invalid response').exception_type(GlobalTestException),
            }

    def get_global_errors(self):
        return self._global_errors

