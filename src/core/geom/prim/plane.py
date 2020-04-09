from .base import *


def _define_geom_data(segments, temp=False):

    geom_data = []

    # Define vertex data

    segs1 = segments["x"]
    segs2 = segments["y"]
    i1 = 0
    i2 = 1
    range1 = range(segs1 + 1)
    range2 = range(segs2 + 1)

    vert_id = 0
    vert_data = {}
    normal = Vec3(0., 0., 1.)

    for i in range2:

        b = (1. / segs2) * i
        y = b - .5

        for j in range1:

            a = (1. / segs1) * j
            x = a - .5
            pos = (x, y, 0.)

            if temp:
                vert_data[vert_id] = {"pos": PosObj(pos), "normal": normal}
            else:
                vert_data[vert_id] = {"pos": PosObj(pos), "normal": normal, "uvs": {0: (a, b)},
                    "pos_ind": vert_id}

            vert_id += 1

    # Define faces

    for i in range(segs2):
        for j in range(segs1):
            vi1 = i * (segs1 + 1) + j
            vi2 = vi1 + 1
            vi3 = vi2 + segs1
            vi4 = vi3 + 1
            vert_ids = (vi1, vi2, vi4)
            tri_data1 = [vert_data[vi] for vi in vert_ids]
            vert_ids = (vi1, vi4, vi3)
            tri_data2 = [vert_data[vi] for vi in vert_ids]
            vert_ids = (vi1, vi2, vi4, vi3)
            poly_verts = [vert_data[vi] for vi in vert_ids]
            tris = (tri_data1, tri_data2)
            poly_data = {"verts": poly_verts, "tris": tris}
            geom_data.append(poly_data)

    return geom_data


class TemporaryPlane(TemporaryPrimitive):

    def __init__(self, segments, color, pos):

        TemporaryPrimitive.__init__(self, "plane", color, pos)

        self._size = {"x": 0., "y": 0.}
        geom_data = _define_geom_data(segments, True)
        self.create_geometry(geom_data)

    def update_size(self, x=None, y=None):

        origin = self.origin
        size = self._size

        if x is not None:

            sx = max(abs(x), .001)
            sy = max(abs(y), .001)

            origin.set_x((-sx if x < 0. else sx) * .5)
            origin.set_y((-sy if y < 0. else sy) * .5)

            if size["x"] != sx:
                size["x"] = sx
                origin.set_sx(sx)

            if size["y"] != sy:
                size["y"] = sy
                origin.set_sy(sy)

    def get_size(self):

        return self._size

    def is_valid(self):

        return max(self._size.values()) > .001

    def finalize(self):

        pos = self.pivot.get_pos()
        pivot = self.pivot
        origin = self.origin
        x, y, z = origin.get_pos()
        pos = GD.world.get_relative_point(pivot, Point3(x, y, 0.))
        pivot.set_pos(GD.world, pos)
        origin.set_x(0.)
        origin.set_y(0.)

        return TemporaryPrimitive.finalize(self)


class Plane(Primitive):

    def __init__(self, model, segments, picking_col_id, geom_data):

        self._segments = segments
        self._size = {"x": 0., "y": 0.}

        prop_ids = [f"size_{axis}" for axis in "xy"]
        prop_ids.append("segments")

        Primitive.__init__(self, "plane", model, prop_ids, picking_col_id, geom_data)

    def recreate(self):

        geom_data = _define_geom_data(self._segments)
        Primitive.recreate(self, geom_data)

    def set_segments(self, segments):

        if self._segments == segments:
            return False

        self._segments = segments

        return True

    def __update_size(self):

        size = self._size
        sx = size["x"]
        sy = size["y"]
        mat = Mat4.scale_mat(sx, sy, 1.)

        for i, geom in enumerate((self.geom, self.aux_geom)):
            vertex_data = geom.node().modify_geom(0).modify_vertex_data()
            pos_view = memoryview(vertex_data.modify_array(0)).cast("B").cast("f")
            pos_view[:] = self.initial_coords[i]
            vertex_data.transform_vertices(mat)

        self.update_poly_centers()

        self.model.bbox.update(self.geom.get_tight_bounds())

    def init_size(self, x, y):

        size = self._size
        size["x"] = max(abs(x), .001)
        size["y"] = max(abs(y), .001)

        self.__update_size()

    def set_dimension(self, axis, value):

        if self._size[axis] == value:
            return False

        self._size[axis] = value

        return True

    def get_data_to_store(self, event_type, prop_id=""):

        if event_type == "prop_change" and prop_id in self.get_type_property_ids():

            data = {}
            data[prop_id] = {"main": self.get_property(prop_id)}

            return data

        return Primitive.get_data_to_store(self, event_type, prop_id)

    def get_property(self, prop_id, for_remote_update=False):

        if prop_id == "segments":
            if for_remote_update:
                return self._segments
            else:
                return {"count": self._segments, "pos_data": self.initial_coords,
                        "geom_data": self.geom_data, "geom": self.geom_for_pickling,
                        "aux_geom": self.aux_geom_for_pickling}
        elif "size" in prop_id:
            axis = prop_id.split("_")[1]
            return self._size[axis]
        else:
            return Primitive.get_property(self, prop_id, for_remote_update)

    def set_property(self, prop_id, value, restore=""):

        def update_app():

            Mgr.update_remotely("selected_obj_prop", "plane", prop_id,
                                self.get_property(prop_id, True))

        obj_id = self.toplevel_obj.id

        if prop_id == "segments":

            if restore:
                segments = value["count"]
                self.initial_coords = value["pos_data"]
                self.geom_data = value["geom_data"]
                self.geom = value["geom"]
                self.aux_geom = value["aux_geom"]
                self.model.bbox.update(self.geom.get_tight_bounds())
                self.setup_geoms()
            else:
                segments = self._segments.copy()
                segments.update(value)

            task = self.__update_size
            sort = PendingTasks.get_sort("set_normals", "object") - 1
            PendingTasks.add(task, "upd_size", "object", sort, id_prefix=obj_id)
            self.model.update_group_bbox()

            change = self.set_segments(segments)

            if change:

                if not restore:
                    self.recreate()

                update_app()

            return change

        elif "size" in prop_id:

            axis = prop_id.split("_")[1]
            change = self.set_dimension(axis, value)

            if change:
                task = self.__update_size
                sort = PendingTasks.get_sort("set_normals", "object") - 1
                PendingTasks.add(task, "upd_size", "object", sort, id_prefix=obj_id)
                self.model.update_group_bbox()
                update_app()

            return change

        else:

            return Primitive.set_property(self, prop_id, value, restore)


