#!/usr/bin/env python
# coding: utf-8

# Author : Rahul Bhadani
# Initial Date: Apr 19, 2020
# About: strymUI is used to facilitate front end UI for taking advantage of strym package
# Read associated README for full description
# License: MIT License

#   Permission is hereby granted, free of charge, to any person obtaining
#   a copy of this software and associated documentation files
#   (the "Software"), to deal in the Software without restriction, including
#   without limitation the rights to use, copy, modify, merge, publish,
#   distribute, sublicense, and/or sell copies of the Software, and to
#   permit persons to whom the Software is furnished to do so, subject
#   to the following conditions:

#   The above copyright notice and this permission notice shall be
#   included in all copies or substantial portions of the Software.

#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF
#   ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
#   TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
#   PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
#   SHALL THE AUTHORS, COPYRIGHT HOLDERS OR ARIZONA BOARD OF REGENTS
#   BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN
#   AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#   OR OTHER DEALINGS IN THE SOFTWARE.

__maintainer__ = 'Rahul Bhadani'
__email__  = 'rahulbhadani@email.arizona.edu'

# base Class of the App inherits from the App class.
# app: always refers to the instance of the application.
from kivy.app import App

from kivy.modules import inspector

from kivy.core.window import Window

from kivy.uix.button import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget

from kivy.uix.floatlayout import FloatLayout

class strymwidget(Widget):
    pass

class strymLayout(FloatLayout):
    pass

class strymapp(App):
    def __init__(self, **kwargs):
        self.title = "Strym"
        self.icon = "../../docs/source/favicon.ico"
        super().__init__(**kwargs)

    def build(self):
        inspector.create_inspector(Window, self)
        return  strymLayout()


if __name__ == "__main__":
    strymapp().run()