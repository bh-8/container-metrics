class ExampleFormat():
    """
    container_format: AbstractContainerFormat   - required for recursive parsing call (see example)
    parsing_data: bytes                         - copy of origin data to parse
    parsing_layer: int                          - recursive depth
    origin_position: int                        - parsing_data offset in origin file

    example to initiate recursive parsing:
    container_format.parse(parsing_layer + 1, origin_position + offset, length)
    """
    @staticmethod
    def format_specific_parsing(container_format, parsing_data: bytes, parsing_layer: int, origin_position: int) -> dict:

        # TODO: implement parsing here

        return {
            "key": "Hello, World!",
            "parsing_data": str(parsing_data),
            "parsing_layer": parsing_layer,
            "origin_position": origin_position
        }
