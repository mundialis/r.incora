## DESCRIPTION

*r.incora.postproc* uses post processing to deal with mixed pixels
identified in v.incora.training_data. Mixed pixels (class 70) are
removed from the map. The gaps are then filled using
[r.grow.distance](r.grow.distance).

## EXAMPLE

```sh
r.incora.postproc classification=classification_map output=classification_map_postproc
```

## SEE ALSO

*[v.incora.training_data](v.incora.training_data),
[r.grow.distance](r.grow.distance)*

## AUTHORS

Guido Riembauer, [mundialis](https://www.mundialis.de/)
