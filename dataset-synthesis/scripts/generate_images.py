import subprocess
import sys
import os
import argparse
import numpy as np
import math
import bpy
import csv
import json

# # uncomment if working locally 
# from dotenv import load_dotenv
# from pathlib import Path


# env_path = Path('.') / '.env'
# load_dotenv(dotenv_path=env_path)

# data_path = os.getenv('DATAPATH') #TODO: change to your own :) path to your data
# data_path = data_path.replace("\\", "/")

# scratch_path = os.getenv('SCRATCHPATH') #TODO: path you want to render to
# scratch_path = data_path.replace("\\", "/")

# with open("./dataset-synthesis/params.json") as f:
# 	params = json.load(f)

# comment out if working locally
data_path = "/path/to/data/on/cluster"
scratch_path = "/path/to/scratch/on/cluster"

with open("/path/to/your/dataset-synthesis/params.json") as f:
  params = json.load(f)

# Blender is super weird about passing arguments so here's a fix
try:
	idx = sys.argv.index("--")
	my_args = sys.argv[idx+1:] # the list after '--'
except ValueError as e: # '--' not in the list:
	my_args = []

num_lights = params["num_lights"]
num_cams = params["num_cameras"]

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--start", type = int, default = 0, help="Start frame to render")
parser.add_argument("-e", "--end", type = int, default = num_lights*num_cams, help="End frame to render")
parser.add_argument("-o", "--object_num", type = int, default = 0, help = "Object's number in the lookup table")
args = parser.parse_args(args = my_args)

start = args.start
end = args.end
object_num = args.object_num
object_id = "{:05d}".format(object_num)

'''
	This code sets up the light stage and keyframes all the light and camera changes for a particular object
	It then renders this configurations as an animation.  Think it as a wrapper for rendering our particular data from shell.

'''

# Render settings -- important for runtime and memory!
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
bpy.context.scene.render.engine = "CYCLES"
bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "CUDA"
bpy.context.scene.cycles.device = "GPU"
for d in bpy.context.preferences.addons["cycles"].preferences.devices:
	d["use"] = 1
bpy.context.scene.cycles.use_denoising = True
bpy.context.scene.render.image_settings.file_format = 'JPEG'
bpy.context.scene.render.resolution_percentage = 100
bpy.context.scene.cycles.taa_render_samples = 512 # sample rays
bpy.context.scene.render.resolution_x = 512
bpy.context.scene.render.resolution_y = 512


# STEP 1: Bring in the generated coordinates data
def get_csv_data():
	camera_coordinates_path = data_path + "coordinate_data/camera_coordinates.csv"
	light_coordinates_path = data_path + "coordinate_data/light_coordinates.csv"

	camera_coordinates = np.empty((num_cams, 3))
	light_coordinates = np.empty((num_lights, 3))

	cam_start = object_num*num_cams
	cam_end = cam_start + num_cams
	all_cams = np.genfromtxt(camera_coordinates_path, delimiter=",")
	camera_coordinates[:] = all_cams[cam_start:cam_end]
	

	light_start = object_num*num_lights
	light_end = light_start + num_lights
	all_lights = np.genfromtxt(light_coordinates_path, delimiter=",")
	light_coordinates[:] = all_lights[light_start:light_end]


	return camera_coordinates, light_coordinates



