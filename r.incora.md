[![image-alt](grass_logo.png)](https://grass.osgeo.org/grass-stable/manuals/index.html)

------------------------------------------------------------------------

## NAME

***r.incora*** - Toolset for Incora landcover classification.

## KEYWORDS

[raster](https://grass.osgeo.org/grass-stable/manuals/raster.html),
[classification](https://grass.osgeo.org/grass-stable/manuals/topic_classification.html)

## DESCRIPTION

The *r.incora* toolset consists of currently three modules.

*Processing modules:*

[v.incora.training_data](v.incora.training_data.md)  
creates a vector map containing training points from a set of rules
containing the output classes: forest, low vegetation, water, built-up,
bare soil and agriculture.

[r.incora.postproc](r.incora.postproc.md)  
uses post processing to deal with mixed pixels identified in
[v.incora.training_data](v.incora.training_data). Mixed pixels
(class 70) are removed from the map. The gaps are then filled using
[r.grow.distance](https://grass.osgeo.org/grass-stable/manuals/r.grow.distance.html).

[r.incora.change](r.incora.change.md)  
runs a change detection based on two input maps. The nomenclature is
optimized for the incora project.

## REQUIREMENTS

The following GRASS GIS Addons are required:

- [r.sample.category](https://grass.osgeo.org/grass-stable/manuals/addons/r.sample.category.html)
- [r.change.stats](https://github.com/mundialis/r.change.stats.html)
- [r.change.info](https://grass.osgeo.org/grass-stable/manuals/addons/r.change.info.html)

## AUTHORS

Anika Weinmann and Guido Riembauer,
[mundialis](https://www.mundialis.de/), Germany
