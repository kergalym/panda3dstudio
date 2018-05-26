from ...base import *


class VertexEditBase(BaseObject):

    def break_vertices(self):

        selected_vert_ids = self._selected_subobj_ids["vert"]

        if not selected_vert_ids:
            return False

        verts = self._subobjs["vert"]
        merged_verts = self._merged_verts
        verts_to_break = set(merged_verts[v_id] for v_id in selected_vert_ids)
        edge_ids = set(e_id for v in verts_to_break for v_id in v
                       for e_id in verts[v_id].get_edge_ids())

        return self.split_edges(edge_ids)

    def smooth_vertices(self, smooth=True):

        selected_vert_ids = self._selected_subobj_ids["vert"]

        if not selected_vert_ids:
            return False, False

        merged_verts = self._merged_verts
        shared_normals = self._shared_normals
        verts_to_update = set(merged_verts[v_id] for v_id in selected_vert_ids)
        merged_verts_to_resmooth = set()
        normals_to_sel = False

        if smooth:

            selected_normal_ids = set(self._selected_subobj_ids["normal"])

            for merged_vert in verts_to_update:

                if len(shared_normals[merged_vert[0]]) == len(merged_vert):
                    continue

                shared_normal = Mgr.do("create_shared_normal", self, set(merged_vert))

                for vert_id in merged_vert:
                    shared_normals[vert_id] = shared_normal

                merged_verts_to_resmooth.add(merged_vert)

                # Make sure that all normals in the same merged vertex become
                # selected if at least one of them is already selected.

                ids = set(merged_vert)
                sel_ids = selected_normal_ids.intersection(ids)

                if not sel_ids or len(sel_ids) == len(ids):
                    continue

                tmp_normal = Mgr.do("create_shared_normal", self, ids.difference(sel_ids))
                tmp_id = tmp_normal.get_id()
                orig_normal = shared_normals[tmp_id]
                shared_normals[tmp_id] = tmp_normal
                self.update_selection("normal", [tmp_normal], [])
                shared_normals[tmp_id] = orig_normal
                normals_to_sel = True

        else:

            for merged_vert in verts_to_update:

                if len(merged_vert) == 1:
                    continue

                for vert_id in merged_vert:

                    if len(shared_normals[vert_id]) == 1:
                        continue

                    shared_normals[vert_id] = Mgr.do("create_shared_normal", self, [vert_id])
                    merged_verts_to_resmooth.add(merged_vert)

        if not merged_verts_to_resmooth:
            return False, False

        self._normal_sharing_change = True
        self.update_vertex_normals(merged_verts_to_resmooth)

        return True, normals_to_sel

    def init_vertex_picking_via_poly(self, poly, category=""):

        # Allow picking the vertices of the poly picked in the previous step
        # (see prepare_subobj_picking_via_poly) instead of other vertices;
        # as soon as the mouse is released over a vertex, it gets picked and
        # polys become pickable again.

        origin = self._origin
        verts = self._subobjs["vert"]
        edges = self._subobjs["edge"]
        count = poly.get_vertex_count()

        # create pickable geometry, specifically for the vertices of the
        # given polygon and belonging to the given category, if any
        vertex_format = Mgr.get("vertex_format_basic")
        vertex_data = GeomVertexData("vert_data", vertex_format, Geom.UH_static)
        vertex_data.reserve_num_rows(count)
        pos_writer = GeomVertexWriter(vertex_data, "vertex")
        col_writer = GeomVertexWriter(vertex_data, "color")
        pickable_id = PickableTypes.get_id("vert")
        rows = self._tmp_row_indices
        by_aiming = GlobalData["subobj_edit_options"]["pick_by_aiming"]

        if by_aiming:

            # To further assist with vertex picking, create two quads for each
            # vertex, with the picking color of that vertex and perpendicular to
            # the view plane;
            # the border of each quad will pass through the corresponding vertex
            # itself, and through either of the centers of the 2 edges connected
            # by that vertex;
            # an auxiliary picking camera will be placed at the clicked point under
            # the mouse and follow the mouse cursor, rendering the picking color
            # of the quad it is pointed at.

            aux_picking_root = Mgr.get("aux_picking_root")
            aux_picking_cam = Mgr.get("aux_picking_cam")
            cam = self.cam()
            cam_pos = cam.get_pos(self.world)
            normal = self.world.get_relative_vector(cam, Vec3.forward()).normalized()
            plane = Plane(normal, cam_pos + normal * 10.)
            aux_picking_cam.set_plane(plane)
            aux_picking_cam.update_pos()
            normal *= 5.
            vertex_data_poly = GeomVertexData("vert_data_poly", vertex_format, Geom.UH_static)
            vertex_data_poly.reserve_num_rows(count * 6)
            pos_writer_poly = GeomVertexWriter(vertex_data_poly, "vertex")
            col_writer_poly = GeomVertexWriter(vertex_data_poly, "color")
            tmp_poly_prim = GeomTriangles(Geom.UH_static)
            tmp_poly_prim.reserve_num_vertices(count * 12)
            rel_pt = lambda point: self.world.get_relative_point(origin, point)
            lens_is_ortho = self.cam.lens_type == "ortho"

        for i, vert_id in enumerate(poly.get_vertex_ids()):

            vertex = verts[vert_id]
            pos = vertex.get_pos()
            pos_writer.add_data3f(pos)
            color_id = vertex.get_picking_color_id()
            picking_color = get_color_vec(color_id, pickable_id)
            col_writer.add_data4f(picking_color)
            rows[color_id] = i

            if by_aiming:

                edge1_id, edge2_id = vertex.get_edge_ids()
                edge1_center = edges[edge1_id].get_center_pos()
                edge2_center = edges[edge2_id].get_center_pos()
                p1 = Point3()
                point1 = rel_pt(edge1_center)
                point2 = point1 + normal if lens_is_ortho else cam_pos
                plane.intersects_line(p1, point1, point2)
                p2 = Point3()
                point1 = rel_pt(pos)
                point2 = point1 + normal if lens_is_ortho else cam_pos
                plane.intersects_line(p2, point1, point2)
                p3 = Point3()
                point1 = rel_pt(edge2_center)
                point2 = point1 + normal if lens_is_ortho else cam_pos
                plane.intersects_line(p3, point1, point2)
                pos_writer_poly.add_data3f(p1 - normal)
                pos_writer_poly.add_data3f(p1 + normal)
                pos_writer_poly.add_data3f(p2 - normal)
                pos_writer_poly.add_data3f(p2 + normal)
                pos_writer_poly.add_data3f(p3 - normal)
                pos_writer_poly.add_data3f(p3 + normal)

                for _ in range(6):
                    col_writer_poly.add_data4f(picking_color)

                j = i * 6
                tmp_poly_prim.add_vertices(j, j + 1, j + 2)
                tmp_poly_prim.add_vertices(j + 1, j + 3, j + 2)
                tmp_poly_prim.add_vertices(j + 2, j + 3, j + 4)
                tmp_poly_prim.add_vertices(j + 3, j + 5, j + 4)

        tmp_prim = GeomPoints(Geom.UH_static)
        tmp_prim.reserve_num_vertices(count)
        tmp_prim.add_next_vertices(count)
        geom = Geom(vertex_data)
        geom.add_primitive(tmp_prim)
        node = GeomNode("tmp_geom_pickable")
        node.add_geom(geom)
        geom_pickable = origin.attach_new_node(node)
        geom_pickable.set_bin("fixed", 51)
        geom_pickable.set_depth_test(False)
        geom_pickable.set_depth_write(False)
        geom_sel_state = geom_pickable.copy_to(origin)
        geom_sel_state.set_name("tmp_geom_sel_state")
        geom_sel_state.set_light_off()
        geom_sel_state.set_color_off()
        geom_sel_state.set_texture_off()
        geom_sel_state.set_material_off()
        geom_sel_state.set_transparency(TransparencyAttrib.M_alpha)
        geom_sel_state.set_render_mode_thickness(9)
        geom = geom_sel_state.node().modify_geom(0)
        vertex_data = geom.get_vertex_data().set_color((.3, .3, .3, .5))
        geom.set_vertex_data(vertex_data)
        self._tmp_geom_pickable = geom_pickable
        self._tmp_geom_sel_state = geom_sel_state

        if by_aiming:
            geom_poly = Geom(vertex_data_poly)
            geom_poly.add_primitive(tmp_poly_prim)
            node = GeomNode("tmp_geom_pickable")
            node.add_geom(geom_poly)
            geom_poly_pickable = aux_picking_root.attach_new_node(node)
            geom_poly_pickable.set_two_sided(True)

        # to determine whether the mouse is over the polygon or not, create a
        # duplicate with a white color to distinguish it from the black background
        # color (so it gets detected by the picking camera) and any other pickable
        # objects (so no attempt will be made to pick it)
        vertex_data_poly = GeomVertexData("vert_data_poly", vertex_format, Geom.UH_static)
        vertex_data_poly.reserve_num_rows(count)
        pos_writer_poly = GeomVertexWriter(vertex_data_poly, "vertex")
        col_writer_poly = GeomVertexWriter(vertex_data_poly, "color")
        tmp_poly_prim = GeomTriangles(Geom.UH_static)
        tmp_poly_prim.reserve_num_vertices(len(poly))
        vert_ids = poly.get_vertex_ids()
        white = (1., 1., 1., 1.)

        for vert_id in vert_ids:
            vertex = verts[vert_id]
            pos = vertex.get_pos()
            pos_writer_poly.add_data3f(pos)
            col_writer_poly.add_data4f(white)

        for _ in range(count):
            col_writer_poly.add_data4f(white)

        for tri_vert_ids in poly:
            for vert_id in tri_vert_ids:
                tmp_poly_prim.add_vertex(vert_ids.index(vert_id))

        geom_poly = Geom(vertex_data_poly)
        geom_poly.add_primitive(tmp_poly_prim)
        node = GeomNode("tmp_geom_poly_pickable")
        node.add_geom(geom_poly)
        geom_poly_pickable = geom_pickable.attach_new_node(node)
        geom_poly_pickable.set_bin("fixed", 50)

        render_masks = Mgr.get("render_masks")["all"]
        picking_masks = Mgr.get("picking_masks")["all"]
        geom_pickable.hide(render_masks)
        geom_pickable.show_through(picking_masks)

        if by_aiming:
            aux_picking_cam.set_active()
            Mgr.do("start_drawing_aux_picking_viz")

        geoms = self._geoms
        geoms["poly"]["pickable"].show(picking_masks)


