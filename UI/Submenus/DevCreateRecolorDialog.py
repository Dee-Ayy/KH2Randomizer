from pathlib import Path

import numpy
from PIL import Image
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QDialog, QGridLayout, QLabel, QLineEdit, QHBoxLayout, QSpinBox, QCheckBox
from numpy import ndarray

from Module.texture import make_hsva_conditions, recolor_image, RecolorDefinition


class DevCreateRecolorDialog(QDialog):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Texture Recolor")

        hbox = QHBoxLayout()
        hbox.setAlignment(Qt.AlignTop)

        grid = QGridLayout()
        row = 0

        grid.addWidget(QLabel("Image File"), row, 0)
        self.image_path_field = QLineEdit(r"C:\games\kh2\extract\kh2\remastered\obj\P_EX100.mdlx\-0.dds")
        self.image_path_field.textChanged.connect(self._do_preview)
        grid.addWidget(self.image_path_field, row, 1, 1, 2)
        row = row + 1

        grid.addWidget(QLabel("Hue Range"), row, 0)
        self.hue_start_field = QSpinBox()
        self.hue_start_field.setValue(0)
        self.hue_start_field.setRange(0, 360)
        self.hue_start_field.valueChanged.connect(self._do_preview)
        self.hue_end_field = QSpinBox()
        self.hue_end_field.setRange(0, 360)
        self.hue_end_field.setValue(360)
        self.hue_end_field.valueChanged.connect(self._do_preview)
        grid.addWidget(self.hue_start_field, row, 1)
        grid.addWidget(self.hue_end_field, row, 2)
        row = row + 1

        grid.addWidget(QLabel("Saturation Range"), row, 0)
        self.saturation_start_field = QSpinBox()
        self.saturation_start_field.setValue(0)
        self.saturation_start_field.setRange(0, 100)
        self.saturation_start_field.valueChanged.connect(self._do_preview)
        self.saturation_end_field = QSpinBox()
        self.saturation_end_field.setRange(0, 100)
        self.saturation_end_field.setValue(100)
        self.saturation_end_field.valueChanged.connect(self._do_preview)
        grid.addWidget(self.saturation_start_field, row, 1)
        grid.addWidget(self.saturation_end_field, row, 2)
        row = row + 1

        grid.addWidget(QLabel("Value Range"), row, 0)
        self.value_start_field = QSpinBox()
        self.value_start_field.setValue(0)
        self.value_start_field.setRange(0, 100)
        self.value_start_field.valueChanged.connect(self._do_preview)
        self.value_end_field = QSpinBox()
        self.value_end_field.setRange(0, 100)
        self.value_end_field.setValue(100)
        self.value_end_field.valueChanged.connect(self._do_preview)
        grid.addWidget(self.value_start_field, row, 1)
        grid.addWidget(self.value_end_field, row, 2)
        row = row + 1

        self.apply_saturation_and_value = QCheckBox("Apply New Saturation and Value")
        self.apply_saturation_and_value.stateChanged.connect(self._do_preview)
        grid.addWidget(self.apply_saturation_and_value, row, 0, 1, 3)
        row = row + 1

        grid.addWidget(QLabel("New Saturation"), row, 0)
        self.new_saturation_field = QSpinBox()
        self.new_saturation_field.setRange(0, 100)
        self.new_saturation_field.setValue(50)
        self.new_saturation_field.valueChanged.connect(self._do_preview)

        grid.addWidget(self.new_saturation_field, row, 1, 1, 2)
        row = row + 1

        grid.addWidget(QLabel("Value Offset"), row, 0)
        self.value_offset_field = QSpinBox()
        self.value_offset_field.setRange(-100, 100)
        self.value_offset_field.setValue(0)
        self.value_offset_field.valueChanged.connect(self._do_preview)

        grid.addWidget(self.value_offset_field, row, 1, 1, 2)
        row = row + 1

        hbox.addLayout(grid)

        image_grid = QGridLayout()
        self.image_view = QLabel()
        self.image_view.setScaledContents(True)
        self.image_view.setFixedSize(320, 320)
        row = 0
        image_grid.addWidget(self.image_view, row, 0)

        self.updated_image_view_0 = QLabel()
        self.updated_image_view_0.setScaledContents(True)
        self.updated_image_view_0.setFixedSize(320, 320)
        image_grid.addWidget(self.updated_image_view_0, row, 1)
        row = row + 1

        self.updated_image_view_1 = QLabel()
        self.updated_image_view_1.setScaledContents(True)
        self.updated_image_view_1.setFixedSize(320, 320)
        image_grid.addWidget(self.updated_image_view_1, row, 0)

        self.updated_image_view_2 = QLabel()
        self.updated_image_view_2.setScaledContents(True)
        self.updated_image_view_2.setFixedSize(320, 320)
        image_grid.addWidget(self.updated_image_view_2, row, 1)
        row = row + 1

        hbox.addLayout(image_grid)

        self.setLayout(hbox)
        self.setMinimumWidth(1200)
        self.setMinimumHeight(800)

        self._do_preview()

    def _do_preview(self):
        image_path = Path(self.image_path_field.text())
        if not image_path.is_file():
            self.image_view.clear()
            self.updated_image_view_0.clear()
            self.updated_image_view_1.clear()
            self.updated_image_view_2.clear()
            return
        with Image.open(image_path) as base_image:
            self.image_view.setPixmap(base_image.toqpixmap())

            conditions = make_hsva_conditions(
                hue_range=((self.hue_start_field.value()), (self.hue_end_field.value())),
                saturation_range=((self.saturation_start_field.value()), (self.saturation_end_field.value())),
                value_range=((self.value_start_field.value()), (self.value_end_field.value()))
            )

            if self.apply_saturation_and_value.isChecked():
                new_saturation = self.new_saturation_field.value()
                value_offset = self.value_offset_field.value()
            else:
                new_saturation = None
                value_offset = None

            image_array = numpy.array(base_image)

            recolor_90 = RecolorDefinition(conditions, 90, new_saturation, value_offset)
            recolored_image = Image.fromarray(self._recolor_image(image_array, recolor_90), "RGBA")
            self.updated_image_view_0.setPixmap(recolored_image.toqpixmap())

            recolor_180 = RecolorDefinition(conditions, 180, new_saturation, value_offset)
            recolored_image = Image.fromarray(self._recolor_image(image_array, recolor_180), "RGBA")
            self.updated_image_view_1.setPixmap(recolored_image.toqpixmap())

            recolor_270 = RecolorDefinition(conditions, 270, new_saturation, value_offset)
            recolored_image = Image.fromarray(self._recolor_image(image_array, recolor_270), "RGBA")
            self.updated_image_view_2.setPixmap(recolored_image.toqpixmap())

    @staticmethod
    def _recolor_image(rgb_array: ndarray, recolor_definition: RecolorDefinition) -> ndarray:
        return recolor_image(rgb_array, recolor_definitions=[recolor_definition])
