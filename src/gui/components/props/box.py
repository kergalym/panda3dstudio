from .base import *


class BoxProperties:

    def __init__(self, panel):

        self._panel = panel
        self._fields = {}
        self._segments_default = {"x": 1, "y": 1, "z": 1}

        section = panel.add_section("box_props", "Box properties", hidden=True)

        axes = "xyz"
        dimensions = ("width", "depth", "height")
        prop_types = ("size", "segments")
        val_types = ("float", "int")
        parsers = (self.__parse_dimension_input, self.__parse_segments_input)

        for prop_type, val_type, parser in zip(prop_types, val_types, parsers):

            group = section.add_group(prop_type.title())
            sizer = GridSizer(rows=0, columns=2, gap_h=5, gap_v=2)
            group.add(sizer, expand=True)

            for axis, dim in zip(axes, dimensions):
                prop_id = f"{prop_type}_{axis}"
                text = f"{axis.upper()} ({dim}):"
                sizer.add(PanelText(group, text), alignment_v="center_v")
                field = PanelInputField(group, prop_id, val_type, self.__handle_value, 80)
                field.set_input_parser(parser)
                self._fields[prop_id] = field
                sizer.add(field, proportion_h=1., alignment_v="center_v")

        self._fields["size_z"].set_input_parser(self.__parse_height_input)

        text = "Convert to planes"
        tooltip_text = "Turn sides into separate plane primitives"
        command = self.__replace_with_planes
        btn = PanelButton(section, text, "", tooltip_text, command)
        borders = (10, 10, 0, 10)
        section.add(btn, alignment="center_h", borders=borders)

    def setup(self): pass

    def __handle_value(self, value_id, value, state="done"):

        in_creation_mode = GD["active_creation_type"]

        if "segments" in value_id:
            prop_id, axis = value_id.split("_")
            val = self._segments_default if in_creation_mode else {}
            val[axis] = value
            val = val.copy()
        else:
            prop_id = value_id
            val = value

        if in_creation_mode:
            Mgr.update_app("box_prop_default", prop_id, val)
            return

        Mgr.update_remotely("selected_obj_prop", prop_id, val)

    def __parse_dimension_input(self, input_text):

        try:
            return max(.001, abs(float(eval(input_text))))
        except:
            return None

    def __parse_height_input(self, input_text):

        try:
            value = float(eval(input_text))
        except:
            return None

        sign = -1. if value < 0. else 1.

        return max(.001, abs(value)) * sign

    def __parse_segments_input(self, input_text):

        try:
            return max(1, abs(int(eval(input_text))))
        except:
            return None

    def __replace_with_planes(self):

        if GD["active_creation_type"] != "":
            return

        Mgr.update_remotely("box_to_planes")

    def get_base_type(self):

        return "primitive"

    def get_section_ids(self):

        return ["box_props"] + self.get_extra_section_ids()

    def get_extra_section_ids(self):

        return []

    def set_object_property_default(self, prop_id, value):

        color = (1., 1., 0., 1.)

        if prop_id == "segments":
            self._segments_default.update(value)
            for axis in "xyz":
                value_id = "segments_" + axis
                field = self._fields[value_id]
                field.show_text()
                field.set_value(value[axis])
                field.set_text_color(color)
        elif prop_id in self._fields:
            field = self._fields[prop_id]
            field.show_text()
            field.set_value(value)
            field.set_text_color(color)

    def set_object_property(self, prop_id, value):

        if not (prop_id == "segments" or prop_id in self._fields):
            return

        if prop_id == "segments":
            for axis in "xyz":
                value_id = "segments_" + axis
                field = self._fields[value_id]
                field.set_value(value[axis])
        else:
            field = self._fields[prop_id]
            field.set_value(value)

    def check_selection_count(self):

        sel_count = GD["selection_count"]
        multi_sel = sel_count > 1
        color = (.5, .5, .5, 1.) if multi_sel else None

        for field in self._fields.values():
            field.set_text_color(color)
            field.show_text(not multi_sel)


ObjectTypes.add_type("box", "Box")
PropertyPanel.add_properties("box", BoxProperties)
