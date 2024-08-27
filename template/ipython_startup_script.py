import pandas
from matplotlib.pyplot import Figure, gca
import IPython

from IPython.core.formatters import BaseFormatter
from traitlets.traitlets import Unicode, ObjectName


def _figure_repr_e2b_data_(self: Figure):
    """
    This method is used to extract data from the figure object to a dictionary
    """
    ax = gca()
    lines = ax.get_lines()
    data = {
        'lines': [
            {
                'x': line.get_xdata().tolist(),
                'y': line.get_ydata().tolist(),
            }
            for line in lines if line.figure == self]
    }

    return data


def _data_frame_repr_e2b_data_(self: pandas.DataFrame):
    return self.to_dict(orient='list')


class E2BFormatter(BaseFormatter):
    format_type = Unicode('e2b/data')

    print_method = ObjectName('_repr_e2b_data_')
    _return_type = (dict, str)

    type_printers = {pandas.DataFrame: _data_frame_repr_e2b_data_}

    def __call__(self, obj):
        if isinstance(obj, Figure):
            # Figure object is for some reason removed from type_printers
            return _figure_repr_e2b_data_(obj)
        return super().__call__(obj)


ip = IPython.get_ipython()
ip.display_formatter.formatters["e2b/data"] = E2BFormatter(parent=ip.display_formatter)
