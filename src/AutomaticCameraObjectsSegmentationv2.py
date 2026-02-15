bl_info = {
    "name": "Automatic Camera Segmentation",
    "description": "Addon per generare dataset con rotazioni e posizioni casuali della camera e segmentazione oggetti, con parametri Z, random Y, DOF, FOV, risoluzione, formato, con monitoraggio tempo. Bisogna settare manualmente in output properties, post Elaborazione retinatura a 0 quando si calcola il GT (prima di avviare il reader).",
    "author": "Alfio Palermo",
    "version": (1, 8),
    "blender": (4, 1, 0),
    "location": "3D View > Sidebar > Tools > Create Dataset",
    "category": "Camera"
}

import bpy
import os
import csv
import time
from random import uniform, random
from math import radians

# --- Parametri hard-coded modificabili ---
MIN_FOV = 20
MAX_FOV = 70
MIN_DOF_DISTANCE = 2.0
MAX_DOF_DISTANCE = 10.0
MIN_DOF_FSTOP = 1.4
MAX_DOF_FSTOP = 8.0

# --- Proprietà scena ---
bpy.types.Scene.my_int_Iteration = bpy.props.IntProperty(name="# Photos", default=10)
bpy.types.Scene.my_int_minX = bpy.props.FloatProperty(name="MinX", default=-10)
bpy.types.Scene.my_int_maxX = bpy.props.FloatProperty(name="MaxX", default=10)
bpy.types.Scene.my_int_minY = bpy.props.FloatProperty(name="MinY", default=-10)
bpy.types.Scene.my_int_maxY = bpy.props.FloatProperty(name="MaxY", default=10)
bpy.types.Scene.my_int_minZ = bpy.props.FloatProperty(name="MinZ", default=1)
bpy.types.Scene.my_int_maxZ = bpy.props.FloatProperty(name="MaxZ", default=5)
bpy.types.Scene.enable_random_fov = bpy.props.BoolProperty(name="Random FOV", default=True)
bpy.types.Scene.enable_random_dof = bpy.props.BoolProperty(name="Random DOF", default=False)
bpy.types.Scene.my_int_ResX = bpy.props.IntProperty(name="Width", default=1920)
bpy.types.Scene.my_int_ResY = bpy.props.IntProperty(name="Height", default=1080)
bpy.types.Scene.image_format = bpy.props.EnumProperty(
    name="Image Format",
    items=[('PNG', "PNG", ""), ('JPEG', "JPEG", "")],
    default='PNG'
)

# --- Path base ---
BASE_PATH = "C:/tmp"
NON_LABELLED_PATH = os.path.join(BASE_PATH, "non_etichettate")
LABELLED_PATH = os.path.join(BASE_PATH, "etichettate")
os.makedirs(NON_LABELLED_PATH, exist_ok=True)
os.makedirs(LABELLED_PATH, exist_ok=True)

# --- Funzione helper ---
def apply_material_recursively(obj, material):
    if hasattr(obj.data, "materials") and obj.data is not None:
        obj.data.materials.clear()
        obj.data.materials.append(material)
    for child in obj.children:
        apply_material_recursively(child, material)