# STEP 2: Add lights and cameras to the scene
def make_cameras_and_lights(camera_coordinates, light_coordinates):
	
	# cameras
	for i, camCoordinate in enumerate(camera_coordinates):
		cam_data = bpy.data.cameras.new(name = 'MyCamera.{:03d}'.format(i))
		
		cam_object = bpy.data.objects.new(name = 'MyCamera.{:03d}'.format(i), object_data = cam_data)
		bpy.context.collection.objects.link(cam_object)
		bpy.context.view_layer.objects.active = cam_object
		cam_object.location = (camCoordinate[0], camCoordinate[1], camCoordinate[2])
		
		# Adding constraint so that camera always points towards the origin
		bpy.ops.object.constraint_add(type = "TRACK_TO")
		bpy.context.object.constraints["Track To"].target = bpy.data.objects["Target"] 
		bpy.context.object.constraints["Track To"].track_axis = 'TRACK_NEGATIVE_Z'
		bpy.context.object.constraints["Track To"].up_axis = 'UP_Y'

		bpy.context.object.data.lens_unit = 'FOV'
		bpy.context.object.data.clip_start = 0.1
		bpy.context.object.data.clip_end = 100

		bpy.context.active_object.name = 'MyCamera.{:03d}'.format(i)
		bpy.context.active_object.select_set(False)

		
	# Light source
	for i, lCoordinate in enumerate(light_coordinates):
		light_data = bpy.data.lights.new(name = 'MyLight.{:03d}'.format(i), type='SUN')

		# Cycles
		light_data.use_nodes = True
		light_data.energy = 10.0

		data_path = 'nodes["Emission"].inputs[1].default_value'
		emmision_node = light_data.node_tree.nodes["Emission"]
		emmision_node.inputs[1].default_value = 0.001
		light_data.node_tree.keyframe_insert(data_path = data_path, frame = 0)

		
		light_object = bpy.data.objects.new(name = 'MyLight.{:03d}'.format(i), object_data = light_data)  # create new object with our light datablock
		bpy.context.collection.objects.link(light_object)  # link light object
		bpy.context.view_layer.objects.active = light_object 
		light_object.location = (lCoordinate[0], lCoordinate[1], lCoordinate[2]) 
		
		bpy.ops.object.constraint_add(type = "TRACK_TO")
		bpy.context.object.constraints["Track To"].target = bpy.data.objects["Target"] 
		bpy.context.object.constraints["Track To"].track_axis = 'TRACK_NEGATIVE_Z'
		bpy.context.object.constraints["Track To"].up_axis = 'UP_Y'
		
		bpy.context.active_object.select_set(False)
		


# Just driver code for positioning lights and cameras (Steps 1 and 2)
def position_lights_and_cameras():
	bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0))
	bpy.context.active_object.name = "Target"
	
	camera_coordinates, light_coordinates = get_csv_data()
	
	make_cameras_and_lights(camera_coordinates, light_coordinates)
	
	
# STEP 3: Load the appropriate model from assets
def load_model():
	file_path = data_path + "shapenet/models/{}.obj".format(object_id)# gets the obj in directory
	bpy.ops.import_scene.obj(filepath = file_path)
	current_object =  bpy.context.scene.objects[0]


# STEP 4: Keyframe lights and cams
def setup_animation():
	load_model() # loads obj
	position_lights_and_cameras() # reads samples from csv
	
	for light_num in range(num_lights): # OLAT #rows
		# Eevee
		data_path = 'nodes["Emission"].inputs[1].default_value'
		
		current_light = bpy.data.objects["MyLight." + f'{light_num:03}']
		emmision_node = current_light.data.node_tree.nodes["Emission"]
		emmision_node.inputs[1].default_value = 1.0

		
				 
		for cam_num in range(num_cams): # cols
				
			frame_idx = cam_num + num_cams * light_num # row majoir matrix of r,c = lights, cameras

			current_light.data.node_tree.keyframe_insert(data_path = data_path, frame = frame_idx)  
		  
			# can't really keyframe camera switching so do this instead (markers)
			marker = bpy.context.scene.timeline_markers.new(str(frame_idx), frame = frame_idx)
			marker.camera = bpy.data.objects["MyCamera." + f'{cam_num:03}']
			
		# Turn off light at end of cameras
		# Turn off light at end of cameras
		emmision_node.inputs[1].default_value = 0.001
		current_light.data.node_tree.keyframe_insert(data_path = data_path, frame = frame_idx + 1)
		
		
		fcurves = current_light.data.node_tree.animation_data.action.fcurves
		for fcurve in fcurves: #We don't want interpolation between lighting
			for kf in fcurve.keyframe_points:
				kf.interpolation = 'CONSTANT' # Stop-action mode

				
