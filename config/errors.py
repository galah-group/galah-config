class ConfigLoaded(Exception):
    "The configuration file has already been loaded."

class ConfigVariableNotFound(Exception):
    "The configuration file did not define a config global variable."

class NoConfigurationFile(Exception):
    "The configuration file was not found."

class MissingValue(Exception):
    "A value was not provided for a required option."

    def __init__(self, uri):
        self.uri = uri

    def __str__(self):
        return "No value provided for required option '%s'." % (self.uri, )

class UnknownConfigOption(Exception):
    "An unknown configuration value was given in the current domain."

    def __init__(self, uri):
        self.uri = uri

    def __str__(self):
        return "Unknown configuration option '%s'." % (self.uri, )

class ValidationFailure(Exception):
    """
    Raised when an option's value is invalid.

    :ivar reason: A string describing the reason for the failure.
    :ivar uri: The uri of the configuration option.
    :ivar value: The value that failed validation.
    :ivar exc_info: A tuple as returned by `sys.exc_info()` that is used when
            an unexpected exception is raised in a validation function.

    """

    def __init__(self, reason = None, uri = None, value = None,
            exc_info = None):

        self.uri = uri
        self.reason = reason
        self.exc_info = exc_info

    def __str__(self):
        result = StringIO.StringIO()
        result.write("Option '%s' has invalid value '%s'" % (uri, value))
        if reason is not None:
            result.write(": %s" % (reason, ))
        if exc_info is not None:
            result.write(" -- %s was raised in validation function" % (
                repr(exc_info[1]), ))
        return result.getvalue()
