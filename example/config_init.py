from config import *

def is_color(value):
	if value not in ["orange", "blue", "red"]:
		raise ValidationError("Not a color.")

options = [
	ConfigOption(uri = "test/APPLE_COLOR", validator = is_color),
	ConfigOption(uri = "test/BOOLEAN", expected_type = bool)
]
register_options(options)

load("test.conf.py", current_domain = "test")

print "test/BOOLEAN = %s" % (get("test/BOOLEAN"), )
