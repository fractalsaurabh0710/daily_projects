# Property Order

JavaScript objects are not insertion-ordered. `OrdinaryOwnPropertyKeys` lists
integer-index keys first, in ascending numeric order, then the remaining string
keys in creation order, then symbols in creation order. `main.js` reimplements
that rule from the insertion sequence alone and checks the prediction against
`Reflect.ownKeys` on 4000 randomly built objects.

## Run

    node main.js

No dependencies. It prints a short report and exits non-zero if any prediction
misses.

## The part worth knowing

A key counts as an index only in *canonical* numeric form — `ToString(ToUint32(P))`
has to be `P` itself — so `"1"` sorts but `"01"`, `"1.0"`, `"-0"` and `" 1"` are
ordinary strings sitting wherever you put them. And the range stops one short:
`"4294967294"` is the largest array index there is, while `"4294967295"` is
reserved as a length and never sorts.

The asymmetry under deletion falls out of the same rule. Delete a string key and
re-add it and it moves to the end, because its position was remembered; do that
to an index key and nothing moves, because its position is computed from its
value. A `Map` is the structure that actually keeps insertion order, and it
keeps `"1"` and `1` apart while an object cannot.
