# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

from flask import request, g, Response

from . import Resource
from .. import schemas

import sqlite3
import json

class TimeslotsIdReserve(Resource):
    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def get(self, id):
        conn = sqlite3.connect('dentist.db')
        conn.row_factory = self.dict_factory
        c = conn.cursor()
        c.execute("Delete from TimeSlots where section='%s' " %str(id))
        conn.commit()
        conn.close()
        return Response(status = 200, response = str(id)+' is reserved')
