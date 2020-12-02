"""
Copyright 2015 Medical Research Council Harwell.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

E-mail the developers: sig@har.mrc.ac.uk



Creates a YAMl file in app directory that stores details such as last directory browsed

"""
from .lib import appdirs
import yaml
from os.path import expanduser
import os
import fnmatch

default_ignore = ['*spr.bmp', '*spr.tif', '*spr.tiff', '*spr.jpg', '*spr.jpeg', '*.txt', '*.text', '*.log', '*.crv']
default_use = ['*rec*.bmp', '*rec*.tif', '*rec*.tiff', '*rec*.jpg', '*rec*.jpeg']

default_center = 'HAR'


class AppData(object):
    def __init__(self):
        self.using_appdata = True  # Set to false if we weren't able to find a directory to save the appdata
        appname = 'harp'
        appdata_dir = appdirs.user_data_dir(appname)
        self.app_data = {}

        if not os.path.isdir(appdata_dir):
            try:
                os.mkdir(appdata_dir)
            except OSError:
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
            yaml_load_error = False
            if os.path.isfile(self.app_data_file):
                with open(self.app_data_file, 'r') as fh:
                    try:
                        self.app_data = yaml.load(fh)
                    except yaml.reader.ReaderError as e:
                        # try to remove file
                        try:
                            os.remove(self.app_data_file)
                        except OSError as e:
                            print(('the harp app data config file at {} is corrupt, nad it cannot be deleted. '
                                  'Please remove it before restarting'.format(self.app_data_file)))
                            yaml_load_error = True

                # In case loading failed
                if not self.app_data or not isinstance(self.app_data, dict) or yaml_load_error:
                    self.app_data = {}

    def save(self):
        if self.using_appdata:
            with open(self.app_data_file, 'w') as fh:
                fh.write(yaml.dump(self.app_data))

    @property
    def center(self):
        if not self.app_data.get('center'):
            self.app_data['center'] = default_center
        return self.app_data['center']

    @center.setter
    def center(self, cen):
        self.app_data['center'] = cen

    @property
    def last_dir_browsed(self):
        if not self.app_data.get('last_dir_browsed'):
            self.app_data['last_dir_browsed'] = expanduser("~")
        return self.app_data['last_dir_browsed']

    @last_dir_browsed.setter
    def last_dir_browsed(self, path):
         self.app_data['last_dir_browsed'] = path

    @property
    def files_to_ignore(self):

        if not self.app_data.get('files_to_ignore'):
            self.app_data['files_to_ignore'] = default_ignore
        return self.app_data['files_to_ignore']


    @files_to_ignore.setter
    def files_to_ignore(self, pattern_list):

        self.app_data['files_to_ignore'] = pattern_list

    @property
    def files_to_use(self):
        if not self.app_data.get('files_to_use'):
            self.app_data['files_to_use'] = default_use
        return self.app_data['files_to_use']

    @files_to_use.setter
    def files_to_use(self, pattern_list):
        self.app_data['files_to_use'] = pattern_list

    def reset_ignore_file(self):
        self.app_data['files_to_ignore'] = default_ignore

    def reset_use_file(self):
        self.app_data['files_to_use'] = default_use

    @property
    def suppress_name_warnings(self):

        if not self.app_data.get('suppress_name_warnings'):
            self.app_data['suppress_name_warnings'] = False

        return self.app_data['suppress_name_warnings']


    @suppress_name_warnings.setter
    def suppress_name_warnings(self, suppress):

        self.app_data['suppress_name_warnings'] = suppress

    @property
    def suppress_modality_warnings(self):

        if not self.app_data.get('suppress_modality_warnings'):
            self.app_data['suppress_modality_warnings'] = False
        return self.app_data['suppress_modality_warnings']


    @suppress_modality_warnings.setter
    def suppress_modality_warnings(self, suppress):

        self.app_data['suppress_modality_warnings'] = suppress

    def getfilelist(self, input_folder):
        """
        Get the list of files from filedir. Exclude known non slice files
        """
        files = []

        for fn in os.listdir(input_folder):

            if any(fnmatch.fnmatch(fn.lower(), x.lower()) for x in self.files_to_ignore):
                continue

            if any(fnmatch.fnmatch(fn.lower(), x.lower()) for x in self.files_to_use):
                files.append(os.path.join(input_folder, fn))

        return sorted(files)

class HarpDataError(Exception):
    """
    Raised when some of the supplied data is found to be faulty
    """
    pass


