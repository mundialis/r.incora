#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.incora.change
# AUTHOR(S):    Guido Riembauer
# PURPOSE:      Runs r.change.stats and does post processing for incora
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
# % description: Runs r.change.stats and does post processing for incora.
# % keyword: raster
# % keyword: classification
# % keyword: change detection
# %end

# %option G_OPT_R_INPUT
# % key: input
# % label: Two input raster maps to calculate the change detection on
# % description: It is assumed that the second raster is the later one
# %end

# %option G_OPT_R_OUTPUT
# % key: output_cd
# % required: no
# % multiple: no
# % label: Name of total output change detection map
# %end

# %option G_OPT_R_OUTPUT
# % key: output_water
# % required: no
# % multiple: no
# % label: Name of output change detection map of water areas
# %end

# %option G_OPT_R_OUTPUT
# % key: output_bu
# % required: no
# % multiple: no
# % label: Name of output change detection map of built-up areas
# %end

# %option G_OPT_R_OUTPUT
# % key: output_forest
# % required: no
# % multiple: no
# % label: Name of output change detection map of forest areas
# %end

# %option G_OPT_R_OUTPUT
# % key: output_lowveg
# % required: no
# % multiple: no
# % label: Name of output change detection map of low vegetation areas
# %end

# %option G_OPT_R_OUTPUT
# % key: output_bare
# % required: no
# % multiple: no
# % label: Name of output change detection map of bare soil areas
# %end

# %option G_OPT_R_OUTPUT
# % key: output_agr
# % required: no
# % multiple: no
# % label: Name of output change detection map of agriculture areas
# %end

# %option
# % key: minsize
# % type: string
# % required: no
# % multiple: no
# % answer: 1.0
# % label: Minimum size of changed areas (in ha)
# % description: Smaller areas will be deleted from the output raster(s)
# %end

# %option
# % key: mode_winsize
# % type: integer
# % required: no
# % multiple: no
# % answer: 3
# % label: Size of mode filter if -f flag is set
# % description: -f flag must be set
# %end

# %option
# % key: gain_winsize
# % type: integer
# % required: no
# % multiple: no
# % answer: 4
# % label: Window size of information gain filter in r.change.info
# %end

# %option
# % key: gain_thresh
# % type: string
# % required: no
# % multiple: no
# % answer: 0.5
# % label: Threshold for the information gain map
# % description: All areas < gain_thresh are omitted from the output maps
# %end

# %flag
# % key: f
# % description: Filter change detection product using a mode filter of size window_size
# %end

import atexit
import os
import grass.script as grass

# initialize global vars
rm_rasters = []


def cleanup():
    nuldev = open(os.devnull, "w")
    kwargs = {
        "flags": "f",
        "quiet": True,
        "stderr": nuldev
    }
    for rmrast in rm_rasters:
        if grass.find_file(name=rmrast, element="raster")["file"]:
            grass.run_command("g.remove", type="raster", name=rmrast, **kwargs)


def main():

    global rm_rasters
    # parameters
    input = options["input"].split(",")
    if len(input) != 2:
        grass.fatal(_("Input must consist of two raster maps"))
    if options["output_cd"]:
        outrast_cd = options["output_cd"]
    else:
        outrast_cd = "cd_rast_%s" % os.getpid()
        rm_rasters.append(outrast_cd)

    output_agr = options["output_agr"]
    output_forest = options["output_forest"]
    output_lowveg = options["output_lowveg"]
    output_water = options["output_water"]
    output_bu = options["output_bu"]
    output_bare = options["output_bare"]

    if not grass.find_program("r.change.stats", "--help"):
        grass.fatal(_("The 'r.change.stats' module was not found, install it first:") +
                    "\n" +
                    "g.extension r.change.stats url=path/to/module")
    if not grass.find_program("r.change.info", "--help"):
        grass.fatal(
            _("The 'r.change.info' module was not found, install it first:")
            + "\n g.extension r.change.info")
    cd_temprast = "cd_tempraster_%s" % os.getpid()
    rm_rasters.append(cd_temprast)
    cd_params = {
        "input": input,
        "output": cd_temprast,
        "flags": "cl"
    }
    if flags["f"]:
        cd_params["window_size"] = options["mode_winsize"]
        cd_params["flags"] += "f"
    grass.message(_("Calculating change detection..."))
    grass.run_command("r.change.stats", **cd_params)
    output_list = [output_forest, output_lowveg, output_water, output_bu,
                   output_bare, output_agr]
    values_list = ["10", "20", "30", "40", "50", "60"]
    output_used = []
    values_used = []
    for idx, item in enumerate(output_list):
        if len(item) > 0:
            output_used.append(item)
            values_used.append(values_list[idx])

    grass.message(_("Calculating Information Gain..."))
    gainmap = "gainmap_%s" % os.getpid()
    rm_rasters.append(gainmap)
    steps = int(options["gain_winsize"])/2
    grass.run_command("r.change.info", input=input, method="gain1",
                      size=options["gain_winsize"], step=steps,
                      output=gainmap, quiet=True)
    if len(output_used) > 0:
        tempraster_1 = "%s_tmp1_%s" % (item, os.getpid())
        rm_rasters.append(tempraster_1)
        # correct the outrast_cd raster with the information gain
        eq = f"{outrast_cd} = if({gainmap}>{options['gain_thresh']},{cd_temprast},0)"
        grass.run_command("r.mapcalc", expression=eq, quiet=True)
        # this binary raster contains where changes occured
        expression_1 = "%s = if(%s > %s && %s != 0, 1, null())" % (
                       tempraster_1, gainmap, options["gain_thresh"],
                       outrast_cd)
        grass.run_command("r.mapcalc", expression=expression_1, quiet=True)
    for idx, item in enumerate(output_used):
        grass.message(_("Calculating change raster %s..." % item))
        tempraster_2 = "%s_tmp2_%s" % (item, os.getpid())
        rm_rasters.append(tempraster_2)
        # this raster contains where changes occured and one of the input
        # rasters contains the respective class (1 = map1, 2 = map2)
        expression_2 = f"{tempraster_2} = if({tempraster_1} == 1 && " \
            f"{input[0]} == {values_used[idx]},1, " \
            f"if({tempraster_1} == 1 && {input[1]} == {values_used[idx]}," \
            f"2,null()))"
        grass.run_command("r.mapcalc", expression=expression_2, quiet=True)
        # omit areas smaller < threshold
        grass.run_command(
            "r.reclass.area",
            input=tempraster_2,
            output=item,
            value=options["minsize"],
            mode="greater",
            method="reclass",
            quiet=True,
        )
    grass.message(_("Generated output maps:"))
    if options["output_cd"]:
        grass.message(_(f"<{outrast_cd}>"))
    for item in output_used:
        grass.message(_(f"<{item}>"))


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