# Helper for rendering rgb to one folder and depth to another
def setup_compositer():
	bpy.context.scene.use_nodes = True

	bpy.context.scene.view_layers["View Layer"].use_pass_normal = True # normals
	bpy.context.scene.view_layers["View Layer"].use_pass_diffuse_color = True  # diffuse color (Lambertian assumption here)

	tree = bpy.context.scene.node_tree
	links = tree.links

	# Clean up compositor
	for every_node in tree.nodes:
		tree.nodes.remove(every_node)
	
	RenderLayers_node = tree.nodes.new('CompositorNodeRLayers')

	# where we want to send our render passes
	file_out_path = scratch_path + "images/".format(object_id)
	file_out_node = tree.nodes.new("CompositorNodeOutputFile")
	file_out_node.base_path = file_out_path
	file_out_node.file_slots.remove(file_out_node.inputs[0])
	file_out_node.file_slots.new("{}d-".format(object_id)) # 00101d-0024
	file_out_node.file_slots.new("{}n-".format(object_id)) # 00101n-0024
	file_out_node.file_slots.new("{}a-".format(object_id)) # 00101a-0024

	
	# depth valus -> normalizer -> depth_maps folder
	normalize_node = tree.nodes.new('CompositorNodeNormalize')
	links.new(RenderLayers_node.outputs[2], normalize_node.inputs[0])
	links.new(normalize_node.outputs[0], file_out_node.inputs[0])


	# TODO: Still very confused about screenspace normals, worldspace normals, or object normals
	# normals -> multiply(normals, RGB(0.5, 0.5, -0.5)) -> add(multiply, (0.5, 0.5, 0.5)) -> Invert Red channel -> out
	combine_node = tree.nodes.new("CompositorNodeCombRGBA")
	combine_node.inputs[0].default_value = 0.5
	combine_node.inputs[1].default_value = 0.5
	combine_node.inputs[2].default_value = -0.5 
	
	multiply_node = tree.nodes.new("CompositorNodeMixRGB") # multiply(normals, RGB(0.5, 0.5, -0.5))
	multiply_node.blend_type = "MULTIPLY"
	links.new(RenderLayers_node.outputs[3], multiply_node.inputs[1])
	links.new(combine_node.outputs[0], multiply_node.inputs[2]) 

	add_node = tree.nodes.new("CompositorNodeMixRGB") # add(multiply, (0.5, 0.5, 0.5))
	add_node.blend_type = "ADD"
	add_node.inputs[1].default_value = (0.5, 0.5, 0.5, 1)
	links.new(multiply_node.outputs[0], add_node.inputs[2])
	
	split_node = tree.nodes.new("CompositorNodeSepRGBA") # Invert R channel
	invert_node = tree.nodes.new("CompositorNodeInvert")
	recombine_node = tree.nodes.new("CompositorNodeCombRGBA")
	links.new(add_node.outputs[0], split_node.inputs[0]) # add -> split
	links.new(split_node.outputs[0], invert_node.inputs[1]) #invert red
	links.new(invert_node.outputs[0], recombine_node.inputs[0]) #inverted to recombine
	links.new(split_node.outputs[1], recombine_node.inputs[1]) # G -> G
	links.new(split_node.outputs[2], recombine_node.inputs[2]) # B -> B
	links.new(split_node.outputs[3], recombine_node.inputs[3]) # A -> A

	# send to normals to file
	links.new(recombine_node.outputs[0], file_out_node.inputs[1]) # render to file 

	# albedo
	links.new(RenderLayers_node.outputs[4], file_out_node.inputs[2]) # render to file



# Step 5: Actually render the images for this object         
def render(): 
	# Storing data without any color space conversion, we might want to convert to sRGB when we preprocess the beauty pass
	bpy.context.scene.sequencer_colorspace_settings.name = 'Raw' 
	setup_compositer()
	bpy.context.scene.frame_start = start
	bpy.context.scene.frame_end = end

	rgb_path = scratch_path + "images/{}rgb-####.jpg".format(object_id) # 00101rgb-0023
	bpy.context.scene.render.filepath = rgb_path
	bpy.ops.render.render(animation = True)

			   
# Step 6: Clean up workspace
def clean_up():
	bpy.ops.object.select_all(action = "SELECT")
	bpy.ops.object.delete()
	bpy.context.scene.timeline_markers.clear()
	
	# Clean up compositor
	tree = bpy.context.scene.node_tree
	for node in tree.nodes:
		tree.nodes.remove(node)
	
								
if __name__ == "__main__":
	bpy.ops.object.select_all(action = "SELECT")
	bpy.ops.object.delete()

	setup_animation() # places everything
	render()
	clean_up()
