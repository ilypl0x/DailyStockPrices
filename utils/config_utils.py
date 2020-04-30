import yaml
import inspect
import os


def get_yaml_params(yaml_fname=''):

    frame = inspect.stack()[-1]
    module = inspect.getmodule(frame[0])
    if os.name == 'nt':
        module_name = (module.__file__).split('\\')[1].split('.')[0]
    else:
        module_name = (module.__file__).split('.')[0]
    yaml_fname = module_name + '.yaml'

    try:
        stream = open(yaml_fname, 'r')
        return yaml.load(stream, Loader=yaml.FullLoader)
    except FileNotFoundError:
        yaml_dict = {'email' : {
                    'enabled': False,
                    'to': '',
                    'subject': '',
                    'attachments': False,
                    'attachment': '',
                    'title': ''},
            'log_filename' : module_name + '.log',
            'console_print': False,
            'debug_level': 'INFO'
            }
        with open(yaml_fname, 'w') as file:
            y = yaml.dump(yaml_dict, file)