class PlaneManager(PrimitiveManager):

    def __init__(self):

        PrimitiveManager.__init__(self, "plane", custom_creation=True)

        for axis in "xy":
            self.set_property_default(f"size_{axis}", 1.)

        self.set_property_default("temp_segments", {"x": 1, "y": 1})
        self.set_property_default("segments", {"x": 1, "y": 1})

    def setup(self):

        creation_phases = []
        creation_phase = (lambda: None, self.__creation_phase1,
                          self.__finish_creation_phase1)
        creation_phases.append(creation_phase)

        status_text = {}
        status_text["obj_type"] = "plane"
        status_text["phase1"] = "draw out the plane"

        return PrimitiveManager.setup(self, creation_phases, status_text)

    def define_geom_data(self):

        segments = self.get_property_defaults()["segments"]

        return _define_geom_data(segments)

    def create_temp_primitive(self, color, pos):

        segs = self.get_property_defaults()["segments"]
        tmp_segs = self.get_property_defaults()["temp_segments"]
        segments = {axis: min(segs[axis], tmp_segs[axis]) for axis in "xy"}
        tmp_prim = TemporaryPlane(segments, color, pos)

        return tmp_prim

    def create_primitive(self, model, picking_col_id, geom_data):

        segments = self.get_property_defaults()["segments"]
        prim = Plane(model, segments, picking_col_id, geom_data)

        return prim

    def init_primitive_size(self, prim, size=None):

        if size is None:
            prop_defaults = self.get_property_defaults()
            x, y = [prop_defaults[f"size_{axis}"] for axis in "xy"]
        else:
            x, y = [size[axis] for axis in "xy"]

        prim.init_size(x, y)

    def __creation_phase1(self):
        """ Draw out plane """

        point = None
        grid = Mgr.get("grid")
        grid_origin = grid.origin
        origin_pos = grid_origin.get_relative_point(GD.world, self.get_origin_pos())
        snap_settings = GD["snap"]
        snap_on = snap_settings["on"]["creation"] and snap_settings["on"]["creation_phase_1"]
        snap_tgt_type = snap_settings["tgt_type"]["creation_phase_1"]

        if snap_on and snap_tgt_type != "increment":
            point = Mgr.get("snap_target_point")

        if point is None:

            if snap_on and snap_tgt_type != "increment":
                Mgr.do("set_projected_snap_marker_pos", None)

            if not GD.mouse_watcher.has_mouse():
                return

            screen_pos = GD.mouse_watcher.get_mouse()
            point = grid.get_point_at_screen_pos(screen_pos, origin_pos)

        else:

            proj_point = grid.get_projected_point(point, origin_pos)
            proj_point = GD.world.get_relative_point(grid_origin, proj_point)
            Mgr.do("set_projected_snap_marker_pos", proj_point)

        if not point:
            return

        tmp_prim = self.get_temp_primitive()
        pivot = tmp_prim.pivot
        x, y, _ = pivot.get_relative_point(grid_origin, point)

        if snap_on and snap_tgt_type == "increment":
            offset_incr = snap_settings["increment"]["creation_phase_1"]
            x = round(x / offset_incr) * offset_incr
            y = round(y / offset_incr) * offset_incr

        tmp_prim.update_size(x, y)

    def __finish_creation_phase1(self):
        """ End creation phase 1 by setting default plane size """

        prop_defaults = self.get_property_defaults()
        x, y = [prop_defaults[f"size_{axis}"] for axis in "xy"]
        tmp_prim = self.get_temp_primitive()
        tmp_prim.update_size(x, y)

    def create_custom_primitive(self, name, x, y, segments, pos, inverted=False,
                                rel_to_grid=False):

        model_id = self.generate_object_id()
        model = Mgr.do("create_model", model_id, name, pos)

        if not rel_to_grid:
            pivot = model.pivot
            pivot.clear_transform()
            pivot.set_pos(GD.world, pos)

        next_color = self.get_next_object_color()
        model.set_color(next_color, update_app=False)
        picking_col_id = self.get_next_picking_color_id()
        geom_data = _define_geom_data(segments)
        prim = Plane(model, segments, picking_col_id, geom_data)
        prim.init_size(x, y)
        self.set_next_object_color()

        if inverted:
            prim.set_property("inverted_geom", True)

        return model


MainObjects.add_class(PlaneManager)
