# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GPSbinding
                                 A QGIS plugin
 Description
                             -------------------
        copyright            : (C) 2022 by Ronya14
        email                : ronya14@mail.ru
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load GPSbinding class from file GPSbinding.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .gps_binding_plugin import GPSbinding
    return GPSbinding(iface)
