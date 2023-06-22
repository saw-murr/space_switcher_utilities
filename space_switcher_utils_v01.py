import maya.OpenMayaUI
from maya import cmds
from PySide2 import QtWidgets, QtCore
from shiboken2 import wrapInstance


def main():
    ui = SpaceSwitcherUI()
    ui.show()


def get_maya_main_win():
    """Return the Maya main window widget"""
    main_window = maya.OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(main_window), QtWidgets.QWidget)


class SpaceSwitcherUI(QtWidgets.QDialog):
    """Space Switcher GUI Class"""

    def __init__(self):
        super().__init__(parent=get_maya_main_win())
        self.setWindowTitle("Space Switcher Utilities")
        self.resize(850, 200)
        self._create_ui()
        self._create_script_jobs()
        self.bake_down = False

        self.SpaceSwitcher = SpaceSwitcher()

    def _create_script_jobs(self):
        """
        Class that creates script jobs, which allow the GUI to
        react to user input that occurs in Maya. In the future,
        I'd like to implement more script jobs to update the GUI
        in case of undoing, redoing, deleting, etc., but currently it just
        supports updating the selection labels.
        """
        self.script_jobs = []
        self.sel_labels_sj = cmds.scriptJob(event=["SelectionChanged",
                                            self._update_sel_labels])
        self.script_jobs.append(self.sel_labels_sj)

    def closeEvent(self, event):
        """
        Overwrites the original closeEvent method inherited from
        QtWidgets.QDialog to kill all active script jobs when the GUI
        is closed, ensuring no scripts are bogging down Maya after the
        script is closed.
        """
        for job in self.script_jobs:
            cmds.scriptJob(kill=job)
        event.accept()

    def _create_ui(self):
        """Main GUI creation class which creates main layout and runs
        all methods to build UI"""
        self.main_layout = QtWidgets.QVBoxLayout()
        self._add_params_form()
        self.setLayout(self.main_layout)

    def _update_sel_labels(self):
        """Updates the selection labels to show the name of the selected
        objects"""
        selections = cmds.ls(selection=True)

        if len(selections) == 0:
            self.tc_ledit_l.setText(self.tr("[No selections.]"))
            self.tc_ledit_r.setText(self.tr("[No selections.]"))
        if len(selections) == 1:
            self.tc_ledit_l.setText(self.tr(selections[0]))
            self.tc_ledit_r.setText(self.tr("[World Space]"))
        if len(selections) == 2:
            self.tc_ledit_l.setText(selections[1])
            self.tc_ledit_r.setText(selections[0])
        if len(selections) > 2:
            self.tc_ledit_l.setText(self.tr("[Too many selections!]"))
            self.tc_ledit_r.setText(self.tr("[Too many selections!]"))

    def _add_params_form(self):
        """Adds all the secondary UI elements into a form layout underneath
        the main layout"""
        self.form_layout = QtWidgets.QFormLayout()
        self._add_snap_tools_form()
        self._add_hline()
        self._add_temp_ctrls_form()
        self._add_tmp_ctrl_options()
        self._add_hline()
        self._add_tmp_cc_panel()
        self.main_layout.addLayout(self.form_layout)

    def _add_hline(self):
        """Adds horizontal line to the form layout"""
        self.hline = QtWidgets.QFrame()
        self.hline.setFrameShape(QtWidgets.QFrame.HLine)
        self.form_layout.addRow(self.hline)

    def _add_snap_tools_form(self):
        """Adds the top row snap utility"""
        self.snap_tools_row = QtWidgets.QHBoxLayout()

        self.loc_chkbx = QtWidgets.QCheckBox("Location", checked=True)
        self.snap_tools_row.addWidget(self.loc_chkbx)

        self.rot_chkbx = QtWidgets.QCheckBox("Rotation", checked=True)
        self.snap_tools_row.addWidget(self.rot_chkbx)

        self.scl_chkbx = QtWidgets.QCheckBox("Scale")
        self.snap_tools_row.addWidget(self.scl_chkbx)

        self.snap_btn = QtWidgets.QPushButton("Snap!")
        self.snap_btn.clicked.connect(self.snap_tools_button)
        self.snap_tools_row.addWidget(self.snap_btn)

        self.form_layout.addRow(self.tr("Quick Snap: "),
                                self.snap_tools_row)

    def _add_temp_ctrls_form(self):
        """Adds the main temp control row, with the selection labels and
        generate button"""
        self.temp_ctrls_row = QtWidgets.QHBoxLayout()

        self._add_temp_ctrls_sel_labels()

        self.temp_ctrl_btn = QtWidgets.QPushButton("Create Temp " +
                                                   "Controller!")
        self.temp_ctrl_btn.clicked.connect(self.create_temp_ctrl)
        self.temp_ctrls_row.addWidget(self.temp_ctrl_btn)

        self.form_layout.addRow(self.tr("New Temp Control: "),
                                self.temp_ctrls_row)

    def _add_tmp_cc_panel(self):
        """Adds the bottom manage controls panel, with the dropdown
        QComboBox that holds all created temp controls as well as the
        Delete and Bake Down buttons"""
        self.temp_ctrl_panel_hb = QtWidgets.QHBoxLayout()
        self.temp_ctrl_panel_cmb = QtWidgets.QComboBox()
        self.temp_ctrl_panel_cmb.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        self.temp_ctrl_panel_hb.addWidget(self.temp_ctrl_panel_cmb)
        self.temp_ctrl_panel_del_btn = QtWidgets.QPushButton(
            "Delete")
        self.temp_ctrl_panel_del_btn.clicked.connect(self.delete_temp_cc)
        self.temp_ctrl_panel_hb.addWidget(self.temp_ctrl_panel_del_btn)
        self.temp_ctrl_panel_bake_btn = QtWidgets.QPushButton(
            "Bake Down")
        self.temp_ctrl_panel_bake_btn.clicked.connect(self.bake_back_anim)
        self.temp_ctrl_panel_hb.addWidget(self.temp_ctrl_panel_bake_btn)
        self.form_layout.addRow(self.tr("Manage Controls"),
                                self.temp_ctrl_panel_hb)

    def _add_temp_ctrls_sel_labels(self):
        """Adds the QLineEdit selection labels that show the currently
        selected objects"""
        self.tc_ledit_l = QtWidgets.QLineEdit(readOnly=True)
        self.tc_ledit_l.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                      QtWidgets.QSizePolicy.Preferred)
        self.tc_ledit_l.setAlignment(QtCore.Qt.AlignRight)
        self.temp_ctrls_row.addWidget(self.tc_ledit_l)

        self.tc_const_lbl = QtWidgets.QLabel(" is constrained to ")
        self.temp_ctrls_row.addWidget(self.tc_const_lbl)

        self.tc_ledit_r = QtWidgets.QLineEdit(readOnly=True)
        self.tc_ledit_r.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                      QtWidgets.QSizePolicy.Preferred)
        self.tc_ledit_r.setAlignment(QtCore.Qt.AlignLeft)
        self.temp_ctrls_row.addWidget(self.tc_ledit_r)
        self._update_sel_labels()

    def _add_tmp_ctrl_options(self):
        """Creates the main QHBoxLayout for all the options/parameters"""
        self.tmp_cc_opt_hb = QtWidgets.QHBoxLayout()

        self._add_tmp_ctrl_const_type_options()
        self._add_tmp_ctrl_baking_options()
        self._add_cc_options()

        self.form_layout.addRow(self.tr("Temp CC Options: "),
                                self.tmp_cc_opt_hb)

    def _add_tmp_ctrl_const_type_options(self):
        """Adds the constraint type options checkboxes"""
        self.tmp_cc_opt_type_vb = QtWidgets.QVBoxLayout()
        self.tmp_cc_opt_type_vb.setAlignment(QtCore.Qt.AlignTop)
        self.tmp_cc_opt_type_lbl = QtWidgets.QLabel("Constraint Type:")
        self.tmp_cc_opt_type_vb.addWidget(self.tmp_cc_opt_type_lbl)

        self.tmp_cc_opt_type_loc_chk = QtWidgets.QCheckBox("Location",
                                                           checked=True)
        self.tmp_cc_opt_type_rot_chk = QtWidgets.QCheckBox("Rotation",
                                                           checked=True)
        self.tmp_cc_opt_type_scl_chk = QtWidgets.QCheckBox("Scale")
        self.tmp_cc_opt_type_aim_chk = QtWidgets.QCheckBox("Aim")

        self.tmp_cc_opt_type_vb.addWidget(self.tmp_cc_opt_type_loc_chk)
        self.tmp_cc_opt_type_vb.addWidget(self.tmp_cc_opt_type_rot_chk)
        self.tmp_cc_opt_type_vb.addWidget(self.tmp_cc_opt_type_scl_chk)
        self.tmp_cc_opt_type_vb.addWidget(self.tmp_cc_opt_type_aim_chk)

        self.tmp_cc_opt_type_loc_chk.clicked.connect(
            self.temp_cc_opt_const_type_mutual_exclusion_loc_rot)
        self.tmp_cc_opt_type_rot_chk.clicked.connect(
            self.temp_cc_opt_const_type_mutual_exclusion_loc_rot)
        self.tmp_cc_opt_type_aim_chk.clicked.connect(
            self.temp_cc_opt_const_type_mutual_exclusion_aim)

        self.tmp_cc_opt_hb.addLayout(self.tmp_cc_opt_type_vb)

    def _add_tmp_ctrl_baking_options(self):
        """Adds baking options for tmp_ctrls"""
        self.tmp_cc_opt_baking_vb = QtWidgets.QVBoxLayout()
        self.tmp_cc_opt_baking_vb.setAlignment(QtCore.Qt.AlignTop)
        self.tmp_cc_opt_baking_lbl = QtWidgets.QLabel(
            "Bake Animation Options: ")
        self.tmp_cc_opt_baking_vb.addWidget(self.tmp_cc_opt_baking_lbl)

        self.tmp_cc_opt_baking_none_rad = QtWidgets.QRadioButton(
            "Don't Bake")
        self.tmp_cc_opt_baking_vb.addWidget(
            self.tmp_cc_opt_baking_none_rad)
        self.tmp_cc_opt_baking_time_slider_rad = QtWidgets.QRadioButton(
            "Bake Time Slider Range", checked=True)
        self.tmp_cc_opt_baking_vb.addWidget(
            self.tmp_cc_opt_baking_time_slider_rad)
        self.tmp_cc_opt_baking_start_end_rad = QtWidgets.QRadioButton(
            "Bake Start/End Range")
        self.tmp_cc_opt_baking_vb.addWidget(
            self.tmp_cc_opt_baking_start_end_rad)

        self.tmp_cc_opt_baking_smart_chk = QtWidgets.QCheckBox("Smart Bake")
        self.tmp_cc_opt_baking_vb.addWidget(self.tmp_cc_opt_baking_smart_chk)

        self.tmp_cc_opt_hb.addLayout(self.tmp_cc_opt_baking_vb)

    def _add_cc_options(self):
        """Adds the CC shape options, including shape, color, size,
        and orientation"""
        self._add_cc_shape_options()
        self._add_cc_color_options()
        self._add_cc_orient_options()
        self._add_cc_scale_options()

        self.tmp_cc_opt_hb.addLayout(self.tmp_cc_opt_shape_form)

    def _add_cc_scale_options(self):
        self.tmp_cc_opt_shape_scale_spn = QtWidgets.QDoubleSpinBox(value=1.25)
        self.tmp_cc_opt_shape_scale_spn.setSingleStep(0.25)
        self.tmp_cc_opt_shape_scale_spn.setRange(0.25, 10)
        self.tmp_cc_opt_shape_form.addRow("Scale: ",
                                          self.tmp_cc_opt_shape_scale_spn)

    def _add_cc_orient_options(self):
        self.tmp_cc_opt_shape_orient_hb = QtWidgets.QHBoxLayout()
        self.tmp_cc_opt_shape_orient_cmb = QtWidgets.QComboBox()
        self.tmp_cc_opt_shape_orient_cmb.addItems(
            ["X", "Y", "Z"])
        self.tmp_cc_opt_shape_orient_hb.addWidget(
            self.tmp_cc_opt_shape_orient_cmb)
        self.tmp_cc_opt_shape_orient_negative_chk = (
            QtWidgets.QCheckBox("Negative"))
        self.tmp_cc_opt_shape_orient_hb.addWidget(
            self.tmp_cc_opt_shape_orient_negative_chk)
        self.tmp_cc_opt_shape_form.addRow("Orientation: ",
                                          self.tmp_cc_opt_shape_orient_hb)

    def _add_cc_color_options(self):
        self.tmp_cc_opt_shape_color_cmb = QtWidgets.QComboBox()
        self.tmp_cc_opt_shape_color_cmb.addItems(
            ["Pink", "Red", "Blue", "Green", "Yellow"])
        self.tmp_cc_opt_shape_form.addRow("Color: ",
                                          self.tmp_cc_opt_shape_color_cmb)

    def _add_cc_shape_options(self):
        self.tmp_cc_opt_shape_form = QtWidgets.QFormLayout()
        self.tmp_cc_opt_shape_form.setAlignment(QtCore.Qt.AlignTop)

        self.tmp_cc_opt_shape_lbl = QtWidgets.QLabel("CC Options:")
        self.tmp_cc_opt_shape_form.addRow(self.tmp_cc_opt_shape_lbl)

        self.tmp_cc_opt_shape_type_cmb = QtWidgets.QComboBox()
        self.tmp_cc_opt_shape_type_cmb.addItems(
            ["Circle", "Diamond", "Square"])
        self.tmp_cc_opt_shape_form.addRow("Shape: ",
                                          self.tmp_cc_opt_shape_type_cmb)

    def _add_new_temp_ctrl_to_cmb(self):
        self.new_temp_cc_name = self.SpaceSwitcher.temp_controllers[-1]["name"]
        self.temp_ctrl_panel_cmb.addItem(self.new_temp_cc_name)

    def _get_temp_cc_user_params(self):
        """Gets all user input paramters to create the temp controller"""
        self.tmp_cc_loc = self.tmp_cc_opt_type_loc_chk.isChecked()
        self.tmp_cc_rot = self.tmp_cc_opt_type_rot_chk.isChecked()
        self.tmp_cc_scl = self.tmp_cc_opt_type_scl_chk.isChecked()
        self.tmp_cc_aim = self.tmp_cc_opt_type_aim_chk.isChecked()

        self.tmp_cc_color = str(
            self.tmp_cc_opt_shape_color_cmb.currentText()).lower()
        self.tmp_cc_shape = str(
            self.tmp_cc_opt_shape_type_cmb.currentText()).lower()
        self.tmp_cc_orient = str(
            self.tmp_cc_opt_shape_orient_cmb.currentText()).lower()
        self.tmp_cc_size = self.tmp_cc_opt_shape_scale_spn.value()
        self.tmp_cc_orient_negative = (
            self.tmp_cc_opt_shape_orient_negative_chk.isChecked())

        self.tmp_cc_smart_bake = self.tmp_cc_opt_baking_smart_chk.isChecked()

        if self.tmp_cc_opt_baking_time_slider_rad.isChecked():
            self.tmp_cc_time_range = "time slider"
        elif self.tmp_cc_opt_baking_start_end_rad.isChecked():
            self.tmp_cc_time_range = "start/end"
        elif self.tmp_cc_opt_baking_none_rad.isChecked():
            self.tmp_cc_time_range = "none"

    @QtCore.Slot()
    def snap_tools_button(self):
        """Uses the snap_to_selected() function, passing
        the quick snap checkboxes as parameters."""
        snap_to_selected(loc=self.loc_chkbx.isChecked(),
                         rot=self.rot_chkbx.isChecked(),
                         scl=self.scl_chkbx.isChecked())

    @QtCore.Slot()
    def create_temp_ctrl(self):
        """Creates the temporary controller through the SpaceSwitcher class,
        which instantiates a TempControl object, stores it in memory to allow
        for deleting/baking down, and creates the temp control in Maya. Also
        handles selection errors."""
        if len(cmds.ls(selection=True)) < 1:
            cmds.warning("At least one object must be selected.")
            return None
        if len(cmds.ls(selection=True)) > 2:
            cmds.warning("No more than two objects must be selected.")
            return None

        self._get_temp_cc_user_params()

        cmds.undoInfo(openChunk=True)

        self.SpaceSwitcher.create_new_temp_ctrl(
            loc=self.tmp_cc_loc, rot=self.tmp_cc_rot, scl=self.tmp_cc_scl,
            aim=self.tmp_cc_aim, color=self.tmp_cc_color,
            shape=self.tmp_cc_shape, size=self.tmp_cc_size,
            orient=self.tmp_cc_orient, smart_bake=self.tmp_cc_smart_bake,
            time_range=self.tmp_cc_time_range,
            orient_negative=self.tmp_cc_orient_negative)
        self._add_new_temp_ctrl_to_cmb()

        cmds.undoInfo(closeChunk=True)

    @QtCore.Slot()
    def temp_cc_opt_const_type_mutual_exclusion_aim(self):
        """
        Controls logic around selecting the aim constraint checkbox.
        Basically, it doesn't make sense to use the aim constraint with
        a point or orient constraint, so this logic auto prevents those
        combinations
        """
        if self.tmp_cc_opt_type_aim_chk.isChecked():
            self.tmp_cc_opt_type_loc_chk.setChecked(False)
            self.tmp_cc_opt_type_rot_chk.setChecked(False)

    @QtCore.Slot()
    def temp_cc_opt_const_type_mutual_exclusion_loc_rot(self):
        """
        Controls logic around selecting the location/rotation constraint
        checkbox. Basically, it doesn't make sense to use the aim
        constraint with a point or orient constraint, so this logic
        auto prevents those combinations
        """
        if (self.tmp_cc_opt_type_loc_chk.isChecked()
                or self.tmp_cc_opt_type_rot_chk.isChecked()):
            self.tmp_cc_opt_type_aim_chk.setChecked(False)

    @QtCore.Slot()
    def delete_temp_cc(self):
        """
        Delete associated temp_cc in Maya, in the SpaceSwitcher class'
        memory, and clears it from the Temp CCs QComboBox.
        Will also bake original CC back to curve if bake is True
        """
        selected_temp_cc = self.temp_ctrl_panel_cmb.currentText()
        for temp_cc in self.SpaceSwitcher.temp_controllers:
            if temp_cc["name"] == selected_temp_cc:
                if self.bake_down:
                    temp_cc["object"].bake_child_anim()
                temp_cc["object"].kill_hierarchy()
                break

        self.bake_down = False

        self.temp_ctrl_panel_cmb.removeItem(
            self.temp_ctrl_panel_cmb.currentIndex())

    @QtCore.Slot()
    def bake_back_anim(self):
        """Bakes temp cc anim data back to ctrl"""
        self.bake_down = True
        self.delete_temp_cc()


