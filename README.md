# ferret

ferret is an experimental approach to combining Mixed Boolean-Arithmetic simplification techniques using e-graphs.
It is primarily based on the work of Matteo Favaro and Tim Blazytko from [their blog post](https://secret.club/2022/08/08/eqsat-oracle-synthesis.html).

As of right now this implementation uses [egglog](https://github.com/egraphs-good/egglog) to combine MBA-Blast, SiMBA, QSynth, LLVM-based optimization and boolean circuit simplification.


## Building

Technically on a fresh server running the `util/install.sh` script should work. But in practice the full installation process is a bit annoying and not super clean.

Compiling Bitwuzla can be a bit annoying but is optional (and instead Z3 will be used, but will lead to worse performance).
This release, right now, also depends on custom patches in egglog and egglog-python for multiset support, though future versions might not.
The thirdparty installations are only required for their datasets and validating the custom implementations of the respective tools.
Pyeda might cause installation problems without the provided patch, but it is also only used for the ESPRESSO bindings and the depdendency might be removed in the future.


## Usage

As of right now the tool is designed to work through entire datasets at once.
See the `run_eval.py` for the supported command line arguments for that.
An example of code for individual expressions can be seen in `test/test_nastyexpr.py`.

## Results

See `thesis.pdf` for the design considerations and my detailed evaluation of this implementation.
The primary result is that while it generalizes better than other existing tooling the very high computational overhead makes it sadly not quite practical to use as is.