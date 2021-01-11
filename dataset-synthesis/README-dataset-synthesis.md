# README - Dataset Synthesis

Things in this folder build our dataset.

## Preprocessing
We obtained our 3D assets from ShapeNetSem, a relatively small subset of the ShapeNet that is 12,000 CAD models.  However, these models aren't natively appropriate for our application so we had to do a few things.

1. Instead of using the obj's directly from ShapeNet, it's recommended to first convert them to gltf's, turn off backface culling, and turn off autosmooth normals.  This is so that the model displays accurately in Blender. (We do this in another module called `file-conversion` that is written in JS)
2. The origin of the imported object is not necessarily center.  We set the origin to its geometry making the following transformations easier.
3. First, we scale the model so that it fits within our virtual lightstage 
4. Second, we rotate to make the model face upright
5. Next, we move the model to the origin in world space
6. Finally, we export our preprocessed model as an obj to be consumed by the synthesis pipeline

To preprocess data: `blender -b -P dataset-synthesis/scripts/preprocessing.py -- -o <OBJECT's NUMBER IN THE LOOKUP TABLE, DEFAULT = 0>`.  

To preprocess many, run the bash command, `bash <LOCATION OF preprocess_many.sh>`.  There are variables in the shell script you can change (defaults: START=0, STEP=1, END=9).  

This lookup table is generated in `generate_lookup_table` which just enumerates the ShapeNet data and puts the filename in a csv.

## Positioning lights and Cameras
As of now, we sample uniformly from a sphere to get camera and light positions.  Cameras are constrained to always point towards the origin, where we'll place our object.  Generate coordinate data by running `python generate_coordinates.py`

We use Sun Lamps, Blender's implentation of directional lighting, which light the scene uniformly at the incident angle.  We use the light position to find a light direction that crosses the random position and the origin of the scene.  

## Rendering the Data
Since we set up each (light, camera) configuration as a frame, we can render the data as an animation.  This way, we can distribute different frames to different machines or pick-up where we left off if there's an interuption.  

To render data: `blender -b -P dataset-synthesis/scripts/generate_images.py -- -s <START FRAME Default = 0> -e <END FRAME Default = 3600> -o <OBJECT's NUMBER IN THE LOOKUP TABLE, DEFAULT = 0>`

To render multiple objects, `bash <LOCATION OF render_many.sh`, whose defaults are (OBJ_START=0, OBJ_STEP=1, OBJ_END=9, FRAME_START=0, FRAME_END=10).  We used Brown's CCV to batch render with SLURM.

## Additional Notes
Note that you will need blender on your machine and the `blender` alias might not work.  If `blender` alias doesn't work, you might need to  make `blender` point to where you installed Blender.  Additionally, you might need to `pip install` some dependencies in your Blender Python binary.  For example, you might call, `<LOCATION OF BLENDER APP CONTENTS ON YOUR MACHINE>/python/bin/python3.7m -m pip install <PACKAGE NAME>`.
