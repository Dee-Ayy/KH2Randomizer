from Class import settingkey
from Class.seedSettings import SeedSettings
from List.ItemList import Items
from UI.Submenus.SubMenu import KH2Submenu
from PySide6.QtWidgets import (QPushButton,QHBoxLayout,QWidget)


class SeedModMenu(KH2Submenu):

    def __init__(self, settings: SeedSettings):
        super().__init__(title='Seed Modifiers', settings=settings, in_layout='horizontal')

        self.start_column()
        self.add_option(settingkey.GLASS_CANNON)
        self.add_option(settingkey.START_NO_AP)
        self.end_column()

        self.start_column()
        # self.add_option(settingkey.BETTER_JUNK)
        self.add_option(settingkey.JUNK_ITEMS)


        junk_widget_layout = QHBoxLayout()
        junk_widget = QWidget()
        junk_widget.setLayout(junk_widget_layout)
        select_all_junk = QPushButton("Select All")
        select_better_junk = QPushButton("Better Junk")
        junk_widget_layout.addWidget(select_all_junk)
        junk_widget_layout.addWidget(select_better_junk)
        self._add_option_widget("","",junk_widget)
        self.end_column(stretch_at_end=False)

        select_all_junk.clicked.connect(lambda: self.toggle_all_items())
        select_better_junk.clicked.connect(lambda: self.toggle_better_junk())

        self.start_column()
        self.add_option(settingkey.AS_DATA_SPLIT)
        self.add_option(settingkey.CUPS_GIVE_XP)
        self.add_option(settingkey.RETRY_DFX)
        self.add_option(settingkey.REMOVE_DAMAGE_CAP)
        self.end_column()

        self.finalizeMenu()

    def toggle_all_items(self):
        setting,widget = self.widgets_and_settings_by_name[settingkey.JUNK_ITEMS]
        for selected in setting.choice_keys:
            index = setting.choice_keys.index(selected)
            widget.item(index).setSelected(True)

    def toggle_better_junk(self):
        betterJunk = [
            int(elem.Id) for elem in Items.getJunkList(True)
        ]
        setting,widget = self.widgets_and_settings_by_name[settingkey.JUNK_ITEMS]
        for selected in setting.choice_keys:
            index = setting.choice_keys.index(selected)
            widget.item(index).setSelected(int(selected) in betterJunk)