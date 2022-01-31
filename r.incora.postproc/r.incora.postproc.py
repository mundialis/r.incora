#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.incora.postproc
# AUTHOR(S):    Guido Riembauer
# PURPOSE:      Postprocesses classification maps containing a mixed pixels
#               class
# COPYRIGHT:	(C) 2020-2022 by mundialis GmbH & Co. KG and the GRASS
#               Development Team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#############################################################################

# %Module
# % description: Postprocesses classification maps containing a mixed pixels class.
# % keyword: raster
# % keyword: classification
# % keyword: postprocessing
# %end

# %option G_OPT_R_INPUT
# % key: classification
# % label: Name of classification map with 7 classes
# %end

# %option G_OPT_R_INPUT
# % key: elevation
# % label: Name of digital elevation model
# %end

# %option G_OPT_R_INPUT
# % key: coastline
# % label: Name of binary land/sea raster
# %end

# %option G_OPT_R_INPUT
# % key: water
# % label: Name of water/non-water raster
# %end

# %option G_OPT_R_INPUT
# % key: roads
# % label: Name of roads raster
# %end

# %option G_OPT_R_OUTPUT
# % key: output
# % label: Name of output classification map with 6 classes
# %end

import atexit
import os
import grass.script as grass

# initialize global vars
rm_rasters = []


def cleanup():
    nuldev = open(os.devnull, "w")
    kwargs = {"flags": "f", "quiet": True, "stderr": nuldev}
    for rmrast in rm_rasters:
        if grass.find_file(name=rmrast, element="raster")["file"]:
            grass.run_command("g.remove", type="raster", name=rmrast, **kwargs)


def main():

    global rm_rasters

    raster_7classes = options["classification"]
    coastline = options["coastline"]
    dem = options["elevation"]
    water = options["water"]
    roads = options["roads"]
    output = options["output"]

    # rebrand high altitude water pixels to mixed class to remove them
    # (mountain shadow)
    water_elevation = "water_elevation_%s" % os.getpid()
    rm_rasters.append(water_elevation)
    grass.run_command(
        "r.mapcalc",
        expression="%s = if(%s>1000 && %s==30,70,%s)"
        % (water_elevation, dem, raster_7classes, raster_7classes),
        quiet=True,
    )

    postproc_raster2 = "postproc_raster2_%s" % os.getpid()
    rm_rasters.append(postproc_raster2)
    # grass.run_command('r.mapcalc', expression="%s = if(%s==70,null(),%s)" % (
    #                   postproc_raster2, postproc_raster1, postproc_raster1),
    #                   quiet=True)
    grass.run_command(
        "r.mapcalc",
        expression="%s = if(%s==70,null(),%s)"
        % (postproc_raster2, water_elevation, water_elevation),
        quiet=True,
    )
    grow_raster = "grow_distance_raster_%s" % os.getpid()
    rm_rasters.append(grow_raster)

    grass.run_command(
        "r.grow.distance", input=postproc_raster2, value=grow_raster, quiet=True
    )

    rounded = "rounded_grow_distance_raster_%s" % os.getpid()
    rm_rasters.append(rounded)

    grass.run_command(
        "r.mapcalc", expression="%s = round(%s)" % (rounded, grow_raster), quiet=True
    )

    # reclassify urban areas outside coastline to bare soil
    coast_corrected = "coast_corrected_%s" % os.getpid()
    rm_rasters.append(coast_corrected)

    grass.run_command(
        "r.mapcalc",
        expression="%s = if(isnull(%s) &&& %s==40,50,%s)"
        % (coast_corrected, coastline, rounded, rounded),
        quiet=True,
    )

    # reclassify urban areas > 1500m to bare soil and agriculture > 900 m to
    # low vegetation
    elevation_corrected = "elevation_corrected_%s" % os.getpid()
    rm_rasters.append(elevation_corrected)
    el_expression = "%s = if(%s>1500 && %s==40,50,if(%s>800 && %s==60,20,%s))" % (
        elevation_corrected,
        dem,
        coast_corrected,
        dem,
        coast_corrected,
        coast_corrected,
    )
    grass.run_command("r.mapcalc", expression=el_expression, quiet=True)

    # reclassifiy agriculture < 1.5 ha to low vegetation
    # get agriculture areas only
    agr_only = "agr_only_%s" % os.getpid()
    rm_rasters.append(agr_only)
    grass.run_command(
        "r.mapcalc",
        expression="%s = if(%s==60,60,null())" % (agr_only, elevation_corrected),
    )

    # get all areas smaller 1.5 ha
    small_areas = "areas_smaller_1_5_ha_%s" % os.getpid()
    rm_rasters.append(small_areas)
    grass.run_command(
        "r.reclass.area",
        input=agr_only,
        output=small_areas,
        value=1.5,
        mode="lesser",
        quiet=True,
    )

    # get corrected agriculture
    agr_corrected = "agr_corrected_%s" % os.getpid()
    rm_rasters.append(agr_corrected)
    grass.run_command(
        "r.mapcalc",
        expression="%s = if(isnull(%s),%s,20)"
        % (agr_corrected, small_areas, elevation_corrected),
        quiet=True,
    )

    # remove builtup areas on water
    grass.run_command(
        "r.mapcalc",
        expression="%s = if(not(isnull(%s)) && isnull(%s) && %s==40,30,%s)"
        % (output, water, roads, agr_corrected, agr_corrected),
    )

    grass.message(_("Generated output map <%s>" % output))


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
