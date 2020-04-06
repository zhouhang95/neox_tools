import struct, math, argparse
import numpy as np
import transformations as tf
import pymeshio.pmx as pmx
import pymeshio.common as common
import pymeshio.pmx.writer
import pymeshio.pmx.reader
from bone_name import *


def readuint8(f):
    return int(struct.unpack('B', f.read(1))[0])

def readuint16(f):
    return int(struct.unpack('H', f.read(2))[0])

def readuint32(f):
    return struct.unpack('I', f.read(4))[0]

def readfloat(f):
    return struct.unpack('f', f.read(4))[0]

def get_parser():
    parser = argparse.ArgumentParser(description='NeoX Model Conveter')
    parser.add_argument('path', type=str)
    parser.add_argument('--mode', type=str, choices=['obj', 'iqe', 'pmx'], default='pmx')
    opt = parser.parse_args()
    return opt

def saveobj(model, filename):
    with open(filename + '.obj', 'w') as f:
        f.write('o {}\n'.format(filename))

        for x, y, z in model['position']:
            f.write('v {} {} {}\n'.format(-x, y, z))
        for x, y, z in model['normal']:
            f.write('vn {} {} {}\n'.format(-x, y, z))
        for u, v in model['uv']:
            f.write('vt {} {}\n'.format(u, 1-v))
        for v1, v2, v3 in model['face']:
            f.write('f {}/{}/{} {}/{}/{} {}/{}/{}\n'.format(
                v2+1,v2+1,v2+1,
                v1+1,v1+1,v1+1,
                v3+1,v3+1,v3+1
            ))

def saveiqe(model, filename):
    model['bone_translate'] = []
    model['bone_rotation'] = []
    for i in range(bone_count):
        matrix = tf.identity_matrix()
        parent_node = model['bone_parent'][i]
        if parent_node >= 0:
            matrix = model['bone_original_matrix'][parent_node]
        matrix = np.dot(model['bone_original_matrix'][i], np.linalg.inv(matrix))
        model['bone_translate'].append(tf.translation_from_matrix(matrix.T))
        model['bone_rotation'].append(tf.quaternion_from_matrix(matrix.T))
    with open(filename + '.iqe ', 'w') as f:
        f.write('# Inter-Quake Export\n')
        f.write('\n')
        parent_child_dict = {}
        old2new = {}
        index_pool = [-1]
        for i in range(len(model['bone_parent'])):
            p = model['bone_parent'][i]
            if p not in parent_child_dict:
                parent_child_dict[p] = []
            parent_child_dict[p].append(i)

        def print_joint(index, parent_index):
            f.write('joint "{}" {}\n'.format(model['bone_name'][index], parent_index))
            x, y, z = model['bone_translate'][index]
            r, i, j, k = model['bone_rotation'][index]
            f.write('pq {} {} {} {} {} {} {}\n'.format(
                -x, y, z, i, -j, -k, r
            ))

        def deep_first_search(index, index_pool, parent_index):
            index_pool[0] += 1
            current_node_index = index_pool[0]
            old2new[index] = current_node_index
            print_joint(index, parent_index)
            if index in parent_child_dict:
                for child in parent_child_dict[index]:
                    deep_first_search(child, index_pool, current_node_index)

        deep_first_search(model['bone_parent'].index(-1), index_pool, -1)

        f.write('\n')


        mesh_vertex_counter = 0
        mesh_face_counter = 0

        for mesh_i in range(len(model['mesh'])):

            mesh_vertex_counter_end = mesh_vertex_counter + model['mesh'][mesh_i][0]
            mesh_face_counter_end = mesh_face_counter + model['mesh'][mesh_i][1]

            f.write('mesh mesh{}\n'.format(mesh_i))
            f.write('material "mesh{}Mat"\n'.format(mesh_i))
            f.write('\n')


            for i in range(mesh_vertex_counter, mesh_vertex_counter_end):
                x, y, z = model['position'][i]
                f.write('vp {} {} {}\n'.format(-x, y, z))
            f.write('\n')


            for i in range(mesh_vertex_counter, mesh_vertex_counter_end):
                x, y, z = model['normal'][i]
                f.write('vn {} {} {}\n'.format(-x, y, z))
            f.write('\n')

            for i in range(mesh_vertex_counter, mesh_vertex_counter_end):
                u, v = model['uv'][i]
                f.write('vt {} {}\n'.format(u, 1-v))
            f.write('\n')

            for i in range(mesh_vertex_counter, mesh_vertex_counter_end):
                f.write('vb')
                for j in range(4):
                    v = model['vertex_joint'][i][j]
                    if v == 255:
                        break
                    v = old2new[v]
                    w = model['vertex_joint_weight'][i][j]
                    f.write(' {} {}'.format(v, w))
                f.write('\n')
            f.write('\n')

            for i in range(mesh_face_counter, mesh_face_counter_end):
                v1, v2, v3 = model['face'][i]
                v1 -= mesh_vertex_counter
                v2 -= mesh_vertex_counter
                v3 -= mesh_vertex_counter
                f.write('fm {} {} {}\n'.format(v3, v1, v2))
            f.write('\n')

            mesh_vertex_counter = mesh_vertex_counter_end
            mesh_face_counter = mesh_face_counter_end

