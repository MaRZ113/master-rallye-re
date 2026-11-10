"""Master Rallye Course Studio core: one project model from authoring to a native Course.

The package has no ``bpy`` dependency. The Blender add-on and the
``tools/mr_course_studio.py`` command line share every builder below:

* :mod:`.model` - versioned project model and its portable on-disk form;
* :mod:`.materials` - shader/surface vocabulary and native material names;
* :mod:`.textures` - PNG <-> FEED texture container;
* :mod:`.dx_build` - render records, land surface database, bounds, DX assembly;
* :mod:`.collision` - collision BSP build, validation probes and differences;
* :mod:`.race` - RaceTest scene, markers, checkpoints, pace notes, HNT;
* :mod:`.ai` - RaceLine resampling, limits, route checks and the AI SFL field;
* :mod:`.validate` - project validator with error/warning/info findings;
* :mod:`.build` - staged, atomically published Course build and registry rows;
* :mod:`.importer` - Retail course and external mesh import.
"""

SCHEMA = "mr-course-studio-project/2"
