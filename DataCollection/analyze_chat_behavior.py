import os
import json

def analyze_chat_percentages(streamer):
    """
    Calculate the percentage of messages that are "W" or "L" only and those that contain "pog" for a given streamer.
    """
    chat_downloads_folder = "./DataCollection/ChatDownloads"
    total_messages = 0
    wl_messages = 0
    pog_messages = 0

    # Get all JSON files for the streamer
    found_files = []
    for filename in os.listdir(chat_downloads_folder):
        lower_filename = filename.lower()
        lower_streamer = streamer.lower()
        if f"{lower_streamer}" in lower_filename and lower_filename.endswith(".json"):
            found_files.append(filename) 
            file_path = os.path.join(chat_downloads_folder, filename)
            try:
                # Read JSON file
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Extract messages from comments
                if "comments" in data:
                    for comment in data["comments"]:
                        if "message" in comment and "body" in comment["message"]:
                            message = comment["message"]["body"].strip().replace(' ', '').lower()
                            total_messages += 1

                            # Count messages that only contain "W" or "L"
                            if message and (all(c == 'w' for c in message) or all(c == 'l' for c in message)):
                                wl_messages += 1
                            elif message and all(c == 'l' for c in message):
                                l_messages += 1

                            # Count messages that contain "pog"
                            if "pog" in message:
                                pog_messages += 1
            
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    # Calculate percentages
    wl_percentage = (wl_messages / total_messages * 100) if total_messages > 0 else 0
    pog_percentage = (pog_messages / total_messages * 100) if total_messages > 0 else 0

    if found_files:
        print(f"Found files for {streamer}: {', '.join(found_files)}")
    else:
        print(f"No files found for streamer: {streamer}")

    return {
        "streamer": streamer,
        "total_messages": total_messages,
        "wl_percentage": wl_percentage,
        "pog_percentage": pog_percentage,
    }

def normalize_percentages(results, key):
    raw_values = {res['streamer']: res[key] for res in results}
    values = list(raw_values.values())
    min_val, max_val = (min(values), max(values)) if values else (0, 0)
    if max_val > min_val:
        for res in results:
            res[f'normalized_{key}'] = (res[key] - min_val) / (max_val - min_val) * 100
    else:
        for res in results:
            res[f'normalized_{key}'] = 100 if max_val > 0 else 0
    values = [res[key] for res in results]
    min_val, max_val = min(values), max(values)
    if max_val > min_val:
        for res in results:
            res[f'normalized_{key}'] = (res[key] - min_val) / (max_val - min_val) * 100
    else:
        for res in results:
            res[key] = 100 if max_val > 0 else 0

def calculate_wl_pog_scale(results):
    """
    Calculate the W/L to POG scale as a percentage.
    """
    for res in results:
        total = res['normalized_wl_percentage'] + res['normalized_pog_percentage']
        if total > 0:
            res['wl_pog_scale'] = (res['normalized_wl_percentage'] / total) * 100
        else:
            res['wl_pog_scale'] = 50  # Neutral if no data

def rank_streamers(streamers, times):
    
    """
    Rank streamers based on W/L and POG percentages.
    """
    results = []
    for streamer in streamers:
        result = analyze_chat_percentages(streamer)
        results.append(result)
    
    # Sort by W/L percentage
    normalize_percentages(results, 'wl_percentage')
    ranked_wl = sorted(results, key=lambda x: x['wl_percentage'], reverse=True)
    # Sort by POG percentage
    normalize_percentages(results, 'pog_percentage')
    ranked_pog = sorted(results, key=lambda x: x['pog_percentage'], reverse=True)
    
    # print("Ranking by W/L Percentage (Raw & Normalized):")
    # for i, res in enumerate(ranked_wl, 1):
    #     print(f"{i}. {res['streamer']} - Raw: {res['wl_percentage']:.2f}%, Normalized: {res['normalized_wl_percentage']:.2f}%")

    # print("Ranking by POG Percentage (Raw & Normalized):")
    # for i, res in enumerate(ranked_pog, 1):
    #     print(f"{i}. {res['streamer']} - Raw: {res['pog_percentage']:.2f}%, Normalized: {res['normalized_pog_percentage']:.2f}%")
    
    calculate_wl_pog_scale(results)
    
    # calculate_wl_pog_scale(results)
    ranked_scale = sorted(results, key=lambda x: x['wl_pog_scale'], reverse=True)
    
    print("Ranking on the W/L to POG Scale:")
    for i, res in enumerate(ranked_scale, 1):
        print(f"{i}. {res['streamer']} - {res['wl_pog_scale']:.2f}% W/L, {100 - res['wl_pog_scale']:.2f}% POG")
    ranked_wl_pog = sorted(results, key=lambda x: x['normalized_wl_percentage'], reverse=True)
    ranked_pog_only = sorted(results, key=lambda x: x['normalized_pog_percentage'], reverse=True)
    
    print("Streamers Most Likely to Spam W/L:")
    for i, res in enumerate(ranked_wl_pog, 1):
        print(f"{i}. {res['streamer']} - {res['normalized_wl_percentage']:.2f}% W/L")
    
    print("Streamers Most Likely to Spam POG:")
    for i, res in enumerate(ranked_pog_only, 1):
        print(f"{i}. {res['streamer']} - {res['normalized_pog_percentage']:.2f}% POG")
        # print(f"{i}. {res['streamer']} - Ratio: {res['wl_to_pog_ratio']:.2f}")
    
    return results


import csv

def save_results_to_csv(results, times):
    """
    Save streamer ranking data to a CSV file.
    """
    with open("streamer_rankings.csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["streamer", "time", "pog/w ratio"])
        for res in results:
            time = times.get(res['streamer'], "N/A")
            minutes = sum(float(x) * 60 ** i for i, x in enumerate(reversed(time.split(':'))))
            writer.writerow([res['streamer'], f"{minutes:.2f}", f"{100 - res['wl_pog_scale']:.2f}"])


times = {
        "Pikabooirl": "2:00.18", "Lacy": "2:06.31", "Northernlion": "2:08.16", "sodapoppin": "2:12.77", "summit1g": "2:28.77",
        "MISTERARTHER": "2:58.48", "HasanAbi": "3:32.99", "shroud": "4:29.31", "caseoh_": "5:10.74", "Tubbo": "11:19.13",
        "Nmplol": "15:32.61", "Mizkif": "16:26.73", "LCK": "17:59.48", "zackrawrr": "20:35.64", "loltyler1": "20:40.22",
        "MrSavage": "22:37.29", "MOONMOON": "26:56.16", "xQc": "34:25.06", "plaqueboymax": "38:38.87", "Thebausffs": "54:19.27",
        "KaiCenat": "1:05:59.76", "Caedrel": "1:46:32.08", "ohnePixel": "1:53:07.70", "stableronaldo": "3:26:30.44", "PirateSoftware": "7:58:40.71"
    }

if __name__ == "__main__":
    streamers = [
        "Pikabooirl", "Lacy", "Northernlion", "sodapoppin", "summit1g", "MISTERARTHER", "HasanAbi", "shroud",
        "caseoh_", "Tubbo", "Nmplol", "Mizkif", "LCK", "zackrawrr", "loltyler1", "MrSavage", "MOONMOON", "xQc",
        "plaqueboymax", "Thebausffs", "KaiCenat", "Caedrel", "ohnePixel", "stableronaldo", "PirateSoftware"
    ]
    results = rank_streamers(streamers, times)
    save_results_to_csv(results, times)

