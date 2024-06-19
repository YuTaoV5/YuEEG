import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtkmodules.all as vtk

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("VTK with PyQt Example")
        self.frame = QWidget()
        self.vl = QVBoxLayout()

        # VTK Renderer
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        self.vl.addWidget(self.vtkWidget)

        self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()

        # Load OBJ and MTL files
        self.load_obj_file("resource/PCB.obj", "resource/PCB.mtl")

        # Add a light to the renderer
        self.add_light()

        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)

        self.show()
        self.iren.Initialize()

    def load_obj_file(self, obj_file_path, mtl_file_path):
        # Create an OBJ importer
        importer = vtk.vtkOBJImporter()
        importer.SetFileName(obj_file_path)
        importer.SetFileNameMTL(mtl_file_path)
        importer.SetTexturePath("resource")
        importer.SetRenderWindow(self.vtkWidget.GetRenderWindow())
        importer.Update()

        self.ren.ResetCamera()

    def add_light(self):
        # Create a light
        light = vtk.vtkLight()
        light.SetFocalPoint(0, 0, 0)
        light.SetPosition(1, 1, 1)
        light.SetIntensity(0.3)  # Adjust intensity to make the scene darker

        self.ren.AddLight(light)
        # Set a darker background color
        colors = vtk.vtkNamedColors()
        self.ren.SetBackground(colors.GetColor3d("DarkSlateGray"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
