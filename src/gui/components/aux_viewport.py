from ..base import *
from ..button import Button
from ..tooltip import ToolTip
from ..dialog import *
from direct.interval.IntervalGlobal import LerpColorScaleInterval, Sequence


class ViewportButton(Button):

    _gfx = {
        "normal": (("viewport_button_normal_left", "viewport_button_normal_center",
                    "viewport_button_normal_right"),),
        "hilited": (("viewport_button_hilited_left", "viewport_button_hilited_center",
                     "viewport_button_hilited_right"),),
        "pressed": (("viewport_button_pressed_left", "viewport_button_pressed_center",
                     "viewport_button_pressed_right"),)
    }

    def __init__(self, parent, name, icon_id, tooltip_text, command):

        Button.__init__(self, parent, self._gfx, "", icon_id, tooltip_text, command,
                        button_type="viewport_button")

        self._cursor_region = MouseWatcherRegion(f"viewport_button_{name}", 0., 0., 0., 0.)
        self.mouse_region.sort = 11

    def get_cursor_region(self):

        return self._cursor_region

    def update_mouse_region_frames(self, exclude="", recurse=True):

        Button.update_mouse_region_frames(self, exclude, recurse)

        x, y = self.get_pos(from_root=True)
        w, h = self.get_size()
        w_ref, h_ref = Mgr.get("window_size")
        l, r, b, t = get_relative_region_frame(x, y, w, h, w_ref, h_ref)
        self._cursor_region.frame = (2. * l - 1., 2. * r - 1., 2. * b - 1., 2. * t - 1.)


class ViewportButtonBar(WidgetCard):

    height = 0

    def __init__(self, parent):

        WidgetCard.__init__(self, "viewport_button_bar", parent)

        self.sizer = Sizer("horizontal")
        self._is_hidden = False
        self._btns = []

    def add_button(self, name, icon_id, tooltip_text, command, proportion=0.):

        sizer = self.sizer
        btn = ViewportButton(self, name, icon_id, tooltip_text, command)
        sizer.add(btn, proportion=proportion)
        self._btns.append(btn)

        if not self.height:
            ViewportButtonBar.height = btn.min_size[1]

    def get_buttons(self):

        return self._btns

    def update_images(self):

        if self._is_hidden:
            return

        self._sizer.update_images()
        width, height = self.get_size()
        img = PNMImage(width, height, 4)

        x, y = self.get_pos()

        for widget in self._sizer.get_widgets(include_children=False):

            x_w, y_w = widget.get_pos(from_root=True)
            x_w -= x
            y_w -= y
            widget_img = widget.get_image()

            if widget_img:
                img.copy_sub_image(widget_img, x_w, y_w, 0, 0)

        tex = self.texture
        tex.load(img)

        l = x
        r = x + width
        b = -(y + height)
        t = -y
        quad = self.create_quad((l, r, b, t))
        quad.set_texture(tex)
        self._image = img

    def update_mouse_region_frames(self, exclude=""):

        self._sizer.update_mouse_region_frames(exclude)

    def hide(self):

        if self._is_hidden:
            return False

        mouse_watcher = self.mouse_watcher

        for widget in self._sizer.get_widgets():

            mouse_region = widget.mouse_region

            if mouse_region and not widget.is_hidden():
                mouse_watcher.remove_region(mouse_region)

        self.quad.hide()
        self._is_hidden = True

        return True

    def show(self):

        if not self._is_hidden:
            return False

        mouse_watcher = self.mouse_watcher

        for widget in self.sizer.get_widgets():

            mouse_region = widget.mouse_region

            if mouse_region and not widget.is_hidden(check_ancestors=False):
                mouse_watcher.add_region(mouse_region)

        self.quad.show()
        self._is_hidden = False
        self.update_images()

        return True

    def is_hidden(self, check_ancestors=True):

        return self._is_hidden


