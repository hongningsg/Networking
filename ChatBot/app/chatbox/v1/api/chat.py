# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

from flask import request, g, Response
from rivescript import RiveScript
import json

from . import Resource
from .. import schemas


class Chat(Resource):
    def startBot(self, url):
        bot = RiveScript()
        bot.load_directory(url)
        bot.sort_replies()
        return bot

    def post(self):
        bot = self.startBot("v1/api/brain")
        msg = g.json["message"]
        msg = msg.lower()
        msg = msg.replace("'", " a")
        print(msg)
        reply = bot.reply("localuser", msg)
        response = Response(status = 200, response = json.dumps(reply))
        response.headers['Content-Type'] = 'application/json'
        return response
