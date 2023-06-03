#
# Copyright (C) 2007 - Mark Dillavou
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

class Singleton(object):
    '''A class in which all instances are the same instance.

    Any subclass of Singleton that does not override __new__ has exactly
    one instance.  If the subclass defines an __init__ method, the
    subclass should wrap code that should only be executed once in an
    \'if self._isFirstInit():\' block.
    
    (Adapted from _Python in a Nutshell_ by Alex Martelli.)'''

    __singletons= {}
    __numberOfInits= 0

    def __new__(cls, *args, **kwds):
        if not cls in cls.__singletons.keys():
            cls.__singletons[cls]= object.__new__(cls)
        return cls.__singletons[cls]
    
    @classmethod
    def _isFirstInit(cls):
        cls.__numberOfInits += 1
        return (cls.__numberOfInits == 1)

