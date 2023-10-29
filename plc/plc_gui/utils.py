#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Perevoshchikov Egor
#
# This file is part of PlasmaLabControl.
#
# PlasmaLabControl is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PlasmaLabControl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PlasmaLabControl.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations
import logging
from abc import abstractmethod
from typing import List, Protocol

import tkinter as tk

from .misc.splash import Splasher

from .read_config_file import read_config_file


class SU(Protocol):
    update_list: List[SU]

    @abstractmethod
    def upd(self) -> None:
        ...

    @abstractmethod
    def add4update(self, el: SU) -> None:
        ...


class supports_update(SU):
    def __init__(self) -> None:
        self.update_list = []
        # self.update_list: List[supports_update] = []

    def upd(self) -> None:
        for el in self.update_list:
            el.upd()

    # def add4update(self, el: supports_update) -> None:
    def add4update(self, el: SU) -> None:
        self.update_list.append(el)


class SE(Protocol):
    exit_list: List[SE]

    @abstractmethod
    def exit(self) -> None:
        ...

    @abstractmethod
    def add4exit(self, el: SE) -> None:
        ...


class supports_exit(SE):
    def __init__(self) -> None:
        self.exit_list = []
        # self.exit_list: List[supports_exit] = []

    def exit(self) -> None:
        for el in self.exit_list:
            el.exit()

    # def add4exit(self, el: supports_exit) -> None:
    def add4exit(self, el: SE) -> None:
        self.exit_list.append(el)


class SUE(SU, SE, Protocol):
    ...


class HR(Protocol):
    root: HR


class HR_impl(HR):
    def __init__(self, _root: HR) -> None:
        self.root = _root


class LC(Protocol):
    log: logging.Logger
    configs: read_config_file


class LC_impl(LC):
    def __init__(self, _log: logging.Logger, _configs: read_config_file) -> None:
        self.log = _log
        self.configs = _configs


class HRLC(HR, LC, Protocol):
    ...
    # root: Self
    # log: logging.Logger
    # configs: read_config_file


# class HRLC_impl(HR_impl, LC_impl):
#     def __init__(self, _root: HRLC) -> None:
#         HR_impl.__init__(self, _root)
#         LC_impl.__init__(self, _root.log, _root.configs)


class SEHRLC(SE, HR, LC, Protocol):
    ...


class SUHRLC(SU, HR, LC, Protocol):
    ...


class SUEHRLC(SU, SE, HR, LC, Protocol):
    ...


class hrlc(HR_impl, LC_impl):
    def __init__(self, _root: HRLC) -> None:
        HR_impl.__init__(self, _root=_root)
        LC_impl.__init__(self, _root.log, _root.configs)


class tkSEHRLC(tk.Misc, hrlc, supports_exit):
    pass


class tkSUEHRLC(tk.Misc, hrlc, supports_exit, supports_update):
    pass


class tkSUHRLC(tk.Misc, hrlc, supports_update):
    pass


class SUEHRLCS(Protocol):
    # _froot: SUEHRLCS
    log: logging.Logger
    configs: read_config_file
    splasher: Splasher
    update_list: List[SUEHRLCS]
    exit_list: List[SUEHRLCS]

    # def add4update(self, child: SUEHRLCS) -> None:
    #     self.update_list.append(child)

    # def add4exit(self, child: SUEHRLCS) -> None:
    #     self.exit_list.append(child)

    def upd(self) -> None:
        for child in self.update_list:
            child.upd()

    def exit(self) -> None:
        for child in self.exit_list:
            child.exit()


class SUEHRLCS_impl(SUEHRLCS):
    def __init__(self, _root: SUEHRLCS) -> None:
        self._froot = _root
        self.log = _root.log
        self.configs = _root.configs
        self.splasher = _root.splasher
        self.update_list = []
        self.exit_list = []
        self._froot.update_list.append(self)
        self._froot.exit_list.append(self)


class Master:
    def __init__(
        self,
        master: Master | None = None,
        log: logging.Logger | None = None,
        configs: read_config_file | None = None,
        splasher: Splasher | None = None,
        custom_name: str | None = None,
    ) -> None:
        self.log: logging.Logger
        self.configs: read_config_file
        self.splasher: Splasher
        if master is None:
            if log is not None and configs is not None and splasher is not None:
                self.log = log
                self.configs = configs
                self.splasher = splasher
            else:
                raise RuntimeError
        else:
            self.log = master.log
            self.configs = master.configs
            self.splasher = master.splasher
            master.update_list.append(self)
            master.exit_list.append(self)
        if custom_name is not None:
            self.log = self.log.getChild(custom_name)
        self.update_list: List[Master] = []
        self.exit_list: List[Master] = []

    def upd(self) -> None:
        for el in self.update_list:
            el.upd()

    def exit(self) -> None:
        for el in self.exit_list:
            el.exit()


# class Notebook(tk.Frame, hrlc, supports_exit):
#     def __init__(self, _root: tkSUEHRLC) -> None:
#         tk.Frame.__init__(self, _root)
#         supports_exit.__init__(self)
#         # supports_update.__init__(self)
#         hrlc.__init__(self, _root)


# def sf(obj: tkSEHRLC) -> None:
#     pass


# class Proto(Protocol):
#     root: Self
#     childs: List[Self]

#     @abstractmethod
#     def addChild(self, child: Self):
#         ...


# class Proto_impl(Proto):
#     def __init__(self, _root: Proto) -> None:
#         self.root = _root
#         self.childs: List[Proto_impl] = []

#     def addChild(self, child: Proto_impl) -> None:
#         self.childs.append(child)


# class First(Proto_impl):
#     def __init__(self) -> None:
#         Proto_impl.__init__(self, self)


# class Second(Proto_impl):
#     def __init__(self, _root: Proto) -> None:
#         Proto_impl.__init__(self, _root)


# d1 = First()
# d2 = Second(d1)

# d1.addChild(d2)


if __name__ == "__main__":
    pass
    # tr = tk.Tk()
    # obj = Notebook(tr)
    # sf(obj)
