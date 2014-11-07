"""Creates a YAMl file in app directory that stores details such as last directory browsed

"""
from lib import appdirs
import os
import yaml
from os.path import expanduser
import os
import collections


class AppData(object):
    def __init__(self):
        self.using_appdata = True  # Set to false if we weren't able to find a directory to save the appdata
        appname = 'harp'
        appdata_dir = appdirs.user_data_dir(appname)

        if not os.path.isdir(appdata_dir):
            try:
                os.mkdir(appdata_dir)
            except WindowsError:
                #Can't find the AppData directory. So just make one in home directory
                appdata_dir = os.path.join(expanduser("~"), '.' + appname)
                if not os.path.isdir(appdata_dir):
                    try:
                        os.mkdir(appdata_dir)
                    except:
                        self.using_appdata = False
            except OSError:
                self.using_appdata = False

        if self.using_appdata:
            self.app_data_file = os.path.join(appdata_dir, 'app_data.yaml')

            if os.path.isfile(self.app_data_file):
                with open(self.app_data_file, 'r') as fh:
                    self.app_data = yaml.load(fh)
            else:
                self.app_data = {}


    def write_app_data(self):
        if self.using_appdata:
            with open(self.app_data_file, 'w') as fh:
                fh.write(yaml.dump(self.app_data))

    @property
    def last_dir_browsed(self):
        if self.using_appdata:
            if not self.app_data.get('last_dir_browsed'):
                self.app_data['last_dir_browsed'] = expanduser("~")
            return self.app_data['last_dir_browsed']

    @last_dir_browsed.setter
    def last_dir_browsed(self, path):
        if self.using_appdata:
            self.app_data['last_dir_browsed'] = path

