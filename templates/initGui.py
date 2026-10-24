# Natron Templates — Menu Commands
# Copy this file to ~/.Natron/initGui.py to register templates in the menu bar.
# Templates appear under: Menu bar > Templates > ...

from NatronGui import *


def _createTemplate3DBasic():
    app = natron.getGuiInstance(0)
    if not app:
        return

    sphere = app.createNode("fr.inria.built-in.Sphere3D")
    light = app.createNode("fr.inria.built-in.Light3D")
    scene = app.createNode("fr.inria.built-in.Scene3D")
    camera = app.createNode("fr.inria.built-in.Camera3D")
    cycles = app.createNode("fr.inria.built-in.CyclesRender")
    viewer = app.createNode("fr.inria.built-in.Viewer")

    scene.connectInput(0, sphere)
    scene.connectInput(1, light)
    cycles.connectInput(0, camera)
    cycles.connectInput(1, scene)
    viewer.connectInput(0, cycles)

    sphere.setPosition(-100, -200)
    light.setPosition(100, -200)
    scene.setPosition(0, -50)
    camera.setPosition(-200, 100)
    cycles.setPosition(0, 100)
    viewer.setPosition(0, 250)

    camera.getParam("translateZ").setValue(5.0)


def _createTemplateVDBFire():
    app = natron.getGuiInstance(0)
    if not app:
        return

    vdb = app.createNode("fr.inria.built-in.ReadVDB")
    light = app.createNode("fr.inria.built-in.Light3D")
    scene = app.createNode("fr.inria.built-in.Scene3D")
    camera = app.createNode("fr.inria.built-in.Camera3D")
    cycles = app.createNode("fr.inria.built-in.CyclesRender")
    viewer = app.createNode("fr.inria.built-in.Viewer")

    scene.connectInput(0, vdb)
    scene.connectInput(1, light)
    cycles.connectInput(0, camera)
    cycles.connectInput(1, scene)
    viewer.connectInput(0, cycles)

    vdb.setPosition(-100, -200)
    light.setPosition(100, -200)
    scene.setPosition(0, -50)
    camera.setPosition(-200, 100)
    cycles.setPosition(0, 100)
    viewer.setPosition(0, 250)

    light.getParam("lightType").setValue(4)
    light.getParam("intensity").setValue(1.0)
    camera.getParam("translateZ").setValue(5.0)


def _createTemplateParticles():
    app = natron.getGuiInstance(0)
    if not app:
        return

    emitter = app.createNode("fr.inria.built-in.ParticleEmitter")
    gravity = app.createNode("fr.inria.built-in.ParticleGravity")
    solver = app.createNode("fr.inria.built-in.ParticleSolver")
    scene = app.createNode("fr.inria.built-in.Scene3D")
    camera = app.createNode("fr.inria.built-in.Camera3D")
    scanline = app.createNode("fr.inria.built-in.ScanlineRender")
    viewer = app.createNode("fr.inria.built-in.Viewer")

    gravity.connectInput(0, emitter)
    solver.connectInput(0, gravity)
    scene.connectInput(0, solver)
    # ScanlineRender inputs: 0 = bg, 1 = obj/scn, 2 = cam.
    scanline.connectInput(2, camera)
    scanline.connectInput(1, scene)
    viewer.connectInput(0, scanline)

    emitter.setPosition(0, -350)
    gravity.setPosition(0, -200)
    solver.setPosition(0, -50)
    scene.setPosition(0, 100)
    camera.setPosition(-200, 250)
    scanline.setPosition(0, 250)
    viewer.setPosition(0, 400)

    emitter.getParam("translateY").setValue(2.0)
    camera.getParam("translateZ").setValue(8.0)


# Register menu commands
natron.addMenuCommand("Templates/Basic 3D Scene", "_createTemplate3DBasic")
natron.addMenuCommand("Templates/VDB Fire-Smoke", "_createTemplateVDBFire")
natron.addMenuCommand("Templates/Particle System", "_createTemplateParticles")


