from configuration import *
from rich.console import Console

console = Console()


def vprint(*args, **kwargs):
    return None


# The 'if' statement below will check if verbose_mode flag from configuration is set to true, in which case defined
#  vprint function as such that it works as Console.log() function from the Rich library (so that all the verbose
#  messages which are passed to vprint are actually printed), otherwise, vprint function does nothing (as per
#  definition) and the messages are not displayed.
if verbose_mode:
    vprint = console.log