import random
import pandas as pd
from datetime import datetime, timezone
from skyfield.api import Topos, load, EarthSatellite

# Satellite catalog (NORAD IDs) — organized by category
SATELLITE_CATALOG = {
    # ── Space Station ──
    "ISS (ZARYA)": "25544",
    "TIANGONG": "48274",
    # ── Weather Satellites ──
    "NOAA 15": "25338",
    "NOAA 18": "28654",
    "NOAA 19": "33591",
    "NOAA 20 (JPSS-1)": "43013",
    "METOP-A": "29499",
    "METOP-B": "38771",
    "METOP-C": "43689",
    "SUOMI NPP": "37849",
    "GOES 16": "41866",
    "GOES 18": "51850",
    "HIMAWARI-8": "40267",
    "FY-3D": "43010",
    # ── Earth Observation ──
    "LANDSAT 8": "39084",
    "LANDSAT 9": "49260",
    "SENTINEL-1A": "39634",
    "SENTINEL-2A": "40697",
    "SENTINEL-2B": "42063",
    "SENTINEL-3A": "41335",
    "TERRA (EOS AM-1)": "25994",
    "AQUA (EOS PM-1)": "27424",
    "AURA": "28376",
    # ── Communication ──
    "IRIDIUM 180": "56730",
    # ── Navigation ──
    "GPS BIIR-2 (PRN 13)": "24876",
    "BEIDOU-3 M1": "43001",
    # ── Science ──
    "HUBBLE": "20580",
    "CALIPSO": "29108",
    "CLOUDSAT": "29107",
    "ICESat-2": "43613",
    # ── Military/Surveillance ──
    "USA 326 (NROL-82)": "48859",
}

