import pandas as pd


def _repr_mimebundle_(self, include=None, exclude=None):
    data = {
        'text/html': self.to_html(),
        'text/plain': self.to_string(),
        'e2b/df': self.to_dict(orient='list'),
    }

    if include:
        data = {k: v for (k, v) in data.items() if k in include}
    if exclude:
        data = {k: v for (k, v) in data.items() if k not in exclude}
    return data


setattr(pd.DataFrame, '_repr_mimebundle_', _repr_mimebundle_)