class ViewportBorder(Widget):

    _frame_viz = None
    _sequence = None

    @classmethod
    def init(cls):

        vertex_format = GeomVertexFormat.get_v3()
        vertex_data = GeomVertexData("viewport_frame_viz", vertex_format, Geom.UH_static)
        pos_writer = GeomVertexWriter(vertex_data, "vertex")
        pos_writer.add_data3(0., 0., 0.)
        pos_writer.add_data3(-1., 0., 0.)
        pos_writer.add_data3(-1., 0., 1.)
        pos_writer.add_data3(0., 0., 1.)
        geom_node = GeomNode("viewport_frame_viz")
        geom = Geom(vertex_data)
        geom_node.add_geom(geom)
        lines = GeomLines(Geom.UH_static)
        geom.add_primitive(lines)
        lines.add_vertices(0, 1)
        lines.add_vertices(1, 2)
        lines.add_vertices(2, 3)
        lines.add_vertices(0, 3)
        cls._frame_viz = viz = Mgr.get("gui_root").attach_new_node(geom_node)
        viz.hide()
        viz.set_bin("gui", 4)
        lerp_interval1 = LerpColorScaleInterval(viz, .5, 0., 1., blendType="easeInOut")
        lerp_interval2 = LerpColorScaleInterval(viz, .5, 1., blendType="easeInOut")
        cls._sequence = Sequence(lerp_interval1, lerp_interval2)

    def __init__(self, parent, viewport, size, resize_dir=""):

        Widget.__init__(self, "draggable_viewport_border", parent, {}, "", True)

        self._size = self._min_size = size
        self._resize_dir = resize_dir
        self._viewport = viewport
        self.mouse_region.sort = 11

        prefix = resize_dir if resize_dir else "corner"
        name = f"{prefix}_viewport_border"
        self._cursor_region = MouseWatcherRegion(name, 0., 0., 0., 0.)
        self._mouse_start_pos = ()
        self._listener = DirectObject()

    def get_cursor_region(self):

        return self._cursor_region

    def update_images(self, recurse=True, size=None): pass

    def update_mouse_region_frames(self, exclude="", recurse=True):

        Widget.update_mouse_region_frames(self, exclude, recurse)

        x, y = self.get_pos(from_root=True)
        w, h = self.get_size()
        w_ref, h_ref = Mgr.get("window_size")
        l, r, b, t = get_relative_region_frame(x, y, w, h, w_ref, h_ref)
        self._cursor_region.frame = (2. * l - 1., 2. * r - 1., 2. * b - 1., 2. * t - 1.)

    def __get_offsets(self):

        mouse_pointer = Mgr.get("mouse_pointer", 0)
        mouse_start_x, mouse_start_y = self._mouse_start_pos
        mouse_x, mouse_y = mouse_pointer.x, mouse_pointer.y
        resize_dir = self._resize_dir

        if resize_dir == "vertical":
            return (int(mouse_x - mouse_start_x), 0)
        elif resize_dir == "horizontal":
            return (0, int(mouse_y - mouse_start_y))
        else:
            return (int(mouse_x - mouse_start_x), int(mouse_y - mouse_start_y))

    def _resize_aux_viewport(self, task):

        mouse_pointer = Mgr.get("mouse_pointer", 0)
        mouse_x, mouse_y = mouse_pointer.x, mouse_pointer.y
        viz = self._frame_viz
        w_v, h_v = GD["viewport"]["size"]
        resize_dir = self._resize_dir

        if resize_dir == "vertical":
            sx = min(w_v, max(1, viz.get_pos()[0] - mouse_x))
            viz.set_sx(sx)
        elif resize_dir == "horizontal":
            sz = min(h_v, max(1, -mouse_y - viz.get_pos()[2]))
            viz.set_sz(sz)
        else:
            x, _, y = viz.get_pos()
            sx = min(w_v, max(1, x - mouse_x))
            sz = min(h_v, max(1, -mouse_y - y))
            viz.set_scale(sx, 1., sz)

        return task.cont

    def on_left_down(self):

        viz = self._frame_viz
        viz.show()
        self._sequence.loop()
        sizer = self._viewport.sizer
        x, y = sizer.get_pos(from_root=True)
        w, h = sizer.get_size()
        viz.set_pos(x + w, 0., -y - h)
        viz.set_scale(w, 1., h)
        mouse_pointer = Mgr.get("mouse_pointer", 0)
        self._mouse_start_pos = (mouse_pointer.x, mouse_pointer.y)
        Mgr.add_task(self._resize_aux_viewport, "resize_aux_viewport")
        self._listener.accept("gui_mouse1-up", self.__on_left_up)
        cancel_resize = lambda: self.__on_left_up(cancel_resize=True)
        self._listener.accept("gui_mouse3", cancel_resize)
        self._listener.accept("focus_loss", cancel_resize)
        Mgr.do("enable_gui", False)
        Mgr.enter_state("inactive")
        interface_ids = GD["viewport"]

        if interface_ids[2] is not None:
            interface_id = interface_ids[2 if interface_ids[1] == "main" else 1]
            Mgr.enter_state("inactive", interface_id)

    def __on_left_up(self, cancel_resize=False):

        Mgr.do("enable_gui")
        Mgr.exit_state("inactive")
        interface_ids = GD["viewport"]

        if interface_ids[2] is not None:
            interface_id = interface_ids[2 if interface_ids[1] == "main" else 1]
            Mgr.exit_state("inactive", interface_id)

        Mgr.remove_task("resize_aux_viewport")
        self._sequence.finish()
        self._listener.ignore_all()
        self._frame_viz.hide()
        delta_x, delta_y = self.__get_offsets()
        self._mouse_start_pos = ()

        if not cancel_resize:
            self._viewport.resize(delta_x, delta_y)


