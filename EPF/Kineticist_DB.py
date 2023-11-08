Kineticist_DB = {
    "aerial boomerang": {
        "complex": True,
        "category": "kineticist",
        "title": "aerial boomerang",
        "lvl": 1,
        "traits": ["air", "impulse", "kineticist", "primal"],
        "type": {"value": "save", "save": "reflex", "type": "basic"},
        "effect": {"basic dmg": "2d4 slashing"},
        "heighten": {"interval": 2, "effect": "1d4"},
    },
    "flying flame": {
        "complex": True,
        "category": "kineticist",
        "title": "flying flame",
        "lvl": 1,
        "traits": ["fire", "impulse", "kineticist", "primal"],
        "type": {"value": "save", "save": "reflex", "type": "basic"},
        "effect": {"basic dmg": "1d6 fire"},
        "heighten": {"interval": 2, "effect": "1d6"},
    },
    "hail of splinters": {
        "complex": True,
        "category": "kineticist",
        "title": "hail of splinters",
        "lvl": 1,
        "traits": ["overflow", "impulse", "kineticist", "primal", "wood"],
        "type": {"value": "save", "save": "reflex", "type": "complex"},
        "effect": {
            "critical success": None,
            "success": "(1d4)/2 piercing, pd (1d4)/2 piercing / dc15 flat",
            "failure": "1d4 piercing, pd 1d4 piercing / dc15 flat",
            "critical failure": "(1d4)*2 piercing / pd (1d4)*2 piercing / dc15 flat ",
        },
        "heighten": {"interval": 2, "effect": "1d4"},
    },
    "magnetic pinions": {
        "complex": True,
        "category": "kineticist",
        "title": "magnetic pinions",
        "lvl": 1,
        "traits": ["overflow", "impulse", "kineticist", "primal", "metal"],
        "type": {
            "value": "attack",
        },
        "effect": {"success": "1d4 piercing, 1d4 bludgeoning"},
        "heighten": {"interval": 2, "effect": "1d4"},
    },
}
