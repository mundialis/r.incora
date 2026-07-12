## DESCRIPTION

*v.incora.training_data* creates a vector map containing training points
from a set of rules. Output classes (incora) are:

- 10 (forest)
- 20 (low veg)
- 30 (water)
- 40 (builtup)
- 50 (bare soil)
- 60 (agriculture)

## EXAMPLE

```sh
v.incora.training_data imperviousness=HRL_Imperviousness_null \
landcover=S2GLC_Europe_2017_v1.2 ndvi_max=maja_2019_NDVI_maximum_Mar_May_Jul_Sep \
ndvi_min=maja_2019_NDVI_minimum_Mar_May_Jul_Sep \
ndvi_range=maja_2019_NDVI_range_Mar_May_Jul_Sep \
ndwi=July19_NDWI ndbi=July19_NDBI asm=July19_asm_ASM \
buildings=NRW_OSM_buildings_rast_10m roads=NRW_OSM_roads_rast_10m \
npoints=10000 output=incora_training_auto_2019
```

## SEE ALSO

*[r.sample.category](r.sample.category), [r.buffer](r.buffer),
[r.mapcalc](r.mapcalc), [r.mask](r.mask), [r.quantile](r.quantile)*

## AUTHORS

Guido Riembauer, [mundialis](https://www.mundialis.de/) Anika Weinmann,
[mundialis](https://www.mundialis.de/)
