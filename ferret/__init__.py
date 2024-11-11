from .bitvec import *
from .expressionast import *
from .equalityprovider import *
from .llvmliteprovider import LLVMLiteEqualityProvider
from .ref.mbablastproviderref import MBABlastEqualityProviderReference
from .mbablastprovider import MBABlastEqualityProvider
from .ferret import * 


# Fix equality bug in egglog.declarations.CallDecl
def egglog_fixeq(self, other: object) -> bool:
    # Override eq to use cached hash for perf
    if not isinstance(other, CallDecl):
        return False
    #return hash(self) == hash(other)
    return self.callable == other.callable and self.args == other.args and self.bound_tp_params == other.bound_tp_params

import egglog
egglog.declarations.CallDecl.__eq__ = egglog_fixeq