import time
import requests
import os
import sys
from google.transit import gtfs_realtime_pb2
from sqlalchemy.orm import Session
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from backend.data.database import SessionLocal
from backend.data.realtime_schema import RealtimeUpdate, ServiceAlert

load_dotenv()

MTA_BASE_URL = os.getenv("MTA_BASE_URL", "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2F")
HEADERS = {}

# Feeds to poll
FEEDS = {
    "NUMBERS": "gtfs",
    "ACE": "gtfs-ace",
    "NQRW": "gtfs-nqrw",
    "BDFM": "gtfs-bdfm",
    "L": "gtfs-l",
    "G": "gtfs-g",
    "JZ": "gtfs-jz",
    "SIR": "gtfs-si"
}

def fetch_and_update():
    print("Starting Update Cycle...")
    db = SessionLocal()
    
    try:
        # Clear old updates? 
        # For prototype, truncating is safest to avoid stale ghosts.
        # In production we'd upsert intelligently.
        db.query(RealtimeUpdate).delete()
        db.query(ServiceAlert).delete()
        db.commit()
        
        counts = {"trips": 0, "alerts": 0}

        for name, suffix in FEEDS.items():
            url = f"{MTA_BASE_URL}{suffix}"
            try:
                response = requests.get(url, headers=HEADERS, timeout=10)
                if response.status_code != 200:
                    print(f"Failed {name}: {response.status_code}")
                    continue
                
                feed = gtfs_realtime_pb2.FeedMessage()
                feed.ParseFromString(response.content)
                timestamp = feed.header.timestamp
                
                for entity in feed.entity:
                    # 1. Trip Updates (Arrival Times)
                    if entity.HasField('trip_update'):
                        tu = entity.trip_update
                        trip_id = tu.trip.trip_id
                        route_id = tu.trip.route_id
                        
                        for stu in tu.stop_time_update:
                            if stu.arrival.time > 0: # Only valid times
                                record = RealtimeUpdate(
                                    trip_id=trip_id,
                                    route_id=route_id,
                                    stop_id=stu.stop_id,
                                    arrival_time=stu.arrival.time,
                                    departure_time=stu.departure.time,
                                    last_updated=timestamp
                                )
                                db.add(record)
                                counts['trips'] += 1
                                
                    # 2. Service Alerts
                    if entity.HasField('alert'):
                        al = entity.alert
                        # Extract simple text
                        header = al.header_text.translation[0].text if al.header_text.translation else ""
                        desc = al.description_text.translation[0].text if al.description_text.translation else ""
                        
                        # Entities
                        affected = []
                        for ie in al.informed_entity:
                            if ie.route_id: affected.append(ie.route_id)
                        
                        alert_rec = ServiceAlert(
                            alert_id=entity.id,
                            header_text=header,
                            description_text=desc,
                            affected_entities=",".join(affected),
                            created_at=timestamp
                        )
                        db.add(alert_rec)
                        counts['alerts'] += 1
                        
                db.commit()
                
            except Exception as e:
                print(f"Error processing {name}: {e}")
                db.rollback()
                
        print(f"Cycle Complete. Loaded {counts['trips']} updates and {counts['alerts']} alerts.")
        
    finally:
        db.close()

if __name__ == "__main__":
    while True:
        fetch_and_update()
        print("Sleeping 60s...")
        time.sleep(60)
