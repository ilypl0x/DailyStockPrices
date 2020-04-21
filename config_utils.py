import yaml
import inspect
from log_utils import get_logger

logger = get_logger()

def get_yaml_params(yaml_fname=''):

    frame = inspect.stack()[-1]
    module = inspect.getmodule(frame[0])
    module_name = (module.__file__).split('\\')[1].split('.')[0]
    yaml_fname = module_name + '.yaml'

    try:
        stream = open(yaml_fname, 'r')
        logger.info("Successfully loaded the {}".format(yaml_fname))
        return yaml.load(stream, Loader=yaml.FullLoader)
    except FileNotFoundError:
        logger.error('{0} did not exist and so a blank {1} file was created. Please fill in accordingly and re-run.'.format(yaml_fname,yaml_fname))
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
