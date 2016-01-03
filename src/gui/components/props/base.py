from ...base import *
from ...panel import *


class ObjectTypes(object):

    _types = {}

    @classmethod
    def add_type(cls, obj_type_id, obj_type_name):

        cls._types[obj_type_id] = obj_type_name

    @classmethod
    def get_types(cls):

        return cls._types


class PropertyPanel(Panel):

    _property_classes = {}
    _properties = {}

    @classmethod
    def add_properties(cls, obj_type, properties):

        cls._property_classes[obj_type] = properties

    def __init__(self, parent):

        Panel.__init__(self, parent, "Object properties")

        self._obj_type = ""
        self._sel_obj_type = ""
        self._sel_obj_count = 0
        self._parent = parent
        self._width = parent.get_width()

        self._colors = {
            "disabled": wx.Colour(127, 127, 127),
            "custom": wx.Colour(255, 255, 0)
        }

        self.GetSizer().SetMinSize(wx.Size(self._width, 1))
        self._parent.GetSizer().Add(self)

        id_section = self.add_section("id", "Name and color")
        section_sizer = id_section.get_client_sizer()
        sizer = wx.BoxSizer()
        section_sizer.Add(sizer)
        self._name_field = PanelInputField(self, id_section, sizer, 130)
        self._name_field.add_value(
            "name", "string", handler=self.__handle_value)
        self._name_field.set_input_init("name", self.__init_input)
        self._name_field.show_value("name")
        self._name_field.show_text(False)
        self._name_field.enable(False)
        self._name_field.set_input_parser("name", self.__parse_object_name)
        sizer.Add((5, 0))
        self._color_picker = PanelColorPickerCtrl(
            self, id_section, sizer, self.__handle_color)
        self._color_picker.show_color("none")
        self._color_picker.Enable(False)

        create_section = self.add_section("create", "Creation")

        yellow = wx.Colour(255, 255, 0)
        radio_btns = PanelRadioButtonGroup(
            self, create_section, "Position", dot_color=yellow)
        radio_btns.add_button("grid_pos", "Coord. system origin")
        radio_btns.add_button("cam_target_pos", "Camera target")
        radio_btns.set_selected_button("grid_pos")
        self._radio_btns = radio_btns

        sizer = create_section.get_client_sizer()

        bitmap_paths = PanelButton.get_bitmap_paths("panel_button")

        label = "Create object"
        bitmaps = PanelButton.create_button_bitmaps(
            "*%s" % label, bitmap_paths)
        sizer_args = (0, wx.ALIGN_CENTER_HORIZONTAL)
        btn = PanelButton(self, create_section, sizer, bitmaps, label, "",
                          self.__create_object, sizer_args)

        for obj_type, prop_cls in self._property_classes.iteritems():
            self._properties[obj_type] = prop_cls(self)

        sizer = self.get_bottom_ctrl_sizer()
        sizer_args = (0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 10)

        label = "Make editable"
        bitmaps = PanelButton.create_button_bitmaps(
            "*%s" % label, bitmap_paths)
        PanelButton(self, create_section, sizer, bitmaps, label, "Turn into editable geometry",
                    self.__make_editable, sizer_args)

        parent.add_panel(self)
        self.update()
        self.finalize()

        def finalize_sections():

            create_section.set_title_hilite_color((1., 1., .5, .65))
            create_section.set_title_hilited()
            create_section.expand(False)
            self.show_section("create", False, update=False)
            self.show_bottom_controls(False, update=False)

            for props in self._properties.itervalues():
                for section_id in props.get_section_ids():
                    self.show_section(section_id, False, update=False)

            self.update_parent()

        wx.CallAfter(finalize_sections)

        def set_obj_prop(obj_type, *args, **kwargs):

            if obj_type:
                self._properties[obj_type].set_object_property(*args, **kwargs)

        def check_selection_count():

            if self._obj_type:
                self._properties[self._obj_type].check_selection_count()

        def set_obj_prop_default(obj_type, *args, **kwargs):

            if obj_type:
                self._properties[obj_type].set_object_property_default(
                    *args, **kwargs)

        Mgr.add_app_updater("selected_obj_type", self.show)
        Mgr.add_app_updater("selected_obj_prop", set_obj_prop)
        Mgr.add_app_updater("selection_count", check_selection_count)
        Mgr.add_app_updater("obj_prop_default", set_obj_prop_default)
        Mgr.add_app_updater("creation", self.__update_sections)
        Mgr.add_app_updater("selected_obj_name", self.__set_object_name)
        Mgr.add_app_updater("selected_obj_color", self.__set_object_color)
        Mgr.add_app_updater("selection_count", self.__check_selection_count)
        Mgr.add_app_updater("sel_color_count",
                            self.__check_selection_color_count)
        Mgr.add_app_updater("next_obj_name", self.__set_next_object_name)
        Mgr.accept("display_next_obj_color", self.__set_next_object_color)

    def setup(self):

        for props in self._properties.itervalues():
            props.setup()

    def get_clipping_rect(self):

        panel_rect = self.GetRect()
        width, height = panel_rect.size
        y_orig = self.GetParent().GetPosition()[1] + panel_rect.y
        clipping_rect = wx.Rect(0, -y_orig, *self.GetGrandParent().GetSize())

        return clipping_rect

    def __make_editable(self):

        Mgr.update_remotely("selected_obj_prop", "editable state", True)

    def __update_sections(self, creation_status):

        obj_type = self._sel_obj_type
        props = self._properties[obj_type] if obj_type else None
        extra_section_ids = props.get_extra_section_ids() if props else []

        if creation_status == "started":

            self.show_section("create", update=False)
            self.show_bottom_controls(False, update=False)

            for section_id in extra_section_ids:
                self.show_section(section_id, False, update=False)

        elif creation_status == "ended":

            if self._sel_obj_count == 1:
                for section_id in extra_section_ids:
                    self.show_section(section_id, update=False)

            if props and props.get_base_type() == "primitive":
                self.show_bottom_controls(update=False)

            self.show_section("create", False, update=False)

        self._parent.Refresh()
        self.GetSizer().Layout()
        self.update_parent()

    def __init_input(self):

        if self._name_field.get_text_color() == self._colors["disabled"]:
            self._name_field.clear()

    def __handle_value(self, value_id, value):

        if Mgr.get_global("active_creation_type"):
            Mgr.update_remotely("custom_obj_name", self._obj_type, value)
        else:
            Mgr.update_remotely("selected_obj_name", value)

    def __parse_object_name(self, name):

        parsed_name = name.strip(" *")

        if Mgr.get_global("active_creation_type"):
            return parsed_name

        return parsed_name if parsed_name else None

    def __set_object_name(self, name=None):

        if name is None:
            self._name_field.show_text(False)
            return

        self._name_field.set_value("name", name)
        self._name_field.show_text()

    def __set_next_object_name(self, name):

        self._name_field.enable()
        self._name_field.set_text_color(self._colors["custom"])
        self._name_field.set_value("name", name)
        self._name_field.show_text()

    def __handle_color(self, color):

        color_values = Mgr.convert_to_remote_format("color", color.Get())

        if Mgr.get_global("active_creation_type"):
            Mgr.set_global("next_%s_color" % self._obj_type, color_values)
            self._color_picker.set_color(color_values)
        else:
            Mgr.update_remotely("selected_obj_color", color_values)

    def __set_object_color(self, color_values):

        self._color_picker.set_color(color_values)

    def __set_next_object_color(self):

        next_color = Mgr.get_global("next_%s_color" % self._obj_type)
        self._color_picker.Enable(True if next_color else False)
        self._color_picker.show_color("single" if next_color else "none")

        if next_color:
            self._color_picker.set_color(next_color)

    def __check_selection_count(self):

        self._sel_obj_count = sel_count = Mgr.get_global("selection_count")
        self._name_field.enable(sel_count > 0)
        self._name_field.show_text(sel_count > 0)
        self._name_field.set_text_color(
            self._colors["disabled"] if sel_count > 1 else None)

        if self._obj_type:

            extra_section_ids = self._properties[
                self._obj_type].get_extra_section_ids()

            if extra_section_ids:

                if sel_count > 1:
                    for section_id in extra_section_ids:
                        self.show_section(section_id, False, update=False)
                else:
                    for section_id in extra_section_ids:
                        self.show_section(section_id, True, update=False)

                self._parent.Refresh()
                self.GetSizer().Layout()
                self.update_parent()

    def __check_selection_color_count(self):

        count = Mgr.get_global("sel_color_count")
        self._color_picker.Enable(count > 0)
        self._color_picker.show_color(("single" if count == 1 else "multiple")
                                      if count > 0 else "none")

    def __create_object(self):

        pos_id = self._radio_btns.get_selected_button()
        Mgr.update_app("instant_creation", pos_id)
        self.__set_next_object_color()

    def enable(self, enable=True):

        if not Panel.enable(self, enable):
            return

        if Mgr.get_global("active_creation_type"):
            self._name_field.enable()
            self._color_picker.enable()
        else:
            self.__check_selection_count()
            self.__check_selection_color_count()

    def disable(self, show=True):

        if not Panel.disable(self, show):
            return

        self._name_field.enable(False)
        self._color_picker.disable()

    def get_width(self):

        return self._width

    def get_client_width(self):

        return self._width - self.get_client_offset() * 2

    def show(self, obj_type):

        props = self._properties

        if (obj_type and obj_type not in props) or self._obj_type == obj_type:
            return

        prev_section_ids = props[
            self._obj_type].get_section_ids() if self._obj_type else []
        next_section_ids = props[
            obj_type].get_section_ids() if obj_type else []
        extra_section_ids = props[
            obj_type].get_extra_section_ids() if obj_type else []

        in_creation_mode = Mgr.get_global("active_creation_type") != ""

        for section_id in next_section_ids:
            self.show_section(section_id, update=False)

        if obj_type and props[obj_type].get_base_type() == "primitive":
            self.show_bottom_controls(update=False)
        else:
            self.show_bottom_controls(False, update=False)

        if in_creation_mode:

            self.show_bottom_controls(False, update=False)

            for section_id in extra_section_ids:
                self.show_section(section_id, False, update=False)

        for section_id in prev_section_ids:
            self.show_section(section_id, False, update=False)

        self._obj_type = obj_type

        if in_creation_mode:
            self._color_picker.show_color("single")
            self.__set_next_object_color()
        else:
            self._sel_obj_type = obj_type

        self._parent.Refresh()
        self.GetSizer().Layout()
        self.update_parent()