from typing import Literal, List

from matplotlib.axes import Axes
from pydantic import BaseModel, Field

from .base import Graph, GraphType


class PieData(BaseModel):
    label: str
    angle: float
    radius: float


class PieGraph(Graph):
    type: Literal[GraphType.PIE] = GraphType.PIE

    elements: List[PieData] = Field(default_factory=list)

    def _extract_info(self, ax: Axes) -> None:
        super()._extract_info(ax)

        for wedge in ax.patches:
            pie_data = PieData(
                label=wedge.get_label(),
                angle=abs(round(wedge.theta2 - wedge.theta1, 4)),
                radius=wedge.r,
            )

            self.elements.append(pie_data)
