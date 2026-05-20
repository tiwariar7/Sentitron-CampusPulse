import csv
import requests
import time
import uuid

url = "http://localhost:8000/ingestion/mock"

def push_data():
    with open('datasets/campuspulse_stream_dataset.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            if count >= 20: # Push 20 records
                break
            
            # Generate a unique complaint ID by appending a random suffix
            unique_id = f"{row['complaint_id']}-{uuid.uuid4().hex[:4].upper()}"
            
            payload = {
                "complaint_id": unique_id,
                "source": row["source"],
                "department": row["department"],
                "category": row["category"],
                "subcategory": row["subcategory"],
                "complaint_text": row["complaint_text"],
                "sentiment_score": float(row["sentiment_score"]),
                "urgency_level": int(row["urgency_level"]),
                "escalation_flag": row["escalation_flag"].lower() == "true",
                "resolved": row["resolved"].lower() == "true",
                "duplicate_group_id": row["duplicate_group_id"],
                "toxicity_score": float(row["toxicity_score"]),
                "anonymous": row["anonymous"].lower() == "true",
                "response_delay_hours": row["response_delay_hours"]
            }
            
            # Since pydantic schemas expect strings for boolean in my definition:
            payload["escalation_flag"] = str(payload["escalation_flag"]).lower()
            payload["resolved"] = str(payload["resolved"]).lower()
            payload["anonymous"] = str(payload["anonymous"]).lower()
            
            try:
                response = requests.post(url, json=payload)
                print(f"Sent {unique_id} - Status: {response.status_code}")
            except Exception as e:
                print(f"Failed to send: {e}")
                
            time.sleep(1.5) # nice delay so UI shows them coming in one by one
            count += 1

if __name__ == "__main__":
    print("Starting data push in 5 seconds...")
    time.sleep(5)
    push_data()
