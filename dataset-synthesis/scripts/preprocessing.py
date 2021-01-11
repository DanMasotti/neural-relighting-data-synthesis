import bpy
import os 
import json
import numpy as np
from math import pi
from mathutils import Matrix, Vector
import argparse
import sys

from dotenv import load_dotenv
from pathlib import Path

# # uncomment if working locally
with open("./dataset-synthesis/params.json") as f:
  params = json.load(f)

path = os.getenv('DATAPATH') #TODO: change to your own :) Path to your data folder
# print("PATH", path)
path = path.replace("\\", "/")
#path = './data/'


# SLURM Batch
# with open("/users/dmasotti/data/dmasotti/dataset-synthesis/params.json") as f:
#   params = json.load(f)

# Blender is super weird about passing arguments so here's a fix
try:
    idx = sys.argv.index("--")
    my_args = sys.argv[idx+1:] # the list after '--'
except ValueError as e: # '--' not in the list:
    my_args = []


parser = argparse.ArgumentParser()
parser.add_argument("-o", "--object_num", type = int, default = 0, help = "The cleaned obj's number in the lookup table")
args = parser.parse_args(args = my_args)

object_id = "{:05d}".format(args.object_num)

# Given a single .gltf file, use blender to preprocess the mesh
# Then, convert this transformed object to a .obj file.
def process_gltf():
    # STEP 1: Import gltf object
    table_path = path + "shapenet/lookup_table.json"
    with open(table_path, "r+") as f:
        table = json.load(f)
        name = table[str(args.object_num)]
        infile = path + "shapenet/models/{}".format(name)

    bpy.ops.import_scene.gltf(filepath=infile)

    bpy.ops.file.pack_all() #Pack all images into the file

    current_object =  bpy.context.scene.objects[0] # Assuming that imported is only object in scene
    
    # STEP 2: turn off back face culling
    mesh = current_object.data
    for face in mesh.polygons:
        slot = current_object.material_slots[face.material_index]
        material = slot.material
        if material is not None:
            material.use_backface_culling = False

    
    # STEP 4: set local origin to center of object's geometry
    world_coordinates = current_object.matrix_world
    
    origin = sum((vertex.co for vertex in mesh.vertices), Vector()) / len(mesh.vertices) # average of vertices
    
    T = Matrix.Translation(-origin)
    mesh.transform(T)
    world_coordinates.translation = world_coordinates @ origin # M*p
    mesh.update()
    
    # STEP 5: scale to fit inside light stage radius
    radius_squared = params["lightstage_radius"]
    
    # get largest dimension of object's bounding box
    max_dimension = max([current_object.dimensions.x, current_object.dimensions.y, current_object.dimensions.z])
    scaling_coeff = np.sqrt(radius_squared)/max_dimension 
    S = Matrix.Scale(scaling_coeff, 4)
    mesh.transform(S)
    mesh.update()
    
    # STEP 6: Rotate by -90 on x-axis to re-orient upwards
    R = Matrix.Rotation(-pi/2, 4, 'X')
    mesh.transform(R)
    mesh.update()
    
    # STEP 7: set the local origin to world origin, this is easier because we can just hardcode the location
    
    current_object.location = (0, 0, 0)


    # STEP 8: export preprocessed file
    file_path = path + "shapenet/models/{}.obj".format(object_id)
    bpy.ops.export_scene.obj(filepath = file_path, use_triangles = True, path_mode = "COPY")
    
    
def clean_up():
    bpy.ops.object.select_all(action = "SELECT")
    bpy.ops.object.delete()


if __name__ == "__main__":
    bpy.ops.object.select_all(action = "SELECT")
    bpy.ops.object.delete()
    
    process_gltf()