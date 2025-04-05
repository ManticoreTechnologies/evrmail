import zmq
import binascii
import time

# === CONFIG ===
ZMQ_URL = "tcp://77.90.40.55:28332"
TOPICS = [b"rawtx", b"rawblock", b"sequence"]  # Add or remove as needed

def main():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.linger = 0  # don't wait on close
    socket.setsockopt(zmq.RCVHWM, 10000)

    # Connect and subscribe to each topic
    socket.connect(ZMQ_URL)
    for topic in TOPICS:
        socket.setsockopt(zmq.SUBSCRIBE, topic)

    print("✅ ZMQ Listener running on:", ZMQ_URL)
    print("🟢 Subscribed to topics:", [t.decode() for t in TOPICS])

    while True:
        try:
            topic, body, seq = socket.recv_multipart()
            print(f"\n📡 Topic: {topic.decode()}")
            print(f"🔢 Seq: {int.from_bytes(seq, 'little')}")
            print(f"📦 Payload (hex, first 100 chars): {binascii.hexlify(body).decode()[:100]}...")
        except KeyboardInterrupt:
            print("🛑 Stopping listener...")
            break
        except Exception as e:
            print("❌ Error:", e)
            time.sleep(1)

if __name__ == "__main__":
    main()
