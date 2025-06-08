import json
import folium
from folium.plugins import MarkerCluster
import argparse
import math

def calculate_path_distance(path_coords_folium_style):
    """
    Calculates the total Cartesian distance of a path.

    Args:
        path_coords_folium_style (list): A list of [y, x] coordinate pairs.

    Returns:
        float: The total distance of the path.
    """
    if not path_coords_folium_style or len(path_coords_folium_style) < 2:
        return 0.0

    total_distance = 0.0
    # Assuming path_coords_folium_style is list of [y, x]
    # For distance calculation, we use (x, y)

    for i in range(len(path_coords_folium_style) - 1):
        p1_folium = path_coords_folium_style[i]
        p2_folium = path_coords_folium_style[i+1]

        # Extract as (x, y) for cartesian distance calculation
        x1, y1 = p1_folium[1], p1_folium[0]
        x2, y2 = p2_folium[1], p2_folium[0]

        segment_distance = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
        total_distance += segment_distance

    return total_distance

def create_interactive_map(data_file="spawn_data.json", output_file="spawn_locations_map.html", user_path_str=None, desired_type_ids_list=None, travel_speed=50.0, vertical_stretch_factor=1.0):
    """
    Creates an interactive HTML map of spawn locations using Folium.

    Args:
        data_file (str): Path to the JSON file containing spawn data.
        output_file (str): Path to save the generated HTML map.
    """
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            spawn_points = json.load(f)
    except FileNotFoundError:
        print(f"Error: Data file '{data_file}' not found.")
        return None, None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{data_file}'.")
        return None, None

    if not spawn_points:
        print("No spawn points found in the data. Map will not be generated.")
        return None, None

    # Calculate average coordinates for map center
    # Assuming coordinates are [X, Y, Z]
    # Folium expects [latitude, longitude] which corresponds to [Y, X] in typical game coordinates
    avg_x = sum(p['coordinates'][0] for p in spawn_points) / len(spawn_points)
    # Apply vertical stretch factor to Y for map display
    avg_y = sum(p['coordinates'][1] * vertical_stretch_factor for p in spawn_points) / len(spawn_points)

    # Create map centered at average Y (latitude), average X (longitude)
    # Adjust zoom_start as needed. Smaller numbers zoom out.
    # Given the coordinate ranges observed, a small zoom_start like 0 or 1 might be initially better,
    # or we might need to scale/normalize coordinates if they are very large.
    # For now, let's try a modest zoom. If coordinates are huge, this might not look good.
    # A common strategy for game maps is to use a simple CRS like 'EPSG3857' or 'Simple' if not real-world coords.
    # Folium primarily works with lat/lon. If these are arbitrary game coords, we might need to scale them
    # or use a non-geographic CRS if Folium supports it well, but CircleMarker expects lat/lon.
    # We'll assume for now that Y is latitude-like and X is longitude-like.

    # Let's determine the range of coordinates to set a reasonable zoom
    # Apply vertical stretch factor to Y for map display bounds
    all_lats = [p['coordinates'][1] * vertical_stretch_factor for p in spawn_points]
    all_lons = [p['coordinates'][0] for p in spawn_points]

    map_center_lat = avg_y
    map_center_lon = avg_x

    # Create the map
    game_map = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=2, tiles="CartoDB positron")
    # Using MarkerCluster for better performance with many markers
    marker_cluster = MarkerCluster().add_to(game_map)

    # Define color mapping for type_id
    unique_type_ids = sorted(list(set(str(p['type_id']) for p in spawn_points))) # Ensure type_id is string for dict keys

    # Basic list of colors, can be extended
    colors = [
        'red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred',
        'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple',
        'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray'
    ]

    type_id_to_color = {type_id: colors[i % len(colors)] for i, type_id in enumerate(unique_type_ids)}

    for point in spawn_points:
        coords = point['coordinates'] # [X, Y, Z]
        collection_desc = point.get('collection_desc', 'N/A')
        type_id = str(point.get('type_id', 'N/A')) # Ensure string for lookup
        respawn_time = point.get('respawn_time', 'N/A')

        # Folium location: [latitude, longitude] -> [Y * stretch, X]
        # Original Y (coords[1]) is used for popup, stretched Y for map display
        marker_location = [coords[1] * vertical_stretch_factor, coords[0]]

        popup_html = f"""
        <b>Collection:</b> {collection_desc}<br>
        <b>Type ID:</b> {type_id}<br>
        <b>Respawn (sec):</b> {respawn_time}<br>
        <b>Territory:</b> {point.get('territory_desc', 'N/A')} (ID: {point.get('territory_id', 'N/A')})<br>
        <b>Coords (X,Y,Z):</b> ({coords[0]}, {coords[1]}, {coords[2]})
        """
        popup = folium.Popup(popup_html, max_width=350)

        marker_color = type_id_to_color.get(type_id, 'gray') # Default to gray if type_id somehow not in map

        folium.CircleMarker(
            location=marker_location,
            radius=5,
            popup=popup,
            color=marker_color,
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.7
        ).add_to(marker_cluster) # Add to cluster instead of directly to map

    # Filter points for AI path generation if desired_type_ids_list is provided
    ai_path_candidate_points = []
    if desired_type_ids_list:
        for point in spawn_points:
            if point.get('type_id') in desired_type_ids_list:
                ai_path_candidate_points.append(point)
        print(f"Found {len(ai_path_candidate_points)} spawn points matching Type IDs {desired_type_ids_list} for AI path generation.")

    ai_generated_path_coords = []
    if ai_path_candidate_points: # If there are points to make a path from
        remaining_points = list(ai_path_candidate_points) # Make a mutable copy

        # Start with the first point in the filtered list
        current_node_data = remaining_points.pop(0)
        current_coords_xy = current_node_data['coordinates'][:2] # X, Y for original distance calculation
        # Apply stretch for Folium path display
        ai_generated_path_coords.append([current_node_data['coordinates'][1] * vertical_stretch_factor, current_node_data['coordinates'][0]]) # Stretched Y, X for Folium

        while remaining_points:
            next_node_data = None
            min_distance = float('inf')
            current_point_idx_in_remaining = -1

            for i, potential_node_data in enumerate(remaining_points):
                potential_coords_xy = potential_node_data['coordinates'][:2]
                # Euclidean distance in 2D (X, Y)
                distance = math.sqrt(
                    (current_coords_xy[0] - potential_coords_xy[0])**2 +
                    (current_coords_xy[1] - potential_coords_xy[1])**2
                )
                if distance < min_distance:
                    min_distance = distance
                    next_node_data = potential_node_data
                    current_point_idx_in_remaining = i

            if next_node_data:
                current_coords_xy = next_node_data['coordinates'][:2] # Original X,Y for next distance calc
                # Apply stretch for Folium path display
                ai_generated_path_coords.append([next_node_data['coordinates'][1] * vertical_stretch_factor, next_node_data['coordinates'][0]])
                remaining_points.pop(current_point_idx_in_remaining)
            else: # Should only happen if remaining_points was empty, but loop condition handles this
                break

        if ai_generated_path_coords:
            print(f"AI path generated with {len(ai_generated_path_coords)} points using Nearest Neighbor algorithm.")
            if len(ai_generated_path_coords) >= 2:
                folium.PolyLine(
                    locations=ai_generated_path_coords,
                    color='blue',
                    weight=2.5,
                    opacity=1,
                    tooltip='AI-Generated Path (Nearest Neighbor for selected Type IDs)'
                ).add_to(game_map)
                print("AI-generated path drawn on the map.")
            elif ai_generated_path_coords: # Exactly 1 point
                 print("AI path has only one point, not drawing a line.")
    # Note: ai_path_candidate_points is prepared here, actual pathfinding with it will be in a future step.

    # Process and draw user-defined path
    if user_path_str:
        path_collection_ids = [item.strip() for item in user_path_str.split(',')]
        user_path_coords_folium_style = []

        # Create a quick lookup for spawn points by collection_id
        # This assumes we take the first available spawn point for a given collection_id
        spawn_points_by_collection_id = {}
        for sp in spawn_points:
            cid = str(sp['collection_id']) # Ensure string for matching
            if cid not in spawn_points_by_collection_id:
                spawn_points_by_collection_id[cid] = sp['coordinates']

        for cid_in_path in path_collection_ids:
            if cid_in_path in spawn_points_by_collection_id:
                # coords are [X, Y, Z], Folium needs [lat, lon] -> [Y * stretch, X]
                coords = spawn_points_by_collection_id[cid_in_path]
                user_path_coords_folium_style.append([coords[1] * vertical_stretch_factor, coords[0]])
            else:
                print(f"Warning: Collection ID '{cid_in_path}' in path not found in spawn data. Path point skipped.")

        if len(user_path_coords_folium_style) >= 2:
            num_points_user = len(user_path_coords_folium_style)
            total_distance_user = calculate_path_distance(user_path_coords_folium_style)
            estimated_time_user = total_distance_user / travel_speed if travel_speed > 0 else 0.0

            print(f"User Path Stats: Points = {num_points_user}, Distance = {total_distance_user:.2f} units, Estimated Time = {estimated_time_user:.2f} seconds.")

            user_path_tooltip = (
                f"User-Defined Path<br>"
                f"Points: {num_points_user}<br>"
                f"Distance: {total_distance_user:.2f} units<br>"
                f"Time: {estimated_time_user:.2f} sec @ {travel_speed} units/sec"
            )
            folium.PolyLine(
                locations=user_path_coords_folium_style,
                color="red",
                weight=3,
                opacity=0.8,
                tooltip=user_path_tooltip
            ).add_to(game_map)
            print(f"User path plotted for Collection IDs: {', '.join(path_collection_ids)}")
        elif user_path_coords_folium_style: # Exactly 1 point
             print("User path has only one point. Statistics and line are not applicable.")
        else:
            print("No valid coordinates found for the user-defined path. Path not plotted.")
    else:
        if args.path is not None : # if --path was given but resulted in no points
             print("User path not plotted as no valid collection IDs were found from the input.")


    try:
        game_map.save(output_file)
        print(f"Interactive map saved to {output_file}")
    except Exception as e:
        print(f"Error saving map: {e}")

    return map_center_lat, map_center_lon

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate an interactive map of spawn locations.")
    parser.add_argument("--data_file", default="spawn_data.json", help="Path to the spawn data JSON file.")
    parser.add_argument("--output_file", default="spawn_locations_map.html", help="Path to save the HTML map.")
    parser.add_argument("--path", type=str, default=None, help="Comma-separated string of collection_ids to plot a path (e.g., '1,4,2').")
    parser.add_argument('--gentypes', type=str, help='Generate an optimal path for these comma-separated Type IDs (e.g., "23,123").')
    parser.add_argument(
        '--speed',
        type=float,
        default=50.0,
        help='Assumed travel speed in units per second (default: 50.0).'
    )
    parser.add_argument("--stretch_factor", type=float, default=1.0, help="Visual vertical stretch factor for the map display.")

    args = parser.parse_args()

    travel_speed = args.speed
    print(f"Using travel speed: {travel_speed} units/sec.")

    desired_type_ids_for_ai = []
    if args.gentypes:
        try:
            type_id_str_list = [item.strip() for item in args.gentypes.split(',')]
            desired_type_ids_for_ai = [int(tid_str) for tid_str in type_id_str_list]
            print(f"Successfully parsed Type IDs for AI path generation: {desired_type_ids_for_ai}")
        except ValueError as e:
            print(f"Error: Invalid Type ID provided in --gentypes list ('{args.gentypes}'). All Type IDs must be integers. Example: --gentypes \"23,123\". Proceeding without AI path type filtering.")
            desired_type_ids_for_ai = [] # Reset or ensure it's empty on error

    create_interactive_map(
        data_file=args.data_file,
        output_file=args.output_file,
        user_path_str=args.path,
        desired_type_ids_list=desired_type_ids_for_ai,
        travel_speed=travel_speed,
        vertical_stretch_factor=args.stretch_factor
    )
