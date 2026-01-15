import random
import time
from datetime import datetime

def generate_latency():
    return random.uniform(20, 50)

if __name__ == "__main__":
    with open("data/latency.log", "w") as f:
        for i in range(10):
            latency = generate_latency()
            timestamp = datetime.now().isoformat()
            line = f"{timestamp}, latency={latency:.2f}ms\n"
            print(line.strip())
            f.write(line)
            time.sleep(1)
