from aenum import MultiValueEnum


class ResponseCode(MultiValueEnum):
    operation_successful = "Operation Successfull", 200
    invalid_argument = "Invalid Argument", 400
