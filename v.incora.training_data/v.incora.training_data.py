#!/usr/bin/env python3

############################################################################
#
# MODULE:       v.incora.training_data
# AUTHOR(S):    Anika Weinmann and Guido Riembauer
# PURPOSE:      Creates a vector map containing training points from a set of
#               rules
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
# % description: Creates a vector map containing training points from a set of rules.
# % keyword: vector
# % keyword: classification
# % keyword: training data
# %end

# %option G_OPT_R_INPUT
# % key: imperviousness
# % label: Input imperviousness raster map
# % description: From here: https://land.copernicus.eu/pan-european/high-resolution-layers/imperviousness/status-maps/2015
# %end

# %option G_OPT_R_INPUT
# % key: landcover
# % label: Input landcover raster map
# % description: From here: http://s2glc.cbk.waw.pl/extension
# %end

# %option G_OPT_R_INPUT
# % key: elevation
# % label: Input digital elevation model
# % description: Used to remove builtup training data in high altitudes
# %end

# %option G_OPT_R_INPUT
# % key: ndvi_max
# % label: Input NDVI_maximum raster map from NDVI timeseries
# %end

# %option G_OPT_R_INPUT
# % key: ndvi_min
# % label: Input NDVI_minimum raster map from NDVI timeseries
# %end

# %option G_OPT_R_INPUT
# % key: ndvi_range
# % label: Input NDVI_range raster map from NDVI timeseries
# %end

# %option G_OPT_R_INPUT
# % key: ndwi
# % label: Input NDWI raster map
# %end

# %option G_OPT_R_INPUT
# % key: coastline
# % label: Input coastline raster map
# %end

# %option G_OPT_R_INPUT
# % key: buildings
# % label: Input OSM buildings raster map
# % description: Downloaded from Geofabrik, reprojected using ogr2ogr, rasterized using gdal_rasterize
# %end

# %option G_OPT_R_INPUT
# % key: roads
# % label: Input OSM roads raster map
# % description: Downloaded from Geofabrik, reprojected using ogr2ogr, rasterized using gdal_rasterize
# %end

# %option G_OPT_R_INPUT
# % key: water
# % label: Input OSM water raster map
# % description: Downloaded from Geofabrik, reprojected using ogr2ogr, rasterized using gdal_rasterize
# %end

# %option G_OPT_R_INPUT
# % key: blue
# % label: Input blue band
# % description: Blue band of input satellite image
# %end

# %option G_OPT_R_INPUT
# % key: green
# % label: Input green band
# % description: Green band of input satellite image
# %end

# %option G_OPT_R_INPUT
# % key: red
# % label: Input red band
# % description: Red band of input satellite image
# %end

# %option
# % key: npoints
# % type: integer
# % required: yes
# % label: Number of sampling points per class in the output vector map
# %end

# %option G_OPT_V_OUTPUT
# % key: output
# % label: Name of output vector map containing training points
# %end

import atexit
import os
import grass.script as grass

# initialize global vars
rm_rasters = []
rm_vectors = []
rm_regions = []
oldregion = None
oldmask = None


def cleanup():
    nuldev = open(os.devnull, "w")
    kwargs = {"flags": "f", "quiet": True, "stderr": nuldev}
    if oldmask:
        grass.run_command("r.mask", raster=oldmask)
        rm_rasters.append(oldmask)
    if oldregion:
        grass.run_command("g.region", region=oldregion)
        rm_rasters.append(oldregion)
    for rmrast in rm_rasters:
        if grass.find_file(name=rmrast, element="raster")["file"]:
            grass.run_command("g.remove", type="raster", name=rmrast, **kwargs)
    for rmvect in rm_vectors:
        if grass.find_file(name=rmvect, element="vector")["file"]:
            grass.run_command("g.remove", type="vector", name=rmvect, **kwargs)
    for rmr in rm_regions:
        if rmr in [x for x in grass.parse_command("g.list", type="region")]:
            grass.run_command("g.remove", type="region", name=rmr, **kwargs)


def get_percentile(raster, percentile):
    return float(
        list(
            (
                grass.parse_command(
                    "r.quantile",
                    input=raster,
                    percentiles=percentile,
                )
            ).keys()
        )[0].split(":")[2]
    )


