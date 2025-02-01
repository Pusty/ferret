from .expressionast import *
from .equalityprovider import *
from .llvmliteprovider import LLVMLiteEqualityProvider
from .ref.mbablastproviderref import MBABlastEqualityProviderReference
from .ref.qsynthproviderref import QSynthEqualityProviderReference
from .ref.simbaproviderref import SiMBAEqualityProviderReference
from .mbablastprovider import MBABlastEqualityProvider
from .qsynthprovider import QSynthEqualityProvider
from .qsynthdbserver import startQSynthDBServer, stopQSynthDBServer
from .boolminprovider import BooleanMinifierProvider
from .simbaprovider import SiMBAEqualityProvider
from .ferret import * 


# Fix equality bug in egglog.declarations.CallDecl
def egglog_fixeq(self, other):
    # Override eq to use cached hash for perf
    if not isinstance(other, egglog.declarations.CallDecl):
        return False
    #return hash(self) == hash(other)
    return self.callable == other.callable and self.args == other.args and self.bound_tp_params == other.bound_tp_params

import egglog
egglog.declarations.CallDecl.__eq__ = egglog_fixeq

# Make display() just generate the html
import graphviz.backend.viewing as viewing
viewing.view = lambda x: 0