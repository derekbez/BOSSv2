"""Constellation of the Night mini-app.

Shows visible constellations based on current location, date and time.
Uses seasonal constellation data and hemispheric visibility.
"""
from __future__ import annotations
import time
import datetime
from typing import Dict, List, Tuple, Any


def get_season_and_hemisphere(latitude: float, month: int) -> Tuple[str, str]:
    """Determine season and hemisphere based on latitude and month."""
    hemisphere = "Northern" if latitude >= 0 else "Southern"
    
    # Seasons are opposite in Northern/Southern hemispheres
    if hemisphere == "Northern":
        if month in [12, 1, 2]:
            season = "Winter"
        elif month in [3, 4, 5]:
            season = "Spring"
        elif month in [6, 7, 8]:
            season = "Summer"
        else:  # 9, 10, 11
            season = "Autumn"
    else:  # Southern hemisphere
        if month in [12, 1, 2]:
            season = "Summer"
        elif month in [3, 4, 5]:
            season = "Autumn"
        elif month in [6, 7, 8]:
            season = "Winter"
        else:  # 9, 10, 11
            season = "Spring"
    
    return season, hemisphere


def get_constellation_data() -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """Get constellation visibility data by hemisphere and season."""
    return {
        "Northern": {
            "Winter": [
                {"name": "Orion", "description": "The Hunter - prominent with bright stars Betelgeuse and Rigel"},
                {"name": "Gemini", "description": "The Twins - marked by bright stars Castor and Pollux"},
                {"name": "Taurus", "description": "The Bull - contains the Pleiades star cluster"},
                {"name": "Canis Major", "description": "The Great Dog - contains Sirius, the brightest star"},
            ],
            "Spring": [
                {"name": "Leo", "description": "The Lion - distinctive backwards question mark shape"},
                {"name": "Virgo", "description": "The Maiden - contains bright star Spica"},
                {"name": "Boötes", "description": "The Herdsman - contains bright orange star Arcturus"},
                {"name": "Ursa Major", "description": "The Great Bear - contains the Big Dipper asterism"},
            ],
            "Summer": [
                {"name": "Cygnus", "description": "The Swan - flies along the Milky Way"},
                {"name": "Lyra", "description": "The Harp - contains brilliant blue-white star Vega"},
                {"name": "Aquila", "description": "The Eagle - contains bright star Altair"},
                {"name": "Scorpius", "description": "The Scorpion - distinctive curved tail"},
            ],
            "Autumn": [
                {"name": "Pegasus", "description": "The Winged Horse - marked by the Great Square"},
                {"name": "Andromeda", "description": "The Princess - contains the Andromeda Galaxy"},
                {"name": "Cassiopeia", "description": "The Queen - distinctive W-shaped pattern"},
                {"name": "Perseus", "description": "The Hero - site of meteor showers"},
            ]
        },
        "Southern": {
            "Summer": [  # Dec-Feb in Southern hemisphere
                {"name": "Orion", "description": "The Hunter - appears upside down from Northern view"},
                {"name": "Carina", "description": "The Keel - contains brilliant star Canopus"},
                {"name": "Centaurus", "description": "The Centaur - contains Alpha Centauri, nearest star system"},
                {"name": "Crux", "description": "The Southern Cross - iconic southern constellation"},
            ],
            "Autumn": [  # Mar-May in Southern hemisphere
                {"name": "Leo", "description": "The Lion - visible but appears inverted"},
                {"name": "Hydra", "description": "The Water Snake - largest constellation"},
                {"name": "Corvus", "description": "The Crow - small distinctive quadrilateral"},
                {"name": "Virgo", "description": "The Maiden - contains bright star Spica"},
            ],
            "Winter": [  # Jun-Aug in Southern hemisphere
                {"name": "Scorpius", "description": "The Scorpion - overhead in southern winter"},
                {"name": "Sagittarius", "description": "The Archer - points toward galactic center"},
                {"name": "Lupus", "description": "The Wolf - rich in star clusters"},
                {"name": "Libra", "description": "The Scales - between Virgo and Scorpius"},
            ],
            "Spring": [  # Sep-Nov in Southern hemisphere
                {"name": "Pegasus", "description": "The Winged Horse - visible but low on horizon"},
                {"name": "Grus", "description": "The Crane - distinctive southern constellation"},
                {"name": "Piscis Austrinus", "description": "The Southern Fish - contains bright star Fomalhaut"},
                {"name": "Phoenix", "description": "The Phoenix - faint southern constellation"},
            ]
        }
    }


def get_visible_constellations(latitude: float, current_time: datetime.datetime) -> List[Dict[str, Any]]:
    """Get list of currently visible constellations based on location and time."""
    season, hemisphere = get_season_and_hemisphere(latitude, current_time.month)
    constellation_data = get_constellation_data()
    
    try:
        return constellation_data[hemisphere][season]
    except KeyError:
        # Fallback to Northern Winter if something goes wrong
        return constellation_data["Northern"]["Winter"]


def format_constellation_display(constellations: List[Dict[str, Any]], season: str, hemisphere: str) -> str:
    """Format constellation information for display."""
    if not constellations:
        return "No constellation data available"
    
    # Pick the first constellation as featured
    featured = constellations[0]
    
    # Create display text
    title = f"Tonight's Sky\n{hemisphere} {season}"
    featured_text = f"\nFeatured: {featured['name']}\n{featured['description']}"
    
    # Add other visible constellations
    if len(constellations) > 1:
        others = [c['name'] for c in constellations[1:]]
        others_text = f"\n\nAlso visible: {', '.join(others)}"
    else:
        others_text = ""
    
    return f"{title}{featured_text}{others_text}"


def run(stop_event, api):
    cfg = api.get_app_config() or {}
    
    # Use global location if available, otherwise fall back to config
    global_loc = api.get_global_location() if hasattr(api, "get_global_location") else {}
    if global_loc and global_loc.get("latitude") is not None:
        try:
            latitude = float(global_loc.get("latitude"))  # type: ignore[arg-type]
            api.log_info(f"Using global location: latitude {latitude}")
        except Exception:
            # Fallback to app config
            latitude = float(cfg.get("latitude", 51.5074))  # Default to London
            api.log_info(f"Global location failed, using app config: latitude {latitude}")
    else:
        latitude = float(cfg.get("latitude", 51.5074))  # Default to London
        api.log_info(f"No global location, using app config: latitude {latitude}")
    
    api.screen.clear_screen()
    
    try:
        # Get current time and determine visible constellations
        current_time = datetime.datetime.now()
        season, hemisphere = get_season_and_hemisphere(latitude, current_time.month)
        visible_constellations = get_visible_constellations(latitude, current_time)
        
        # Format and display constellation information
        display_text = format_constellation_display(visible_constellations, season, hemisphere)
        api.screen.display_text(display_text, align="left")
        
        api.log_info(f"Displaying constellations for {hemisphere} {season}")
        
    except Exception as e:
        api.log_error(f"Error getting constellation data: {e}")
        # Fallback to original message
        fallback_message = cfg.get("message", "Orion visible tonight! (fallback)")
        api.screen.display_text(f"Constellation\n\n{fallback_message}", align="left")

    # Simple idle loop until stopped
    while not stop_event.is_set():
        time.sleep(0.5)

    api.screen.clear_screen()
