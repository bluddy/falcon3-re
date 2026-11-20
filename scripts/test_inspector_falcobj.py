import sys
from pathlib import Path
sys.path.append(str(Path('scripts').resolve()))
from PyQt6.QtWidgets import QApplication
import falcon3_viewer_qt

app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

win = falcon3_viewer_qt.Falcon3DViewerWindow()
win.resize(1380, 850)
win.show()

# Select FALCOBJ
for i in range(win.model_list.count()):
    item = win.model_list.item(i)
    if 'FALCOBJ' in item.text():
        win.model_list.setCurrentRow(i)
        break

win.chk_poly_nums.setChecked(True)
win.chk_vert_nums.setChecked(True)
win.chk_cull.setChecked(False)

app.processEvents()

# Grab window image
img = win.grab()
out_file = 'analysis/viewer/inspector_falcobj_test.png'
img.save(out_file)
print(f"Successfully generated {out_file}!")
app.quit()
