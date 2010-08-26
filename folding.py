# -*- coding: utf-8 -*-
import gtk
import gedit

ui_str = """<ui>
	<menubar name="MenuBar">
		<menu name="ToolsMenu" action="Tools">
			<placeholder name="ToolsOps_2">
				<menuitem name="Folding" action="FoldingPy"/>
				<menuitem name="Folding All" action="FoldingPyAll"/>
			</placeholder>
		</menu>
	</menubar>
</ui>
"""
	
class FoldingPyWindowHelper():
	def __init__(self, plugin, window):
		self._window = window
		self._plugin = plugin
		self._insert_menu()
                self._fold_all = True
		self.update_ui()

	def deactivate(self):
		self._remove_menu()
		self._window = None
		self._plugin = None
		self._action_group = None

	def _insert_menu(self):
		manager = self._window.get_ui_manager()
		self._action_group = gtk.ActionGroup("FoldingPyPluginActions")
		self._action_group.add_actions(
			[
				(
					"FoldingPy", None, "Fold",
					"<Alt>Z", "Fold",
					self.fold
				),
				(
					"FoldingPyAll", None, "Fold all",
					"<Alt>K", "Fold all",
					self.fold_all
				)
			],
		)
		manager.insert_action_group(self._action_group, -1)
		self._ui_id = manager.add_ui_from_string(ui_str)

	def _remove_menu(self):
		manager = self._window.get_ui_manager()
		manager.remove_ui(self._ui_id)
		manager.remove_action_group(self._action_group)
		manager.ensure_update()

	def update_ui(self):
		self._action_group.set_sensitive(self._window.get_active_document() != None)
		self.doc=self._window.get_active_document()
		if self.doc:
			self.view=self._window.get_active_view()
			self.view.connect('key-press-event', self.fold_off)
			
			table=self.doc.get_tag_table()
			self.fld=table.lookup('fld')
			if self.fld==None:
				self.fld=self.doc.create_tag('fld',foreground="#333333",paragraph_background="#aadc5c")
			self.inv=table.lookup('inv')
			if self.inv==None:
				self.inv=self.doc.create_tag('inv',invisible=True)

	def detect_sps(self,sps):
		sps_lstrip=sps.lstrip()
		i=sps.index(sps_lstrip)
		sps=sps[:i]
		return sps.count(' ')+sps.count('\t')*self.view.get_tab_width()

	def fold_off(self,widget=None,e=None,force=False):
		if force or (e.hardware_keycode==53 and self.keycode==64):
			s,e=self.doc.get_bounds()
			self.doc.remove_tag(self.fld,s,e)
			self.doc.remove_tag(self.inv,s,e)
			self.keycode=53
			#print "SimpleFolding plugin: remove all fold"
		else:
			self.keycode=e.hardware_keycode

        def fold_all(self, action=None):
            if self._fold_all:
                line = 1
                lines = self.doc.get_line_count()
                while line <= lines:
                    res = self.fold(a=self.doc.get_iter_at_line(line))
                    if res is not None and res>line:
                        line = res
                    else:
                        line = line+1
            else:
                self.fold_off(force=True)

            self._fold_all = not self._fold_all

	def fold(self, action=None, a=None):
                if a is None:
    		    a=self.doc.get_iter_at_mark(self.doc.get_insert())

		if a.has_tag(self.fld):
			try:
				a.set_line_offset(0)
				b=a.copy()
				b.forward_line()
				self.doc.remove_tag(self.fld,a,b)
				a.forward_to_tag_toggle(self.inv)
				b.forward_to_tag_toggle(self.inv)
				self.doc.remove_tag(self.inv,a,b)
				#print "SimpleFolding plugin: remove one fold"
			except:
				pass

		elif len(self.doc.get_selection_bounds())==2:
			a,c=self.doc.get_selection_bounds()
			b=a.copy()
			a.set_line_offset(0)
			b.forward_line()
			c.forward_line()
			self.doc.apply_tag(self.fld,a,b)
			self.doc.remove_tag(self.fld,b,c)
			self.doc.remove_tag(self.inv,b,c)
			self.doc.apply_tag(self.inv,b,c)
			#print "SimpleFolding plugin: create fold by selection"

		else:
			s=a.copy()
			s.set_line_offset(0)
			line = s.get_line()
			e=s.copy()
			e.forward_line()
			t=s.get_text(e)
			if t.strip()!="":
                                ne = None
				main_indent = self.detect_sps(s.get_text(e))
				ns=s.copy()
				fin=ns.copy()
				while 1==1:
					if ns.forward_line():
						ne=ns.copy()
						if ne.get_char()=="\n":
							continue
						ne.forward_to_line_end()
						text=ns.get_text(ne)
						if text.strip()=="":
							continue
						child_indent=self.detect_sps(text)
						if child_indent <= main_indent:
							break
						else:
							line=ns.get_line()
						fin=ns.copy()
						fin.set_line(line)
						fin.forward_line()
					else:
                                                if ne is not None:
        						fin=ne.copy()
        						fin.forward_to_end()
        						line=fin.get_line()
						break
		
				if s.get_line()<line:
					self.doc.apply_tag(self.fld,s,e)
					self.doc.remove_tag(self.fld,e,fin)
					self.doc.remove_tag(self.inv,e,fin)
					self.doc.apply_tag(self.inv,e,fin)
                                        return line
					#print "SimpleFolding plugin: create fold by indent"
                return None


class FoldingPyPlugin(gedit.Plugin):
	def __init__(self):
		gedit.Plugin.__init__(self)
		self._instances = {}
	def activate(self, window):
		self._instances[window] = FoldingPyWindowHelper(self, window)
	def deactivate(self, window):
		self._instances[window].deactivate()
		del self._instances[window]
	def update_ui(self, window):
		self._instances[window].update_ui()