# --- Operatore Writer ---
class CamAutomaticWriter(bpy.types.Operator):
    bl_idname = "wm.writer"
    bl_label = "WRITER"

    def execute(self, context):
        start_time = time.time()
        self.report({'INFO'}, f"WRITER START at {time.strftime('%H:%M:%S')}")
        cam = context.scene.camera
        iterazioni = context.scene.my_int_Iteration
        minlocX, maxlocX = context.scene.my_int_minX, context.scene.my_int_maxX
        minlocY, maxlocY = context.scene.my_int_minY, context.scene.my_int_maxY
        minlocZ, maxlocZ = context.scene.my_int_minZ, context.scene.my_int_maxZ

		# Imposto vista camera
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'CAMERA'

		# CSV coordinate
        csv_file = os.path.join(BASE_PATH, "coordinate.csv")
        with open(csv_file, mode='w', newline='') as f_csv:
            writer = csv.writer(f_csv)
            writer.writerow(['LocationX','LocationY','LocationZ','RotationX','RotationY','RotationZ','FOV','DOF_Distance','DOF_FStop'])

            for i in range(iterazioni):
                cam.location.x = uniform(minlocX, maxlocX)
                cam.location.y = uniform(minlocY, maxlocY)
                cam.location.z = uniform(minlocZ, maxlocZ)
                cam.rotation_euler.x = radians(uniform(80, 100))
                cam.rotation_euler.y = radians(uniform(-5, 5))
                cam.rotation_euler.z = radians(uniform(0, 360))

                if context.scene.enable_random_fov:
                    cam.data.angle = radians(uniform(MIN_FOV, MAX_FOV))
                if context.scene.enable_random_dof:
                    cam.data.dof.use_dof = True
                    cam.data.dof.focus_distance = uniform(MIN_DOF_DISTANCE, MAX_DOF_DISTANCE)
                    cam.data.dof.aperture_fstop = uniform(MIN_DOF_FSTOP, MAX_DOF_FSTOP)
                else:
                    cam.data.dof.use_dof = False

                context.scene.render.resolution_x = context.scene.my_int_ResX
                context.scene.render.resolution_y = context.scene.my_int_ResY
                context.scene.render.resolution_percentage = 100
                context.scene.render.image_settings.file_format = context.scene.image_format

                context.scene.render.filepath = os.path.join(NON_LABELLED_PATH, f"img_{i:03d}")
                bpy.ops.render.render(write_still=True)

                writer.writerow([cam.location.x, cam.location.y, cam.location.z,
                                 cam.rotation_euler.x, cam.rotation_euler.y, cam.rotation_euler.z,
                                 cam.data.angle,
                                 cam.data.dof.focus_distance if cam.data.dof.use_dof else 0,
                                 cam.data.dof.aperture_fstop if cam.data.dof.use_dof else 0])

        elapsed = time.time() - start_time
        self.report({'INFO'}, f"WRITER FINISHED at {time.strftime('%H:%M:%S')}, elapsed {elapsed:.2f} sec")
        print(f"WRITER elapsed time: {elapsed:.2f} seconds")
        return {'FINISHED'}

# --- Operatore Reader Segmentation ---
class CamAutomaticReaderSegmented(bpy.types.Operator):
    bl_idname = "wm.reader_segmented"
    bl_label = "READER SEGMENTED"

    def execute(self, context):
        start_time = time.time()
        self.report({'INFO'}, f"READER START at {time.strftime('%H:%M:%S')}")
        scene = context.scene
        cam = scene.camera

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'CAMERA'

        # --- Impostazioni Eevee e disabilitazione post-process ---
        scene.render.engine = 'BLENDER_EEVEE'
        scene.eevee.use_gtao = False
        scene.eevee.use_bloom = False
        scene.eevee.use_ssr = False
        scene.eevee.use_ssr_refraction = False
        scene.eevee.use_volumetric_lights = False
        scene.eevee.use_motion_blur = False
        scene.eevee.use_soft_shadows = False
        scene.eevee.taa_render_samples = 1
        scene.eevee.taa_samples = 1

		# Disabilito compositing e sequencer
        scene.render.use_compositing = False
        scene.render.use_sequencer = False

        # Color Management
        scene.view_settings.view_transform = 'Standard'
        scene.view_settings.exposure = 0
        scene.view_settings.gamma = 1
        scene.view_settings.look = 'None'
		# --- Sfondo uniforme nero ---
        scene.world.use_nodes = True
        bg = scene.world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs[0].default_value = (0, 0, 0, 1)
            bg.inputs[1].default_value = 1.0

        csv_coord_file = os.path.join(BASE_PATH, "coordinate.csv")
        csv_color_file = os.path.join(BASE_PATH, "object_colors.csv")

        used_colors = set()

        # ================== MODIFICA IGNORE_SEGMENTATION ==================
        ignore_col = bpy.data.collections.get("IGNORE_SEGMENTATION")

        black_mat = bpy.data.materials.get("Mat_IGNORE_BLACK")
        if not black_mat:
            black_mat = bpy.data.materials.new("Mat_IGNORE_BLACK")
            black_mat.use_nodes = True
            nodes = black_mat.node_tree.nodes
            links = black_mat.node_tree.links
            nodes.clear()
            em = nodes.new(type='ShaderNodeEmission')
            em.inputs['Color'].default_value = (0, 0, 0, 1)
            out = nodes.new(type='ShaderNodeOutputMaterial')
            links.new(em.outputs['Emission'], out.inputs['Surface'])
        # ==================================================================

        with open(csv_color_file, mode='w', newline='') as f_colors:
            color_writer = csv.writer(f_colors)
            color_writer.writerow(['ObjectName','ColorR','ColorG','ColorB','ColorR_255','ColorG_255','ColorB_255'])

			# --- assegna materiali per oggetti padre ---
            for obj in scene.objects:
                if obj.parent is None: # solo oggetti di primo livello

                    # === MODIFICA: oggetti da ignorare ===
                    if ignore_col and obj.name in ignore_col.objects:
                        apply_material_recursively(obj, black_mat)
                        continue
                    # =====================================

                    while True:
                        r, g, b = round(random(),3), round(random(),3), round(random(),3)
                        if (r,g,b) not in used_colors:
                            used_colors.add((r,g,b))
                            break

                    mat = bpy.data.materials.new(name=f"Mat_{obj.name}")
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes
                    links = mat.node_tree.links
                    nodes.clear()

                    emission_node = nodes.new(type='ShaderNodeEmission')
                    emission_node.inputs['Color'].default_value = (r, g, b, 1)
                    output_node = nodes.new(type='ShaderNodeOutputMaterial')
                    links.new(emission_node.outputs['Emission'], output_node.inputs['Surface'])

                    apply_material_recursively(obj, mat)

                    color_writer.writerow([obj.name, r, g, b, int(r*255), int(g*255), int(b*255)])

