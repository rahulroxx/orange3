import numpy
from PyQt4.QtCore import Qt

import Orange.data
import Orange.misc
from Orange import distance
from Orange.widgets import widget, gui, settings
from Orange.widgets.utils.sql import check_sql_input


_METRICS = [
    ("Euclidean", distance.Euclidean),
    ("Manhattan", distance.Manhattan),
    ("Cosine", distance.Cosine),
    ("Jaccard", distance.Jaccard),
    ("Spearman", distance.SpearmanR),
    ("Spearman absolute", distance.SpearmanRAbsolute),
    ("Pearson", distance.PearsonR),
    ("Pearson absolute", distance.PearsonRAbsolute),
]


class OWDistances(widget.OWWidget):
    name = "Distances"
    description = "Compute a matrix of pairwise distances."
    icon = "icons/Distance.svg"

    inputs = [("Data", Orange.data.Table, "set_data")]
    outputs = [("Distances", Orange.misc.DistMatrix)]

    axis = settings.Setting(0)
    metric_idx = settings.Setting(0)
    autocommit = settings.Setting(False)

    want_main_area = False
    buttons_area_orientation = Qt.Vertical

    def __init__(self):
        super().__init__()

        self.data = None

        gui.radioButtons(self.controlArea, self, "axis", ["rows", "columns"],
                         box="Distances between", callback=self._invalidate
        )
        gui.comboBox(self.controlArea, self, "metric_idx",
                     box="Distance Metric", items=list(zip(*_METRICS))[0],
                     callback=self._invalidate
        )
        box = gui.auto_commit(self.buttonsArea, self, "autocommit", "Apply",
                              box=False, checkbox_label="Apply on any change")
        box.layout().insertWidget(0, self.report_button)
        box.layout().insertSpacing(1, 8)

        self.layout().setSizeConstraint(self.layout().SetFixedSize)

    @check_sql_input
    def set_data(self, data):
        self.data = data
        self.unconditional_commit()

    def commit(self):
        self.warning(1)
        self.error(1)

        data = distances = None
        if self.data is not None:
            metric = _METRICS[self.metric_idx][1]
            if not any(a.is_continuous for a in self.data.domain.attributes):
                self.error(1, "No continuous features")
                data = None
            elif (any(a.is_discrete for a in self.data.domain.attributes) or
                  numpy.any(numpy.isnan(self.data.X))):
                data = distance._preprocess(self.data)
                if len(self.data.domain.attributes) - len(data.domain.attributes) > 0:
                    self.warning(1, "Ignoring discrete features")
            else:
                data = self.data

        if data is not None:
            shape = (len(data), len(data.domain.attributes))
            if numpy.product(shape) == 0:
                self.error(1, "Empty data (shape == {})".format(shape))
            else:
                distances = metric(data, data, 1 - self.axis, impute=True)

        self.send("Distances", distances)

    def _invalidate(self):
        self.commit()

    def send_report(self):
        self.report_items((
            ("Distances between", ["rows", "columns"][self.axis]),
            ("Metric", _METRICS[self.metric_idx][0])
        ))
