#modules that have tests
TEST_MODULES=.

#modules that are installable (ie: ones w/ setup.py)
INSTALL_MODULES=.

#packages to cover
COVER_PACKAGES=connectome_tools

PYTHON_PIP_VERSION=pip==9.0.1

##### DO NOT MODIFY BELOW #####################

CI_REPO?=ssh://bbpcode.epfl.ch/platform/ContinuousIntegration.git
CI_DIR?=ContinuousIntegration

FETCH_CI := $(shell \
        if [ ! -d $(CI_DIR) ]; then \
            git clone $(CI_REPO) $(CI_DIR) > /dev/null ;\
        fi;\
        echo $(CI_DIR) )
include $(FETCH_CI)/python/common_makefile
