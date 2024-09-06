import enum

import pandas
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.pyplot import Figure
import IPython

from IPython.core.formatters import BaseFormatter
from traitlets.traitlets import Unicode, ObjectName


class PlotType(enum.Enum):
    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"
    UNKNOWN = "unknown"


def get_type_of_plot(ax: Axes) -> PlotType:
    # Check for Line plots
    if any(isinstance(line, Line2D) for line in ax.get_lines()):
        return PlotType.LINE

    # Check for Scatter plots
    if any(isinstance(collection, PathCollection) for collection in ax.collections):
        return PlotType.SCATTER

    # Check for Bar plots (Rectangle objects with height > 0)
    if any(isinstance(rect, Rectangle) for rect in ax.get_children()):
        return PlotType.BAR

    return PlotType.UNKNOWN


def _figure_repr_e2b_data_(self: Figure):
    """
    This method is used to extract data from the figure object to a dictionary
    """
    # Get all Axes objects from the Figure
    axes = self.get_axes()

    data = []
    # Iterate through all Axes to extract data
    for ax in axes:
        ax_data = {
            "title": ax.get_title(),
            "x_label": ax.get_xlabel(),
            "x_ticks": ax.get_xticks(),
            "x_tick_labels": [label.get_text() for label in ax.get_xticklabels()],
            "x_scale": ax.get_xscale(),
            "y_label": ax.get_ylabel(),
            "y_ticks": ax.get_yticks(),
            "y_tick_labels": [label.get_text() for label in ax.get_yticklabels()],
            "y_scale": ax.get_yscale(),
            "data": [],
        }

        plot_type = get_type_of_plot(ax)
        ax_data["type"] = plot_type.value

        if plot_type == PlotType.LINE:
            for line in ax.get_lines():
                line_data = {
                    "x": line.get_xdata().tolist(),
                    "y": line.get_ydata().tolist(),
                    "label": line.get_label(),
                }
                ax_data["data"].append(line_data)

        if plot_type == PlotType.SCATTER:
            for collection in ax.collections:
                offsets = collection.get_offsets()
                scatter_data = {
                    "label": collection.get_label(),
                    "x": offsets[:, 0].tolist(),
                    "y": offsets[:, 1].tolist(),
                }

                ax_data["data"].append(scatter_data)

        if plot_type == PlotType.BAR:
            for container in ax.containers:
                orientation = "unknown"

                widths = [rect.get_width() for rect in container]
                heights = [rect.get_height() for rect in container]
                if all(height == heights[0] for height in heights):
                    orientation = "vertical"

                if all(width == widths[0] for width in widths):
                    orientation = "horizontal"

                container_data = {
                    "label": container.get_label(),
                    "x": [rect.get_x() for rect in container],
                    "y": [rect.get_y() for rect in container],
                    "widths": widths,
                    "heights": heights,
                    "orientation": orientation,
                }

                ax_data["data"].append(container_data)

        # If there are other types of plots (like bar plots), you can access them similarly
        data.append(ax_data)

    return {"graphs": data}


def _data_frame_repr_e2b_data_(self: pandas.DataFrame):
    return self.to_dict(orient="list")


class E2BFormatter(BaseFormatter):
    format_type = Unicode("e2b/data")

    print_method = ObjectName("_repr_e2b_data_")
    _return_type = (dict, str)

    type_printers = {pandas.DataFrame: _data_frame_repr_e2b_data_}

    def __call__(self, obj):
        # Figure object is for some reason removed on execution of the cell,
        # so it can't be used in type_printers or with top-level import
        from matplotlib.pyplot import Figure

        if isinstance(obj, Figure):
            return _figure_repr_e2b_data_(obj)
        return super().__call__(obj)


ip = IPython.get_ipython()
ip.display_formatter.formatters["e2b/data"] = E2BFormatter(parent=ip.display_formatter)