# ── Built-in TLE cache (updated 2026-03-11) ─────────────────────────────────
# Used as fallback when CelesTrak is unreachable (e.g. Streamlit Cloud)
_TLE_FALLBACK = {
    "25544": ["1 25544U 98067A   26070.19118651  .00009215  00000+0  17770-3 0  9998",
              "2 25544  51.6325  64.9326 0007932 179.9008 180.1983 15.48575655556567"],
    "48274": ["1 48274U 21035A   26070.12336260  .00029353  00000+0  34529-3 0  9991",
              "2 48274  41.4661 199.4375 0006951 281.6206  78.3852 15.60746125277830"],
    "25338": ["1 25338U 98030A   26070.17103473  .00000167  00000+0  85874-4 0  9991",
              "2 25338  98.5162  93.4137 0009056 275.1809  84.8338 14.27113198447313"],
    "28654": ["1 28654U 05018A   26070.16963991  .00000058  00000+0  53546-4 0  9997",
              "2 28654  98.8154 151.2561 0015262  71.5591 288.7239 14.13711269 72460"],
    "33591": ["1 33591U 09005A   26070.15108813  .00000036  00000+0  43213-4 0  9992",
              "2 33591  98.9604 140.9245 0012841 310.2633  49.7416 14.13457060880635"],
    "43013": ["1 43013U 17073A   26070.16761345  .00000125  00000+0  80043-4 0  9993",
              "2 43013  98.7692  10.5401 0001290 135.5989 224.5291 14.19536621430568"],
    "29499": ["1 29499U 06044A   26069.94781052  .00002000  00000+0  23589-3 0  9997",
              "2 29499  98.3242 173.6474 0175317  22.9831  36.8767 14.75584590 10965"],
    "38771": ["1 38771U 12049A   26070.13439739  .00000125  00000+0  77063-4 0  9990",
              "2 38771  98.6639 123.5339 0001225 257.5990 102.5050 14.21445223699333"],
    "43689": ["1 43689U 18087A   26070.15872454  .00000121  00000+0  74970-4 0  9999",
              "2 43689  98.6762 131.5067 0002178  97.9023 262.2401 14.21497488380906"],
    "37849": ["1 37849U 11061A   26070.15293174  .00000127  00000+0  81445-4 0  9992",
              "2 37849  98.7870  11.7440 0000519 218.4417 141.6722 14.19544084744537"],
    "41866": ["1 41866U 16071A   26070.20461681 -.00000090  00000+0  00000+0 0  9991",
              "2 41866   0.1306  87.8283 0002216 228.5280 181.4670  1.00272569 34120"],
    "51850": ["1 51850U 22021A   26070.16572359  .00000098  00000+0  00000+0 0  9994",
              "2 51850   0.0315  51.8923 0000788   5.2131  34.3629  1.00271827  5610"],
    "40267": ["1 40267U 14060A   26070.20530921 -.00000274  00000+0  00000+0 0  9999",
              "2 40267   0.0147 185.7741 0000338 139.9259  57.7485  1.00272928 41774"],
    "43010": ["1 43010U 17072A   26070.18662374  .00000574  00000+0  29320-3 0  9991",
              "2 43010  99.0038  42.8898 0001518   9.9348 350.1857 14.19717058431084"],
    "39084": ["1 39084U 13008A   26070.17109410  .00000448  00000+0  10944-3 0  9990",
              "2 39084  98.1916 141.8725 0001193  91.6620 268.4715 14.57132555683622"],
    "49260": ["1 49260U 21088A   26070.20558234  .00000473  00000+0  11498-3 0  9993",
              "2 49260  98.1937 141.9674 0001077  93.5957 266.5365 14.57126960236730"],
    "39634": ["1 39634U 14016A   26070.17323434  .00000232  00000+0  58919-4 0  9991",
              "2 39634  98.1824  79.1227 0001342  83.2427 276.8925 14.59198956635722"],
    "40697": ["1 40697U 15028A   26056.18000490  .00000159  00000+0  76852-4 0  9999",
              "2 40697  98.5024 132.8928 0054368 194.7437 165.2162 14.30192923557712"],
    "42063": ["1 42063U 17013A   26070.16552722  .00000166  00000+0  79995-4 0  9997",
              "2 42063  98.5648 146.3377 0001133  95.5913 264.5399 14.30821011470626"],
    "41335": ["1 41335U 16011A   26070.17492777  .00000136  00000+0  74110-4 0  9990",
              "2 41335  98.6226 138.9399 0001238  98.7741 261.3579 14.26742226524081"],
    "25994": ["1 25994U 99068A   26070.14568253  .00000517  00000+0  11451-3 0  9997",
              "2 25994  97.9591 123.5248 0002790 148.1025 232.1613 14.61016433395290"],
    "27424": ["1 27424U 02022A   26070.18931897  .00001285  00000+0  26618-3 0  9997",
              "2 27424  98.4177  37.5815 0000561  86.3395 329.8412 14.61981074268952"],
    "28376": ["1 28376U 04026A   26070.13508721  .00001271  00000+0  26797-3 0  9994",
              "2 28376  98.3312  25.8473 0001045  86.3975 273.7345 14.61153138151899"],
    "56730": ["1 56730U 23068W   26069.94595919  .00000631  00000+0  79590-4 0  9997",
              "2 56730  86.6720  75.1072 0002346  95.6178 264.5311 14.80239843151837"],
    "24876": ["1 24876U 97035A   26069.98141493  .00000004  00000+0  00000+0 0  9995",
              "2 24876  55.9392 102.4136 0098106  56.2204 304.7730  2.00564057209983"],
    "43001": ["1 43001U 17069A   26069.87017477 -.00000009  00000+0  00000+0 0  9993",
              "2 43001  56.6072  66.3209 0012507 309.5882  50.3185  1.86231512 56778"],
    "20580": ["1 20580U 90037B   26070.18250526  .00008894  00000+0  29415-3 0  9990",
              "2 20580  28.4721  29.8149 0001855 140.1494 219.9238 15.29510230773544"],
    "29108": ["1 29108U 06016B   26070.16172726  .00001434  00000+0  25283-3 0  9994",
              "2 29108  98.4531  82.4719 0001020 108.4401 251.6914 14.69141288 58661"],
    "29107": ["1 29107U 06016A   26070.19546944  .00001444  00000+0  17142-3 0  9999",
              "2 29107  98.4052 102.0114 0004051 295.0891  64.9902 14.86176667 59952"],
    "43613": ["1 43613U 18070A   26070.13288338  .00003665  00000+0  13278-3 0  9997",
              "2 43613  91.9993 264.5568 0003928 122.1998 237.9632 15.28337850417487"],
    "48859": ["1 48859U 21054A   26070.05044681 -.00000094  00000+0  00000+0 0  9991",
              "2 48859  55.2181 336.4073 0023788 231.8324 314.0720  2.00575429 34788"],
}


