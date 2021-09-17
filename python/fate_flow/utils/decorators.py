#
#  Copyright 2019 The FATE Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import time
from fate_flow.utils.log_utils import getLogger
from functools import wraps

LOGGER = getLogger()


def trys(times=20):
    def wrapper(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            for n in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if n + 1 < times:
                        LOGGER.warning(f"function {func.__name__} error, try again {n} times", exc_info=True)
                    else:
                        LOGGER.error(f"function {func.__name__} error, no retries", exc_info=True)
                        raise e
                time.sleep(0.1 * n)
        return decorated_function
    return wrapper