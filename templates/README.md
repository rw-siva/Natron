# 3D plate templates

The two new commands in initGui.py build editable node graphs. They do not
include footage or a camera solve. Open the theme editor's "Open preview
Natron" button to launch Natron with this template menu enabled, or set
NATRON_PLUGIN_PATH to this directory before starting Natron.

From PowerShell, run:

    wsl -d Ubuntu --exec env QT_QPA_PLATFORM=wayland NATRON_PLUGIN_PATH=/opt/assets/scripts/vibe/claude/Natron/templates OFX_PLUGIN_PATH=/opt/assets/software/natron/Natron-2.5.0-Linux-x86_64-no-installer/Plugins/OFX /opt/assets/scripts/vibe/claude/Natron/build-qt6/App/Natron

A restart is needed after changing initGui.py. The OFX_PLUGIN_PATH shown above
enables the locally installed Natron effects for this development build.

## Templates > Camera Track + Test Geometry

Creates Read -> CameraTracker alongside a branch that composites a Cube3D and
Sphere3D over the same original plate using Scene3D and ScanlineRender. A
temporary Camera3D makes the graph usable before tracking.

1. Set the file on "PLATE - SET FOOTAGE FILE" to your footage sequence.
2. In CameraTracker, set focal length and sensor width if known. Detect
   features, track them across the shot, and solve.
3. Use "Create Camera3D" in CameraTracker. Connect the generated camera to
   ScanlineRender's "cam" input in place of "TEMP CAMERA - REPLACE AFTER SOLVE".
4. Move the Cube3D and Sphere3D into the solved scene and adjust lighting.
   The original plate stays connected to ScanlineRender's "bg" input.

## Templates > Backplate + 3D Card Insert

Creates a backplate Read, a second Read used as the texture on Card3D, a
Sphere3D for scale, and a Camera3D -> ScanlineRender -> Viewer branch.

1. Set "BACKPLATE - SET FOOTAGE FILE" to the live-action sequence.
2. Set "CARD TEXTURE - SET IMAGE FILE" to the image or sequence you want on
   the 3D card.
3. Align the Camera3D manually or replace it with a solved Camera3D from a
   tracker. Position the card and sphere in the scene.

The plate is a 2D background in the render, while the card is actual 3D
geometry. These templates use ScanlineRender, so they do not depend on Cycles.
