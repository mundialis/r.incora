## DESCRIPTION

*r.incora.change* runs a change detection based on two input maps and
does post processing for incora. The nomenclature is optimized for the
incora project. The **-f** flag can be used to to eliminate isolated
pixels and edge effects from the change detection product using a mode
filter of size window_size.

## EXAMPLE

```sh
r.incora.change -f input=incora_germany_2019,incora_germany_2020 output_cd=cd_19_20_total output_water=cd_19_20_water output_bu=cd_19_20_built_up output_forest=cd_19_20_forest output_lowveg=cd_19_20_lowvegetation output_bare=cd_19_20_bare_soil output_agr=cd_19_20_agriculture
# Computes a change map between both classifications, as well as change maps for each class.
# The resulting change maps will be labelled according to input raster category values, e.g.
# 1002  Change from 20 to 10
# 1003  Change from 30 to 10
# ...
```

## SEE ALSO

*[r.sample.category](r.change.stats) (addon), [r.buffer](r.change.info)
(addon),
[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc)*

## AUTHOR

Guido Riembauer, [mundialis](https://www.mundialis.de/), Germany
