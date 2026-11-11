import os
import asyncio
import websockets

# Key: room_id, Value: {"sender": ws, "receiver": ws}
ROOMS = {}

async def handler(websocket):
    try:
        role_info = await websocket.recv()
        if not isinstance(role_info, str):
            await websocket.close()
            return

        parts = role_info.split(":")
        if len(parts) != 3 or parts[0] != "JOIN":
            await websocket.close()
            return

        _, room_id, role = parts
        if room_id not in ROOMS:
            ROOMS[room_id] = {"sender": None, "receiver": None}

        ROOMS[room_id][role] = websocket
        print(f"[+] {role.capitalize()} connected to room '{room_id}'", flush=True)

        async for message in websocket:
            target_role = "receiver" if role == "sender" else "sender"
            target_ws = ROOMS[room_id].get(target_role)
            
            # Send directly without checking .open (compatible with websockets v14+)
            if target_ws is not None:
                try:
                    await target_ws.send(message)
                except websockets.exceptions.ConnectionClosed:
                    ROOMS[room_id][target_role] = None

    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"[!] Relay error: {e}", flush=True)
    finally:
        if 'room_id' in locals() and 'role' in locals():
            print(f"[-] {role.capitalize()} disconnected from '{room_id}'", flush=True)
            if ROOMS.get(room_id, {}).get(role) == websocket:
                ROOMS[room_id][role] = None

async def main():
    # Render assigns a dynamic port via the PORT environment variable
    port = int(os.environ.get("PORT", 8765))
    async with websockets.serve(
        handler,
        "0.0.0.0",
        port,
        max_size=10_000_000,
        ping_interval=20,
        ping_timeout=20
    ):
        print(f"[*] Relay server listening on port {port}", flush=True)
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
