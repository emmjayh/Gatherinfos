import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np

def parse_collections_xml_for_plot(file_path="collections.xml"):
    """
    Parses the collections.xml file and extracts spawn point data for plotting.

    Args:
        file_path (str): The path to the XML file.

    Returns:
        list: A list of dictionaries, where each dictionary represents a spawn point
              and contains 'collection_id' and 'coordinates'.
    """
    spawn_points_for_plot = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        for territory in root.findall('Territory'):
            for collections in territory.findall('Collections'):
                collection_id = collections.get('id')
                for spawn in collections.findall('Spawn'):
                    pos_str = spawn.get('pos')
                    try:
                        coords = tuple(map(float, pos_str.split(',')))
                        spawn_points_for_plot.append({
                            'collection_id': collection_id,
                            'coordinates': coords
                        })
                    except (ValueError, TypeError) as e:
                        print(f"Warning: Could not parse coordinates for pos='{pos_str}': {e}")
                        # Optionally skip this point or use a default
                        continue
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except ET.ParseError:
        print(f"Error: Could not parse XML file at {file_path}")
    return spawn_points_for_plot

def plot_spawn_points(spawn_data):
    """
    Generates and saves a scatter plot of spawn points.

    Args:
        spawn_data (list): A list of spawn point dictionaries.
    """
    if not spawn_data:
        print("No spawn data to plot.")
        return

    x_coords = [point['coordinates'][0] for point in spawn_data]
    y_coords = [point['coordinates'][1] for point in spawn_data]
    # For Z coordinates, if needed for 3D plot later:
    # z_coords = [point['coordinates'][2] for point in spawn_data]

    collection_ids_str = [point['collection_id'] for point in spawn_data]

    # Map collection_id (string) to unique integers for coloring
    unique_collection_ids = sorted(list(set(collection_ids_str)))
    collection_id_to_int = {cid: i for i, cid in enumerate(unique_collection_ids)}
    color_values = [collection_id_to_int[cid] for cid in collection_ids_str]

    plt.figure(figsize=(12, 8))
    scatter = plt.scatter(x_coords, y_coords, c=color_values, cmap='viridis', alpha=0.7, edgecolors='k', s=50)

    plt.title("Spawn Point Distribution by Collection ID")
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")

    # Create a colorbar
    # The ticks should correspond to the integer mapping of collection_ids
    # We can label them with the actual collection_id strings
    num_unique_colors = len(unique_collection_ids)
    if num_unique_colors > 0 :
        cbar = plt.colorbar(scatter, ticks=np.arange(num_unique_colors))
        cbar.set_label("Collection ID")
        # Set custom tick labels if there aren't too many, otherwise it might get crowded
        if num_unique_colors <= 15: # Arbitrary threshold for readability
             cbar.ax.set_yticklabels(unique_collection_ids)
        else:
            cbar.ax.set_yticklabels([str(i) for i in range(num_unique_colors)]) # Show integers if too many
            print("Info: Too many unique Collection IDs to display all on colorbar. Displaying integer mapping.")


    plt.grid(True)
    plt.axhline(0, color='black', linewidth=0.5)
    plt.axvline(0, color='black', linewidth=0.5)

    # Save the plot
    try:
        plt.savefig("spawn_map.png")
        print("Plot saved as spawn_map.png")
    except Exception as e:
        print(f"Error saving plot: {e}")

    # plt.show() # Commented out for non-blocking execution in automated environments
    # To display the plot locally, uncomment the line above and ensure your environment supports GUI.
    plt.close() # Close the plot figure to free up memory

if __name__ == "__main__":
    parsed_spawn_data = parse_collections_xml_for_plot()
    if parsed_spawn_data:
        plot_spawn_points(parsed_spawn_data)
    else:
        print("No data was parsed. Plot will not be generated.")
