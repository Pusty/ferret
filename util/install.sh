#!/bin/bash

# Tested on Ubuntu 24.04 on Digital Ocean Droplets

# ~/ferret/util/install.sh
cd ..
cd ..
# ~/

apt-get -y install python3-full
apt-get -y install python3-dev
apt-get -y install git
apt-get -y install build-essential
apt-get -y install meson ninja-build
apt-get -y install libgmp-dev m4
apt-get -y install python3-pip
apt-get -y install cargo 


python3 -m venv .venv
source .venv/bin/activate

pip install Cython
pip install meson-python
pip install maturin


# Download main repo for requirements and patch files
#git clone https://github.com/Pusty/ferret.git

# Install bitwuzla

git clone --depth 1 --branch 0.7.0 https://github.com/bitwuzla/bitwuzla.git
pip install ./bitwuzla

# Install egglog-python 8.0.1 with patched egglog with multisets support
# This should not be necessary once egglog-python officially supports an egglog version that has this

git clone -n https://github.com/egraphs-good/egglog.git
cd egglog
git checkout 993582f34ed4ec7653ae54d15c69b920f24b3f55
git apply ../ferret/util/egglog-multisets.patch
cd ..

git clone --depth 1 --branch v8.0.1 https://github.com/egraphs-good/egglog-python.git
cd egglog-python
git apply ../ferret/util/egglog-python-multisets.patch
maturin develop
cd ..

# install qsynthesis / triton (optional)
#apt-get -y install cmake
#apt-get -y install libz3-4 libz3-dev
#apt-get -y install libcapstone-dev
#apt-get -y install libboost-all-dev
#git clone -n https://github.com/JonathanSalwan/Triton.git
#cd Triton
#git checkout b022f3179b3ff6fbafd597099ab0e2f5f07df23a
#mkdir build ; cd build
#cmake ..
#make -j3
#make install
#cd ..
#cd ..
#git clone -n https://github.com/quarkslab/qsynthesis.git
#cd qsynthesis
#git checkout 87f29fb36ad4aab767e51565cc6d8dd8fed2e50a
#pip install '.[all]'
#cd ..

# install pyEDA (newer C compilers need this fix for espresso to compile)
git clone --depth 1 --branch v0.29.0 https://github.com/cjdrake/pyeda
cd pyeda


# install third party libraries (used for datasets)

cd ferret
pip install -r requirements.txt


cd thirdparty

git clone -n https://github.com/softsec-unh/MBA-Blast.git
cd MBA-Blast
git checkout ceb12c28ac25ada0b5b9f3ffbf4dcec8e8fa3c39
cd ..

git clone -n https://github.com/softsec-unh/MBA-Solver.git
cd MBA-Solver
git checkout c76231aadb8b033d9e8e6be2baa05ff1464f247e
cd ..

git clone -n https://github.com/nhpcc502/MBA-Obfuscator.git
cd MBA-Obfuscator
git checkout 8574ef8537f884ed7bd38da7b7bc630e8e8fc8f6
cd ..

git clone -n https://github.com/DenuvoSoftwareSolutions/SiMBA.git
cd SiMBA
git checkout 228179970f5906ed763afb33fc8649de2846696e
cd ..

cd ..

# in ~/ferret