def _createTemplateTrackedPlate():
    app = natron.getGuiInstance(0)
    if not app:
        return

    plate = app.createNode("fr.inria.built-in.Read")
    tracker = app.createNode("fr.inria.built-in.CameraTracker")
    cube = app.createNode("fr.inria.built-in.Cube3D")
    sphere = app.createNode("fr.inria.built-in.Sphere3D")
    light = app.createNode("fr.inria.built-in.Light3D")
    scene = app.createNode("fr.inria.built-in.Scene3D")
    camera = app.createNode("fr.inria.built-in.Camera3D")
    render = app.createNode("fr.inria.built-in.ScanlineRender")
    viewer = app.createNode("fr.inria.built-in.Viewer")

    tracker.connectInput(0, plate)
    scene.connectInput(0, cube)
    scene.connectInput(1, sphere)
    scene.connectInput(2, light)
    render.connectInput(0, plate)   # Keep the original plate as the 2D background.
    render.connectInput(1, scene)
    render.connectInput(2, camera)  # Replace with the tracker's solved camera.
    viewer.connectInput(0, render)

    plate.setLabel("PLATE - SET FOOTAGE FILE")
    camera.setLabel("TEMP CAMERA - REPLACE AFTER SOLVE")
    plate.setPosition(-400, -300)
    tracker.setPosition(-400, -100)
    cube.setPosition(-100, -300)
    sphere.setPosition(100, -300)
    light.setPosition(300, -300)
    scene.setPosition(100, -100)
    camera.setPosition(350, -100)
    render.setPosition(100, 100)
    viewer.setPosition(100, 300)

    cube.getParam("translateX").setValue(-1.0)
    sphere.getParam("translateX").setValue(1.0)
    camera.getParam("translateZ").setValue(6.0)
    print("[Template] Set the plate file, detect/track/solve, create a Camera3D from the tracker, then connect it to ScanlineRender's cam input.")


def _createTemplatePlateWithCard():
    app = natron.getGuiInstance(0)
    if not app:
        return

    plate = app.createNode("fr.inria.built-in.Read")
    insert = app.createNode("fr.inria.built-in.Read")
    card = app.createNode("fr.inria.built-in.Card3D")
    sphere = app.createNode("fr.inria.built-in.Sphere3D")
    light = app.createNode("fr.inria.built-in.Light3D")
    scene = app.createNode("fr.inria.built-in.Scene3D")
    camera = app.createNode("fr.inria.built-in.Camera3D")
    render = app.createNode("fr.inria.built-in.ScanlineRender")
    viewer = app.createNode("fr.inria.built-in.Viewer")

    card.connectInput(0, insert)
    scene.connectInput(0, card)
    scene.connectInput(1, sphere)
    scene.connectInput(2, light)
    render.connectInput(0, plate)
    render.connectInput(1, scene)
    render.connectInput(2, camera)
    viewer.connectInput(0, render)

    plate.setLabel("BACKPLATE - SET FOOTAGE FILE")
    insert.setLabel("CARD TEXTURE - SET IMAGE FILE")
    plate.setPosition(-400, -300)
    insert.setPosition(-150, -300)
    card.setPosition(-150, -100)
    sphere.setPosition(100, -100)
    light.setPosition(300, -100)
    scene.setPosition(100, 100)
    camera.setPosition(350, 100)
    render.setPosition(100, 300)
    viewer.setPosition(100, 500)

    card.getParam("translateX").setValue(-1.0)
    sphere.getParam("translateX").setValue(1.0)
    camera.getParam("translateZ").setValue(6.0)
    print("[Template] Set plate and card files, then align or replace Camera3D with a tracked camera.")


natron.addMenuCommand("Templates/Camera Track + Test Geometry", "_createTemplateTrackedPlate")
natron.addMenuCommand("Templates/Backplate + 3D Card Insert", "_createTemplatePlateWithCard")