# --- ora fai il render loop (FUORI dal blocco colore!) ---
        with open(csv_coord_file, newline='') as f_csv:
            reader = csv.reader(f_csv)
            next(reader)

            for i, row in enumerate(reader):
                cam.location.x = float(row[0])
                cam.location.y = float(row[1])
                cam.location.z = float(row[2])
                cam.rotation_euler.x = float(row[3])
                cam.rotation_euler.y = float(row[4])
                cam.rotation_euler.z = float(row[5])

                if scene.enable_random_fov:
                    cam.data.angle = float(row[6])

                cam.data.dof.use_dof = False

                scene.render.resolution_x = scene.my_int_ResX
                scene.render.resolution_y = scene.my_int_ResY
                scene.render.resolution_percentage = 100
                scene.render.image_settings.file_format = scene.image_format
                scene.render.dither_intensity = 0
                scene.render.filter_size = 0.0

                scene.render.filepath = os.path.join(LABELLED_PATH, f"img_label_{i:03d}")
                bpy.ops.render.render(write_still=True)

        elapsed = time.time() - start_time
        self.report({'INFO'}, f"READER FINISHED, elapsed {elapsed:.2f} sec")
        print(f"READER elapsed time: {elapsed:.2f} seconds")
        return {'FINISHED'}

# --- Pannello ---
class CreateDatasetPanel(bpy.types.Panel):
    bl_label = "Create Dataset"
    bl_idname = "VIEW3D_PT_create_dataset"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tools"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.operator("wm.writer", text="WRITER")
        layout.operator("wm.reader_segmented", text="READER SEGMENTED")
        layout.prop(scene,"my_int_minX")
        layout.prop(scene,"my_int_maxX")
        layout.prop(scene,"my_int_minY")
        layout.prop(scene,"my_int_maxY")
        layout.prop(scene,"my_int_minZ")
        layout.prop(scene,"my_int_maxZ")
        layout.prop(scene,"my_int_Iteration")
        layout.prop(scene,"enable_random_fov")
        layout.prop(scene,"enable_random_dof")
        layout.prop(scene,"my_int_ResX")
        layout.prop(scene,"my_int_ResY")
        layout.prop(scene,"image_format")

# --- Registrazione ---
classes = [CamAutomaticWriter, CamAutomaticReaderSegmented, CreateDatasetPanel]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
