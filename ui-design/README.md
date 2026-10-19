# Natron workspace in Qt Designer

## Run the WSL development build from PowerShell

The working WSLg launch uses Qt Wayland. In PowerShell, run:

```powershell
wsl -d Ubuntu --exec sh -lc 'cd /opt/assets/scripts/vibe/claude/Natron && cmake --build build-qt6 --target Natron -j2 && QT_QPA_PLATFORM=wayland ./build-qt6/App/Natron'
```

Close an older Natron window before relaunching if you want the rebuilt UI in
that window. On this WSLg setup, forcing `QT_QPA_PLATFORM=xcb` made Natron's
window unresponsive to mouse clicks; the Wayland launch responds normally.

## Edit the actual Natron theme

Run `python3 ui-design/theme_editor.py` in WSL. Change colors, border widths,
corner radii, font family and size, selected-tab accent underline, and transport
icons in the left pane; the right pane previews Qt controls and a node.
Corner controls include tabs, buttons, dropdowns and their lists, input fields,
group boxes, menus, tooltips, list/tree views, panels, and graph nodes.
The **Individual borders** section gives each of these control families its own
border color and pixel width. Viewer Layer, Alpha, Channels, Zoom, Render Scale,
A, Composite, and B each have independent border color and width controls.
The Viewer Channels, Zoom, A/B input, and compositing dropdowns use Natron's
custom-painted `ComboBox`, not Qt's `QComboBox`. Their closed control uses the
same **Dropdown / Viewer corner radius** setting after rebuilding Natron; menu
corners use **Menu corner radius**. Subsequent radius changes update the new
preview through the live stylesheet.
The searchable icon browser lists all PNGs compiled into Natron's GUI resource
collection, including grouping and tool icons. Filter by folder, select an icon,
and replace it with a PNG or SVG file. Click **Open real Natron workspace** in
the **Real Natron** tab to launch a fresh Natron session with a Sphere node,
Viewer, and animated Sphere parameter. Select Sphere1 to inspect the actual
Properties panel; open Natron's Dope Sheet and Curve Editor for the keyframes.
Changes to the generated stylesheet update this preview when auto-save runs.
Use `python3 ui-design/theme_editor.py --open-live` to open both windows at once.
The editor's other tabs are labeled sketches because they do not reproduce
Natron's custom widgets exactly. They show all 39
bundled viewer/playback icon states and representative field and animation
states; plugin-specific controls still depend on the node and project loaded
in Natron. Edits auto-save after a short pause.
**Apply to Natron source** also saves immediately, converting chosen icons
to Natron's existing PNG resources and writing `theme.json`,
`Gui/Resources/Stylesheets/theme-editor.qss`, and `Gui/ThemeValues.h`. Then use
**Build Natron** and open a new Natron preview to see icon and custom node
appearance changes. The
generated files can be checked with `python3 ui-design/theme_editor.py --check`.
`theme-editor-preview.png` shows the editor's starting appearance.

Plugin-provided icons outside Natron's bundled GUI resources are not listed.
The optional node fill override replaces category and saved node colors, while
Backdrop colors stay as configured in Natron. Other custom-painted elements,
such as the viewer canvas and graph connections, are outside this editor.

## Layout prototype

`NatronWorkspace.ui` is an editable layout study based on `Gui::setupUi()` in
`Gui/Gui05.cpp` and `Gui::createDefaultLayout1()` in `Gui/Gui10.cpp`. It mirrors
the left tool strip, viewer and histogram tabs, node graph/curve editor/dope
sheet tabs, and properties pane. The form uses Natron's default dark palette,
11 pt Droid Sans font, 30 px tool-strip buttons, and 22 px playback buttons.
Its 65/35 center/properties split follows `Gui/Gui10.cpp`.

Open it in WSLg with `designer6 ui-design/NatronWorkspace.ui` from the repo root.
`NatronDesign.qrc` links the existing Natron toolbar and playback PNGs into
Designer. Keep it alongside the `.ui` file when moving or sharing the form.
`preview.png` is an offscreen render of the current layout.

The live Natron workspace is constructed in C++ using `Splitter` and
`TabWidget`; this form is a design reference. Use the theme editor above to
apply colors and corner changes to Natron itself.
The viewer, node graph, histogram, curve editor, and dope sheet are custom
widgets and are placeholders here. Implement accepted changes in `Gui/` and
the runtime icon resources in `Gui/Resources/Images/`.

For a quick visual refresh, replace the PNGs used by playback controls in
`Gui/Resources/Images/` (for example `firstFrame.png`, `back1.png`,
`rewind.png`, `play.png`, `forward1.png`, `lastFrame.png`, and their enabled
variants). `Gui/GuiApplicationManager.cpp` maps these files to icon IDs;
`Gui/ViewerTab.cpp` assigns them to buttons. Left tool strip grouping icons
live under `Gui/Resources/Images/GroupingIcons/Set*/`. Icons drawn on nodes
come from each plugin's icon path, when enabled, and are handled by
`Gui/NodeGui.cpp`. Rebuild Natron after changing embedded resources.
