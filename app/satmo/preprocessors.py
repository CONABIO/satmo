import subprocess
import jinja2

# Make a class that holds all the information of a 

class l2gen(object):
    def __init__(self):
        pass
    def make_parfile(self):
        env = Environment(loader=PackageLoader('jbook', 'templates'))
               template = env.get_template('default.html')
               html_out = template.render(infiles = self.infiles_string)
    def execute(self):
        status = subprocess.call(['multilevel_processor.py', 'modis_SR.par'])
        # Status should be zero if command completed successfully
    def clean(self):
        



