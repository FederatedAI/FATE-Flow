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
import numpy


def get_component_output_data_line(src_key, src_value, schema=None):
    data_line = [src_key]
    is_str = False
    extend_header = []
    if hasattr(src_value, "is_instance"):
        for inst in ["inst_id", "label", "weight"]:
            if getattr(src_value, inst) is not None:
                data_line.append(getattr(src_value, inst))
                if inst == "inst_id" and schema:
                    extend_header.append(schema.get("match_id_name"))
                else:
                    extend_header.append(inst)
        data_line.extend(dataset_to_list(src_value.features))
    elif isinstance(src_value, str):
        data_line.extend([value for value in src_value.split(',')])
        is_str = True
    else:
        data_line.extend(dataset_to_list(src_value))
    return data_line, is_str, extend_header


def get_deserialize_value(src_value, id_delimiter):
    extend_header = []
    if hasattr(src_value, "is_instance"):
        v_list = []
        for inst in ["inst_id", "label", "weight"]:
            if getattr(src_value, inst) is not None:
                v_list.append(getattr(src_value, inst))
                extend_header.append(inst)
        v_list.extend(dataset_to_list(src_value.features))
        v_list = list(map(str, v_list))
        deserialize_value = id_delimiter.join(v_list)
    elif isinstance(src_value, str):
        deserialize_value = src_value
    else:
        deserialize_value = id_delimiter.join(list(map(str, dataset_to_list(src_value))))
    return deserialize_value, extend_header


def dataset_to_list(src):
    if isinstance(src, numpy.ndarray):
        return src.tolist()
    elif isinstance(src, list):
        return src
    elif hasattr(src, "is_sparse_vector"):
        vector = [0] * src.get_shape()
        for idx, v in src.get_all_data():
            vector[idx] = v
        return vector
    else:
        return [src]