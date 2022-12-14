# Copyright 2022 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""Sample kernel bootstrap code"""
# pylint: skip-file


def __bootstrap__():
    global __bootstrap__, __loader__, __file__
    import sys
    import pkg_resources
    import importlib.util
    __file__ = pkg_resources.resource_filename(
        __name__, 'sample_kernel.cpython-37m-x86_64-linux-gnu.so')
    __loader__ = None
    del __bootstrap__, __loader__
    spec = importlib.util.spec_from_file_location(__name__, __file__)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)


__bootstrap__()
