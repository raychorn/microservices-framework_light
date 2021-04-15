import json
from typing import Union


class CompactJSONEncoder(json.JSONEncoder):
    """A JSON Encoder that puts small containers on single lines."""

    CONTAINER_TYPES = (list, tuple, dict)
    """Container datatypes include primitives or other containers."""

    MAX_WIDTH = 70
    """Maximum width of a container that might be put on a single line."""

    MAX_ITEMS = 2
    """Maximum number of items in container that might be put on single line."""

    INDENTATION_CHAR = " "

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.indentation_level = 0

    def encode(self, o):
        """Encode JSON object *o* with respect to single line lists."""
        if isinstance(o, (list, tuple)):
            if self._put_on_single_line(o):
                return "[" + ", ".join(self.encode(el) for el in o) + "]"
            else:
                self.indentation_level += 1
                output = [self.indent_str + self.encode(el) for el in o]
                self.indentation_level -= 1
                return "[\n" + ",\n".join(output) + "\n" + self.indent_str + "]"
        elif isinstance(o, dict):
            if o:
                if self._put_on_single_line(o):
                    return "{ " + ", ".join(f"{self.encode(k)}: {self.encode(el)}" for k, el in o.items()) + " }"
                else:
                    self.indentation_level += 1
                    output = [self.indent_str + f"{json.dumps(k)}: {self.encode(v)}" for k, v in o.items()]
                    self.indentation_level -= 1
                    return "{\n" + ",\n".join(output) + "\n" + self.indent_str + "}"
            else:
                return "{}"
        elif isinstance(o, float):  # Use scientific notation for floats, where appropiate
            return format(o, "g")
        elif isinstance(o, str):  # escape newlines
            o = o.replace("\n", "\\n")
            return f'"{o}"'
        else:
            return json.dumps(o)

    def _put_on_single_line(self, o):
        return self._primitives_only(o) and len(o) <= self.MAX_ITEMS and len(str(o)) - 2 <= self.MAX_WIDTH

    def _primitives_only(self, o: Union[list, tuple, dict]):
        if isinstance(o, (list, tuple)):
            return not any(isinstance(el, self.CONTAINER_TYPES) for el in o)
        elif isinstance(o, dict):
            return not any(isinstance(el, self.CONTAINER_TYPES) for el in o.values())

    @property
    def indent_str(self) -> str:
        return self.INDENTATION_CHAR*(self.indentation_level*self.indent)

def get_environment_for_terraform_from(fpath, logger=None):
    '''
        environment = {
        VAR_1               = "hello"
        VAR_2               = "world"
        }      
    '''
    import os
    import sys
    from io import StringIO

    assert os.path.exists(fpath) and os.path.isfile(fpath), 'Cannot find the terraform environment from "{}".'.format(fpath)

    __env = {}
    
    from . import __env__
    m = sys.modules.get('libs.__env__')
    assert m is not None, 'Cannot find "libs.__env__". Please resolve.'
    f = getattr(m, 'read_env')
    f(fpath=fpath, environ=__env, is_ignoring=True, override=False, logger=logger)
    
    oBuf = StringIO()
    print('environment = {\n', file=oBuf)
    for k,v in __env.items():
        print('{} = "{}"\n'.format(k,v), file=oBuf)
    print('}\n', file=oBuf)
    
    return oBuf.getvalue()

if (__name__ == '__main__'):
    __env = get_environment_for_terraform_from('/home/raychorn/projects/python-projects/securex.ai/data/docker/.env')
    __json = json.dumps(__env, cls=CompactJSONEncoder)
    print(__json)