class AdjacentViewportBorder(ViewportBorder):

    def __init__(self, parent, viewport, size):

        ViewportBorder.__init__(self, parent, viewport, size, "vertical")

    def _resize_aux_viewport(self, task):

        viz = self._frame_viz
        sizer = self._viewport.sizer
        w = GD["viewport"]["size"][0] + 3
        w += sizer.get_size()[0]
        sx = min(w, max(1, viz.get_pos()[0] - Mgr.get("mouse_pointer", 0).x))
        viz.set_sx(sx)

        return task.cont


class AuxiliaryViewport:

    def __init__(self, window, viewport_sizer, adjacent_viewport_sizer):

        ViewportBorder.init()

        self._interface_name = ""
        self._placement = "overlaid"  # alternative: "adjacent"
        self._viewport_sizer = viewport_sizer
        self._viewport_sizer_adj = adjacent_viewport_sizer
        self._display_region = None
        self._cursor_region = MouseWatcherRegion("viewport2", 0., 0., 0., 0.)
        Mgr.expose("viewport2_cursor_region", lambda: self._cursor_region)
        self._mouse_region_mask = mask = MouseWatcherRegion("aux_viewport_mask", 0., 0., 0., 0.)
        flags = MouseWatcherRegion.SF_mouse_button | MouseWatcherRegion.SF_mouse_position
        mask.suppress_flags = flags
        mask.sort = 900
        self._spacer_h_item = viewport_sizer.add((0, 0), proportion=100.)
        sizer = Sizer("vertical")
        self._sizer = subsizer = Sizer("horizontal")
        border_sizer = Sizer("vertical")
        subsizer2 = Sizer("vertical")
        self._display_sizer = display_sizer = Sizer("horizontal")
        display_sizer.default_size = (300, 200)
        l, r, b, t = TextureAtlas["inner_borders"]["aux_viewport"]
        r = b = 3
        self._spacer_v_item = sizer.add((0, 0), proportion=100.)
        sizer.add(subsizer, proportion=1., expand=True)
        subsizer.add(border_sizer, expand=True)
        subsizer.add(subsizer2, proportion=1., expand=True)
        self._border_topleft = border = ViewportBorder(window, self, (l, t))
        border_sizer.add(border)
        self._border_left = border = ViewportBorder(window, self, (l, 200), "vertical")
        border_sizer.add(border, proportion=1.)
        self._border_top = border = ViewportBorder(window, self, (300, t), "horizontal")
        subsizer2.add(border, expand=True)
        borders = (0, r, 0, 0)
        subsizer2.add(display_sizer, proportion=1., expand=True, borders=borders)
        btn_bar = ViewportButtonBar(window)
        btn_bar.add_button("swap", "icon_viewport_swap", "Swap viewports",
                           self.__swap_viewports, proportion=1.)
        btn_bar.add_button("make_adjacent", "icon_viewport_adjacent", "Place viewports side-by-side",
                           lambda: self.__overlay(False), proportion=1.)
        btn_bar.add_button("exit", "icon_viewport_exit", "",
                           self.__close, proportion=1.)
        self._on_close = None
        self._btn_bar = btn_bar
        borders = (0, r, b, 0)
        subsizer2.add(btn_bar, expand=True, borders=borders)
        item = viewport_sizer.add(sizer, proportion=1., expand=True)
        viewport_sizer.remove_item(item)
        self.sizer_item = item

        # Create the adjacent viewport components

        self._sizer_adj = sizer = Sizer("horizontal")
        self._display_sizer_adj = display_sizer = Sizer("horizontal")
        display_sizer.default_size = (300, 200)
        self._border_adj = border = AdjacentViewportBorder(window, self, (l, 206))
        sizer.add(border, expand=True)
        borders = (0, 3, 3, 3)
        subsizer = Sizer("vertical")
        sizer.add(subsizer, proportion=1., expand=True, borders=borders)
        subsizer.add(display_sizer, proportion=1., expand=True)
        btn_bar = ViewportButtonBar(window)
        btn_bar.add_button("swap", "icon_viewport_swap", "Swap viewports",
                           self.__swap_viewports, proportion=1.)
        btn_bar.add_button("overlay", "icon_viewport_overlaid", "Overlay auxiliary viewport",
                           self.__overlay, proportion=1.)
        btn_bar.add_button("exit", "icon_viewport_exit", "",
                           self.__close, proportion=1.)
        self._btn_bar_adj = btn_bar
        subsizer.add(btn_bar, expand=True)
        item = adjacent_viewport_sizer.add(sizer, proportion=1., expand=True)
        adjacent_viewport_sizer.remove_item(item)
        self._sizer_item_adj = item

        GD["viewport"]["aux_region"] = (0, 0, 0, 0)

        Mgr.accept("open_aux_viewport", self.__open)
        Mgr.accept("close_aux_viewport", self.__request_close)

    @property
    def sizer(self):

        return self._sizer if self._placement == "overlaid" else self._sizer_adj

    def update(self):

        sizer = self._display_sizer if self._placement == "overlaid" else self._display_sizer_adj
        x, y = sizer.get_pos(from_root=True)
        w, h = sizer.get_size()
        w_ref, h_ref = Mgr.get("window_size")
        GD["viewport"]["pos_aux"] = (x, y)
        GD["viewport"]["size_aux"] = (w, h)
        GD["viewport"]["frame_aux"] = get_relative_region_frame(x, y, w, h, w_ref, h_ref)
        l, r, b, t = TextureAtlas["inner_borders"]["aux_viewport"]
        r = b = 3

        if self._placement == "adjacent":
            t = 3

        x -= l
        y -= t
        w += l + r
        h += ViewportButtonBar.height + b + t
        GD["viewport"]["aux_region"] = (x, y, w, h)
        l, r, b, t = get_relative_region_frame(x, y, w, h, w_ref, h_ref)
        self._display_region.dimensions = (l, r, b, t)
        l_v, r_v, b_v, t_v = GD["viewport"]["frame"]
        w = r_v - l_v
        h = t_v - b_v
        l = (l - l_v) / w
        r = (r - l_v) / w
        b = (b - b_v) / h
        t = (t - b_v) / h
        self._mouse_region_mask.frame = (2. * l - 1., 2. * r - 1., 2. * b - 1., 2. * t - 1.)

    def __on_enter(self, *args):

        viewport1_id = GD["viewport"][1]
        mask = self._mouse_region_mask

        if viewport1_id == "main":
            GD.mouse_watcher.add_region(mask)
        else:
            for mw in GD["viewport"]["mouse_watchers2"]:
                mw.add_region(mask)

    def __on_leave(self, *args):

        viewport1_id = GD["viewport"][1]
        mask = self._mouse_region_mask

        if viewport1_id == "main":
            GD.mouse_watcher.remove_region(mask)
        else:
            for mw in GD["viewport"]["mouse_watchers2"]:
                mw.remove_region(mask)

    def __swap_viewports(self):

        viewport1_id = GD["viewport"][1]
        viewport2_id = GD["viewport"][2]
        GD["viewport"][1] = viewport2_id
        GD["viewport"][2] = viewport1_id
        color1 = GD["viewport"]["border_color1"]
        color2 = GD["viewport"]["border_color2"]
        GD["viewport"]["border_color1"] = color2
        GD["viewport"]["border_color2"] = color1
        index = GD["viewport"]["active"]
        color = GD["viewport"][f"border_color{index}"]
        GD["viewport"][f"border{index}"].clear_color = color
        Mgr.update_app("viewport")
        mask = self._mouse_region_mask
        interface_id = GD["viewport"][index]
        Mgr.do("set_interface_status", interface_id)

        if viewport1_id == "main":

            GD.mouse_watcher.remove_region(mask)

            for mw in GD["viewport"]["mouse_watchers2"]:
                mw.add_region(mask)

            Mgr.update_app("viewport_region_sort_incr", 22)

            for dr in GD["viewport"]["display_regions"]:
                dr.sort += 22

            for dr in GD["viewport"]["display_regions2"]:
                dr.sort -= 22

        else:

            GD.mouse_watcher.add_region(mask)

            for mw in GD["viewport"]["mouse_watchers2"]:
                mw.remove_region(mask)

            Mgr.update_app("viewport_region_sort_incr", -22)

            for dr in GD["viewport"]["display_regions"]:
                dr.sort -= 22

            for dr in GD["viewport"]["display_regions2"]:
                dr.sort += 22

    def __overlay(self, overlaid=True):

        self._placement = "overlaid" if overlaid else "adjacent"
        Mgr.remove_cursor_regions("aux_viewport")
        Mgr.add_cursor_region("aux_viewport", self._cursor_region)

        if overlaid:

            self._border_adj.hide()
            self._btn_bar_adj.hide()
            self._viewport_sizer_adj.remove_item(self._sizer_item_adj)
            self._viewport_sizer_adj.sizer_item.proportion = 0.

            self._border_topleft.show()
            cursor_region = self._border_topleft.get_cursor_region()
            Mgr.add_cursor_region("aux_viewport", cursor_region)
            cursor_id = "move_nwse"
            Mgr.set_cursor(cursor_id, cursor_region.name)
            self._border_top.show()
            cursor_region = self._border_top.get_cursor_region()
            Mgr.add_cursor_region("aux_viewport", cursor_region)
            cursor_id = "move_ns"
            Mgr.set_cursor(cursor_id, cursor_region.name)
            self._border_left.show()
            cursor_region = self._border_left.get_cursor_region()
            Mgr.add_cursor_region("aux_viewport", cursor_region)
            cursor_id = "move_ew"
            Mgr.set_cursor(cursor_id, cursor_region.name)
            self._btn_bar.show()

            for btn in self._btn_bar.get_buttons():
                cursor_region = btn.get_cursor_region()
                Mgr.add_cursor_region("aux_viewport", cursor_region)

            viewport_sizer = self._viewport_sizer
            viewport_sizer.add_item(self.sizer_item)

        else:

            self._border_topleft.hide()
            self._border_top.hide()
            self._border_left.hide()
            self._btn_bar.hide()
            self._viewport_sizer.remove_item(self.sizer_item)

            self._border_adj.show()
            cursor_region = self._border_adj.get_cursor_region()
            Mgr.add_cursor_region("aux_viewport", cursor_region)
            cursor_id = "move_ew"
            Mgr.set_cursor(cursor_id, cursor_region.name)
            self._btn_bar_adj.show()

            for btn in self._btn_bar_adj.get_buttons():
                cursor_region = btn.get_cursor_region()
                Mgr.add_cursor_region("aux_viewport", cursor_region)

            viewport_sizer = self._viewport_sizer_adj
            viewport_sizer.add_item(self._sizer_item_adj)
            viewport_sizer.sizer_item.proportion = 1.

        viewport_sizer.update_min_size()
        viewport_sizer.set_size(viewport_sizer.get_size())
        viewport_sizer.calculate_positions(viewport_sizer.get_pos(from_root=True))
        viewport_sizer.update_images()
        viewport_sizer.update_mouse_region_frames()
        Mgr.do("update_window")

    def resize(self, delta_x=0, delta_y=0):

        if not (delta_x or delta_y):
            return

        if self._placement == "overlaid":

            viewport_sizer = self._viewport_sizer
            w_v, h_v = viewport_sizer.get_size()
            w, h = self._sizer.get_size()
            w -= delta_x
            h -= delta_y
            w = min(w_v, max(1, w))
            h = min(h_v, max(1, h))

            if delta_x:
                proportion = (w_v - w) / w
                self._spacer_h_item.proportion = proportion

            if delta_y:
                proportion = (h_v - h) / h
                self._spacer_v_item.proportion = proportion

            viewport_sizer.set_min_size_stale()
            viewport_sizer.update_min_size()
            viewport_sizer.set_size(viewport_sizer.get_size())
            viewport_sizer.calculate_positions(viewport_sizer.get_pos(from_root=True))
            viewport_sizer.update_images()
            viewport_sizer.update_mouse_region_frames()
            self.update()
            Mgr.update_app("viewport")

        else:

            viewport_sizer = self._viewport_sizer_adj
            w1 = self._viewport_sizer.get_size()[0]
            w2 = viewport_sizer.get_size()[0]
            w1 += w2
            sizer_item = self._viewport_sizer.sizer_item
            w2 -= delta_x
            w2 = min(w1, max(1, w2))
            proportion = max(.0001, (w1 - w2) / w2)
            sizer_item.proportion = proportion
            viewport_sizer.update_min_size()
            viewport_sizer.set_size(viewport_sizer.get_size())
            viewport_sizer.calculate_positions(viewport_sizer.get_pos(from_root=True))
            viewport_sizer.update_images()
            viewport_sizer.update_mouse_region_frames()
            Mgr.do("update_window")

    def __open(self, button_prefix="", interface_name="", on_close=None):

        self._interface_name = interface_name
        self._on_close = on_close
        btn = self._btn_bar.get_buttons()[-1]
        btn.set_tooltip_text(f"Exit {interface_name} interface")
        btn = self._btn_bar_adj.get_buttons()[-1]
        btn.set_tooltip_text(f"Exit {interface_name} interface")
        ToolTip.hide()

        Mgr.add_cursor_region("aux_viewport", self._cursor_region)

        if self._placement == "overlaid":

            self._border_topleft.show()
            cursor_region = self._border_topleft.get_cursor_region()
            Mgr.add_cursor_region("aux_viewport", cursor_region)
            cursor_id = "move_nwse"
            Mgr.set_cursor(cursor_id, cursor_region.name)
            self._border_top.show()
            cursor_region = self._border_top.get_cursor_region()
            Mgr.add_cursor_region("aux_viewport", cursor_region)
            cursor_id = "move_ns"
            Mgr.set_cursor(cursor_id, cursor_region.name)
            self._border_left.show()
            cursor_region = self._border_left.get_cursor_region()
            Mgr.add_cursor_region("aux_viewport", cursor_region)
            cursor_id = "move_ew"
            Mgr.set_cursor(cursor_id, cursor_region.name)
            self._btn_bar.show()

            for btn in self._btn_bar.get_buttons():
                cursor_region = btn.get_cursor_region()
                Mgr.add_cursor_region("aux_viewport", cursor_region)

            viewport_sizer = self._viewport_sizer
            viewport_sizer.add_item(self.sizer_item)

        else:

            self._border_adj.show()
            cursor_region = self._border_adj.get_cursor_region()
            Mgr.add_cursor_region("aux_viewport", cursor_region)
            cursor_id = "move_ew"
            Mgr.set_cursor(cursor_id, cursor_region.name)
            self._btn_bar_adj.show()

            for btn in self._btn_bar_adj.get_buttons():
                cursor_region = btn.get_cursor_region()
                Mgr.add_cursor_region("aux_viewport", cursor_region)

            viewport_sizer = self._viewport_sizer_adj
            viewport_sizer.add_item(self._sizer_item_adj)
            viewport_sizer.sizer_item.proportion = 1.

        viewport_sizer.update_min_size()
        viewport_sizer.set_size(viewport_sizer.get_size())
        viewport_sizer.calculate_positions(viewport_sizer.get_pos(from_root=True))
        viewport_sizer.update_images()
        viewport_sizer.update_mouse_region_frames()
        self._display_region = region = GD.window.make_display_region(0., 1., 0., 1.)
        region.active = True
        region.sort = 21
        color = Skin["colors"]["viewport_frame_inactive"]
        region.clear_color = color
        region.clear_depth = 1000.
        region.set_clear_color_active(True)
        region.set_clear_depth_active(True)
        GD["viewport"]["border2"] = region

        l, r, b, t = GD["viewport"]["frame"]
        region = GD.window.make_display_region(l, r, b, t)
        region.active = True
        color = GD.window.get_display_region(1).clear_color
        region.clear_color = color
        region.clear_depth = 1000.
        region.set_clear_color_active(True)
        region.set_clear_depth_active(True)
        GD["viewport"]["display_regions2"].append(region)
        input_ctrl = GD.showbase.mouseWatcher.parent
        mouse_watcher_node = MouseWatcher("main")
        mouse_watcher_node.set_display_region(region)
        mouse_watcher_node.set_modifier_buttons(ModifierButtons())
        mouse_watcher_node.add_region(self._mouse_region_mask)
        GD["viewport"]["mouse_watchers2"].append(mouse_watcher_node)
        mouse_watcher = input_ctrl.attach_new_node(mouse_watcher_node)
        btn_thrower_node = ButtonThrower(f"btn_thrower_{button_prefix}")
        btn_thrower_node.prefix = f"{button_prefix}_"
        btn_thrower_node.modifier_buttons = ModifierButtons()
        mouse_watcher.attach_new_node(btn_thrower_node)
        self.update()

        Mgr.update_app("viewport")
        Mgr.update_app("viewport_region_sort_incr", 22)

        for dr in GD["viewport"]["display_regions"]:
            dr.sort += 22

        return region, mouse_watcher_node

    def __close(self):

        self._interface_name = ""
        index = GD["viewport"]["active"]
        interface_id = GD["viewport"][index]

        if interface_id != "main":
            Mgr.do("set_interface_status")

        GD["viewport"]["active"] = 1

        if GD["viewport"][1] != "main":
            self.__swap_viewports()
        else:
            color = GD["viewport"]["border_color1"]
            GD["viewport"]["border1"].clear_color = color

        GD["viewport"][2] = None
        w, h = Mgr.get("window_size")
        l, r, b, t = GD["viewport"]["frame"]
        GD["fps_meter_display_region"].dimensions = (r - 800./w, r, b, b + 600./h)
        GD.mouse_watcher.remove_region(self._mouse_region_mask)
        Mgr.remove_cursor_regions("aux_viewport")

        if self._placement == "overlaid":
            self._border_topleft.hide()
            self._border_top.hide()
            self._border_left.hide()
            self._btn_bar.hide()
            self._viewport_sizer.remove_item(self.sizer_item)
        else:
            self._border_adj.hide()
            self._btn_bar_adj.hide()
            self._viewport_sizer_adj.remove_item(self._sizer_item_adj)
            self._viewport_sizer_adj.sizer_item.proportion = 0.

        region = self._display_region
        self._display_region = None
        GD["viewport"]["border1"] = GD.window
        GD["viewport"]["border2"] = None
        GD.window.remove_display_region(region)
        del GD["viewport"]["display_regions2"][:]
        del GD["viewport"]["mouse_watchers2"][:]

        if self._on_close:
            self._on_close()

    def __request_close(self, on_close):

        if GD["viewport"][2] is None:
            on_close()
            return

        def on_yes():

            self.__close()
            command = lambda task: on_close()
            Mgr.do_next_frame(command, "on_close_aux_viewport")

        title = f"Exit {self._interface_name} interface"
        message = f"The {self._interface_name} interface needs to be exited and any changes saved."
        message += "\n\nContinue?"
        MessageDialog(title=title,
                      message=message,
                      choices="yesno",
                      on_yes=on_yes,
                      icon_id="icon_exclamation")