def savepmx(model, filename):
    pmx_model = pmx.Model()
    pmx_model.english_name = u'Empty model'
    pmx_model.comment = u'NeoX Model Converterで生成'
    pmx_model.english_comment = u'Created by NeoX Model Converter.'

    parent_child_dict = {}
    old2new = {}
    index_pool = [-1]
    bone_pool = []
    for i in range(len(model['bone_parent'])):
        p = model['bone_parent'][i]
        if p not in parent_child_dict:
            parent_child_dict[p] = []
        parent_child_dict[p].append(i)

    def build_joint(index, parent_index):
        matrix = model['bone_original_matrix'][index]
        x, y, z = tf.translation_from_matrix(matrix.T)
        bone_pool.append(pmx.Bone(
                name=model['bone_name'][index],
                english_name=model['bone_name'][index],
                position=common.Vector3(-x, y, -z),
                parent_index=parent_index,
                layer=0,
                flag=0
            ))
        bone_pool[-1].setFlag(pmx.BONEFLAG_CAN_ROTATE, True)
        bone_pool[-1].setFlag(pmx.BONEFLAG_IS_VISIBLE, True)
        bone_pool[-1].setFlag(pmx.BONEFLAG_CAN_MANIPULATE, True)

    def deep_first_search(index, index_pool, parent_index):
        index_pool[0] += 1
        current_node_index = index_pool[0]
        old2new[index] = current_node_index
        build_joint(index, parent_index)
        if index in parent_child_dict:
            for child in parent_child_dict[index]:
                deep_first_search(child, index_pool, current_node_index)

    deep_first_search(model['bone_parent'].index(-1), index_pool, -1)

    pmx_model.bones = bone_pool


    for i in range(len(model['position'])):
        x, y, z = model['position'][i]
        nx, ny, nz = model['normal'][i]
        u, v = model['uv'][i]
        vertex_joint_index = list(map(lambda x: old2new[x] if x != 255 else 0,model['vertex_joint'][i]))

        vertex = pmx.Vertex(
            common.Vector3(-x, y, -z),
            common.Vector3(-nx, ny, -nz),
            common.Vector2(u, v),
            pmx.Bdef4(*vertex_joint_index, *(model['vertex_joint_weight'][i])),
            0.0
        )
        pmx_model.vertices.append(vertex)

    for i in range(len(model['face'])):
        pmx_model.indices += list(model['face'][i])

    pmx_model.materials[0].vertex_count = len(model['face']) * 3

    ###########
    pmx_model.materials = []
    for i in range(len(model['mesh'])):
        _, mesh_face_count, _, _ = model['mesh'][i]
        pmx_model.materials.append(
            pmx.Material(u'Mat{}'.format(i)
                    , u'material{}'.format(i)
                    , common.RGB(0.5, 0.5, 1)
                    , 1.0
                    , 1
                    , common.RGB(1, 1, 1)
                    , common.RGB(0, 0, 0)
                    , 0
                    , common.RGBA(0, 0, 0, 1)
                    , 0
                    , -1
                    , -1
                    , pmx.MATERIALSPHERE_NONE
                    , 1
                    , 0
                    , u"comment"
                    , mesh_face_count * 3
            )
        )


    filename = filename.replace('.mesh', '')
    pymeshio.pmx.writer.write_to_file(pmx_model, filename + '.pmx')
    for bone in pmx_model.bones:
        if bone.english_name in paj_middle_bone_name:
            bone.position.x = 0.0

    if 'bip001_l_finger13'  in [bone.english_name for bone in pmx_model.bones]:
        paj_bone_name.update(paj_hand1_name)
    else:
        paj_bone_name.update(paj_hand0_name)


    for bone in pmx_model.bones:
        if bone.english_name in paj_bone_name:
            bone.name = paj_bone_name[bone.english_name][0]
            bone.english_name = paj_bone_name[bone.english_name][1]

    def add_bone(pmxm, bone, index):
        assert index <= len(pmxm.bones)
        pmxm.bones.insert(index, bone)
        for bone in pmxm.bones:
            if bone.parent_index >= index:
                bone.parent_index += 1

        for vertex in pmxm.vertices:
            if vertex.deform.index0 >= index:
                vertex.deform.index0 += 1
            if vertex.deform.index1 >= index:
                vertex.deform.index1 += 1
            if vertex.deform.index2 >= index:
                vertex.deform.index2 += 1
            if vertex.deform.index3 >= index:
                vertex.deform.index3 += 1

        return index

    def find_bone_index_by_name(pmxm, bone_english_name):
        ret = None
        for i in range(len(pmxm.bones)):
            if pmxm.bones[i].english_name == bone_english_name:
                ret = i
                break
        return ret

    #######################
    parent_node_index = find_bone_index_by_name(pmx_model, 'ParentNode')

    center_bone = pmx.Bone(
                name='センター',
                english_name='Center',
                position=common.Vector3(0, 8.0, 0),
                parent_index=parent_node_index,
                layer=0,
                flag=0
            )
    center_bone.setFlag(pmx.BONEFLAG_CAN_ROTATE, True)
    center_bone.setFlag(pmx.BONEFLAG_IS_VISIBLE, True)
    center_bone.setFlag(pmx.BONEFLAG_CAN_MANIPULATE, True)

    waist_index = find_bone_index_by_name(pmx_model, 'Waist')
    center_index = add_bone(pmx_model, center_bone, waist_index)


    groove_bone = pmx.Bone(
                name='グルーブ',
                english_name='Groove',
                position=common.Vector3(0, 8.2, 0),
                parent_index=center_index,
                layer=0,
                flag=0
            )
    groove_bone.setFlag(pmx.BONEFLAG_CAN_ROTATE, True)
    groove_bone.setFlag(pmx.BONEFLAG_IS_VISIBLE, True)
    groove_bone.setFlag(pmx.BONEFLAG_CAN_MANIPULATE, True)
    waist_index = find_bone_index_by_name(pmx_model, 'Waist')
    groove_index = add_bone(pmx_model, groove_bone, waist_index)

    waist_index = find_bone_index_by_name(pmx_model, 'Waist')
    pmx_model.bones[waist_index].parent_index = groove_index

    waist_index = find_bone_index_by_name(pmx_model, 'Waist')
    upper_body_index = find_bone_index_by_name(pmx_model, 'UpperBody')
    pmx_model.bones[upper_body_index].parent_index = waist_index



    ##########################
    for LR in ['Left', 'Right']:
        ankle_index = find_bone_index_by_name(pmx_model, '{}Ankle'.format(LR))
        ankle_x, ankle_y, ankle_z = pmx_model.bones[ankle_index].position.to_tuple()
        toe_index = find_bone_index_by_name(pmx_model, '{}Toe'.format(LR))
        toe_vec = pmx_model.bones[toe_index].position
        toe_vec.y = ankle_y - 1.0
        toe_vec.z = -1.65
        leg_ik_parent_bone = pmx.Bone(
                name='左足IK親' if LR == 'Left' else '右足IK親',
                english_name='{}LegIkParent'.format(LR),
                position=common.Vector3(ankle_x, 0, ankle_z),
                parent_index=parent_node_index,
                layer=0,
                flag=0
            )
        leg_ik_parent_bone.setFlag(pmx.BONEFLAG_CAN_ROTATE, True)
        leg_ik_parent_bone.setFlag(pmx.BONEFLAG_CAN_TRANSLATE, True)
        leg_ik_parent_bone.setFlag(pmx.BONEFLAG_IS_VISIBLE, True)
        leg_ik_parent_bone.setFlag(pmx.BONEFLAG_CAN_MANIPULATE, True)
        leg_ik_parent_index = add_bone(pmx_model, leg_ik_parent_bone, len(pmx_model.bones))

        leg_ik_bone = pmx.Bone(
                name='左足ＩＫ' if LR == 'Left' else '右足ＩＫ',
                english_name='{}LegIk'.format(LR),
                position=common.Vector3(ankle_x, ankle_y, ankle_z),
                parent_index=leg_ik_parent_index,
                layer=0,
                flag=0
            )

        leg_ik_bone.setFlag(pmx.BONEFLAG_CAN_ROTATE, True)
        leg_ik_bone.setFlag(pmx.BONEFLAG_CAN_TRANSLATE, True)
        leg_ik_bone.setFlag(pmx.BONEFLAG_IS_IK, True)
        leg_ik_bone.setFlag(pmx.BONEFLAG_IS_VISIBLE, True)
        leg_ik_bone.setFlag(pmx.BONEFLAG_CAN_MANIPULATE, True)

        knee_index = find_bone_index_by_name(pmx_model, '{}Knee'.format(LR))
        leg_index = find_bone_index_by_name(pmx_model, '{}Leg'.format(LR))
        leg_ik_link = [
            pmx.IkLink(knee_index, 1, common.Vector3(-180.0/57.325, 0, 0), common.Vector3(-0.5/57.325, 0, 0)),
            pmx.IkLink(leg_index, 0)
        ]
        leg_ik_bone.ik = pmx.Ik(ankle_index, 40, 2, leg_ik_link)
        leg_ik_index = add_bone(pmx_model, leg_ik_bone, len(pmx_model.bones))

        toe_ik_bone = pmx.Bone(
                name='左つま先ＩＫ' if LR == 'Left' else '右つま先ＩＫ',
                english_name='{}LegIk'.format(LR),
                position=common.Vector3(toe_vec.x, toe_vec.y, toe_vec.z),
                parent_index=leg_ik_index,
                layer=0,
                flag=0
            )
        toe_ik_bone.setFlag(pmx.BONEFLAG_CAN_ROTATE, True)
        toe_ik_bone.setFlag(pmx.BONEFLAG_CAN_TRANSLATE, True)
        toe_ik_bone.setFlag(pmx.BONEFLAG_IS_IK, True)
        toe_ik_bone.setFlag(pmx.BONEFLAG_IS_VISIBLE, True)
        toe_ik_bone.setFlag(pmx.BONEFLAG_CAN_MANIPULATE, True)
        toe_ik_bone.ik = pmx.Ik(toe_index, 3, 4, [
            pmx.IkLink(ankle_index, 0)
        ])
        add_bone(pmx_model, toe_ik_bone, len(pmx_model.bones))


    '''
    # build local axis and get rotation
    left_arm_index = find_bone_index_by_name(pmx_model, 'LeftArm')
    left_elbow_index = find_bone_index_by_name(pmx_model, 'LeftElbow')
    left_wrist_index = find_bone_index_by_name(pmx_model, 'LeftWrist')
    larm_pos = np.array(list(pmx_model.bones[left_arm_index].position.to_tuple()))
    lelbow_pos = np.array(list(pmx_model.bones[left_elbow_index].position.to_tuple()))
    lwrist_pos = np.array(list(pmx_model.bones[left_wrist_index].position.to_tuple()))
    vec_ew = lwrist_pos - lelbow_pos
    vec_ea = larm_pos - lelbow_pos
    vec_ew = vec_ew / np.linalg.norm(vec_ew)
    vec_ea = vec_ea / np.linalg.norm(vec_ea)
    cos_ew_ea = np.dot(vec_ea, vec_ew)
    if -1 * math.cos(3/180 * 3.14) < cos_ew_ea and cos_ew_ea < 0:
        y_axis = np.cross(vec_ew, vec_ea)
        y_axis = y_axis / np.linalg.norm(y_axis)
        z_axis = np.cross(vec_ea, y_axis)
        z_axis = z_axis / np.linalg.norm(z_axis)
        x_axis = np.cross(z_axis, y_axis)
        x_axis = x_axis / np.linalg.norm(x_axis)
        # pmx_model.bones[left_elbow_index].setFlag(pmx.BONEFLAG_HAS_LOCAL_COORDINATE, True)
        pmx_model.bones[left_elbow_index].local_x_vector = common.Vector3(*x_axis.tolist())
        pmx_model.bones[left_elbow_index].local_z_vector = common.Vector3(*z_axis.tolist())
    '''
    head_index = find_bone_index_by_name(pmx_model, 'Head')
    eyes_bone = pmx.Bone(
                name='両目',
                english_name='Eyes',
                position=common.Vector3(0, 25, 0),
                parent_index=head_index,
                layer=0,
                flag=0
            )
    eyes_bone.setFlag(pmx.BONEFLAG_CAN_ROTATE, True)
    eyes_bone.setFlag(pmx.BONEFLAG_IS_VISIBLE, True)
    eyes_bone.setFlag(pmx.BONEFLAG_CAN_MANIPULATE, True)

    pmx_model.bones.append(eyes_bone)
    eyes_index = find_bone_index_by_name(pmx_model, 'Eyes')
    for LR in 'lr':
        eyeball_index = find_bone_index_by_name(pmx_model, 'bone_eyeball_{}'.format(LR))
        pmx_model.bones[eyeball_index].effect_index = eyes_index
        pmx_model.bones[eyeball_index].effect_factor = 2.2
        pmx_model.bones[eyeball_index].setFlag(pmx.BONEFLAG_IS_EXTERNAL_ROTATION, True)



    '''
    morph_ref_model = pymeshio.pmx.reader.read_from_file('morph_ref')
    pmx_model.morphs = morph_ref_model.morphs
    for morph in pmx_model.morphs:
        for offset in morph.offsets:
            bone_english_name = morph_ref_model.bones[offset.bone_index].english_name
            offset.bone_index = find_bone_index_by_name(pmx_model, bone_english_name)
    '''

    pymeshio.pmx.writer.write_to_file(pmx_model, filename + '_modified.pmx')

def parse_mesh(path):
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

def main():
    opt = get_parser()
    model = parse_mesh(opt.path)
    if opt.mode == 'obj':
        saveobj(model, opt.path)
    elif opt.mode == 'iqe':
        saveiqe(model, opt.path)
    elif opt.mode == 'pmx':
        savepmx(model, opt.path)


if __name__ == '__main__':
    main()
