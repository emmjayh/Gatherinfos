import xml.etree.ElementTree as ET
import json

def parse_collections_xml(file_path="collections.xml"):
    """
    Parses the collections.xml file and extracts spawn point data.

    Args:
        file_path (str): The path to the XML file.

    Returns:
        tuple: A tuple containing:
            - list: A list of dictionaries, where each dictionary represents a spawn point.
            - int: The total number of Collections elements found.
            - int: The total number of Spawn points extracted.
    """
    all_spawn_points = []
    total_collections_count = 0
    total_spawn_points_count = 0

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        for territory in root.findall('Territory'):
            territory_id = territory.get('id')
            territory_desc = territory.get('desc')

            for collections in territory.findall('Collections'):
                total_collections_count += 1
                collection_id = collections.get('id')
                collection_desc = collections.get('desc')
                raw_type_id = collections.get('typeId')
                raw_respawn_time = collections.get('respawnTime')

                try:
                    type_id = int(raw_type_id)
                except (ValueError, TypeError) as e:
                    print(f"Warning: Could not parse type_id '{raw_type_id}' as int for collection {collection_id}. Using -1. Error: {e}")
                    type_id = -1

                try:
                    respawn_time = int(raw_respawn_time)
                except (ValueError, TypeError) as e:
                    print(f"Warning: Could not parse respawn_time '{raw_respawn_time}' as int for collection {collection_id}. Using -1. Error: {e}")
                    respawn_time = -1

                for spawn in collections.findall('Spawn'):
                    total_spawn_points_count += 1
                    pos_str = spawn.get('pos')
                    try:
                        coords = tuple(map(float, pos_str.split(',')))
                    except (ValueError, TypeError) as e:
                        print(f"Warning: Could not parse coordinates for pos='{pos_str}': {e}")
                        coords = (0.0, 0.0, 0.0) # Default or error value

                    spawn_data = {
                        'territory_id': territory_id,
                        'territory_desc': territory_desc,
                        'collection_id': collection_id,
                        'collection_desc': collection_desc,
                        'type_id': type_id,
                        'respawn_time': respawn_time,
                        'coordinates': coords
                    }
                    all_spawn_points.append(spawn_data)

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return [], 0, 0
    except ET.ParseError:
        print(f"Error: Could not parse XML file at {file_path}")
        return [], 0, 0

    return all_spawn_points, total_collections_count, total_spawn_points_count

if __name__ == "__main__":
    spawn_points_data, collections_count, spawn_points_count = parse_collections_xml()

    print(f"Total number of Collections elements found: {collections_count}")
    print(f"Total number of Spawn points extracted: {spawn_points_count}")

    if spawn_points_data:
        try:
            with open("spawn_data.json", "w", encoding="utf-8") as f:
                json.dump(spawn_points_data, f, indent=4, ensure_ascii=False)
            print("Data successfully saved to spawn_data.json")
        except IOError as e:
            print(f"Error saving data to JSON: {e}")
    else:
        print("No data extracted, spawn_data.json not created.")