def main():

    global rm_rasters, rm_regions, rm_vectors, oldmask, oldregion

    id = str(os.getpid())
    # check if mask is activated and save the mask
    if grass.find_file(name="MASK", element="raster")["file"]:
        grass.warning(_("Found MASK will be ignored and restored after completion"))
        oldmask = "mask_%s" % (id)
        grass.run_command("g.rename", raster="MASK,%s" % (oldmask))
    # save actuall region
    oldregion = "region_tmp_%s" % id
    grass.run_command("g.region", save=oldregion)

    red = options["red"]
    green = options["green"]
    blue = options["blue"]
    imperviousness = options["imperviousness"]
    landcover = options["landcover"]
    elevation = options["elevation"]
    NDVI_max = options["ndvi_max"]
    NDVI_min = options["ndvi_min"]
    NDVI_range = options["ndvi_range"]
    NDWI = options["ndwi"]
    coastline = options["coastline"]
    buildings = options["buildings"]
    roads = options["roads"]
    map_water = options["water"]
    npoints = options["npoints"]
    output = options["output"]

    tr_maps = []

    # class numbers for training data
    forest_class = "10"
    forest_name = "forest"
    low_veg_class = "20"
    low_veg_name = "low vegetation"
    water_class = "30"
    water_name = "water"
    builtup_class = "40"
    builtup_name = "built-up"
    baresoil_class = "50"
    baresoil_name = "bare soil"
    agr_class = "60"
    agr_name = "agriculture"
    builtup2_class = "70"
    builtup2_name = "mixed built-up"

    # class numbers in landcover raster map
    lc_forest_class = "82 83"
    lc_low_veg_class = "102"
    # lc_water_class = "162"
    # lc_builtup_class = "62"
    lc_agr_class = "73 75"

    if not grass.find_program("r.sample.category", "--help"):
        grass.fatal(
            _("The 'r.sample.category' module was not found, install it first:")
            + "\n"
            + "g.extension r.sample.category"
        )

    grass.message(_("\nSelecting forest pixels..."))
    # (LC = 82 | LC = 83) & (NDVI max > q1) & (size > 2ha)
    grass.run_command(
        "r.mask",
        raster=landcover,
        maskcats=lc_forest_class,
        quiet=True,
    )
    forest_NDVImax_p5 = get_percentile(NDVI_max, 5)
    forest_tr_tmp = "forest_tr_tmp_%s" % id
    rm_rasters.append(forest_tr_tmp)
    eq = "%s = if(%s>%f,%s,null() )" % (
        forest_tr_tmp,
        NDVI_max,
        forest_NDVImax_p5,
        forest_class,
    )
    grass.run_command("r.mapcalc", expression=eq, quiet=True)
    forest_tr = "forest_tr_%s" % id
    rm_rasters.append(forest_tr)
    tr_maps.append(forest_tr)
    grass.run_command(
        "r.reclass.area",
        input=forest_tr_tmp,
        output=forest_tr,
        mode="greater",
        value=1,
        quiet=True,
    )
    grass.run_command("r.mask", flags="r")

    grass.message(_("\nSelecting low vegetation pixels..."))
    # (LC = 102) & (NDVI min > 25%quantil)  &(size > 1ha)
    grass.run_command(
        "r.mask",
        raster=landcover,
        maskcats=lc_low_veg_class,
        quiet=True,
    )
    low_veg_NDVImin_q1 = get_percentile(NDVI_min, 25)
    low_veg_tr_tmp = "low_veg_tr_tmp_%s" % id
    rm_rasters.append(low_veg_tr_tmp)
    eq = "%s = if(%s>=%f,%s,null() )" % (
        low_veg_tr_tmp,
        NDVI_min,
        low_veg_NDVImin_q1,
        low_veg_class,
    )
    grass.run_command("r.mapcalc", expression=eq, quiet=True)
    low_veg_tr = "low_veg_tr_%s" % id
    tr_maps.append(low_veg_tr)
    rm_rasters.append(low_veg_tr)
    grass.run_command(
        "r.reclass.area",
        input=low_veg_tr_tmp,
        output=low_veg_tr,
        mode="greater",
        value=1,
        quiet=True,
    )
    grass.run_command("r.mask", flags="r")

    grass.message(_("\nSelecting water pixels..."))
    # (NDWI > 1. quartil) & (ASM > median) & (LC =162) & (size > 1ha)
    # (besseres Ergebnis für NRW)

    roads_buf10 = "roads_buf10_tmp_%s" % id
    rm_rasters.append(roads_buf10)
    reflectance_thresh = 500
    grass.run_command(
        "r.buffer",
        input=roads,
        output=roads_buf10,
        distances=10,
        units="meters",
        quiet=True,
    )
    grass.run_command("r.mask", raster=map_water, quiet=True)
    # compute a "bright" raster
    bright_rast = "brightness_%s" % os.getpid()
    rm_rasters.append(bright_rast)
    bright_expression = "%(out)s = if(%(red)s>%(thresh)f && \
                        %(green)s>%(thresh)f && %(blue)s>%(thresh)f, \
                        1,null())" % {
        "out": bright_rast,
        "red": red,
        "green": green,
        "blue": blue,
        "thresh": reflectance_thresh,
    }
    grass.run_command("r.mapcalc", expression=bright_expression, quiet=True)
    # water_NDWI_median = get_percentile(NDWI, 50)
    water_tr = "water_tr_%s" % id

    eq = "%s = if(%s>%f && isnull(%s) && isnull(%s),%s,null() )" % (
        water_tr,
        NDWI,
        130,
        roads_buf10,
        bright_rast,
        water_class,
    )
    grass.run_command("r.mapcalc", expression=eq, quiet=True)
    tr_maps.append(water_tr)
    rm_rasters.append(water_tr)
    grass.run_command("r.mask", flags="r")

    grass.message(_("\nSelecting builtup pixels..."))
    buildings_buf100 = "buildings_buf100_tmp_%s" % id
    rm_rasters.append(buildings_buf100)
    grass.run_command(
        "r.buffer",
        input=buildings,
        output=buildings_buf100,
        distances=100,
        units="meters",
        quiet=True,
    )
    roads_buf100 = "roads_buf100_tmp_%s" % id
    rm_rasters.append(roads_buf100)
    grass.run_command(
        "r.buffer",
        input=roads,
        output=roads_buf100,
        distances=100,
        units="meters",
        quiet=True,
    )
    # (LC=62) & (Imperviousness > 50) & (NDBI > median)
    # grass.run_command("r.mask", raster=imperviousness, quiet=True)

    map_water_buff = "water_buf_tmp_%s" % id
    rm_rasters.append(map_water_buff)
    grass.run_command(
        "r.buffer",
        input=map_water,
        output=map_water_buff,
        distances=50,
        units="meters",
        quiet=True,
    )
    # imp_NDVI_q1 = get_percentile(NDVI_max, 25)
    builtup_tr = "builtup_tr_%s" % id
    tr_maps.append(builtup_tr)
    rm_rasters.append(builtup_tr)

    # eq = "%s = if(%s<=%f && isnull(%s) && %s!=%s && (%s>0 || %s>0),%s,null() )" % (
    #      builtup_tr, NDVI_max, 200, map_water_buff, landcover, lc_agr_class,
    #      buildings_buf100, roads_buf100, builtup_class)
    # grass.run_command("r.mapcalc", expression=eq, quiet=True)
    grass.run_command("r.mask", raster=coastline, quiet=True)

    eq = f"{builtup_tr} = if({NDVI_max}<={200} && isnull({map_water_buff}) " \
        f"&& {landcover}!={lc_agr_class.split(' ')[0]} && " \
        f"{landcover}!={lc_agr_class.split(' ')[1]} && " \
        f"({buildings_buf100}>0 ||| {roads_buf10}>0) &&& " \
        f"{elevation} < 1000,{builtup_class},null() )"
    grass.run_command("r.mapcalc", expression=eq, quiet=True)

    # classify mixed urban pixels
    builtup2_tr = "builtup2_tr_%s" % id
    tr_maps.append(builtup2_tr)
    eq2 = f"{builtup2_tr} = if(isnull({builtup_tr}) && " \
        f"{NDVI_max}<={220} && isnull({map_water_buff}) && " \
        f"{landcover}!={lc_agr_class.split(' ')[0]} && " \
        f"{landcover}!={lc_agr_class.split(' ')[1]} && " \
        f"({buildings_buf100}>0 ||| {roads_buf10}>0) &&& " \
        f"{elevation} < 1000,{builtup2_class},null() )"
    grass.run_command("r.mapcalc", expression=eq2, quiet=True)
    # grass.run_command("r.mask", flags="r")
    grass.run_command("r.mask", flags="r", quiet=True)

    grass.message(_("\nSelecting bare soil pixels..."))
    grass.run_command("r.mask", raster=coastline, quiet=True)
    buildings_buf50 = "buildings_buf50_tmp_%s" % id
    rm_rasters.append(buildings_buf50)
    grass.run_command(
        "r.buffer",
        input=buildings,
        output=buildings_buf50,
        distances=50,
        units="meters",
        quiet=True,
    )
    imp_buf = "imp_buf_tmp_%s" % id
    rm_rasters.append(imp_buf)
    grass.run_command("g.region", flags="ap", res=100)
    grass.run_command(
        "r.buffer",
        input=imperviousness,
        output=imp_buf,
        distances=100,
        units="meters",
        quiet=True,
    )
    grass.run_command("g.region", region=oldregion)
    baresoil_tr_tmp = "baresoil_tr_tmp_%s" % id
    rm_rasters.append(baresoil_tr_tmp)
    eq = f"{baresoil_tr_tmp}=if(isnull({buildings_buf50})&&" \
        f"isnull({roads_buf10})&&isnull({imp_buf})&&" \
        f"{NDVI_range}<=50&&{NDVI_max}<=200&&isnull({map_water})," \
        f"{baresoil_class},null())"
    grass.run_command("r.mapcalc", expression=eq, quiet=True)
    baresoil_tr = "baresoil_tr_%s" % id
    tr_maps.append(baresoil_tr)
    rm_rasters.append(baresoil_tr)
    grass.run_command(
        "r.reclass.area",
        input=baresoil_tr_tmp,
        output=baresoil_tr,
        mode="greater",
        value=0.5,
        quiet=True,
    )
    grass.run_command("r.mask", flags="r", quiet=True)

    grass.message(_("\nSelecting agriculture pixels..."))
    # (NDVI range > 1.quartil) & (LC = 73) & (size > 2ha)
    grass.run_command(
        "r.mask",
        raster=landcover,
        maskcats=lc_agr_class,
        quiet=True,
    )
    agr_NDVIrange_q1 = get_percentile(NDVI_range, 25)
    agr_tr_tmp = "agr_tr_tmp_%s" % id
    rm_rasters.append(agr_tr_tmp)
    eq = "%s = if(%s>=%f&&isnull(%s)&&isnull(%s),%s,null() )" % (
        agr_tr_tmp,
        NDVI_range,
        agr_NDVIrange_q1,
        buildings_buf50,
        roads_buf10,
        agr_class,
    )
    grass.run_command("r.mapcalc", expression=eq, quiet=True)
    agr_tr = "agr_tr_%s" % id
    tr_maps.append(agr_tr)
    rm_rasters.append(agr_tr)
    grass.run_command(
        "r.reclass.area",
        input=agr_tr_tmp,
        output=agr_tr,
        mode="greater",
        value=2,
        quiet=True,
    )
    grass.run_command("r.mask", flags="r")

    grass.message(_("\nMerging training data pixels..."))
    # sum all training maps
    eq = "tr_sum_" + id + " = "
    for rast in tr_maps:
        eq += "if( isnull(" + rast + "), 0, 1 ) +"
    grass.run_command("r.mapcalc", expression=eq[:-2], quiet=True)
    rm_rasters.append("tr_sum_" + id)

    # create mask where the pixel belong only to one class
    grass.run_command(
        "r.mapcalc",
        expression=f"tr_mask{id} = if( tr_sum_{id} == 1, 1, null() )",
        quiet=True,
    )
    rm_rasters.append("tr_mask" + id)
    grass.run_command("r.mask", raster="tr_mask" + id, quiet=True)

    # testif there are pixels inside the training classes
    for rast in tr_maps:
        r_univar = grass.parse_command("r.univar", map=rast, flags="g")
        if int(r_univar["n"]) < int(npoints):
            grass.warning(
                _("For <%s> only %s pixels found.") % (rast, r_univar["n"])
            )

    training_patched = output
    temp_output_column = output.lower()
    # rm_rasters.append(training_patched)
    grass.run_command("r.patch", input=tr_maps, output=training_patched)
    grass.run_command("r.mask", flags="r")
    rm_rasters.extend(tr_maps)
    grass.run_command(
        "r.sample.category",
        input=training_patched,
        output=output,
        npoints=npoints,
    )
    grass.run_command(
        "v.db.renamecolumn",
        map=output,
        column="%s,lulc_class_int" % temp_output_column
    )

    grass.run_command(
        "v.db.addcolumn",
        map=output,
        columns="lulc_class_str VARCHAR(25)"
    )

    grass.run_command(
        "v.db.update",
        map=output,
        layer=1,
        column="lulc_class_str",
        where="lulc_class_int='%s'" % (forest_class),
        value=forest_name,
    )
    grass.run_command(
        "v.db.update",
        map=output,
        layer=1,
        column="lulc_class_str",
        where="lulc_class_int='%s'" % low_veg_class,
        value=low_veg_name,
    )
    grass.run_command(
        "v.db.update",
        map=output,
        layer=1,
        column="lulc_class_str",
        where="lulc_class_int='%s'" % water_class,
        value=water_name,
    )
    grass.run_command(
        "v.db.update",
        map=output,
        layer=1,
        column="lulc_class_str",
        where="lulc_class_int='%s'" % builtup_class,
        value=builtup_name,
    )
    grass.run_command(
        "v.db.update",
        map=output,
        layer=1,
        column="lulc_class_str",
        where="lulc_class_int='%s'" % baresoil_class,
        value=baresoil_name,
    )
    grass.run_command(
        "v.db.update",
        map=output,
        layer=1,
        column="lulc_class_str",
        where="lulc_class_int='%s'" % agr_class,
        value=agr_name,
    )

    # mixed builtup pixels
    grass.run_command(
        "v.db.update",
        map=output,
        layer=1,
        column="lulc_class_str",
        where="lulc_class_int='%s'" % (builtup2_class),
        value=builtup2_name,
    )

    grass.message(_("\nCreated output map <%s>" % (output)))


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
