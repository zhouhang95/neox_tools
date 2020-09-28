import struct, math, argparse
import numpy as np
import transformations as tf
import pymeshio.pmx as pmx
import pymeshio.common as common
import pymeshio.pmx.writer
import pymeshio.pmx.reader
from bone_name import *
from converter import *

def _parse_mesh(path):
    model = {}
    with open(path, 'rb') as f:
        _magic_number = f.read(8)
        model['bone_exist'] = readuint32(f)
        model['mesh'] = []

        if model['bone_exist']:
            bone_count = readuint16(f)
            parent_nodes = []
            for _ in range(bone_count):
                parent_node = readuint8(f)
                readuint8(f)
                if parent_node == 255:
                    parent_node = -1
                parent_nodes.append(parent_node)
            model['bone_parent'] = parent_nodes

            bone_names = []
            for _ in range(bone_count):
                bone_name = f.read(32)
                bone_name = bone_name.decode().replace('\0', '').replace(' ', '_')
                bone_names.append(bone_name)
            model['bone_name'] = bone_names

            flag = readuint8(f)
            assert flag == 1


            for _ in range(bone_count):
                f.read(28)

            model['bone_original_matrix'] = []
            for i in range(bone_count):
                matrix = [readfloat(f) for _ in range(16)]
                matrix = np.array(matrix).reshape(4, 4)
                model['bone_original_matrix'].append(matrix)

            if len(list(filter(lambda x: x == -1, parent_nodes))) > 1:
                num = len(model['bone_parent'])
                model['bone_parent'] = list(map(lambda x: num if x == -1 else x, model['bone_parent']))
                model['bone_parent'].append(-1)
                model['bone_name'].append('dummy_root')
                model['bone_original_matrix'].append(np.identity(4))

            _flag = readuint8(f) # 00
            assert _flag == 0

        _offset = readuint32(f)
        while True:
            flag = readuint16(f)
            if flag == 1:
                break
            f.seek(-2, 1)
            mesh_vertex_count = readuint32(f)
            mesh_face_count = readuint32(f)
            _flag = readuint8(f)
            _flag2 = readuint8(f)

            model['mesh'].append((mesh_vertex_count, mesh_face_count, _flag, _flag2))


        vertex_count = readuint32(f)
        face_count = readuint32(f)

        model['position'] = []
        # vertex position
        for _ in range(vertex_count):
            x = readfloat(f)
            y = readfloat(f)
            z = readfloat(f)
            model['position'].append((x, y, z))

        model['normal'] = []
        # vertex normal
        for _ in range(vertex_count):
            x = readfloat(f)
            y = readfloat(f)
            z = readfloat(f)
            model['normal'].append((x, y, z))

        _flag = readuint16(f)
        if _flag:
            f.seek(vertex_count * 12, 1)

        model['face'] = []
        # face index table
        for _ in range(face_count):
            v1 = readuint16(f)
            v2 = readuint16(f)
            v3 = readuint16(f)
            model['face'].append((v1, v2, v3))


        model['uv'] = []
        # vertex uv
        for mesh_vertex_count, _, _flag, _ in model['mesh']:
            for _ in range(mesh_vertex_count):
                u = readfloat(f)
                v = readfloat(f)
                model['uv'].append((u, v))
            f.read(mesh_vertex_count * 8 * (_flag - 1))

        # vertex weight
        for mesh_vertex_count, _, _, _flag2 in model['mesh']:
            f.read(mesh_vertex_count * 4 * _flag2)

        if model['bone_exist']:
            model['vertex_joint'] = []
            for _ in range(vertex_count):
                vertex_joints = [readuint8(f) for _ in range(4)]
                model['vertex_joint'].append(vertex_joints)

            model['vertex_joint_weight'] = []
            for _ in range(vertex_count):
                vertex_joint_weights = [readfloat(f) for _ in range(4)]
                model['vertex_joint_weight'].append(vertex_joint_weights)

    return model

def _main():
    opt = get_parser()
    model = _parse_mesh(opt.path)
    if opt.mode == 'obj':
        saveobj(model, opt.path)
    elif opt.mode == 'iqe':
        saveiqe(model, opt.path)
    elif opt.mode == 'pmx':
        savepmx(model, opt.path)


if __name__ == '__main__':
    _main()
