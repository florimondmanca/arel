from . import settings
from .content import load_pages
from .resources import hotreload

on_startup = [load_pages]
on_shutdown = []

if settings.DEBUG:
    on_startup += [hotreload.startup]
    on_shutdown += [hotreload.shutdown]
