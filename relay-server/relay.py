import asyncio
import websockets

# Key: room_id, Value: {"sender": ws, "receiver": ws}
ROOMS = {}

async def handler(websocket):
    role_info = await websocket.recv()
    # Format expected: "JOIN:<room_id>:<sender|receiver>"
    parts = role_info.split(":")
    if len(parts) != 3 or parts[0] != "JOIN":
        await websocket.close()
        return

    _, room_id, role = parts
    if room_id not in ROOMS:
        ROOMS[room_id] = {"sender": None, "receiver": None}

    ROOMS[room_id][role] = websocket
    print(f"[+] {role.capitalize()} connected to room '{room_id}'")

    try:
        async for message in websocket:
            target_role = "receiver" if role == "sender" else "sender"
            target_ws = ROOMS[room_id].get(target_role)
            if target_ws and target_ws.open:
                await target_ws.send(message)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        print(f"[-] {role.capitalize()} disconnected from room '{room_id}'")
        if ROOMS.get(room_id, {}).get(role) == websocket:
            ROOMS[room_id][role] = None
        if not ROOMS[room_id]["sender"] and not ROOMS[room_id]["receiver"]:
            ROOMS.pop(room_id, None)

async def main():
    port = 8765
    async with websockets.serve(handler, "0.0.0.0", port):
        print(f"[*] Relay server listening on ws://0.0.0.0:{port}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())