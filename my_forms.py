import copy
from universal import *


class FormUnit:
    def __init__(self, name, header, *args, value='', required=True, **kwargs):
        self.name = name
        self.required = required
        self.header = header
        self.value = value
        self.start(*args, **kwargs)

    def fill(self, d):
        return self._make_filled_copy(d[self.name])
    
    def _make_filled_copy(self, v):
        c = copy.copy(self)
        c.set_value(v)
        return c

    def set_value(self, v):
        self.value = v

    def html(self):
        x = f'name="{self.name}" id="{self.name}"'
        x += ' required' if self.required else ''
        if self.value:
            x += f' value="{self.value}"'
        header = self.header + (' *' if self.required else '')
        label = f'<span class="unit-header">{header}</span>'
        inner = label + self.input_html(x)
        return f'<div class="form-unit">{inner}</div>'

    def input_html(self, x):
        pass

    def start(self, *args, **kwargs):
        pass


class Inputfield(FormUnit):
    def start(self, placeholder='', numeric=False, password=False, email=False):
        self.placeholder = placeholder
        self.numeric = numeric
        self.password = password
        self.email = email

    def get_type(self):
        if self.numeric:
            return 'numeric'
        if self.password:
            return 'password'
        if self.email:
            return 'email'
        return 'text'

    def input_html(self, x):
        return f'<input type="{self.get_type()}" placeholder="{self.placeholder}"' \
            + f' class="inputfield" {x}>'


class Textarea(FormUnit):
    def start(self, placeholder=''):
        self.placeholder = placeholder
    
    def input_html(self, x):
        return '<textarea class="input inputfield multiline"' \
            + f' placeholder="{self.placeholder}" {x}></textarea>'


class Options(FormUnit):
    def start(self, content, radio=False):
        self.content = content
        self.radio = radio

    def _extract_option(self, w):
        return w[len(self.name) + 1:]

    def fill(self, d):
        if self.radio:
            return super().fill(d)
        return self._make_filled_copy([
            option for k in d if (option := 
                self._extract_option(k)) in self.content
        ])
 
    def get_checked_ids(self):
        w = list(self.content.keys())

        if self.radio:
            if self.value not in w:
                return [0]
            return [w.index(self.value)]
        
        return [w.index(v) for v in self.value if v in w]

    def html(self):
        html = f'<span class="input-header">{self.header}</span>'
        checked_ids = self.get_checked_ids()
        for i, (k, v) in enumerate(self.content.items()):
            x = ' checked' if i in checked_ids else ''
            idx = self.name + '_' + k
            type_ = 'radio' if self.radio else 'checkbox'
            name = self.name if self.radio else idx
            html += '<div class="pair-holder">'
            html += f'<input type="{type_}" id="{idx}" name="{name}" value="{k}"{x}>'
            html += f'<label for="{idx}">{v}</label></div>'
        return html
    

class Date(FormUnit):
    def start(self):
        pass

    def input_html(self, x):
        return f'<input type="date" min="2000-01-01" max="2030-12-31" {x}>'


class Form:
    def __init__(self, name, handler, units, exit_cond=lambda: False):
        self.units = units
        self.name = name
        self.handler = handler
        self.exit_cond = exit_cond

    def html(self):
        return ''.join([
            unit.html() for unit in self.units
        ])
    
    def fill(self, d):
        c = copy.copy(self)
        c.units = [u.fill(d)
            for u in self.units]
        return c

    def __call__(self, data):
        return self.handler(data)


