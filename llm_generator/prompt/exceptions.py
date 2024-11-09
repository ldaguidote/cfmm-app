class PromptError(Exception):
    """Custom exception raised for errors related to prompt building or processing."""

    def __init__(self, message="An error occurred while building or processing the prompt.", details=None):
        """
        Initializes the PromptError exception with a message and optional details.
        
        Args:
            message (str): The error message to display.
            details (Any): Optional additional details about the error (e.g., invalid data, parameter values).
        """
        super().__init__(message)
        self.details = details

    def __str__(self):
        """Returns a string representation of the error, including details if available."""
        base_message = super().__str__()
        if self.details:
            return f"{base_message} | Details: {self.details}"
        return base_message
