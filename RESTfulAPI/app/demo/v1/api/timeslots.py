# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

from flask import request, g, Response

from . import Resource
from .. import schemas

import sqlite3
import json

class Timeslots(Resource):
    def dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
    
    def get(self):
        conn = sqlite3.connect('dentist.db')
        conn.row_factory = self.dict_factory
        c = conn.cursor()
        c.execute('Select * from TimeSlots')
        temp=c.fetchall() 
        c.close()
        res = Response(status = 200, response = json.dumps(temp))
        res.headers["Content-type"] = "application/json"
        return res

    def post(self):
        body = request.args.get('body')
        print(body)
        conn = sqlite3.connect('dentist.db')
        c = conn.cursor()
        c.execute("Insert into TimeSlots values ('%s')"%str(body))
        conn.commit()
        conn.close()
        return Response(status = 200, response = "Insert OK")
