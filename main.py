import asyncio
import os
import json
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = 2040
API_HASH = 'b18441a1ff607e10a989891a5462e627'
SESSION = os.environ.get('SESSION', '')
SOURCE_CHANNEL = os.environ.get('SOURCE_CHANNEL', '')
DEST_CHANNEL = os.environ.get('DEST_CHANNEL', '')
PROGRESS_FILE = 'progress.json'

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'done': []}

def save_progress(done_ids):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({'done': done_ids}, f)

async def main():
    print(f"SOURCE: {SOURCE_CHANNEL}")
    print(f"DEST: {DEST_CHANNEL}")
    print(f"SESSION length: {len(SESSION)}")

    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH,
        connection_retries=99, retry_delay=10, auto_reconnect=True)
    await client.connect()
    print("Connected!")

    source = await client.get_entity(int(SOURCE_CHANNEL))
    dest = await client.get_entity(DEST_CHANNEL)
    print("Entities found!")

    progress = load_progress()
    done_ids = progress['done']
    count = len(done_ids)

    async for message in client.iter_messages(source, reverse=True):
        if not message.document:
            continue
        if message.id in done_ids:
            print(f"[SKIP] ID {message.id}")
            continue
        temp_file = None
        for attempt in range(3):
            try:
                temp_file = await client.download_media(message, file='/tmp/')
                await client.send_file(dest, temp_file)
                count += 1
                done_ids.append(message.id)
                save_progress(done_ids)
                print(f"[{count}] Done - ID {message.id}")
                break
            except Exception as e:
                print(f"[RETRY {attempt+1}/3] {e}")
                await asyncio.sleep(5)
            finally:
                if temp_file and os.path.exists(temp_file):
                    os.remove(temp_file)

    print(f"Done! {count} files transferred.")
    await client.disconnect()

asyncio.run(main())