class TempControl():
    """Main class for instantiating and building temporary controllers"""
    def __init__(self, shape="circle", color="pink", size=1.25, orient="x",
                 loc=True, rot=True, scl=False, aim=False, smart_bake=False,
                 time_range="time slider", orient_negative=True):
        self._get_relations()

        self._make_namespace()

        self.shape = shape
        self.orient = orient
        self.orient_negative = orient_negative
        self.cc_color = color
        self.size = size

        self.bake_anim = True
        self.smart_bake = smart_bake
        self.time_range = time_range

        self.constrain_loc = loc
        self.constrain_rot = rot
        self.constrain_scl = scl
        self.constrain_aim = aim

    def _make_namespace(self):
        """
        Used to generate object names with appropriate naming conventions
        while avoiding errors caused by duplicate names. Also allows
        for changing the naming conventions without breaking code.
        """
        default_name = self.child_object + "_tmp_CC"
        increment_suffix = 0
        while cmds.ls(default_name) != []:
            increment_suffix += 1
            default_name = (self.child_object + "_tmp_CC_" +
                            str(increment_suffix))
        self.name = default_name
        self.grp_name = default_name.replace("tmp_CC", "tmp_cc_GRP")

    def _get_relations(self):
        """
        Method used to get the names of the objects in the parent and child
        objects in the temp controller hierarchy. If only one object is
        selected, returns "#world" to signify world space.
        """
        selections = cmds.ls(selection=True)
        if len(selections) < 1:
            cmds.error("At least one object must be selected")
        elif len(selections) == 1:
            self.parent_object = "#world"
        elif len(selections) == 2:
            self.parent_object = selections[0]
        else:
            cmds.error("No more than 2 objects must be selected")

        self.child_object = selections[-1]

    def _create_cc_shape(self):
        """
        Handles all the options associated with the temp control curve
        itself, including changing its color, size, and manipulating its shape
        """
        valid_shapes = ("circle", "square", "diamond")
        if self.shape not in valid_shapes:
            raise ValueError("Shape parameter must be one of the following: "
                             + str(valid_shapes))

        # if chooses from type: locator, circle, square, triangle, diamond
        if self.shape == "circle":
            self._create_circle_cc()
        if self.shape == "square":
            self._manipulate_cc(scale_value=1.5)
        if self.shape == "diamond":
            self._manipulate_cc(scale_value=0)

        self._color_cc()
        self._set_tmp_cc_size()

    def _color_cc(self):
        """Colors temp control curve"""
        # In Maya's drawing overrides, colors are associated with the
        # indices listed below
        valid_colors = {"red": 13, "green": 14, "yellow": 17, "blue": 6,
                        "pink": 9}
        if self.cc_color not in valid_colors:
            raise ValueError("Color parameter must be one of the folloiwng: "
                             + str(valid_colors))

        cmds.setAttr(f"{self.name}Shape.overrideEnabled", 1)
        cmds.setAttr(f"{self.name}Shape.overrideColor",
                     valid_colors[self.cc_color])

    def _create_circle_cc(self):
        """Creates the basic circle temp control curve"""
        cmds.circle(name=self.name)
        # cmds.circle orients to the world Z axis by default
        if self.orient == "x":
            cmds.xform(self.name, rotation=[0, 90, 0])
        if self.orient == "y":
            cmds.xform(self.name, rotation=[90, 0, 0])
        clean(self.name)

    def _manipulate_cc(self, scale_value):
        """Manipulates every other cv of the temp_cc, used to create a
        pointed diamond star shape or a rounded square"""
        self._create_circle_cc()

        cc_cvs = cmds.ls(f"{self.name}.cv[:]", flatten=True)
        cv_num = 0
        while cv_num < len(cc_cvs):
            if cv_num % 2 == 0:
                cmds.select(cc_cvs[cv_num], add=True, toggle=True)
            cv_num += 1

        cmds.hilite(self.name)
        cmds.xform(scale=[scale_value, scale_value, scale_value])
        cmds.hilite(self.name, unHilite=True)
        cmds.select(clear=True)

    def _create_hierarchy(self, master_grp=None):
        """Handles creating the initial hierarchy of the temp controller,
        including all the grouping, parenting, and constraining of the
        temp controller to the child object before baking"""
        cmds.group(self.name,
                   name=self.grp_name)

        if master_grp is not None:
            cmds.parent(self.grp_name, master_grp)

        snap_to(self.name, self.child_object)

        if self.parent_object != "#world":
            self.tmp_cc_grp_const = cmds.parentConstraint(self.parent_object,
                                                          self.grp_name)[0]
        if self.constrain_loc:
            self.tmp_cc_loc_const = cmds.pointConstraint(self.child_object,
                                                         self.name)[0]
        if self.constrain_rot:
            self.tmp_cc_rot_const = cmds.orientConstraint(self.child_object,
                                                          self.name)[0]
        if self.constrain_scl:
            self.tmp_cc_scl_const = cmds.scaleConstraint(self.child_object,
                                                         self.name)[0]
        if self.constrain_aim:
            self._setup_aim_cc()

    def _setup_aim_cc(self):
        """Handles the added setup for making an aim constraint,
        namely offsetting the controller along an axis and parent constraining.
        """
        self.aim_offset = 3
        if self.orient_negative:
            self.aim_offset *= -1
        self.aim_axis = self.orient
        self.aim_trans_vector = [0, 0, 0]
        self.aim_up_vector = [0, 0, 0]
        self.axes = {'x': 0, 'y': 1, 'z': 2}
        self.aim_trans_vector[self.axes[self.aim_axis]] = (
            self.aim_offset * self.def_scale)
        cmds.xform(self.name, translation=self.aim_trans_vector, relative=True)
        self.tmp_cc_aim_const = cmds.parentConstraint(
                self.child_object, self.name, maintainOffset=True)[0]

    def _add_inverse_consts(self):
        """For all none-controlled transforms, adds a constraint from the
        child object to the cc for more user friendly behavior"""
        # Aim controllers  are discluded from using an inverse point/
        # orient constraint to avoid creating a cyclic-dependency.
        if not self.constrain_loc and not self.constrain_aim:
            self.tmp_cc_loc_const_inv = cmds.pointConstraint(self.child_object,
                                                             self.name)[0]
        if not self.constrain_rot and not self.constrain_aim:
            self.tmp_cc_rot_const_inv = cmds.orientConstraint(
                self.child_object, self.name)[0]
        if not self.constrain_scl:
            self._break_connections(self.name, "scale")
            self.tmp_cc_scl_const_inv = cmds.scaleConstraint(
                self.child_object, self.name)[0]

    def _break_connections(self, object, xform_channel):
        """Breaks connections of a specified object's transformation channels.
        Used because there's a weird 'feature' in Maya where you can't seem
        to add scale constraints (and ONLY scale constraints) if there's
        already keys on the scale channel."""
        for axis in ('X', 'Y', 'Z'):
            cmds.delete(f"{object}.{xform_channel}{axis}",
                        inputConnectionsAndNodes=True)

    def _bake_anim(self, object, delete_consts=True,
                   smart_bake_tolerance=10):
        """Bakes out animation from constraints, and optionally deletes them"""
        cmds.bakeResults(object, simulation=True,
                         time=(self.bake_start, self.bake_end),
                         smart=[self.smart_bake, smart_bake_tolerance])
        if delete_consts:
            consts = cmds.listRelatives(object, children=True,
                                        type="constraint")
            for const in consts:
                cmds.delete(const)

    def bake_child_anim(self):
        """Bakes animation data of child object"""
        self._bake_anim(self.child_object, delete_consts=False)

    def _const_child_to_tmp_cc(self):
        """Handles constraining the child object to the temp cc based on
        the type of constraint specified by the user"""
        self.child_obj_consts = []
        if self.constrain_loc:
            self.child_obj_loc_const = (
                cmds.pointConstraint(self.name, self.child_object))[0]
            self.child_obj_consts.append(self.child_obj_loc_const)
        if self.constrain_rot:
            self.child_obj_rot_const = (
                cmds.orientConstraint(self.name, self.child_object))[0]
            self.child_obj_consts.append(self.child_obj_rot_const)
        if self.constrain_scl:
            self._break_connections(self.child_object, "scale")
            self.child_obj_scl_const = (
                cmds.scaleConstraint(self.name, self.child_object))[0]
            self.child_obj_consts.append(self.child_obj_scl_const)
        if self.constrain_aim:
            self.child_obj_aim_const = (
                cmds.aimConstraint(self.name, self.child_object,
                                   maintainOffset=True, worldUpType="none"))
            self.child_obj_consts.append(self.child_obj_aim_const)

    def _get_time_range(self):
        """Used to get time range for baking animation"""
        if self.time_range == "time slider":
            self.bake_start = cmds.playbackOptions(minTime=True, query=True)
            self.bake_end = cmds.playbackOptions(maxTime=True, query=True)
        elif self.time_range == "start/end":
            self.bake_start = cmds.playbackOptions(animationStartTime=True,
                                                   query=True)
            self.bake_end = cmds.playbackOptions(animationEndTime=True,
                                                 query=True)
        elif self.time_range == "none":
            self.bake_start = cmds.currentTime(query=True)
            self.bake_end = self.bake_start
        else:
            raise ValueError("Invalid time range: _get_time_range() only" +
                             "accepts 'time slider' and 'start/end'")

    def _set_tmp_cc_size(self):
        """
        Sets the size of the temporary controller by getting the
        bounding box of the child object and multiplying it against
        the size parameter.
        """
        # The exact world bounding box command returns a list with the
        # minimum and maximum coordinates of each axis
        bb_min_x, bb_min_y, bb_min_z, bb_max_x, bb_max_y, bb_max_z = (
            cmds.exactWorldBoundingBox(self.child_object))

        x_scale = (bb_max_x - bb_min_x)/2
        y_scale = (bb_max_y - bb_min_y)/2
        z_scale = (bb_max_z - bb_min_z)/2

        self.def_scale = 0
        for scale in (x_scale, y_scale, z_scale):
            if scale > self.def_scale:
                self.def_scale = scale

        self.def_scale *= self.size

        cmds.xform(self.name,
                   scale=[self.def_scale, self.def_scale, self.def_scale])
        clean(self.name)

    def _get_locked_transforms(self):
        """Returns true if child object has any locked transforms to abort
        temp cc creation"""
        transforms = []
        if self.constrain_loc:
            transforms.append("translate")
        if self.constrain_rot or self.constrain_aim:
            transforms.append("rotate")
        if self.constrain_scl:
            transforms.append("scale")
        axes = ["X", "Y", "Z"]

        self.locked_transforms = []
        for transform in transforms:
            for axis in axes:
                if cmds.getAttr(f"{self.child_object}.{transform}{axis}",
                                lock=True):
                    self.locked_transforms.append(f"{transform}{axis}")

    def kill_hierarchy(self):
        """
        Method used to delete all components of the temp control hierarchy
        """
        cmds.delete(self.grp_name)

    def create_temp_ctrl(self, master_grp=None):
        """Creates location space switch on selected objects"""
        self._get_locked_transforms()
        if self.locked_transforms != []:
            cmds.warning(f"The child object '{self.child_object}'" +
                         "has locked transformation channels: " +
                         str(self.locked_transforms))
            return None
        self._create_cc_shape()
        self._create_hierarchy(master_grp=master_grp)
        self._get_time_range()
        self._bake_anim(self.name)
        self._add_inverse_consts()
        self._const_child_to_tmp_cc()