class VertexEditManager(BaseObject):

    def __init__(self):

        Mgr.add_app_updater("vert_break", self.__break_vertices)
        Mgr.add_app_updater("vert_smoothing", self.__smooth_vertices)

    def __break_vertices(self):

        selection = Mgr.get("selection_top")
        changed_objs = {}

        for model in selection:

            geom_data_obj = model.get_geom_object().get_geom_data_object()

            if geom_data_obj.break_vertices():
                changed_objs[model.get_id()] = geom_data_obj

        if not changed_objs:
            return

        Mgr.do("update_active_selection")
        Mgr.do("update_history_time")
        obj_data = {}

        for obj_id, geom_data_obj in changed_objs.iteritems():
            obj_data[obj_id] = geom_data_obj.get_data_to_store("prop_change", "subobj_merge")

        event_descr = "Break vertex selection"
        event_data = {"objects": obj_data}
        Mgr.do("add_history", event_descr, event_data, update_time_id=False)

    def __smooth_vertices(self, smooth):

        selection = Mgr.get("selection_top")
        changed_objs = {}
        changed_selections = []

        for model in selection:

            geom_data_obj = model.get_geom_object().get_geom_data_object()
            change, normals_to_sel = geom_data_obj.smooth_vertices(smooth)

            if change:

                changed_objs[model.get_id()] = geom_data_obj

                if normals_to_sel:
                    changed_selections.append(model.get_id())

        if not changed_objs:
            return

        Mgr.do("update_history_time")
        obj_data = {}

        for obj_id, geom_data_obj in changed_objs.iteritems():

            obj_data[obj_id] = geom_data_obj.get_data_to_store()

            if obj_id in changed_selections:
                obj_data[obj_id].update(geom_data_obj.get_property_to_store("subobj_selection"))

        event_descr = "{} vertex selection".format("Smooth" if smooth else "Sharpen")
        event_data = {"objects": obj_data}
        Mgr.do("add_history", event_descr, event_data, update_time_id=False)


MainObjects.add_class(VertexEditManager)
