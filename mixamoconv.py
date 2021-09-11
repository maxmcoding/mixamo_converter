# -*- coding: utf-8 -*-

'''
    Copyright (C) 2017-2018  Antonio 'GNUton' Aloisio
    Copyright (C) 2017-2018  Enzio Probst
  
    Created by Enzio Probst

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from pathlib import Path
import re
import logging
import bpy
from bpy_types import Object
from math import pi
from mathutils import Vector, Quaternion

log = logging.getLogger(__name__)
#log.setLevel('DEBUG')

def remove_namespace(s=''):
    """function for removing all namespaces from strings, objects or even armatrure bones"""

    if type(s) == str:
        i = re.search(r"[:_]", s[::-1])
        if i:
            return s[-(i.start())::]
        else:
            return s

    elif type(s) == Object:
        if s.type == 'ARMATURE':
            for bone in s.data.bones:
                bone.name = remove_namespace(bone.name)
        s.name = remove_namespace(s.name)
        return 1
    return -1


def rename_bones(s='', t='unreal'):
    """function for renaming the armature bones to a target skeleton"""
    unreal = {
        'Root': 'Root',
        'Pelvis': 'Pelvis',
        'spine_01': 'spine_01',
        'spine_02': 'spine_02',
        'spine_03': 'spine_03',
        'clavicle_l': 'clavicle_l',
        'UpperArm_L': 'upperarm_l',
        'lowerarm_l': 'lowerarm_l',
        'Hand_L': 'hand_l',
        'clavicle_r': 'clavicle_r',
        'UpperArm_R': 'upperarm_r',
        'lowerarm_r': 'lowerarm_r',
        'Hand_R': 'hand_r',
        'neck_01': 'neck_01',
        'neck_01': 'neck_01',
        'head': 'head',
        'Thigh_L': 'thigh_l',
        'calf_l': 'calf_l',
        'Foot_L': 'foot_l',
        'Thigh_R': 'thigh_r',
        'calf_r': 'calf_r',
        'Foot_R': 'foot_r',
        'indexFinger_01_l': 'index_01_l',
        'indexFinger_02_l': 'index_02_l',
        'indexFinger_03_l': 'index_03_l',
        'finger_01_l': 'middle_01_l',
        'finger_02_l': 'middle_02_l',
        'finger_03_l': 'middle_03_l',
        'thumb_01_l': 'thumb_01_l',
        'thumb_02_l': 'thumb_02_l',
        'thumb_03_l': 'thumb_03_l',
        'indexFinger_01_r': 'index_01_r',
        'indexFinger_02_r': 'index_02_r',
        'indexFinger_03_r': 'index_03_r',
        'finger_01_r': 'middle_01_r',
        'finger_02_r': 'middle_02_r',
        'finger_03_r': 'middle_03_r',
        'thumb_01_r': 'thumb_01_r',
        'thumb_02_r': 'thumb_02_r',
        'thumb_03_r': 'thumb_03_r',
        'ball_l': 'ball_l',
        'ball_r': 'ball_r'
    }
    schema = {'unreal': unreal }
    if type(s) == str:
        i = schema[t].get(s)
        if i:
            return i
        else:
            log.warning('WARNING %s bone is missing', s)
            return s
    elif type(s) == Object:
        if s.type == 'ARMATURE':
            for bone in s.data.bones:
                bone.name = rename_bones(remove_namespace(bone.name))
        s.name = rename_bones(s.name)
        return 1
    return -1

def key_all_bones(armature, frame_range = (1, 2)):
    """Sets keys for all Bones in frame_range"""
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    for i in range(*frame_range):
        bpy.context.scene.frame_current = i
        bpy.ops.anim.keyframe_insert_menu(type='BUILTIN_KSI_LocRot')
    bpy.ops.object.mode_set(mode='OBJECT')

def apply_restoffset(armature, hipbone, restoffset):
    """function to apply restoffset to rig, should be used if rest-/bindpose does not stand on ground with feet"""
    # apply rest offset to restpose
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.select_all(action='SELECT')
    bpy.ops.transform.translate(value=restoffset, constraint_axis=(False, False, False),
                                orient_type='GLOBAL', mirror=False, use_proportional_edit=False,
                                )
    bpy.ops.object.mode_set(mode='OBJECT')

    # apply restoffset to animation of hip
    restoffset_local = (restoffset[0], restoffset[2], -restoffset[1])
    for axis in range(3):
        fcurve = armature.animation_data.action.fcurves.find("pose.bones[\"" + hipbone.name + "\"].location", index=axis)
        for pi in range(len(fcurve.keyframe_points)):
            fcurve.keyframe_points[pi].co.y -= restoffset_local[axis] / armature.scale.x
    return 1


def apply_kneefix(armature, offset, bonenames=['RightUpLeg', 'LeftUpLeg']):
    """workaround for flickering knees after export (moves joints in restpose by offset, can break animation)"""
    if bpy.context.scene.mixamo.b_unreal_bones:
        bonenames = ["calf_r", "calf_l"]

    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.select_all(action='DESELECT')
    for name in bonenames:
        armature.data.edit_bones[name].select_tail = True
    bpy.ops.transform.translate(value=offset, use_proportional_edit=False, release_confirm=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    return 1

def get_all_quaternion_curves(object):
    """returns all quaternion fcurves of object/bones packed together in a touple per object/bone"""
    fcurves = object.animation_data.action.fcurves
    if fcurves.find('rotation_quaternion'):
        yield (fcurves.find('rotation_quaternion', index=0), fcurves.find('rotation_quaternion', index=1), fcurves.find('rotation_quaternion', index=2), fcurves.find('rotation_quaternion', index=3))
    if object.type == 'ARMATURE':
        for bone in object.pose.bones:
            data_path = 'pose.bones["' + bone.name + '"].rotation_quaternion'
            if fcurves.find(data_path):
                yield (fcurves.find(data_path, index=0), fcurves.find(data_path, index=1),fcurves.find(data_path, index=2),fcurves.find(data_path, index=3))

def quaternion_cleanup(object, prevent_flips=True, prevent_inverts=True):
    """fixes signs in quaternion fcurves swapping from one frame to another"""
    for curves in get_all_quaternion_curves(object):
        start = int(min((curves[i].keyframe_points[0].co.x for i in range(4))))
        end = int(max((curves[i].keyframe_points[-1].co.x for i in range(4))))
        for curve in curves:
            for i in range(start, end):
                curve.keyframe_points.insert(i, curve.evaluate(i)).interpolation = 'LINEAR'
        zipped = list(zip(
            curves[0].keyframe_points,
            curves[1].keyframe_points,
            curves[2].keyframe_points,
            curves[3].keyframe_points))
        for i in range(1, len(zipped)):
            if prevent_flips:
                rot_prev = Quaternion((zipped[i-1][j].co.y for j in range(4)))
                rot_cur = Quaternion((zipped[i][j].co.y for j in range(4)))
                diff = rot_prev.rotation_difference(rot_cur)
                if abs(diff.angle - pi) < 0.5:
                    rot_cur.rotate(Quaternion(diff.axis, pi))
                    for j in range(4):
                        zipped[i][j].co.y = rot_cur[j]
            if prevent_inverts:
                change_amount = 0.0
                for j in range(4):
                    change_amount += abs(zipped[i-1][j].co.y - zipped[i][j].co.y)
                if change_amount > 1.0:
                    for j in range(4):
                        zipped[i][j].co.y *= -1.0

def apply_foot_bone_workaround(armature, bonenames=['RightToeBase', 'LeftToeBase']):
    """workaround for the twisting of the foot bones in some skeletons"""
    if bpy.context.scene.mixamo.b_unreal_bones:
        bonenames = ["ball_r", "ball_l"]

    bpy.ops.object.mode_set(mode='EDIT')
    for name in bonenames:
        armature.data.edit_bones[name].roll = pi

class Status:
    def __init__(self, msg, status_type='default'):
        self.msg = msg
        self.status_type = status_type
    def __str__(self):
        return str(self.msg)

def hip_to_root(armature, use_x=True, use_y=True, use_z=True, on_ground=True, use_rotation=True, scale=1.0, restoffset=(0, 0, 0),
                hipname='', fixbind=True, apply_rotation=True, apply_scale=False, quaternion_clean_pre=True, quaternion_clean_post=True, foot_bone_workaround=False):
    """function to bake hipmotion to RootMotion in MixamoRigs"""

    yield Status("starting hip_to_root")

    root = armature
    root.name = "root"
    root.rotation_mode = 'QUATERNION'
    framerange = root.animation_data.action.frame_range

    for hipname in ('Pelvis', 'mixamorig:Pelvis', 'mixamorig_Pelvis', 'Pelvis', hipname):
        hips = root.pose.bones.get(hipname)
        if hips != None:
            break
    if hips == None:
        log.warning('WARNING I have not found any hip bone for %s and the conversion is stopping here',  root.pose.bones)
        raise ValueError("no Pelvis found")
    else:
        yield Status("Pelvis found")

    key_all_bones(root, (1, 2))

    # Scale by ScaleFactor
    if scale != 1.0:
        for i in range(3):
            fcurve = root.animation_data.action.fcurves.find('scale', index=i)
            if fcurve != None:
                root.animation_data.action.fcurves.remove(fcurve)
        root.scale *= scale
        yield Status("scaling")

    # fix quaternion sign swapping
    if quaternion_clean_pre:
        quaternion_cleanup(root)
        yield Status("quaternion clean pre")

    if foot_bone_workaround:
        apply_foot_bone_workaround(armature)

    # apply restoffset to restpose and correct animation
    apply_restoffset(root, hips, restoffset)
    yield Status("restoffset")

    hiplocation_world = root.matrix_local @ hips.bone.head
    z_offset = hiplocation_world[2]

    # Create helper to bake the root motion
    rootbaker = bpy.data.objects.new(name="rootbaker", object_data=None)
    rootbaker.rotation_mode = 'QUATERNION'

    if use_z:
        print("using z")
        c_rootbaker_copy_z_loc = rootbaker.constraints.new(type='COPY_LOCATION')
        c_rootbaker_copy_z_loc.name = "Copy Z_Loc"
        c_rootbaker_copy_z_loc.target = root
        c_rootbaker_copy_z_loc.subtarget = hips.name
        c_rootbaker_copy_z_loc.use_x = False
        c_rootbaker_copy_z_loc.use_y = False
        c_rootbaker_copy_z_loc.use_z = True
        c_rootbaker_copy_z_loc.use_offset = True
        if on_ground:
            print("using on ground")
            rootbaker.location[2] = -z_offset
            c_on_ground = rootbaker.constraints.new(type='LIMIT_LOCATION')
            c_on_ground.name = "On Ground"
            c_on_ground.use_min_z = True


    c_rootbaker_copy_loc = rootbaker.constraints.new(type='COPY_LOCATION')
    c_rootbaker_copy_loc.use_x = use_x
    c_rootbaker_copy_loc.use_y = use_y
    c_rootbaker_copy_loc.use_z = False
    c_rootbaker_copy_loc.target = root
    c_rootbaker_copy_loc.subtarget = hips.name

    c_rootbaker_copy_rot = rootbaker.constraints.new(type='COPY_ROTATION')
    c_rootbaker_copy_rot.target = root
    c_rootbaker_copy_rot.subtarget = hips.name
    c_rootbaker_copy_rot.use_y = False
    c_rootbaker_copy_rot.use_x = False
    c_rootbaker_copy_rot.use_z = use_rotation
    bpy.context.scene.collection.objects.link(rootbaker)
    yield Status("rootbaker created")

    bpy.ops.object.select_all(action='DESELECT')
    rootbaker.select_set(True)
    bpy.context.view_layer.objects.active = rootbaker

    bpy.ops.nla.bake(frame_start=framerange[0], frame_end=framerange[1], step=1, only_selected=True, visual_keying=True,
                     clear_constraints=True, clear_parents=False, use_current_action=False, bake_types={'OBJECT'})
    yield Status("rootbaker baked")
    quaternion_cleanup(rootbaker)
    yield Status("rootbaker quat_cleanup")

    # Create helper to bake hipmotion in Worldspace
    hipsbaker = bpy.data.objects.new(name="hipsbaker", object_data=None)
    hipsbaker.rotation_mode = 'QUATERNION'

    c_hipsbaker_copy_loc = hipsbaker.constraints.new(type='COPY_LOCATION')
    c_hipsbaker_copy_loc.target = root
    c_hipsbaker_copy_loc.subtarget = hips.name

    c_hipsbaker_copy_rot = hipsbaker.constraints.new(type='COPY_ROTATION')
    c_hipsbaker_copy_rot.target = root
    c_hipsbaker_copy_rot.subtarget = hips.name
    bpy.context.scene.collection.objects.link(hipsbaker)
    yield Status("hipsbaker created")

    bpy.ops.object.select_all(action='DESELECT')
    hipsbaker.select_set(True)
    bpy.context.view_layer.objects.active = hipsbaker

    bpy.ops.nla.bake(frame_start=framerange[0], frame_end=framerange[1], step=1, only_selected=True, visual_keying=True,
                     clear_constraints=True, clear_parents=False, use_current_action=False, bake_types={'OBJECT'})
    yield Status("hipsbaker baked")
    quaternion_cleanup(hipsbaker)
    yield Status("hipsbaker quatClenaup")

    # select armature
    bpy.ops.object.select_all(action='DESELECT')
    root.select_set(True)
    bpy.context.view_layer.objects.active = root

    if apply_rotation or apply_scale:
        bpy.ops.object.transform_apply(location=False, rotation=apply_rotation, scale=apply_scale)
        yield Status("apply transform")

    # Bake Root motion to Armature (root)
    c_root_copy_loc = root.constraints.new(type='COPY_LOCATION')
    c_root_copy_loc.target = rootbaker

    c_root_copy_rot = root.constraints.new(type='COPY_ROTATION')
    c_root_copy_rot.target = rootbaker
    c_root_copy_rot.use_offset = True
    yield Status("root constrained to rootbaker")

    bpy.ops.nla.bake(frame_start=framerange[0], frame_end=framerange[1], step=1, only_selected=True, visual_keying=True,
                     clear_constraints=True, clear_parents=False, use_current_action=True, bake_types={'OBJECT'})

    yield Status("rootbaker baked back")
    quaternion_cleanup(root)
    yield Status("root quaternion cleanup")
    hipsbaker.select_set(False)

    bpy.ops.object.mode_set(mode='POSE')
    hips.bone.select = True
    root.data.bones.active = hips.bone

    c_hips_copy_loc = hips.constraints.new(type='COPY_LOCATION')
    c_hips_copy_loc.target = hipsbaker
    c_hips_copy_rot = hips.constraints.new(type='COPY_ROTATION')
    c_hips_copy_rot.target = hipsbaker
    yield Status("hips constrained to hipsbaker")

    bpy.ops.nla.bake(frame_start=framerange[0], frame_end=framerange[1], step=1, only_selected=True, visual_keying=True,
                     clear_constraints=True, clear_parents=False, use_current_action=True, bake_types={'POSE'})
    bpy.ops.object.mode_set(mode='OBJECT')
    yield Status("hipsbaker baked back")

    if quaternion_clean_post:
        quaternion_cleanup(root)
        yield Status("root quaternion cleanup")

    # Delete helpers
    bpy.data.actions.remove(hipsbaker.animation_data.action)
    bpy.data.actions.remove(rootbaker.animation_data.action)
    bpy.data.objects.remove(hipsbaker)
    bpy.data.objects.remove(rootbaker)

    yield Status("bakers deleted")

    # bind armature to dummy mesh if it doesn't have any
    if fixbind:
        bindmesh = None
        for child in root.children:
            for mod in child.modifiers:
                if mod.type == 'ARMATURE':
                    if mod.object == root:
                        bindmesh = child
                        break
        if bindmesh is None:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.mesh.primitive_plane_add(size=1, align='WORLD', enter_editmode=False, location=(0, 0, 0))
            binddummy = bpy.context.object
            binddummy.name = 'binddummy'
            root.select_set(True)
            bpy.context.view_layer.objects.active = root
            bpy.ops.object.parent_set(type='ARMATURE')
            yield Status("binddummy created")
        elif apply_rotation or apply_scale:
            bindmesh.select_set(True)
            bpy.context.view_layer.objects.active = bindmesh
            bpy.ops.object.transform_apply(location=False, rotation=apply_rotation, scale=apply_scale)
            yield Status("apply transform to bindmesh")
    return 1


def batch_hip_to_root(source_dir, dest_dir, use_x=True, use_y=True, use_z=True, on_ground=True, use_rotation=True, scale=1.0,
                      restoffset=(0, 0, 0), hipname='', fixbind=True, apply_rotation=True, apply_scale=False,
                      b_remove_namespace=True, b_unreal_bones=False, add_leaf_bones=False, knee_offset=(0, 0, 0), ignore_leaf_bones=True, automatic_bone_orientation=True, quaternion_clean_pre=True, quaternion_clean_post=True, foot_bone_workaround=False):
    """Batch Convert MixamoRigs"""
    
    source_dir = Path(source_dir)
    dest_dir = Path(dest_dir)

    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 1

    numfiles = 0
    for file in source_dir.iterdir():
        if not file.is_file():
            continue
        file_ext = file.suffix
        file_loader = {
            ".fbx": lambda filename: bpy.ops.import_scene.fbx(
                filepath=str(filename), axis_forward='-Z',
                axis_up='Y', directory="",
                filter_glob="*.fbx", ui_tab='MAIN',
                use_manual_orientation=False, global_scale=1.0,
                bake_space_transform=False,
                use_custom_normals=True,
                use_image_search=True,
                use_alpha_decals=False, decal_offset=0.0,
                use_anim=True, anim_offset=1.0,
                use_custom_props=True,
                use_custom_props_enum_as_string=True,
                ignore_leaf_bones=ignore_leaf_bones,
                force_connect_children=False,
                automatic_bone_orientation=automatic_bone_orientation,
                primary_bone_axis='Y',
                secondary_bone_axis='X',
                use_prepost_rot=True),
            ".dae": lambda filename: bpy.ops.wm.collada_import(
                filepath=str(filename), filter_blender=False,
                filter_backup=False, filter_image=False,
                filter_movie=False, filter_python=False,
                filter_font=False, filter_sound=False,
                filter_text=False, filter_btx=False,
                filter_collada=True, filter_alembic=False,
                filter_folder=True, filter_blenlib=False,
                filemode=8, display_type='DEFAULT',
                sort_method='FILE_SORT_ALPHA',
                import_units=False, fix_orientation=True,
                find_chains=True, auto_connect=True,
                min_chain_length=0)
        }
        if not file_ext in file_loader:
            continue
        numfiles += 1
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=True)

        # remove all datablocks
        for mesh in bpy.data.meshes:
            bpy.data.meshes.remove(mesh, do_unlink=True)
        for material in bpy.data.materials:
            bpy.data.materials.remove(material, do_unlink=True)
        for action in bpy.data.actions:
            bpy.data.actions.remove(action, do_unlink=True)

        # import FBX
        file_loader[file_ext](file)

        # namespace removal
        if b_remove_namespace:
            for obj in bpy.context.selected_objects:
                remove_namespace(obj)
        # namespace removal
        elif b_unreal_bones:
            for obj in bpy.context.selected_objects:
                rename_bones(obj, 'unreal')

        def getArmature(objects):
            for a in objects:
                if a.type == 'ARMATURE':
                    return a
            raise TypeError("No Armature found")

        armature = getArmature(bpy.context.selected_objects)

        # do hip to Root conversion
        try:
            for step in hip_to_root(armature, use_x=use_x, use_y=use_y, use_z=use_z, on_ground=on_ground, use_rotation=use_rotation, scale=scale,
                        restoffset=restoffset, hipname=hipname, fixbind=fixbind, apply_rotation=apply_rotation,
                        apply_scale=apply_scale, quaternion_clean_pre=quaternion_clean_pre, quaternion_clean_post=quaternion_clean_post, foot_bone_workaround=foot_bone_workaround):
                #DEBUG log.error(str(step))
                pass
        except Exception as e:
            log.error("ERROR hip_to_root raised %s when processing %s" % (str(e), file.name))
            return -1


        if (Vector(knee_offset).length > 0.0):
            apply_kneefix(armature, knee_offset,
                          bonenames=bpy.context.scene.mixamo.knee_bones.split(','))

        # remove newly created orphan actions
        for action in bpy.data.actions:
            if action != armature.animation_data.action:
                bpy.data.actions.remove(action, do_unlink=True)

        # store file to disk
        output_file = dest_dir.joinpath(file.stem + ".fbx")
        bpy.ops.export_scene.fbx(filepath=str(output_file),
                                 use_selection=False,
                                 apply_unit_scale=False,
                                 add_leaf_bones=add_leaf_bones,
                                 axis_forward='-Z',
                                 axis_up='Y',
                                 mesh_smooth_type='FACE')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
    return numfiles


if __name__ == "__main__":
    print("mixamoconv Hello.")
