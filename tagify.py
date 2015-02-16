import sublime
import sublime_plugin
import os
import re

class Prefs:
    @staticmethod
    def read():
        settings = sublime.load_settings('Tagify.sublime-settings')
        Prefs.common_tags = settings.get('common_tags', ["todo", "bug", "workaround"])
        Prefs.blacklisted_tags = set(settings.get('blacklisted_tags', ["property"]))
        Prefs.analyse_on_start = settings.get('analyse_on_start', True)
        Prefs.extensions = settings.get('extensions', ["py", "html", "htm", "js"])

    @staticmethod
    def load():
        settings = sublime.load_settings('Tagify.sublime-settings')
        settings.add_on_change('common_tags', Prefs.read)
        settings.add_on_change('blacklisted_tags', Prefs.read)
        settings.add_on_change('analyse_on_start', Prefs.read)
        settings.add_on_change('extensions', Prefs.read)
        Prefs.read()

class TagifyCommon:
    data = {}
    taglist = []
    ready = False


class Tagifier(sublime_plugin.EventListener):

    def __init__(self, *args, **kw):
        super(Tagifier, self).__init__(*args, **kw)
        self.last_sel = None

    def analyse_regions(self, view, regions):
        for region in regions:
            region = view.line(region)
            tag_region = view.find("@(?:[_a-zA-Z0-9]+)", region.a)
            if tag_region.a >= 0:
                self.tags_regions.append(tag_region)
        view.add_regions("tagify", self.tags_regions, "markup.inserted",
                         "bookmark", sublime.HIDDEN)

    def reanalyse_all(self, view):
        self.tags_regions = []
        regions = view.find_all("#@(?:[_a-zA-Z0-9]+)")
        self.analyse_regions(view, regions)

    def on_post_save_async(self, view):
        self.reanalyse_all(view)

    def on_load_async(self, view):
        self.reanalyse_all(view)

    def on_selection_modified(self, view):
        sel = list(view.sel())
        if len(sel) != 1:
            return
        sel = sel[0]
        if self.last_sel == sel:
            return
        self.last_sel = sel
        for region in view.get_regions('tagify-link'):
            if region.contains(sel) and sel.size() > 0:
                name = view.substr(region)
                real_name = TagifyCommon.data[name]["file"]
                line_no = TagifyCommon.data[name]["line"]
                view.window().open_file(
                    "%s:%i" % (real_name, line_no), sublime.ENCODED_POSITION)
                view.sel().clear()
                return


class ShowTagsMenuCommand(sublime_plugin.TextCommand):
    def run(self, edit):

        tags = list(set(TagifyCommon.taglist+Prefs.common_tags))

        def selected(pos):
            if pos >= 0:
                sel = self.view.sel()
                for region in sel:
                    self.view.run_command("insert", {'characters': "#@"+tags[pos]})

        self.view.show_popup_menu(tags, selected)


class GenerateSummaryCommand(sublime_plugin.TextCommand):
    def run(self, edit, data):
        out = []
        cpos = 0
        regions = []
        for tag in data:
            out.append("- %s - " % tag)
            cpos += len(out[-1]) + 1
            for entry in data[tag]:
                opos = cpos
                out.append("%s" % entry["short_file"])
                cpos += len(out[-1]) + 1
                TagifyCommon.data[entry["short_file"]] = entry
                regions.append(sublime.Region(opos, cpos - 1))
            out.append("")
            cpos += 1
        self.view.insert(edit, 0, "\n".join(out))
        self.view.add_regions(
            "tagify-link", regions, 'link', "",
            sublime.HIDDEN)
        self.view.set_read_only(True)
        self.view.set_scratch(True)


class TagifyCommand(sublime_plugin.WindowCommand):

    def __init__(self, arg):
        super(TagifyCommand, self).__init__(arg)
        self.tag_re = re.compile("#@((?:[_a-zA-Z0-9]+))(.*?)$")
        Prefs.load()
        if Prefs.analyse_on_start and not TagifyCommon.ready:
            TagifyCommon.ready = True
            try:
                sublime.set_timeout_async(lambda: self.run(True), 0)
            except AttributeError:
                sublime.set_timeout(lambda: self.run(True), 0)

    def tagify_file(self, dirname, filename, ctags, folder_prefix):
        try:
            filelines = open(os.path.join(dirname, filename), errors='replace')
            do_encode = False
        except TypeError:
            filelines = open(os.path.join(dirname, filename))
            do_encode = True
        cpos = 0
        for n, line in enumerate(filelines):
            if do_encode:
                line = line.decode('utf-8', 'replace')
            match = self.tag_re.search(line)
            if match:
                tag_name = match.group(1)
                if tag_name in Prefs.blacklisted_tags:
                    continue
                path = os.path.join(dirname, filename)
                data = {
                    'region': (cpos + match.start(1), cpos + match.end(1)),
                    'comment': match.group(2),
                    'file': path,
                    'short_file': "%s:%i" % (path[len(folder_prefix) + 1:], n + 1),
                    'line': n + 1
                }
                if tag_name in ctags:
                    ctags[tag_name].append(data)
                else:
                    ctags[tag_name] = [data]
            cpos += len(line)

    def process_file_list(self, paths, ctags, dir_prefix=None, root_prefix=None):
        for path in paths:
            if dir_prefix:
                dirname = dir_prefix
                filename = path
            else:
                dirname, filename = os.path.split(path)
            if root_prefix:
                folder = root_prefix
            else:
                folder = dirname
            ext = filename.split('.')[-1]
            processed_extensions = Prefs.extensions
            if ext in processed_extensions:
                self.tagify_file(dirname, filename, ctags, folder)


    def run(self, quiet=False):
        ctags = {}

        #process opened folders
        folders = self.window.folders()
        for folder in folders:
            for dirname, dirnames, filenames in os.walk(folder):
                self.process_file_list(filenames, ctags, dirname, folder)

        #process opened files
        self.process_file_list([view.file_name() for view in self.window.views() if view.file_name()], ctags)

        TagifyCommon.taglist = list(ctags.keys())
        if not quiet:
            summary = self.window.new_file()
            summary.set_name("Tags summary")
            summary.run_command("generate_summary", {"data": ctags})
