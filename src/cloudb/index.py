#!/usr/bin/env python
# * coding: utf8 *
"""
index - A module that creates sql indexes
"""

DEFAULT = 'create index if not exists idx_{2}_{0} on {1}.{2} ({0});'
FUZZY = 'create index if not exists trgm_idx_{2}_{0} on {1}.{2} using gin ({0} gin_trgm_ops);'

PARCEL_LAYERS = [
    'beaver', 'box_elder', 'cache', 'carbon', 'daggett', 'davis', 'duchesne', 'emery', 'garfield', 'grand', 'iron',
    'juab', 'kane', 'millard', 'morgan', 'piute', 'rich', 'salt_lake', 'san_juan', 'sanpete', 'sevier', 'summit',
    'tooele', 'uintah', 'utah', 'wasatch', 'washington', 'wayne', 'weber'
]
INDEXES = {
    'location.address_points': [
        DEFAULT.format('fulladd', 'location', 'address_points'),
        FUZZY.format('fulladd', 'location', 'address_points')
    ],
    'location.zoom_locations': [
        DEFAULT.format('name', 'location', 'zoom_locations'),
        FUZZY.format('name', 'location', 'zoom_locations')
    ],
    'location.gnis_place_names': [
        DEFAULT.format('name', 'location', 'gnis_place_names'),
        FUZZY.format('name', 'location', 'gnis_place_names')
    ],
    'transportation.roads': [
        DEFAULT.format('fullname', 'transportation', 'roads'),
        FUZZY.format('fullname', 'transportation', 'roads')
    ],
    'cadastre.land_ownership': [
        DEFAULT.format('admin', 'cadastre', 'land_ownership'),
        DEFAULT.format('owner', 'cadastre', 'land_ownership'),
    ],
}

for county in PARCEL_LAYERS:
    INDEXES[f'cadastre.{county}'] = [DEFAULT.format('parcel_id', 'cadastre', county)]