def fetch_tle(sat_name: str, norad_id: str):
    """Fetch TLE for a satellite — tries online first, falls back to built-in cache."""
    import urllib.request
    import ssl
    ts = load.timescale()
    urls = [
        f"https://celestrak.org/NORAD/elements/gp.php?CATNR={norad_id}&FORMAT=TLE",
        f"https://celestrak.com/NORAD/elements/gp.php?CATNR={norad_id}&FORMAT=TLE",
    ]

    # Method 1: Direct HTTP download
    for url in urls:
        try:
            ctx = ssl.create_default_context()
            req = urllib.request.Request(url, headers={"User-Agent": "SatTelemetry/1.0"})
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                text = resp.read().decode("utf-8").strip()
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            if len(lines) >= 3:
                sat = EarthSatellite(lines[1], lines[2], lines[0], ts)
                if str(sat.model.satnum) == norad_id:
                    return sat
            elif len(lines) == 2:
                sat = EarthSatellite(lines[0], lines[1], sat_name, ts)
                if str(sat.model.satnum) == norad_id:
                    return sat
        except Exception as e:
            print(f"Online TLE fetch failed ({url}): {e}")
            continue

    # Method 2: Built-in TLE fallback cache (always works)
    if norad_id in _TLE_FALLBACK:
        try:
            line1, line2 = _TLE_FALLBACK[norad_id]
            sat = EarthSatellite(line1, line2, sat_name, ts)
            print(f"Using built-in TLE cache for {sat_name}")
            return sat
        except Exception as e:
            print(f"Fallback TLE failed for {sat_name}: {e}")

    return None

def compute_position(satellite: EarthSatellite, dt: datetime = None):
    """Compute satellite position (lat, lon, alt) at a given datetime."""
    ts = load.timescale()
    if dt is None:
        t = ts.now()
    else:
        # Ensure dt is timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        t = ts.from_datetime(dt)

    geocentric = satellite.at(t)
    subpoint = geocentric.subpoint()
    
    return {
        "lat": subpoint.latitude.degrees,
        "lon": subpoint.longitude.degrees,
        "alt_km": subpoint.elevation.km,
        "velocity_km_s": geocentric.velocity.km_per_s, # Vector
        "epoch": satellite.epoch.utc_jpl(),
    }

