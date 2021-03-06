from ...base import *
from ...button import *
from ...panel import *


class SubobjectPanel(Panel):

    def __init__(self, stack):

        Panel.__init__(self, stack, "subobj", "Subobject level")

        self._btns = {}
        self._comboboxes = {}
        self._checkbuttons = {}
        self._colorboxes = {}
        self._fields = {}
        self._radio_btns = {}
        self._uv_lvl_btns = uv_lvl_btns = ToggleButtonGroup()
        self._prev_obj_lvl = ""
        self._subobj_state_ids = {"vert": [], "edge": [], "poly": [], "part": []}

        top_container = self.get_top_container()

        btn_sizer = GridSizer(rows=0, columns=2, gap_h=5, gap_v=5)
        borders = (5, 5, 10, 5)
        top_container.add(btn_sizer, expand=True, borders=borders)

        get_command = lambda subobj_type: lambda: self.__set_subobj_level(subobj_type)
        subobj_types = ("vert", "edge", "poly", "part")
        subobj_text = ("Vertex", "Edge", "Polygon", "Prim. part")
        tooltip_texts = tuple(f"{t} level" for t in subobj_text[:3]) + ("Primitive part level",)
        btns = []

        for subobj_type, text, tooltip_text in zip(subobj_types, subobj_text, tooltip_texts):
            btn = PanelButton(top_container, text, "", tooltip_text)
            toggle = (get_command(subobj_type), lambda: None)
            uv_lvl_btns.add_button(btn, subobj_type, toggle)
            btns.append(btn)
            btn_sizer.add(btn, expand_h=True)

        btn_sizer.set_column_proportion(0, 1.)
        btn_sizer.set_column_proportion(1, 1.)

        # ************************* Vertex section ****************************

        section = self.add_section("uv_vert_props", "Vertices")

        sizer = Sizer("horizontal")
        section.add(sizer, expand=True)

        text = "Pick via polygon"
        checkbtn = PanelCheckButton(section, self.__handle_picking_via_poly, text)
        self._checkbuttons["pick_vert_via_poly"] = checkbtn
        sizer.add(checkbtn, alignment="center_v")
        sizer.add((5, 0), proportion=1.)
        text = "aim"
        checkbtn = PanelCheckButton(section, self.__handle_picking_by_aiming, text)
        self._checkbuttons["pick_vert_by_aiming"] = checkbtn
        sizer.add(checkbtn, alignment="center_v")
        sizer.add((0, 0), proportion=1.)

        section.add((0, 10))

        text = "Break"
        tooltip_text = "Break selected vertices"
        btn = PanelButton(section, text, "", tooltip_text, self.__break_vertices)
        self._btns["break_verts"] = btn
        section.add(btn)

        # ************************* Edge section ******************************

        section = self.add_section("uv_edge_props", "Edges")

        sizer = Sizer("horizontal")
        section.add(sizer, expand=True)

        text = "Pick via polygon"
        checkbtn = PanelCheckButton(section, self.__handle_picking_via_poly, text)
        self._checkbuttons["pick_edge_via_poly"] = checkbtn
        sizer.add(checkbtn, alignment="center_v")
        sizer.add((5, 0), proportion=1.)
        text = "aim"
        checkbtn = PanelCheckButton(section, self.__handle_picking_by_aiming, text)
        self._checkbuttons["pick_edge_by_aiming"] = checkbtn
        sizer.add(checkbtn, alignment="center_v")
        sizer.add((0, 0), proportion=1.)

        def handler(by_seam):

            GD["uv_edit_options"]["sel_edges_by_seam"] = by_seam

        text = "Select by seam"
        checkbtn = PanelCheckButton(section, handler, text)
        self._checkbuttons["sel_edges_by_seam"] = checkbtn
        section.add(checkbtn)

        section.add((0, 10))

        btn_sizer = Sizer("horizontal")
        section.add(btn_sizer, expand=True)

        text = "Split"
        tooltip_text = "Split selected edges"
        btn = PanelButton(section, text, "", tooltip_text, self.__split_edges)
        self._btns["split_edges"] = btn
        btn_sizer.add(btn, proportion=1.)

        btn_sizer.add((5, 0))

        text = "Stitch"
        tooltip_text = "Stitch selected seam edges"
        btn = PanelButton(section, text, "", tooltip_text, self.__stitch_edges)
        self._btns["stitch_edges"] = btn
        btn_sizer.add(btn, proportion=1.)

        # ************************* Polygon section ***************************

        section = self.add_section("uv_poly_props", "Polygons")

        def handler(by_cluster):

            GD["uv_edit_options"]["sel_polys_by_cluster"] = by_cluster

        text = "Select by cluster"
        checkbtn = PanelCheckButton(section, handler, text)
        self._checkbuttons["sel_polys_by_cluster"] = checkbtn
        section.add(checkbtn)

        section.add((0, 10))

        btn_sizer = Sizer("horizontal")
        section.add(btn_sizer, expand=True)

        text = "Detach"
        tooltip_text = "Detach selected polygons"
        btn = PanelButton(section, text, "", tooltip_text, self.__detach_polygons)
        self._btns["detach_polys"] = btn
        btn_sizer.add(btn, proportion=1.)

        btn_sizer.add((5, 0))

        text = "Stitch"
        tooltip_text = "Stitch selected polygon seam edges"
        btn = PanelButton(section, text, "", tooltip_text, self.__stitch_polygons)
        self._btns["stitch_polys"] = btn
        btn_sizer.add(btn, proportion=1.)

        section.add((0, 5))

        group = section.add_group("Color")

        text = "Unselected"
        group.add(PanelText(group, text))

        group.add((0, 6))

        sizer = Sizer("horizontal")
        group.add(sizer)

        text = "RGB:"
        sizer.add(PanelText(group, text), alignment="center_v")
        sizer.add((5, 0))
        dialog_title = "Pick unselected polygon color"
        command = lambda col: self.__handle_poly_rgb("unselected", col)
        colorbox = PanelColorBox(group, command, dialog_title=dialog_title)
        self._colorboxes["unselected_poly_rgb"] = colorbox
        sizer.add(colorbox, alignment="center_v")
        sizer.add((5, 0))
        text = "Alpha:"
        sizer.add(PanelText(group, text), alignment="center_v")
        sizer.add((5, 0))
        val_id = "unselected_poly_alpha"
        field = PanelSliderField(group, val_id, "float", (0., 1.),
                                 self.__handle_poly_value, 50)
        self._fields[val_id] = field
        sizer.add(field, alignment="center_v")

        group.add((0, 10))

        text = "Selected"
        group.add(PanelText(group, text))

        group.add((0, 6))

        sizer = Sizer("horizontal")
        group.add(sizer)

        text = "RGB:"
        sizer.add(PanelText(group, text), alignment="center_v")
        sizer.add((5, 0))
        dialog_title = "Pick selected polygon color"
        command = lambda col: self.__handle_poly_rgb("selected", col)
        colorbox = PanelColorBox(group, command, dialog_title=dialog_title)
        self._colorboxes["selected_poly_rgb"] = colorbox
        sizer.add(colorbox, alignment="center_v")
        sizer.add((5, 0))
        text = "Alpha:"
        sizer.add(PanelText(group, text), alignment="center_v")
        sizer.add((5, 0))
        val_id = "selected_poly_alpha"
        field = PanelSliderField(group, val_id, "float", (0., 1.),
                                 self.__handle_poly_value, 50)
        self._fields[val_id] = field
        sizer.add(field, alignment="center_v")

        # ********************* Primitive part section ***********************

        section = self.add_section("uv_part_props", "Primitive parts")

        text = "Reset UVs to defaults"
        tooltip_text = "Reset UVs of selected parts to their default values"
        btn = PanelButton(section, text, "", tooltip_text, self.__reset_default_part_uvs)
        self._btns["reset_part_uvs"] = btn
        section.add(btn, alignment="center_h")

        section.add((0, 5))

        group = section.add_group("Color")

        text = "Unselected"
        group.add(PanelText(group, text))

        group.add((0, 6))

        sizer = Sizer("horizontal")
        group.add(sizer)

        text = "RGB:"
        sizer.add(PanelText(group, text), alignment="center_v")
        sizer.add((5, 0))
        dialog_title = "Pick unselected primitive part color"
        command = lambda col: self.__handle_part_rgb("unselected", col)
        colorbox = PanelColorBox(group, command, dialog_title=dialog_title)
        self._colorboxes["unselected_part_rgb"] = colorbox
        sizer.add(colorbox, alignment="center_v")
        sizer.add((5, 0))
        text = "Alpha:"
        sizer.add(PanelText(group, text), alignment="center_v")
        sizer.add((5, 0))
        val_id = "unselected_part_alpha"
        field = PanelSliderField(group, val_id, "float", (0., 1.),
                                 self.__handle_part_value, 50)
        self._fields[val_id] = field
        sizer.add(field, alignment="center_v")

        group.add((0, 10))

        text = "Selected"
        group.add(PanelText(group, text))

        group.add((0, 6))

        sizer = Sizer("horizontal")
        group.add(sizer)

        text = "RGB:"
        sizer.add(PanelText(group, text), alignment="center_v")
        sizer.add((5, 0))
        dialog_title = "Pick selected primitive part color"
        command = lambda col: self.__handle_part_rgb("selected", col)
        colorbox = PanelColorBox(group, command, dialog_title=dialog_title)
        self._colorboxes["selected_part_rgb"] = colorbox
        sizer.add(colorbox, alignment="center_v")
        sizer.add((5, 0))
        text = "Alpha:"
        sizer.add(PanelText(group, text), alignment="center_v")
        sizer.add((5, 0))
        val_id = "selected_part_alpha"
        field = PanelSliderField(group, val_id, "float", (0., 1.),
                                 self.__handle_part_value, 50)
        self._fields[val_id] = field
        sizer.add(field, alignment="center_v")

    def setup(self):

        for subobj_lvl in ("vert", "edge", "poly", "part"):
            self.get_section(f"uv_{subobj_lvl}_props").hide()

    def add_interface_updaters(self):

        Mgr.add_app_updater("uv_level", self.__set_uv_level, interface_id="uv")
        Mgr.add_app_updater("poly_color", self.__set_poly_color, interface_id="uv")
        Mgr.add_app_updater("part_color", self.__set_part_color, interface_id="uv")
        Mgr.add_app_updater("uv_edit_options", self.__update_uv_edit_options, interface_id="uv")

    def __update_uv_edit_options(self):

        for option, value in GD["uv_edit_options"].items():
            if option == "pick_via_poly":
                for subobj_type in ("vert", "edge"):
                    self._checkbuttons[f"pick_{subobj_type}_via_poly"].check(value)
            elif option == "pick_by_aiming":
                for subobj_type in ("vert", "edge"):
                    self._checkbuttons[f"pick_{subobj_type}_by_aiming"].check(value)
            elif option in self._checkbuttons:
                self._checkbuttons[option].check(value)
            elif option in self._fields:
                self._fields[option].set_value(value)

    def __set_uv_level(self, uv_level):

        self._uv_lvl_btns.set_active_button(uv_level)
        self.get_section(f"uv_{uv_level}_props").show()

        for subobj_lvl in ("vert", "edge", "poly", "part"):
            if subobj_lvl != uv_level:
                self.get_section(f"uv_{subobj_lvl}_props").hide()

        for state_id in self._subobj_state_ids.get(self._prev_obj_lvl, []):
            Mgr.exit_state(state_id)

        self._prev_obj_lvl = uv_level

    def __set_subobj_level(self, uv_level):

        Mgr.update_interface("uv", "uv_level", uv_level)

    def __handle_picking_via_poly(self, via_poly):

        Mgr.update_interface_remotely("uv", "picking_via_poly", via_poly)

        for subobj_type in ("vert", "edge"):
            self._checkbuttons[f"pick_{subobj_type}_via_poly"].check(via_poly)

    def __handle_picking_by_aiming(self, by_aiming):

        GD["uv_edit_options"]["pick_by_aiming"] = by_aiming
        GD["subobj_edit_options"]["pick_by_aiming"] = by_aiming

        for subobj_type in ("vert", "edge"):
            self._checkbuttons[f"pick_{subobj_type}_by_aiming"].check(by_aiming)

    def __break_vertices(self):

        Mgr.update_interface_remotely("uv", "vert_break")

    def __split_edges(self):

        Mgr.update_interface_remotely("uv", "edge_split")

    def __stitch_edges(self):

        Mgr.update_interface_remotely("uv", "edge_stitch")

    def __detach_polygons(self):

        Mgr.update_interface_remotely("uv", "poly_detach")

    def __stitch_polygons(self):

        Mgr.update_interface_remotely("uv", "poly_stitch")

    def __reset_default_part_uvs(self):

        Mgr.update_interface_remotely("uv", "part_uv_defaults_reset")

    def __handle_poly_rgb(self, sel_state, color):

        r, g, b = color
        Mgr.update_interface_remotely("uv", "poly_color", sel_state, "rgb", (r, g, b, 1.))

    def __handle_poly_value(self, value_id, value, state="done"):

        sel_state = value_id.replace("_poly_alpha", "")
        Mgr.update_interface_remotely("uv", "poly_color", sel_state, "alpha", value)

    def __set_poly_color(self, sel_state, channels, value):

        if channels == "rgb":
            self._colorboxes[f"{sel_state}_poly_rgb"].set_color(value[:3])
        elif channels == "alpha":
            prop_id = f"{sel_state}_poly_alpha"
            self._fields[prop_id].set_value(value)

    def __handle_part_rgb(self, sel_state, color):

        r, g, b = color
        Mgr.update_interface_remotely("uv", "part_color", sel_state, "rgb", (r, g, b, 1.))

    def __handle_part_value(self, value_id, value, state="done"):

        sel_state = value_id.replace("_part_alpha", "")
        Mgr.update_interface_remotely("uv", "part_color", sel_state, "alpha", value)

    def __set_part_color(self, sel_state, channels, value):

        if channels == "rgb":
            self._colorboxes[f"{sel_state}_part_rgb"].set_color(value[:3])
        elif channels == "alpha":
            prop_id = f"{sel_state}_part_alpha"
            self._fields[prop_id].set_value(value)
