import pandas
from matplotlib.pyplot import Figure
import IPython
from IPython.core.formatters import BaseFormatter
from traitlets.traitlets import Unicode, ObjectName

from e2b_charts import chart_figure_to_dict


def _figure_repr_e2b_chart_(self: Figure):
    """
    This method is used to extract data from the figure object to a dictionary
    """
    # Get all Axes objects from the Figure
    try:
        return chart_figure_to_dict(self)
    except:
        return {}


def _dataframe_repr_e2b_data_(self: pandas.DataFrame):
    return self.to_dict(orient="list")


class E2BDataFormatter(BaseFormatter):
    format_type = Unicode("e2b/data")

    print_method = ObjectName("_repr_e2b_data_")
    _return_type = (dict, str)

    type_printers = {pandas.DataFrame: _dataframe_repr_e2b_data_}


class E2BChartFormatter(BaseFormatter):
    format_type = Unicode("e2b/chart")

    print_method = ObjectName("_repr_e2b_chart_")
    _return_type = (dict, str)

    def __call__(self, obj):
        # Figure object is for some reason removed on execution of the cell,
        # so it can't be used in type_printers or with top-level import
        from matplotlib.pyplot import Figure

        if isinstance(obj, Figure):
            return _figure_repr_e2b_chart_(obj)
        return super().__call__(obj)


ip = IPython.get_ipython()
ip.display_formatter.formatters["e2b/data"] = E2BDataFormatter(
    parent=ip.display_formatter
)
ip.display_formatter.formatters["e2b/chart"] = E2BChartFormatter(
    parent=ip.display_formatter
)
