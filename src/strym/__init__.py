from strym._core import hello_from_bin
#from .strym import strym
from .config import config
#from .strym import __version__
#from .strym import __author__
#from .strym import __email__
from .strymread import *
from .meta import meta
from .dashboard import dashboard
from .strymmap import *
from .DBC_Read_Tools import *
from .phasespace import phasespace
from .tools import acd
from .tools import ellipse_fit
from .tools import graham_scan
from .tools import threept_center
from .tools import coord_precheck
from .utils import configure_logworker


from .multimode import platoons
from .ml import AutoEncoder

LOGGER = configure_logworker()

def hello() -> str:
    return hello_from_bin()
