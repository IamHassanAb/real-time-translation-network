class UtilityService:
    @staticmethod
    def extract_lang(input_string):
        try:
            resp = input_string.split(':')
            return resp[0]
        except ValueError:
            raise ValueError("Input string must be in the format 'key:value'")

utility_service = UtilityService()
# Example usage:
# input_string = "key:value"
# parsed_dict = utility_service.parse_string_to_dict(input_string)
# print(parsed_dict)  # Output: {'key': 'value'}