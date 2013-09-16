# stdlib
import imp
import threading
import re
import types
import os
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

# internal
import errors

known_options = []
"A list of all of the ConfigOption objects that have been registered."

user_config_module = None
"The loaded configuration file."

user_config = None
"The user's configuration dictionary."

domain = None

class ConfigOption:
    """
    Represents a settable configuration option.

    :ivar uri: The configuraiton option's URI.
    :ivar expected_type: A valid Python type. If the value in the configuration
            is not an instance of this type then a ValidationFailure will be
            raised (`isinstance(user_value, expected_type)` is used to test
            the type).
    :ivar validator: May be either a function or a string. If it is a string,
            it will parsed as a regex and a configuration value will only be
            valid if it matches the regex. If it is a a function, that
            function will be called with a single parameter `value`. If the
            value is not valid, a ValidationFailure should be raised. The
            return value of the function is ignored.
    :ivar required: If True, a MissingValue will be raised if the
            configuration file does not provide a value for the setting (None
            still counts as a value).
    :ivar default: A default value to use if the configuration file does not
            provide a value for the setting (None is a valid default value).

    """

    class NoValue:
        pass

    def __init__(self, uri, expected_type = str, validator = None,
            required = False, default = NoValue()):
        self.uri = uri
        self.expected_type = expected_type
        self.required = required
        self.default = default

        if self.required and type(self.default) is not NoValue:
            raise ValueError(
                "A configuration option cannot be required and have a default "
                "value as well."
            )

        if isinstance(validator, basestring):
            regex = re.compile(self.validator)
            self.validator = lambda s: regex.match(s) is not None
        else:
            self.validator = validator

    def validate(self, value):
        if not isinstance(value, self.expected_type):
            raise errors.ValidationFailure(
                uri = self.uri,
                value = value,
                reason = "Given value '%s' is not an instance of type %s." % (
                    repr(value), expected_type.__name__)
            )

        try:
            if self.validator is not None:
                self.validator(value)
        except errors.ValidationFailure:
            # If validation function through an error add the URI of the config
            # value to it.
            exc_info = sys.exc_info()
            exc_info[1].uri = self.uri
            exc_info[1].value = self.value
            raise exc_info[1], None, exc_info[2]
        except:
            raise errors.ValidationFailure(
                uri = self.uri,
                value = value,
                exc_info = sys.exc_info()
            )

def register_options(option_list):
    """
    Use this function to provide this module with the configuration options
    your domain supports.

    :param option_list: A list of ConfigOption objects.

    :returns: `None`

    """

    known_options.extend(option_list)

def _load_module(path, name, scope = None):
    """
    Loads a module while ignoring any `.pyc` or `.pyo` objects.

    :param path: The modules path on the filesystem.
    :param name: The name of the module (will be passed to the module class's
            constructor).

    :returns: A module object.

    """

    # Execute the config file and create a module object
    with open(path, "r") as f:
        source = f.read()
    module_scope = {} if scope is None else scope
    exec compile(source, path, "exec") in module_scope

    # Shove in the scope
    module = types.ModuleType(name)
    for k, v in module_scope.items():
        setattr(module, k, v)
    return module

def load(config_file_path, current_domain):
    """
    Loads the given configuration file.

    This function may only be called once per process (regardless of the
    configuration file), if it is called again a `ConfigLoaded` exception will
    be raised.

    :param config_file_path: The path to the configuration file.
    :param current_domain: The domain being used.

    :returns: `None`

    """

    global domain
    domain = current_domain

    global user_config_module
    if user_config_module is not None:
        raise errors.ConfigLoaded(
            "Configuration file has already been loaded.")
    else:
        if os.path.isfile(config_file_path):
            user_config_module = _load_module(config_file_path,
                "user_config_module", {"domain": domain
                })
        else:
            raise errors.NoConfigurationFile()

    global user_config
    assert user_config is None
    try:
        user_config = user_config_module.config
    except NameError:
        raise errors.ConfigVariableNotFound()

    # Check if any configuration values exist for this domain that we don't
    # know about.
    local_prefix = "%s/" % (domain, )
    config_lookup = set(i.uri for i in known_options)
    for i in user_config.keys():
        if i.startswith(local_prefix) and i not in config_lookup:
            raise errors.UnknownConfigOption(i)

    # Check if there are any required values that aren't present, or if there
    # are default values we can use.
    for i in known_options:
        if i.uri not in user_config:
            if i.required:
                raise errors.MissingValue(i.uri)
            elif type(i.default) is not ConfigOption.NoValue:
                user_config[i.uri] = i.default

    for i in known_options:
        if i.uri in user_config:
            # An exception will be thrown on failure... no return value.
            i.validate(user_config[i.uri])

def get(uri):
    return user_config[uri]
