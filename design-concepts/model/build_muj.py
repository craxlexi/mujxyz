"""Procedural, stylized MUJ main-building model from photographic references.

Run: blender -b -t 4 --python design-concepts/model/build_muj.py -- --preview
     blender -b -t 4 --python design-concepts/model/build_muj.py -- --frames
No external model or photograph is embedded in the geometry.
"""
import bpy
import math
import os
import sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
preview = '--preview' in args
frames = '--frames' in args

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for material in list(bpy.data.materials):
    bpy.data.materials.remove(material)


def material(name, color, roughness=0.8, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    return mat

stone = material('Warm Jaipur sandstone', (0.69, 0.52, 0.33))
stone_light = material('Sunlit limestone', (0.85, 0.73, 0.55))
stone_trim = material('Limestone trim', (0.95, 0.83, 0.64))
shadow_stone = material('Recessed sandstone', (0.44, 0.33, 0.25))
arch_dark = material('Shadowed arch openings', (0.17, 0.15, 0.14))
window = material('Dark blue window glass', (0.08, 0.18, 0.21), .23, .1)
window_mullion = material('Window frames', (0.73, 0.65, 0.49), .65)
dome_orange = material('MUJ copper-gold dome', (0.66, 0.30, 0.075), .36, .38)
dome_bright = material('Dome ribs and finial', (0.97, 0.70, 0.27), .32, .5)
roof = material('Roof', (0.49, 0.40, 0.32))


def mesh_obj(name, verts, faces, mat):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def cube(name, loc, scale, mat, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new('Stone edges', 'BEVEL')
        modifier.width = bevel
        modifier.segments = 2
        modifier.affect = 'EDGES'
        obj.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
    return obj


def cylinder(name, loc, radius, depth, mat, vertices=32, rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = name
    if rotation:
        obj.rotation_euler = rotation
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def torus(name, loc, major, minor, mat):
    bpy.ops.mesh.primitive_torus_add(major_segments=64, minor_segments=8,
                                     location=loc, major_radius=major, minor_radius=minor)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def arch(name, x, y, z, width, height, mat):
    """Dark inset with rounded arch top, facing the front (-Y)."""
    n = 12
    half = width / 2
    shoulder = height - half
    verts = [(x-half,y,z),(x+half,y,z),(x+half,y,z+shoulder)]
    for i in range(n+1):
        t = math.pi * i/n
        verts.append((x+half*math.cos(t),y,z+shoulder+half*math.sin(t)))
    verts.append((x-half,y,z+shoulder))
    return mesh_obj(name, verts, [tuple(range(len(verts)))], mat)


def facade_window(x, y, z, w=.55, h=.9, name='Window'):
    cube(name+' reveal', (x,y,z), (w+.12,.05,h+.13), stone_trim)
    cube(name+' glass', (x,y-.035,z), (w,.025,h), window)
    cube(name+' mullion', (x,y-.054,z), (.035,.02,h), window_mullion)
    cube(name+' transom', (x,y-.055,z+.13), (w,.02,.025), window_mullion)
    cube(name+' sill', (x,y-.07,z-h/2-.09), (w+.27,.15,.08), stone_trim)


# Symmetrical long administrative wings, three visible floors.
for side in (-1, 1):
    center = side*12.25
    cube('Wing mass', (center, .9, 2.55), (14.5, 5.0, 5.1), stone)
    cube('Wing roof slab', (center,.9,5.14), (14.75,5.25,.27), stone_trim, .04)
    cube('Wing upper cornice', (center,-1.74,4.83), (14.7,.32,.22), stone_trim)
    cube('Wing floor cornice', (center,-1.7,2.47), (14.7,.27,.17), stone_trim)
    cube('Wing base', (center,-1.72,.23), (14.7,.35,.46), stone_light)
    # The repeated windows and pilasters are the building's strongest rhythm.
    for j in range(9):
        x = side*(5.8 + j*1.55)
        cube('Wing front pilaster', (x-.64*side,-1.67,3.66), (.14,.25,2.42), stone_trim)
        facade_window(x,-1.665,3.8,.53,.85,'Upper window')
        facade_window(x,-1.665,2.93,.49,.58,'Middle window')
        arch('Ground arch',x,-1.715,.37,.70,1.52,arch_dark)
        cube('Ground arch jamb', (x,-1.68,.37), (.95,.15,.08), stone_trim)
    # End walls are visible during the turn.
    end_x = side*19.54
    cube('Wing end wall', (end_x,.9,2.55), (.13,4.97,5.1), stone_light)
    for y in (-.8,.5,1.8,3.1):
        for z in (1.55,3.1,4.1):
            cube('End-wall window frame',(end_x+side*.08,y,z),(.055,.68,.88),stone_trim)
            cube('End-wall glazing',(end_x+side*.113,y,z),(.025,.55,.73),window)

# A solid core connects wings to the rounded colonnade.
cube('Central administration block',(0,1.0,2.74),(11.6,6.1,5.48),stone_light)
cube('Core roof',(0,1.0,5.55),(11.9,6.3,.36),stone_trim,.04)
cube('Central entablature',(0,-2.62,5.05),(10.4,.72,.46),stone_trim,.06)
cube('Central base',(0,-2.65,.32),(10.4,.66,.64),stone_trim)
# Recessed front wall and tall door.
cube('Portico shadow',(0,-2.82,2.73),(8.1,.07,4.2),shadow_stone)
arch('Main doorway',0,-2.93,.38,1.27,2.38,arch_dark)
for x in (-2.4,2.4):
    facade_window(x,-2.94,2.70,.75,1.55,'Portico window')

# Semi-circular colonnade projecting toward the viewer.
# The flattened ellipse approximates the portico visible in front and oblique photos.
for i in range(11):
    theta=math.pi*(i/10)
    x=4.33*math.cos(theta)
    y=-2.5-1.25*math.sin(theta)
    cylinder('Front portico column', (x,y,2.72), .235, 4.25, stone_trim,20)
    cylinder('Column foot',(x,y,.64),.39,.16,stone_light,20)
    cylinder('Column capital',(x,y,4.82),.36,.22,stone_trim,20)
# Curved portico lintel using small segments.
for i in range(20):
    a=math.pi*i/20
    b=math.pi*(i+1)/20
    x=4.45*math.cos((a+b)/2)
    y=-2.5-1.25*math.sin((a+b)/2)
    segment=cube('Curved portico entablature',(x,y,5.0),(.78,.52,.42),stone_trim)
    segment.rotation_euler.z=(a+b)/2 - math.pi/2

# The circular drum and copper dome. The drum is high enough to silhouette clearly.
cylinder('Rotunda drum',(0,.1,6.25),3.05,1.75,stone_light,64)
torus('Drum lower ring',(0,.1,5.38),3.12,.13,stone_trim)
torus('Drum upper ring',(0,.1,7.14),3.10,.15,stone_trim)
for i in range(16):
    a=2*math.pi*i/16
    x=3.06*math.sin(a)
    y=.1-3.06*math.cos(a)
    cylinder('Drum engaged column',(x,y,6.28),.125,1.49,stone_trim,12)
    # Small dark windows within the drum bays.
    if i%2==0:
        phi=a+math.pi/16
        wx=3.07*math.sin(phi)
        wy=.1-3.07*math.cos(phi)
        cube('Drum glazed opening',(wx,wy,6.34),(.38,.10,.70),window)

# Lathed dome surface: hemisphere-ish shell, with actual depth from any orbit angle.
R=2.82
H=2.30
rings=20
segments=64
verts=[]
for i in range(rings+1):
    theta=(math.pi/2)*i/rings
    r=R*math.sin(theta)
    z=7.24+H*math.cos(theta)
    for j in range(segments):
        a=2*math.pi*j/segments
        verts.append((r*math.sin(a), .1-r*math.cos(a), z))
faces=[]
for i in range(rings):
    for j in range(segments):
        nxt=(j+1)%segments
        faces.append((i*segments+j,i*segments+nxt,(i+1)*segments+nxt,(i+1)*segments+j))
dome=mesh_obj('Golden central dome',verts,faces,dome_orange)
for poly in dome.data.polygons:
    poly.use_smooth=True
for rib in range(16):
    a=2*math.pi*rib/16
    points=[]
    for i in range(1,rings+1):
        theta=(math.pi/2)*i/rings
        r=R*math.sin(theta)+.018
        points.append((r*math.sin(a),.1-r*math.cos(a),7.24+H*math.cos(theta)+.02))
    curve=bpy.data.curves.new('Dome rib','CURVE')
    curve.dimensions='3D'
    curve.bevel_depth=.025
    curve.bevel_resolution=2
    spline=curve.splines.new('POLY')
    spline.points.add(len(points)-1)
    for point,co in zip(spline.points,points):
        point.co=(*co,1)
    obj=bpy.data.objects.new('Gold dome rib',curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(dome_bright)
torus('Dome edge band',(0,.1,7.24),R,.11,dome_bright)
cylinder('Finial pedestal',(0,.1,9.58),.27,.31,dome_bright,16)
bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.23,location=(0,.1,9.87))
bpy.context.object.name='Golden finial orb'
bpy.context.object.data.materials.append(dome_bright)
cylinder('Finial point',(0,.1,10.14),.07,.47,dome_bright,12)

# Symmetrical steps and entrance landing.
for i in range(5):
    cube('Broad front steps',(0,-4.62-i*.43,.29-i*.065),(8.5+i*.52,.45,.23),stone_light)

# Light rig. Film transparency keeps building ready for the page's light and dark themes.
def area(name,loc,power,size):
    data=bpy.data.lights.new(name,'AREA')
    obj=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    obj.location=loc
    data.energy=power
    data.shape='DISK'
    data.size=size
    direction=Vector((0,0,3))-obj.location
    obj.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
area('Warm front key',(-17,-20,29),3800,18)
area('Cool fill',(16,-5,20),1800,15)
area('Edge light',(4,18,25),2400,13)
world=bpy.context.scene.world
world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.55,.60,.69,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.8

camera_data=bpy.data.cameras.new('Orbit camera')
camera=bpy.data.objects.new('Orbit camera',camera_data)
bpy.context.collection.objects.link(camera)
bpy.context.scene.camera=camera
camera_data.type='ORTHO'
camera_data.ortho_scale=42

def set_camera(progress):
    angle=math.radians(progress*34)
    radius=54
    camera.location=(radius*math.sin(angle),-radius*math.cos(angle),14.0)
    target=Vector((0,-.1,4.25))
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()

scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=24 if preview else 18
scene.cycles.use_denoising=False
scene.render.image_settings.color_depth='8'
scene.render.resolution_x=1280
scene.render.resolution_y=720
scene.render.resolution_percentage=75
scene.render.film_transparent=True
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.render.filepath=os.path.join(HERE,'preview-front.png')

if preview:
    for progress,label in ((0,'front'),(.65,'three-quarter')):
        set_camera(progress)
        scene.render.filepath=os.path.join(HERE,'preview-'+label+'.png')
        bpy.ops.render.render(write_still=True)
else:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE,'muj-building.blend'))
    bpy.ops.export_scene.gltf(filepath=os.path.join(HERE,'muj-building.glb'),export_format='GLB',export_cameras=False,export_lights=False)
    if frames:
        count=32
        for i in range(count):
            set_camera(i/(count-1))
            scene.render.filepath=os.path.join(HERE,'frames',f'frame-{i:03d}.png')
            bpy.ops.render.render(write_still=True)
