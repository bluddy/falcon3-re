import json
import sys
from PyQt6.QtWidgets import QApplication
import falcon3_viewer_qt

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

f16 = None
for m in db['flyable_aircraft'] + db['vehicles_and_units']:
    if 'F16' in m['name']:
        f16 = m
        break

# In OpenGL coordinates:
# [x, y, z] = [Y_falcon / 10.0, -Z_falcon / 10.0, -X_falcon / 10.0]
# To change X_falcon, we change z_gl = -X_falcon / 10.0!

# Let's fix the 7 asymmetric port vertices in BOTH primary_verts and lods[0]['vertices']:
# Stbd counterparts:
# v17: x = -15 -> z_gl = 1.50. Port v24 was x = 70 (z_gl = -7.0). Correct to 1.50
# v18: x = -15 -> z_gl = 1.50. Port v21 was x = 70 (z_gl = -7.0). Correct to 1.50
# v19: x = -15 -> z_gl = 1.50. Port v22 was x = 10 (z_gl = -1.0). Correct to 1.50
# v20: x =  10 -> z_gl = -1.0. Port v23 was x = -15 (z_gl = 1.50). Correct to -1.0
# v16: x = -50 -> z_gl = 5.00. Port v25 was x = -15 (z_gl = 1.50). Correct to 5.00
# v43: x = 140 -> z_gl = -14.0. Port v46 was x = 250 (z_gl = -25.0). Correct to -14.0
# v42: x = 180 -> z_gl = -18.0. Port v47 was x = 140 (z_gl = -14.0). Correct to -18.0

corrections = {
    24: 1.50,
    21: 1.50,
    22: 1.50,
    23: -1.00,
    25: 5.00,
    46: -14.00,
    47: -18.00,
}

for vi, z_val in corrections.items():
    f16['vertices'][vi][2] = z_val
    if f16.get('lods'):
        f16['lods'][0]['vertices'][vi][2] = z_val

with open('analysis/viewer/assets_database.json', 'w') as f:
    json.dump(db, f, indent=2)

print("Saved corrected coordinates to assets_database.json")

# Render screenshot
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

win = falcon3_viewer_qt.Falcon3DViewerWindow()
win.resize(1380, 850)
win.show()

# Select F16
for i in range(win.model_list.count()):
    item = win.model_list.item(i)
    if 'F16' in item.text():
        win.model_list.setCurrentRow(i)
        break

win.chk_cull.setChecked(True)
app.processEvents()

img = win.grab()
img.save('analysis/viewer/inspector_f16_test.png')
print("Rendered and saved analysis/viewer/inspector_f16_test.png")
app.quit()