def build_telemetry_40ch(sat_name: str, satellite: EarthSatellite, dt: datetime = None) -> pd.DataFrame:
    """
    Build a 40-channel telemetry matrix matching Figure 3.
    """
    pos = compute_position(satellite, dt)
    velocity_mag = sum(v**2 for v in pos["velocity_km_s"])**0.5
    
    # Extract orbital elements if available (simplified or from satellite model)
    elements = satellite.model
    
    # 40 Channels mapping inspired by Figure 3 and user prompt
    data = [
        ("LATITUDE", f"{pos['lat']:.6f}", "deg N"),
        ("LONGITUDE", f"{pos['lon']:.6f}", "deg E"),
        ("ALTITUDE", f"{pos['alt_km']:.4f}", "km"),
        ("VELOCITY", f"{velocity_mag:.4f}", "km/s"),
        ("NORAD_ID", str(elements.satnum), "ID"),
        ("INCLINATION", f"{elements.inclo:.4f}", "rad"),
        ("ECCENTRICITY", f"{elements.ecco:.7f}", "e"),
        ("RAAN", f"{elements.nodeo:.4f}", "rad"),
        ("MEAN_MOTION", f"{elements.no_kozai:.8f}", "rad/min"),
        ("BSTAR_DRAG", f"{elements.bstar:.8f}", "1/er"),
        ("ORBIT_PERIOD", f"{2 * 3.14159 / elements.no_kozai:.2f}", "min"),
        ("APOGEE_HT", f"{pos['alt_km'] + random.uniform(5, 15):.2f}", "km"),
        ("PERIGEE_HT", f"{pos['alt_km'] - random.uniform(5, 15):.2f}", "km"),
        ("JDSATEPOCH", f"{elements.jdsatepoch:.4f}", "JD"),
        ("MEAN_ANOMALY", f"{elements.mo:.4f}", "rad"),
        ("ARG_PERIGEE", f"{elements.argpo:.4f}", "rad"),
        ("DOPPLER_SHIFT", f"{random.uniform(-5, 5):.4f}", "kHz"),
        ("SIGNAL_DELAY", f"{random.uniform(0.1, 0.5):.4f}", "ms"),
        ("ATMOS_DENSITY", f"{random.uniform(1e-12, 1e-10):.2e}", "kg/m3"),
        ("SOLAR_PRESSURE", f"{random.uniform(4, 5):.2f}", "uN/m2"),
        ("CPU_LOAD", f"{random.uniform(10, 45):.2f}", "%"),
        ("RAM_RESIDUAL", f"{random.uniform(512, 1024):.1f}", "MB"),
        ("BATT_TEMP", f"{random.uniform(15, 35):.2f}", "C"),
        ("BUS_VOLTAGE", f"{random.uniform(28, 32):.2f}", "V"),
        ("TX_POWER", f"{random.uniform(5, 20):.2f}", "W"),
        ("RX_SENSITIVITY", f"{random.uniform(-110, -90):.2f}", "dBm"),
        ("GYRO_DRIFT", f"{random.uniform(0.001, 0.005):.4f}", "deg/h"),
        ("MAGNETIC_FIELD", f"{random.uniform(20, 60):.2f}", "uT"),
        ("SUN_ASPECT", f"{random.uniform(0, 180):.2f}", "deg"),
        ("THERMAL_GRAD", f"{random.uniform(0.1, 0.5):.2f}", "C/m"),
        ("DATA_RATE", f"{random.uniform(1, 10):.2f}", "Mbps"),
        ("BIT_ERROR_RATE", f"{1e-9:.1e}", "BER"),
        ("UPTIME", f"{random.randint(100, 50000):d}", "sec"),
        ("FW_CHECKSUM", hex(random.randint(0, 0xFFFFFFFF)).upper(), "HEX"),
        ("LINK_BUDGET", f"{random.uniform(10, 25):.2f}", "dB"),
        ("ANTENNA_GAIN", f"{random.uniform(12, 15):.2f}", "dBi"),
        ("STAR_TRACKER", "ACTIVE", "Status"),
        ("REACTION_WHEEL", f"{random.randint(2000, 4000):d}", "RPM"),
        ("PROP_RESERVE", f"{random.uniform(85, 95):.2f}", "%"),
        ("MISSION_STATE", "SCIENTIFIC", "Mode"),
    ]
    
    return pd.DataFrame(data, columns=["Parameter", "Value", "Unit"])


def _break_dateline(lats, lons):
    """Insert None at 180 meridian crossings to break the line."""
    if len(lats) < 2:
        return list(lats), list(lons)
    new_lats, new_lons = [lats[0]], [lons[0]]
    for i in range(1, len(lats)):
        if abs(lons[i] - lons[i - 1]) > 180:
            new_lats.append(None)
            new_lons.append(None)
        new_lats.append(lats[i])
        new_lons.append(lons[i])
    return new_lats, new_lons


def compute_ground_track(satellite, minutes_back=45, minutes_forward=45, step_sec=60):
    """Compute orbit ground track (past + future) for map visualization."""
    ts = load.timescale()
    now = ts.now()

    steps_back = int(minutes_back * 60 / step_sec)
    steps_fwd = int(minutes_forward * 60 / step_sec)

    raw_past_lat, raw_past_lon = [], []
    raw_future_lat, raw_future_lon = [], []

    for i in range(-steps_back, steps_fwd + 1):
        t = ts.tt_jd(now.tt + i * step_sec / 86400.0)
        geo = satellite.at(t)
        sub = geo.subpoint()
        lat = sub.latitude.degrees
        lon = sub.longitude.degrees
        if i <= 0:
            raw_past_lat.append(lat)
            raw_past_lon.append(lon)
        if i >= 0:
            raw_future_lat.append(lat)
            raw_future_lon.append(lon)

    past_lats, past_lons = _break_dateline(raw_past_lat, raw_past_lon)
    future_lats, future_lons = _break_dateline(raw_future_lat, raw_future_lon)

    return {
        "past_lats": past_lats,
        "past_lons": past_lons,
        "future_lats": future_lats,
        "future_lons": future_lons,
    }
