"""Field geometry used by the movement visualizer."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


Point = tuple[float, float]


@dataclass(frozen=True)
class FieldDefinition:
    name: str
    width: float
    height: float
    polygon: tuple[Point, ...]
    start_positions: dict[str, Point]
    units_to_map: float = 120.0


FIELD_NAMES = [
    'None',
    'Sunflower',
    'Dandelion',
    'Mushroom',
    'Blue Flower',
    'Clover',
    'Strawberry',
    'Spider',
    'Bamboo',
    'Pineapple',
    'Stump',
    'Cactus',
    'Pumpkin',
    'Pine Tree',
    'Rose',
    'Mountain Top',
    'Pepper',
    'Coconut',
]

DEFAULT_START_POSITIONS = {
    'upper left': (0.0, 0.0),
    'upper right': (1.0, 0.0),
    'center': (0.5, 0.5),
    'lower left': (0.0, 1.0),
    'lower right': (1.0, 1.0),
    'bottom': (0.5, 1.0),
}


PINE_TREE_FIELD = FieldDefinition(
    name='Pine Tree',
    width=409.0,
    height=562.0,
    # Approximate playable boundary traced from the supplied map image.
    polygon=(
        (95.0, 0.0),
        (256.0, 0.0),
        (256.0, 43.0),
        (292.0, 43.0),
        (303.0, 66.0),
        (370.0, 66.0),
        (409.0, 99.0),
        (409.0, 562.0),
        (107.0, 562.0),
        (91.0, 545.0),
        (97.0, 513.0),
        (64.0, 481.0),
        (30.0, 493.0),
        (0.0, 474.0),
        (0.0, 205.0),
        (45.0, 189.0),
        (59.0, 160.0),
        (0.0, 160.0),
        (0.0, 0.0),
    ),
    # The map's top-left corner is the field's upper-left reference.
    start_positions={
        'upper left': (79.0, 190.0),
        'center': (214.0, 340.0),
        'lower left': (61.0, 495.0),
        'upper right': (343.0, 178.0),
        'lower right': (350.0, 500.0),
        'bottom': (214.0, 530.0),
    },
    units_to_map=170.0,
)


FIELD_DEFINITIONS = {
    PINE_TREE_FIELD.name.lower(): PINE_TREE_FIELD,
}


def get_field_definition(name: Optional[str]) -> Optional[FieldDefinition]:
    normalized = str(name or '').replace('_', ' ').strip().lower()
    if normalized in ('', 'none', 'no field bounds'):
        return None
    return FIELD_DEFINITIONS.get(normalized)


def start_positions_for_field(name: Optional[str]) -> list[str]:
    field = get_field_definition(name)
    if field is None:
        return list(DEFAULT_START_POSITIONS.keys())
    return list(field.start_positions.keys())
