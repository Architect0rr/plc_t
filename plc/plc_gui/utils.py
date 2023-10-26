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

from abc import abstractmethod
from typing import List, Protocol, Any


class SU(Protocol):  # type: ignore
    pass


class SU(Protocol):
    update_list: List[SU]

    @abstractmethod
    def upd(self) -> None:
        ...

    @abstractmethod
    def add4update(self, el: SU) -> None:
        ...


class supports_update(SU):  # type: ignore
    pass


class supports_update(SU):
    def __init__(self) -> None:
        self.update_list: List[supports_update] = []

    def upd(self) -> None:
        for el in self.update_list:
            el.upd()

    def add4update(self, el: supports_update) -> None:
        self.update_list.append(el)


class SE(Protocol):  # type: ignore
    pass


class SE(Protocol):
    exit_list: List[SE]

    @abstractmethod
    def exit(self) -> None:
        ...

    @abstractmethod
    def add4exit(self, el: SE) -> None:
        ...


class supports_exit(SE):  # type: ignore
    pass


class supports_exit(SE):
    def __init__(self) -> None:
        self.exit_list: List[supports_exit] = []

    def exit(self) -> None:
        for el in self.exit_list:
            el.exit()

    def add4exit(self, el: supports_exit) -> None:
        self.exit_list.append(el)


class SUE(SU, SE):  # type: ignore
    ...


class have_root(Protocol):
    root: Any


if __name__ == "__main__":
    pass
