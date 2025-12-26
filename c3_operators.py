import bpy
import bmesh
import os
import math
from mathutils import Vector, Matrix
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty
from . import c3_phy
from . import c3_motion
from . import c3_common
from . import c3_main

class IMPORT_OT_c3_model(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.c3_model"
    bl_label = "Import .C3 Model"
    bl_options = {'REGISTER', 'UNDO'}
    
    filename_ext = ".c3"
    filter_glob: StringProperty(default="*.c3", options={'HIDDEN'})
    
    # Add new scene option
    use_debugpy: BoolProperty(
        name="debugpy",
        description="use debugpy to debug code",
        default=False
    )
    create_new_scene: BoolProperty(
        name="New Scene",
        description="Import into a new scene",
        default=True
    )

    def execute(self, context):
        # Start debug server if not already connected
        if self.use_debugpy:
            import debugpy
            if not debugpy.is_client_connected():
               debugpy.listen(("127.0.0.1", 5678))
            print("⏳ Waiting for debugger attach on port 5678...")
            debugpy.wait_for_client()
        
        # Create new scene if requested
        if self.create_new_scene:
            filename = os.path.splitext(os.path.basename(self.filepath))[0]
            scene_name = f"C3_{filename}"
            new_scene = bpy.data.scenes.new(scene_name)
            context.window.scene = new_scene
            context = bpy.context
        
        return self.import_c3_model(context, self.filepath)
    
    def import_c3_model(self, context, filepath):
        filename = os.path.splitext(os.path.basename(self.filepath))[0]
        # Create a parent collection for all imports from this file
        file_collection = bpy.data.collections.new(filename)
        context.scene.collection.children.link(file_collection)
        
        c3_loader = c3_phy.C3Phy()        
        if not c3_loader.C3_Load(filepath):
            self.report({'ERROR'}, "Failed to load C3 file")
            return {'CANCELLED'}
        
        motionpath = filepath
        motion_loader = c3_motion.C3Motion()
        motion_loaded = motion_loader.C3_Load(motionpath)
        
        for phy_idx in range(c3_loader.m_dwPhyNum):
            lpPhy = c3_loader.m_phy[phy_idx]
            
            if lpPhy is None:
                continue
            
            # Store the original phy index
            lpPhy.phy_index = phy_idx
            
            # Create a new collection for each m_phy
            collection_name = lpPhy.lpName if lpPhy.lpName else f"C3_Phy_{phy_idx}"
            new_collection = bpy.data.collections.new(collection_name)
            file_collection.children.link(new_collection)
            
            if motion_loaded and phy_idx < motion_loader.m_dwMotionNum:
                lpPhy.lpMotion = motion_loader.m_motion[phy_idx]
            else:
                lpPhy.lpMotion = c3_motion.C3Motion()
                lpPhy.lpMotion.dwBoneCount = 1
                lpPhy.lpMotion.dwFrames = 1
                lpPhy.lpMotion.matrix = [Matrix.Identity(4)]
                lpPhy.lpMotion.nFrame = 0
            
            mesh_name = lpPhy.lpName if lpPhy.lpName else f"C3_Mesh_{phy_idx}"
            mesh = bpy.data.meshes.new(mesh_name)
            obj = bpy.data.objects.new(mesh_name, mesh)
            
            # Store phy_index and source file path as custom properties on the object
            obj["c3_phy_index"] = phy_idx
            obj["c3_motion_index"] = phy_idx
            obj["c3_phy_file"] = filepath
            obj["c3_motion_file"] = filepath

            # Link object to the new collection instead of scene collection
            new_collection.objects.link(obj)
            context.view_layer.objects.active = obj
            obj.select_set(True)
            obj.rotation_euler = (math.radians(180), 0, math.radians(180))

            if lpPhy.lpMotion:
                c3_phy.C3Phy.Phy_Calculate(lpPhy)
            
            vertices = []
            for v in range(lpPhy.dwNVecCount + lpPhy.dwAVecCount):
                if lpPhy.lpMotion:
                    pos = lpPhy.outputVertices[v].Position
                else:
                    pos = lpPhy.lpVB[v].pos[0]
                vertices.append((pos.x, pos.y, pos.z))
            
            faces = []
            for i in range(0, len(lpPhy.lpIB), 3):
                faces.append((lpPhy.lpIB[i], lpPhy.lpIB[i+1], lpPhy.lpIB[i+2]))
            
            mesh.from_pydata(vertices, [], faces)
            mesh.update()

            if lpPhy.lpVB:
                uv_layer = mesh.uv_layers.new(name="UVMap")
                for poly in mesh.polygons:
                    for loop_idx in poly.loop_indices:
                        vert_idx = mesh.loops[loop_idx].vertex_index
                        if vert_idx < len(lpPhy.lpVB):
                            uv_layer.data[loop_idx].uv = (lpPhy.lpVB[vert_idx].TexCoord.x, 1-lpPhy.lpVB[vert_idx].TexCoord.y)
            
            base_path = os.path.dirname(filepath)
            base_name = os.path.splitext(os.path.basename(filepath))[0]
            
            tex_path = None
            for ext in ['.dds', '.tga', '.png', '.jpg']:
                test_path = os.path.join(base_path, base_name + ext)
                if os.path.exists(test_path):
                    tex_path = test_path
                    break
            
            if tex_path:
                self.apply_texture(obj, tex_path)
            
                # Bake mesh to shape keys for animation
            if lpPhy.lpMotion and lpPhy.lpMotion.dwFrames > 0:
               self.bake_mesh_to_shape_keys(obj, lpPhy)
           
            # if lpPhy.lpMotion and lpPhy.lpMotion.dwBoneCount > 0:
            #     armature = self.create_armature(context, lpPhy, mesh_name, new_collection)
            #     if armature:
            #         # Store phy_index on armature as well
            #         armature["c3_phy_index"] = phy_idx
            #         self.skin_mesh_to_armature(obj, armature, lpPhy)
            #         self.create_animation(armature, lpPhy)
                
        self.set_texture_view(context=context)     
        #Exclude from active view layer (strongest "disable")        
        layer_coll = context.view_layer.layer_collection.children.get(filename)
        if layer_coll:
            layer_coll.exclude = True
            for child_name, child_coll in layer_coll.children.items():
                if child_name.startswith("v_body"):
                    child_coll.exclude = False
                    # Deselect everything first
                    bpy.ops.object.select_all(action='DESELECT')
                    # Select only mesh objects in this collection
                    for obj in child_coll.collection.objects:
                        if obj.type == 'MESH':
                            obj.select_set(True)
                            # Optionally set one as active
                            bpy.context.view_layer.objects.active = obj



        bpy.ops.screen.animation_play()
                
        self.report({'INFO'}, f"Imported C3 model: {filepath}")
        return {'FINISHED'}
        
    def set_texture_view(self, context=None):
        ctx = context or bpy.context
        for area in ctx.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'MATERIAL'
                        space.region_3d.view_distance = 500
                        space.region_3d.view_perspective = 'ORTHO'                        
        
    def apply_texture(self, obj, tex_path):
        mat = bpy.data.materials.new(name="C3_Material")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        
        tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex_image.image = bpy.data.images.load(tex_path)
        
        mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
        
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    
    def create_armature(self, context, lpPhy, mesh_name, collection):
        armature_data = bpy.data.armatures.new(f"{mesh_name}_Armature")
        armature_obj = bpy.data.objects.new(f"{mesh_name}_Armature", armature_data)
        
        # Link armature to the same collection as the mesh
        collection.objects.link(armature_obj)
        
        context.view_layer.objects.active = armature_obj
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Get bone positions from first keyframe if available
        bone_positions = []
        if lpPhy.lpMotion and lpPhy.lpMotion.dwKeyFrames > 0:
            first_keyframe = lpPhy.lpMotion.lpKeyFrame[0]
            for b in range(lpPhy.lpMotion.dwBoneCount):
                matrix = first_keyframe.matrix[b]
                # Extract position from matrix
                bone_x = matrix[0][3]
                bone_y = matrix[1][3]
                bone_z = matrix[2][3]
                bone_positions.append((bone_x, bone_y, bone_z))
        
        for b in range(lpPhy.lpMotion.dwBoneCount):
            bone = armature_data.edit_bones.new(f"Bone_{b}")
            
            if bone_positions:
                bone_x, bone_y, bone_z = bone_positions[b]
                bone.head = (bone_x, bone_y, bone_z)
                bone.tail = (bone_x, bone_y + 10.0, bone_z)
            else:
                bone.head = (0, 0, b * 0.1)
                bone.tail = (0, 0, b * 0.1 + 0.1)
        
        bpy.ops.object.mode_set(mode='OBJECT')
        
        return armature_obj
    
    def skin_mesh_to_armature(self, mesh_obj, armature_obj, lpPhy):
        modifier = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
        modifier.object = armature_obj
        
        # Create vertex groups for all bones
        for b in range(lpPhy.lpMotion.dwBoneCount):
            bone_name = f"Bone_{b}"
            mesh_obj.vertex_groups.new(name=bone_name)
        
        # Assign weights
        for v in range(len(lpPhy.lpVB)):
            for l in range(c3_phy._BONE_MAX_):
                bone_index = lpPhy.lpVB[v].index[l]
                weight = lpPhy.lpVB[v].weight[l]
                
                if weight > 0 and bone_index < lpPhy.lpMotion.dwBoneCount:
                    bone_name = f"Bone_{bone_index}"
                    vgroup = mesh_obj.vertex_groups.get(bone_name)
                    if vgroup:
                        vgroup.add([v], weight, 'REPLACE')
    
    def create_animation(self, armature_obj, lpPhy):
        if not lpPhy.lpMotion or lpPhy.lpMotion.dwKeyFrames == 0:
            return
        
        bpy.context.view_layer.objects.active = armature_obj
        bpy.ops.object.mode_set(mode='POSE')
        
        # Store last rotation for quaternion sign correction
        last_rotations = {}
        
        for b in range(lpPhy.lpMotion.dwBoneCount):
            bone_name = f"Bone_{b}"
            pose_bone = armature_obj.pose.bones.get(bone_name)
            
            if pose_bone:
                for kf_idx in range(lpPhy.lpMotion.dwKeyFrames):
                    keyframe = lpPhy.lpMotion.lpKeyFrame[kf_idx]
                    frame = int(keyframe.pos)
                    
                    matrix = keyframe.matrix[b]
                    
                    # Extract rotation quaternion from matrix
                    rotation_quat = matrix.to_quaternion()
                    
                    # Quaternion sign correction to prevent flipping
                    if kf_idx > 0 and bone_name in last_rotations:
                        last_quat = last_rotations[bone_name]
                        
                        # Calculate distance between current and last quaternion
                        v1 = Vector((rotation_quat.w, rotation_quat.x, rotation_quat.y, rotation_quat.z))
                        v2 = Vector((last_quat.w, last_quat.x, last_quat.y, last_quat.z))
                        
                        # Check if negated version is closer
                        dist_normal = (v2 - v1).length
                        dist_negated = (v2 + v1).length
                        
                        if dist_negated < dist_normal:
                            rotation_quat.negate()
                    
                    # Store current rotation for next frame
                    last_rotations[bone_name] = rotation_quat.copy()
                    
                    pose_bone.matrix = matrix
                    pose_bone.keyframe_insert(data_path="location", frame=frame)
                    pose_bone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                    pose_bone.keyframe_insert(data_path="scale", frame=frame)
        
        bpy.ops.object.mode_set(mode='OBJECT')        
        # Set the scene end frame to the maximum frame from the motion
        max_frame = lpPhy.lpMotion.dwFrames - 1
        bpy.context.scene.frame_end = max_frame
    
    def bake_mesh_to_shape_keys(self, obj, lpPhy):
        if not lpPhy.lpMotion or lpPhy.lpMotion.dwFrames == 0:
            return        
        scene = bpy.context.scene

        # Ensure Basis exists
        if not obj.data.shape_keys:
            obj.shape_key_add(name="Basis")

        for frame in range(lpPhy.lpMotion.dwFrames+1):
            scene.frame_set(frame)

            # Create shape key for this frame
            sk = obj.shape_key_add(name=f"Frame_{frame}", from_mix=False)

            c3_phy.C3Phy.Phy_SetFrame(lpPhy, frame)
            c3_phy.C3Phy.Phy_Calculate(lpPhy)

            for i, v in enumerate(lpPhy.outputVertices):
               sk.data[i].co = v.Position

            # Keyframe shape key value
            sk.value = 0.0
            sk.keyframe_insert(data_path="value", frame=frame - 1)

            sk.value = 1.0
            sk.keyframe_insert(data_path="value", frame=frame)

            sk.value = 0.0
            sk.keyframe_insert(data_path="value", frame=frame + 1)
            
        max_frame = lpPhy.lpMotion.dwFrames - 1
        bpy.context.scene.frame_end = max_frame
        # bpy.context.scene.render.fps = 10
        # bpy.context.scene.render.fps_base = 1.0

class IMPORT_OT_c3_texture(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.c3_texture"
    bl_label = "Import Texture"
    bl_options = {'REGISTER', 'UNDO'}
    
    filename_ext = ".dds;.tga;.png;.jpg"
    filter_glob: StringProperty(default="*.dds;*.tga;*.png;*.jpg", options={'HIDDEN'})
    
    def execute(self, context):
        obj = context.active_object
        
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "No mesh object selected")
            return {'CANCELLED'}
        
        mat = bpy.data.materials.new(name="C3_Custom_Material")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        
        tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex_image.image = bpy.data.images.load(self.filepath)
        
        mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
        
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
        
        self.report({'INFO'}, f"Applied texture: {self.filepath}")
        return {'FINISHED'}

class IMPORT_OT_c3_animation(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.c3_animation"
    bl_label = "Import Animation"
    bl_options = {'REGISTER', 'UNDO'}
    
    filename_ext = ".c3"
    filter_glob: StringProperty(default="*.c3", options={'HIDDEN'})
    
    use_stored_file: BoolProperty(
        name="Use Original File",
        description="Use the original C3 file from model import instead of selecting a new one",
        default=True
    )
    
    def execute(self, context):
        obj = context.active_object
        
        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "No mesh object selected")
            return {'CANCELLED'}
        
        # Try to get stored file path if option is enabled
        model_file = self.filepath
        animation_file = self.filepath
        if self.use_stored_file and "c3_phy_file" in obj:
            model_file = obj["c3_phy_file"]
            self.report({'INFO'}, f"Using stored C3 file: {model_file}")
        
        # Get phy_index from object
        phy_index = obj.get("c3_phy_index", 0)
        motion_index = obj.get("c3_motion_index", 0)
        
        obj["c3_motion_file"] = model_file

        # Load the C3 file
        c3_loader = c3_phy.C3Phy()        
        if not c3_loader.C3_Load(model_file):
            self.report({'ERROR'}, "Failed to load C3 file")
            return {'CANCELLED'}
        
        motion_loader = c3_motion.C3Motion()
        if not motion_loader.C3_Load(animation_file):
            self.report({'ERROR'}, "Failed to load animation from C3 file")
            return {'CANCELLED'}
        
        if motion_loader.m_dwMotionNum == 0:
            self.report({'ERROR'}, "No animation data found in C3 file")
            return {'CANCELLED'}
        
        # Validate phy_index
        if phy_index >= c3_loader.m_dwPhyNum:
            self.report({'ERROR'}, f"Invalid phy_index {phy_index}, file has {c3_loader.m_dwPhyNum} phys")
            return {'CANCELLED'}
        
        if motion_index >= motion_loader.m_dwMotionNum:
            self.report({'ERROR'}, f"Invalid motion_index {motion_index}, file has {motion_loader.m_dwMotionNum} motions")
            return {'CANCELLED'}      
        
        # Get the corresponding phy and motion
        lpPhy = c3_loader.m_phy[phy_index]
        if lpPhy is None:
            self.report({'ERROR'}, f"Phy at index {phy_index} is None")
            return {'CANCELLED'}
        
        if phy_index < motion_loader.m_dwMotionNum:
            lpPhy.lpMotion = motion_loader.m_motion[motion_index]
        else:
            self.report({'ERROR'}, f"No motion data for motion index {motion_index}")
            return {'CANCELLED'}

        if lpPhy.lpMotion:
            c3_phy.C3Phy.Phy_Calculate(lpPhy)
        
        # Clear existing shape keys except Basis
        if obj.data.shape_keys:
            # Remove all shape keys except Basis
            shape_keys_to_remove = [sk for sk in obj.data.shape_keys.key_blocks if sk.name != "Basis"]
            for sk in shape_keys_to_remove:
                obj.shape_key_remove(sk)
        
        # Bake new animation to shape keys
        if lpPhy.lpMotion and lpPhy.lpMotion.dwFrames > 0:
            self.bake_mesh_to_shape_keys(obj, lpPhy)
            self.report({'INFO'}, f"Imported animation with {lpPhy.lpMotion.dwFrames} frames")
        else:
            self.report({'WARNING'}, "No animation frames found")
            return {'CANCELLED'}
        
        return {'FINISHED'}
    
    def bake_mesh_to_shape_keys(self, obj, lpPhy):
        if not lpPhy.lpMotion or lpPhy.lpMotion.dwFrames == 0:
            return        
        scene = bpy.context.scene

        # Ensure Basis exists
        if not obj.data.shape_keys:
            obj.shape_key_add(name="Basis")

        for frame in range(lpPhy.lpMotion.dwFrames+1):
            scene.frame_set(frame)

            # Create shape key for this frame
            sk = obj.shape_key_add(name=f"Frame_{frame}", from_mix=False)

            c3_phy.C3Phy.Phy_SetFrame(lpPhy, frame)
            c3_phy.C3Phy.Phy_Calculate(lpPhy)

            for i, v in enumerate(lpPhy.outputVertices):
               sk.data[i].co = v.Position

            # Keyframe shape key value
            sk.value = 0.0
            sk.keyframe_insert(data_path="value", frame=frame - 1)

            sk.value = 1.0
            sk.keyframe_insert(data_path="value", frame=frame)

            sk.value = 0.0
            sk.keyframe_insert(data_path="value", frame=frame + 1)
            
        max_frame = lpPhy.lpMotion.dwFrames - 1
        bpy.context.scene.frame_end = max_frame

class IMPORT_OT_c3_parts(bpy.types.Operator, ImportHelper):
    """Load C3 part to replace existing mesh by name"""
    bl_idname = "import_scene.c3_parts"
    bl_label = "Load C3 Parts"
    bl_options = {'REGISTER', 'UNDO'}
    
    filename_ext = ".c3"
    filter_glob: StringProperty(default="*.c3", options={'HIDDEN'})
    
    load_texture: BoolProperty(
        name="Load Texture",
        description="Load texture file with same base name",
        default=True
    )
    
    def execute(self, context):
        # Check if a mesh is selected
        if not context.active_object or context.active_object.type != 'MESH':
            self.report({'ERROR'}, "No mesh object selected")
            return {'CANCELLED'}
        
        target_obj = context.active_object
        mesh_name = target_obj.name
        
        # Get the active scene's collections
        scene = context.scene
        
        # Load the new C3 file
        c3_loader = c3_phy.C3Phy()        
        if not c3_loader.C3_Load(self.filepath):
            self.report({'ERROR'}, "Failed to load C3 file")
            return {'CANCELLED'}
        
        if c3_loader.m_dwPhyNum == 0:
            self.report({'ERROR'}, "No physics data found in C3 file")
            return {'CANCELLED'}
        
        # Get the target phy (first one from loaded file)
        target_phy = c3_loader.m_phy[0]
        if target_phy is None:
            self.report({'ERROR'}, "Target phy is None")
            return {'CANCELLED'}
        
        # Store the original motion data and properties
        stored_motion = None
        stored_phy_index = target_obj.get("c3_phy_index", 0)
        stored_motion_index = target_obj.get("c3_motion_index", 0)
        stored_source_file = target_obj.get("c3_phy_file", "")
        stored_motion_file = target_obj.get("c3_motion_file", "")
        target_collection = None
        
        # Find which collection the object belongs to
        for collection in bpy.data.collections:
            if target_obj.name in collection.objects:
                target_collection = collection
                break
        
        # Try to get motion from original file if stored
        if stored_motion_file:
            original_loader = c3_motion.C3Motion()
            if original_loader.C3_Load(stored_motion_file):
                if stored_motion_index < original_loader.m_dwMotionNum:
                    stored_motion = original_loader.m_motion[stored_motion_index]                    
        
        # Create new mesh data
        new_mesh_name = mesh_name
        new_mesh = bpy.data.meshes.new(new_mesh_name)
        
        # Assign the stored motion to target_phy if available
        if stored_motion:
            target_phy.lpMotion = stored_motion
        else:
            # Create default motion
            target_phy.lpMotion = c3_motion.C3Motion()
            target_phy.lpMotion.dwBoneCount = 1
            target_phy.lpMotion.dwFrames = 1
            target_phy.lpMotion.matrix = [Matrix.Identity(4)]
            target_phy.lpMotion.nFrame = 0
        
        # Calculate vertices with motion
        if target_phy.lpMotion:
            c3_phy.C3Phy.Phy_Calculate(target_phy)
        
        # Build vertex list
        vertices = []
        for v in range(target_phy.dwNVecCount + target_phy.dwAVecCount):
            if target_phy.lpMotion:
                pos = target_phy.outputVertices[v].Position
            else:
                pos = target_phy.lpVB[v].pos[0]
            vertices.append((pos.x, pos.y, pos.z))
        
        # Build face list
        faces = []
        for i in range(0, len(target_phy.lpIB), 3):
            faces.append((target_phy.lpIB[i], target_phy.lpIB[i+1], target_phy.lpIB[i+2]))
        
        # Create mesh
        new_mesh.from_pydata(vertices, [], faces)
        new_mesh.update()
        
        # Add UV coordinates
        if target_phy.lpVB:
            uv_layer = new_mesh.uv_layers.new(name="UVMap")
            for poly in new_mesh.polygons:
                for loop_idx in poly.loop_indices:
                    vert_idx = new_mesh.loops[loop_idx].vertex_index
                    if vert_idx < len(target_phy.lpVB):
                        uv_layer.data[loop_idx].uv = (
                            target_phy.lpVB[vert_idx].TexCoord.x, 
                            1 - target_phy.lpVB[vert_idx].TexCoord.y
                        )
        
        # Replace the mesh data
        old_mesh = target_obj.data
        target_obj.data = new_mesh
        
        # Remove old mesh if no other objects use it
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
        
        # Maintain object properties
        target_obj["c3_phy_index"] = 0
        target_obj["c3_motion_index"] = stored_motion_index
        if stored_source_file:
            target_obj["c3_phy_file"] = self.filepath
        if stored_motion_file:
            target_obj["c3_motion_file"] = stored_motion_file
        
        # Load and apply texture if requested
        if self.load_texture:
            base_path = os.path.dirname(self.filepath)
            base_name = os.path.splitext(os.path.basename(self.filepath))[0]
            
            tex_path = None
            for ext in ['.dds', '.tga', '.png', '.jpg']:
                test_path = os.path.join(base_path, base_name + ext)
                if os.path.exists(test_path):
                    tex_path = test_path
                    break
            
            if tex_path:
                self.apply_texture(target_obj, tex_path)
                self.report({'INFO'}, f"Applied texture: {tex_path}")
        
        # # Rebake animation if motion exists
        # if stored_motion and stored_motion.dwFrames > 0:
        #     # Clear existing shape keys
        #     if target_obj.data.shape_keys:
        #         shape_keys_to_remove = [sk for sk in target_obj.data.shape_keys.key_blocks if sk.name != "Basis"]
        #         for sk in shape_keys_to_remove:
        #             target_obj.shape_key_remove(sk)
            
        #     # Bake animation to shape keys
        #     self.bake_mesh_to_shape_keys(target_obj, target_phy)
        #     self.report({'INFO'}, f"Rebaked animation with {stored_motion.dwFrames} frames")
        
        self.report({'INFO'}, f"Replaced mesh part: {mesh_name}")
        return {'FINISHED'}
    
    def apply_texture(self, obj, tex_path):
        """Apply texture to the object"""
        mat = bpy.data.materials.new(name="C3_Part_Material")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        
        tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex_image.image = bpy.data.images.load(tex_path)
        
        mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
        
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    
    def bake_mesh_to_shape_keys(self, obj, lpPhy):
        """Bake animation frames to shape keys"""
        if not lpPhy.lpMotion or lpPhy.lpMotion.dwFrames == 0:
            return        
        scene = bpy.context.scene

        # Ensure Basis exists
        if not obj.data.shape_keys:
            obj.shape_key_add(name="Basis")

        for frame in range(lpPhy.lpMotion.dwFrames + 1):
            scene.frame_set(frame)

            # Create shape key for this frame
            sk = obj.shape_key_add(name=f"Frame_{frame}", from_mix=False)

            c3_phy.C3Phy.Phy_SetFrame(lpPhy, frame)
            c3_phy.C3Phy.Phy_Calculate(lpPhy)

            for i, v in enumerate(lpPhy.outputVertices):
                sk.data[i].co = v.Position

            # Keyframe shape key value
            sk.value = 0.0
            sk.keyframe_insert(data_path="value", frame=frame - 1)

            sk.value = 1.0
            sk.keyframe_insert(data_path="value", frame=frame)

            sk.value = 0.0
            sk.keyframe_insert(data_path="value", frame=frame + 1)
        
        max_frame = lpPhy.lpMotion.dwFrames - 1
        bpy.context.scene.frame_end = max_frame

def register():
    bpy.utils.register_class(IMPORT_OT_c3_model)
    bpy.utils.register_class(IMPORT_OT_c3_texture)
    bpy.utils.register_class(IMPORT_OT_c3_animation)
    bpy.utils.register_class(IMPORT_OT_c3_parts)

def unregister():
    bpy.utils.unregister_class(IMPORT_OT_c3_parts)
    bpy.utils.unregister_class(IMPORT_OT_c3_animation)
    bpy.utils.unregister_class(IMPORT_OT_c3_texture)
    bpy.utils.unregister_class(IMPORT_OT_c3_model)