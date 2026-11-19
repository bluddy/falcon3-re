import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QImage, QPainter
import falcon3_viewer_qt

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

# Enable Poly IDs and select face 38
win.chk_poly_nums.setChecked(True)
win.chk_cull.setChecked(True)
if win.face_list.count() > 38:
    win.face_list.setCurrentRow(38)

app.processEvents()

# Grab window image
img = win.grab()
img.save('analysis/viewer/inspector_f16_test.png')
print("Successfully generated analysis/viewer/inspector_f16_test.png")
app.quit()
