class UserLoggedOutException(Exception):
    """
    Raised when we are unable to refresh an oauth access token
    """


class UnknownUserException(Exception):
    """
    Raised when we fail to find a user.
    """
