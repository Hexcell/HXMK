import colorama
from colorama import Fore
from colorama import Back
from colorama import Style

colorama.init()

reset = Style.RESET_ALL

# schemes
error						= Fore.WHITE + Back.RED + "[ERROR] "
info						= Fore.BLUE
warning						= Fore.YELLOW 			+ "[WARNING] "
okay						= Fore.GREEN
info2						= Fore.MAGENTA

# directories
invalid_directory			= error + "\"%s\" doesn't have a hxmk.py file" + reset

# commands
not_a_command				= error + "%s is not a command" + reset
info_command				= Fore.MAGENTA + ">>> " + reset + "%s"
error_command				= error + "%s" + reset

# rules and patterns
rule_not_found				= "%s" + error + "@%s was not found" + reset
executing_rule				= "%s" + info + "@%s" + reset
invalid_decorator_params	= error + "\"%s\" is not a valid value for %s" + reset
unexpected_param			= error + "Unexpected parameter \"%s\"" + reset
expects_param				= error + "Trigger \"%s\" expects parameter \"%s\"" + reset
always_overrides			= warning + "Trigger \"always\" overrides any other trigger" + reset
cache_file_missing			= error + "File \"%s\" does not exist, change could not be detected" + reset

expectation_not_met			= warning + "Expected rule to create \"%s\"" + reset

up_to_date					= "%s" + okay + "@%s is up to date" + reset

# sub directories
dir_entering				= info2 + "Entering %s" + reset
dir_exiting					= info2 + "Exiting %s" + reset
dir_not_found				= error + "\"%s\" is not a directory" + reset

# other
clean_not_found				= error + ".clean file not found" + reset
cleaning					= info + "Cleaning..." + reset
cleaning_done				= info + "Cleaning done, " + reset + "%i files " + info + "and" + reset + " %i dirs " + info + "removed" + reset
deleting					= Fore.RED + "Deleting %s" + reset