class SpaceSwitcher():
    """A class made chiefly to handle storing TempControl objects in
    the UI's 'memory', allowing the user to optionally continue to edit
    existing temp controllers after their creation, namely in the form
    of deleting or baking down the controllers."""
    def __init__(self):
        self.master_grp = "__space_switch_master__"
        self.temp_controllers = []

    def create_new_temp_ctrl(self, loc, rot, scl, aim, color, shape, size,
                             orient, orient_negative, time_range, smart_bake):
        """The main function of SpaceSwitcher, which creates a new temp
        controller, parents it under a master group node, and adds it to
        memory to be referred to later."""
        new_temp_ctrl = TempControl(loc=loc, rot=rot, scl=scl, aim=aim,
                                    color=color, shape=shape, size=size,
                                    orient=orient, time_range=time_range,
                                    smart_bake=smart_bake,
                                    orient_negative=orient_negative)

        if cmds.ls(self.master_grp) == []:
            self.master_grp = cmds.group(name=self.master_grp, empty=True)

        new_temp_ctrl.create_temp_ctrl(master_grp=self.master_grp)

        new_temp_ctrl_dict = {"name": new_temp_ctrl.name,
                              "object": new_temp_ctrl}

        self.temp_controllers.append(new_temp_ctrl_dict)


def snap_to_selected(loc=True, rot=True, scl=True):
    """Snaps selected objects to last selected"""
    cmds.undoInfo(openChunk=True)
    if len(cmds.ls(selection=True)) < 2:
        cmds.warning("At least two objects must be selected.")
        return None
    children = cmds.ls(selection=True)[0:-1]
    parent = cmds.ls(selection=True)[-1]
    snap_to(children, parent, loc, rot, scl)
    cmds.undoInfo(closeChunk=True)


def snap_to(children, parent, loc=True, rot=True, scl=True):
    """Snaps children object to xforms of the parent"""
    if type(children) == str:
        children = [children]
    for child in children:
        if loc:
            loc_const = cmds.pointConstraint(parent, child)
            cmds.delete(loc_const)
        if rot:
            rot_const = cmds.orientConstraint(parent, child)
            cmds.delete(rot_const)
        if scl:
            scl_const = cmds.scaleConstraint(parent, child)
            cmds.delete(scl_const)


def clean(object, delete_history=True, freeze_transforms=True):
    """Clears mesh construction history, freezes transforms"""
    if delete_history:
        cmds.delete(object, constructionHistory=True)
    if freeze_transforms:
        cmds.makeIdentity(object, apply=True)


if __name__ == "__main__":
    main()
