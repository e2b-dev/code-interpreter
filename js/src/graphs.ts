export enum GraphType {
  LINE = 'line',
  SCATTER = 'scatter',
  BAR = 'bar',
  PIE = 'pie',
  BOX_AND_WHISKER = 'box_and_whisker',
  SUPERGRAPH = 'supergraph',
  UNKNOWN = 'unknown',
}

export type Graph = {
  type: GraphType
  title: string
  elements: any[]
}

type Graph2D = Graph & {
  x_label?: string
  y_label?: string
  x_unit?: string
  y_unit?: string
}

export type PointData = {
  label: string
  points: [number, number][]
}

type PointGraph = Graph2D & {
  x_ticks: number[]
  x_tick_labels: string[]
  y_ticks: number[]
  y_tick_labels: string[]
  elements: PointData[]
}

export type LineGraph = PointGraph & {
  type: GraphType.LINE
}

export type ScatterGraph = PointGraph & {
  type: GraphType.SCATTER
}

export type BarData = {
  label: string
  value: string
}

export type BarGraph = Graph2D & {
  type: GraphType.BAR
  elements: BarData[]
}

export type PieData = {
  label: string
  angle: number
  radius: number
}

export type PieGraph = Graph & {
  type: GraphType.PIE
  elements: PieData[]
}

export type BoxAndWhiskerData = {
  label: string
  min: number
  first_quartile: number
  median: number
  third_quartile: number
  max: number
}

export type BoxAndWhiskerGraph = Graph2D & {
  type: GraphType.BOX_AND_WHISKER
  elements: BoxAndWhiskerData[]
}

export type SuperGraph = Graph & {
  type: GraphType.SUPERGRAPH
  elements: Graph[]
}

export type GraphTypes =
  | LineGraph
  | ScatterGraph
  | BarGraph
  | PieGraph
  | BoxAndWhiskerGraph
  | SuperGraph
export function deserializeGraph(data: any): Graph {
  switch (data.type) {
    case GraphType.LINE:
      return { ...data } as LineGraph
    case GraphType.SCATTER:
      return { ...data } as ScatterGraph
    case GraphType.BAR:
      return { ...data } as BarGraph
    case GraphType.PIE:
      return { ...data } as PieGraph
    case GraphType.BOX_AND_WHISKER:
      return { ...data } as BoxAndWhiskerGraph
    case GraphType.SUPERGRAPH:
      const graphs = data.data.map((g: any) => deserializeGraph(g))
      delete data.data
      return {
        ...data,
        data: graphs,
      } as SuperGraph
    default:
      return { ...data, type: GraphType.UNKNOWN } as Graph
  }
}
