# Copyright (C) 2023, Princeton University.
# This source code is licensed under the BSD 3-Clause license found in the LICENSE file in the root directory of this source tree.

import argparse
import sys
from pathlib import Path
# import shlex # Not strictly needed for this version of format_gin_value

try:
    from infinigen_examples import generate_nature
except ImportError:
    print("Error: Could not import 'generate_nature'.")
    print("Ensure 'infinigen_examples' is in your PYTHONPATH or run this script from its parent directory.")
    sys.exit(1)

def format_gin_value(value):
    """
    Formats a Python value into a string suitable for a Gin override.
    """
    if isinstance(value, str):
        # If the string is already correctly quoted (e.g., for paths or internal gin names)
        # or if it's a gin reference like %OVERALL_SEED or @some_function
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")) or \
           value.startswith('%') or value.startswith('@'):
            return value
        return f'"{value}"'  # Add quotes for regular strings
    elif isinstance(value, (list, tuple)):
        # Gin expects a format like (val1, val2) or [val1, val2]
        # Ensure elements within are also correctly formatted if they are strings
        formatted_elements = [format_gin_value(el) for el in value]
        if isinstance(value, tuple):
            # Gin tuples are often represented as ('val1', 'val2') in .gin files
            # and as ('uniform', 0, 1) when calling functions.
            # The string representation for overrides should be like key=(elem1,elem2)
            return f"({','.join(formatted_elements)})"
        else:  # list
            return f"[{','.join(formatted_elements)}]"
    elif isinstance(value, bool):
        return 'True' if value else 'False'  # Gin uses True/False
    return str(value)  # For numbers and other types

def run_generation_with_dict(params_dict):
    """
    Runs generate_nature.main with parameters from a dictionary.
    """
    args = argparse.Namespace()

    # 1. Map basic parameters to argparse arguments
    args.output_folder = Path(params_dict.get("output_folder", "output_default_infinigen"))
    args.input_folder = params_dict.get("input_folder", None)  # Typically None for new generation
    args.seed = params_dict.get("seed", None)  # Let generate_nature.py pick randomly if not specified
    args.task = params_dict.get("tasks", ["coarse"])  # Default to 'coarse' if not provided
    args.task_uniqname = params_dict.get("task_uniqname", None)
    args.debug = params_dict.get("debug", None)

    # 2. Prepare Gin configurations and overrides
    # generate_nature.py already includes 'base_nature.gin' internally.
    # args.configs should list ADDITIONAL .gin files, like scene types.
    args.configs = params_dict.get("gin_configs", []) # Renamed from "configs_gin" for clarity

    gin_overrides = []
    # Identify keys that are for argparse and should not become gin_overrides
    argparse_specific_keys = ["output_folder", "input_folder", "seed", "tasks", "task_uniqname", "debug", "gin_configs"]

    for key, value in params_dict.items():
        if key not in argparse_specific_keys:
            formatted_value = format_gin_value(value)
            gin_overrides.append(f'{key}={formatted_value}')

    args.overrides = gin_overrides

    print(f"--- Running Infinigen with Programmatic Arguments ---")
    print(f"Output Folder: {args.output_folder}")
    print(f"Seed: {args.seed}")
    print(f"Tasks: {args.task}")
    print(f"Additional Gin Configs: {args.configs}")
    print(f"Gin Overrides: {args.overrides}")
    print(f"--------------------------------------------------")

    # Call the main function from generate_nature.py
    generate_nature.main(args)

# --- Your Parameter Dictionary ---
# This example dictionary demonstrates various parameter types.
# You should customize this to your specific needs.
# Ensure parameter names (e.g., "compose_nature.max_tree_species")
# match those in the .gin files or @gin.configurable functions.
custom_scene_parameters = {
    "output_folder": "output_results/my_custom_desert_scene",
    "seed": 12345,
    "tasks": ["coarse", "populate", "fine_terrain", "render"],
    "gin_configs": ["scene_types/desert.gin"],  # e.g., use a desert scene type config

    # Parameters for 'compose_nature' (likely defined in base_nature.gin or generate_nature.py)
    "compose_nature.terrain_enabled": True,
    "compose_nature.max_tree_species": 0,        # Deserts typically have no trees
    "compose_nature.tree_density": 0.0,
    "compose_nature.bushes_chance": 0.75,
    "compose_nature.max_bush_species": 3,
    "compose_nature.bush_density": 0.02,
    "compose_nature.cactus_chance": 0.95,
    "compose_nature.max_cactus_species": 5,
    "compose_nature.cactus_density": ('uniform', 0.01, 0.06), # Example of a tuple value for Gin
    "compose_nature.boulders_chance": 0.65,
    "compose_nature.boulder_density": 0.025,
    "compose_nature.grass_chance": 0.15,         # Minimal grass in a desert
    "compose_nature.near_distance": 30,          # Camera related distances
    "compose_nature.inview_distance": 90,
    "compose_nature.land_domain_tags": 'landscape,-liquid_covered,-cave', # String value
    "compose_nature.fancy_clouds_chance": 0.1,   # Few clouds
    "compose_nature.ground_creatures_chance": 0.05, # This was duplicated in base_nature.gin, using one from here.
    "compose_nature.flying_creatures_chance": 0.02, # This was also duplicated.

    # Parameters for 'populate_scene'
    "populate_scene.slime_mold_chance": 0.0,     # No slime mold in deserts
    "populate_scene.lichen_chance": 0.15,        # Some lichen might exist
    "populate_scene.fire_warmup": 25,

    # Parameters for other modules (e.g., materials, lighting)
    # These must match parameters defined in .gin files or via @gin.configurable
    # "assets.materials.sand.shader.color_custom_palette": [ (0.8,0.6,0.4), (0.7,0.5,0.3) ], # Example
    # "lighting.sky_lighting.sun_altitude_deg": 75.0, # Example for lighting
}

if __name__ == "__main__":
    # Ensure the output directory exists
    output_dir = Path(custom_scene_parameters["output_folder"])
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Ensured output directory exists: {output_dir.resolve()}")

    run_generation_with_dict(custom_scene_parameters)
    print("Generation process initiated.")
    print(f"Check the output folder: {output_dir.resolve()}")
