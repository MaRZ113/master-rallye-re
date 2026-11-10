# Course Studio: your first course in 20 minutes

You need Blender 4.3 or newer (qualified on 5.2.2) and a Master Rallye install
with unpacked resources (a folder containing `DataGx` and `DataScene`, e.g.
`Data.sma_unpacked`).

## 1. Install

1. Blender > Edit > Preferences > Add-ons > Install from Disk:
   `master_rallye_io-course-studio.zip`. Enable **Master Rallye IO**.
2. In the add-on preferences set **Game resources** (found automatically when
   empty and the add-on sits next to the game folders) and, to register courses
   in the game menu, **COURSE-CAP2 input** (the accepted `build-input.json`).
3. In the 3D View press **N** and open the **MR Course Studio** tab.

The tab has nine sections: Project, Terrain, Objects, Materials, Collision,
Markers, Routes & AI, Environment, Build. **Problems** and **Selected Course
Object** appear under them when relevant.

## 2. New course

Project > **New Course**: name `MyValley`, menu title `My Valley`, environment
`France - Stage 1` (sky, sounds, physics and HUD come from it), start from
**Valley with road** (or **Flat ground** to sculpt everything yourself).

Save the `.blend` (Ctrl+S). The course project is written next to it
automatically (`MyValley_mrcourse/`).

## 3. Shape the land

* Select **Terrain**: Tab for Edit Mode (add/delete vertices, extrude, knife,
  subdivide - any topology), or **Sculpt** from the Terrain section.
* Import ready landscape: **Import Terrain** (OBJ / FBX / glTF). Imported
  meshes get the Terrain role; give other parts **Visual only**, **Collision
  only**, **Water** or **Invisible ground** with the role buttons.
* **Carve Road Along Route** flattens a road bed under the AI route and paints
  the road material.
* Several pieces: **Merge Terrains** (joins and welds seams), **Snap Edges to
  Neighbour** (closes height steps), **Find Gaps**; **Split Into Sections** for
  big maps.

## 4. Materials

Materials > **New Material** (Tarmac road, Gravel road, Grass, Rock face,
Building, Metal, Sign, Tree, Water). Choose a **Texture** (any image), a
**Surface** (the real game surface type: friction, bounce and tyre tracks are
shown), transparency and wrap. In Edit Mode select faces and **Assign to
Faces**. UVs are edited with Blender's UV Editing workspace.

## 5. Objects

Objects > **Building / Wall / Barrier / Rock / Crate** at the 3D cursor - solid
by default (a grounded collision proxy). For your own model: select it,
**Hull Collision** or **Box Collision**. **Add Collision Blocker** makes an
invisible wall. **Add Sound Source** places river/birds/... sounds.
Physical objects (hay bales, tumbleweeds, barrels or your own mesh) are an
optional Renderer feature: without the Renderer the course runs without them.

## 6. Route, start, finish, checkpoints

* Routes & AI > **Draw AI Route**: select the route, Tab, and extend it with
  **E**; delete points with **X**. **Snap Route to Terrain**, **Smooth**.
* Markers > **Place Start** / **Place Finish** (put the 3D cursor on the road
  first; they align to the route). Scale them with S, rotate with R.
* **Add Checkpoint** or **Place Checkpoints Along Route**: native timed gates.
  Radius = object scale; **Extra time** is added to the countdown.
  **Renumber by Route** orders them; arrows in the viewport show the direction.
* **Limits**: Road corridor, Open terrain (drive anywhere within 300 m of the
  route), or Manual curves.
* **Preview AI Path** shows the yellow line an AI car steering by the generated
  field would drive.

## 7. Collision

Collision > **Generate / Rebuild Collision**. The status says when terrain
changed after the last build. The summary lists holes (cars falling through),
bumps and route walls; red markers show them in the viewport and **Problems**
lists them - click the magnifier to jump there. **Show Game Collision** draws
exactly what the game will collide with around the 3D cursor.

## 8. Build and play

Build > **Check Course**, then **Build Course**. Errors stop the build and are
listed with a jump button; warnings do not. The build folder contains the game
files, `course-build.json` and the COURSE-CAP2 registration. Tick **Make
private game package** to create the private launcher package; start it with
its `Launch-*.cmd`. Originals, saves and the installed game are never changed.

**Reopen Exported Course** loads the built files back to check the round trip.

## Edit an original course

Project > choose a course from the gallery > **Open as New Course**. The
terrain, objects, water, exact game collision, markers, checkpoints, route,
limits and pace notes are imported; the build is a new course with its own
name and files.
