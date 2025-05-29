from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
import json
from enum import Enum
import requests

from DefenseServer import NavalBattleFSM, GameState, Ship
from AttackClient import AttackClientFSM, AttackBoard

app = FastAPI(title="Naval Battle API", version="1.0.0")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API requests/responses
class FleetSetup(BaseModel):
    battleship: List[str]
    submarine: List[str]
    destroyer: List[str]
    game_id: str

class AttackRequest(BaseModel):
    position: str

class AttackResponse(BaseModel):
    position: str
    result: str
    hit: bool
    sunk: bool
    game_over: bool
    message: str

class GameStatus(BaseModel):
    state: str
    ships_status: List[Dict]
    total_attacks: int
    grid: Dict[str, str]

class AttackStatus(BaseModel):
    total_attacks: int
    hits: int
    misses: int
    sunk_ships: int
    accuracy: float
    game_won: bool
    grid: Dict[str, str]

# Global game instances (in production, use proper state management)
defense_games: Dict[str, NavalBattleFSM] = {}
attack_games: Dict[str, AttackClientFSM] = {}

# Defense API endpoints
@app.post("/api/defense/setup")
async def setup_defense_fleet(fleet: FleetSetup):
    game_id = fleet.game_id
    print(f"[SETUP] Recibido fleet setup para game_id = {game_id}")
    """Setup defense fleet"""
    try:
        fsm = NavalBattleFSM()
        
        # Validate positions
        all_positions = fleet.battleship + fleet.submarine + fleet.destroyer
        if len(set(all_positions)) != len(all_positions):
            raise HTTPException(status_code=400, detail="Overlapping ship positions")
        
        # Create ships
        fsm.ships = [
            Ship("Battleship", fleet.battleship),
            Ship("Submarine", fleet.submarine),
            Ship("Destroyer", fleet.destroyer)
        ]
        fsm.current_state = GameState.FLEET_INTACT
        defense_games[game_id] = fsm
        print(f"[SETUP] Defensa registrada para game_id = {game_id}")
        return {"message": "Fleet setup successful", "game_id": game_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/defense/attack", response_model=AttackResponse)
async def receive_attack(attack: AttackRequest, game_id: str):
    print("✅ Endpoint /api/attack/send fue llamado correctamente")
    """Process incoming attack: ESTO SE ACABA DE CORREGIR (1)"""
    print(f"[ATTACK] Recibido ataque en posición {attack.position} para game_id = {game_id}")


    if game_id not in defense_games:
        print(f"[ERROR] Game {game_id} not found. Available games: {list(defense_games.keys())}")
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")
    """SEGUNDA CORRECCION (2)"""


    fsm = defense_games[game_id]
    result = fsm.process_attack(attack.position)
    
    # Parse result
    hit = "202" in result or "200" in result or "500" in result
    sunk = "200" in result or "500" in result
    game_over = "500" in result
    
    messages = {
        "404-failed": "Miss - Water!",
        "202-shocked": "Hit!",
        "200-sunken": "Ship Sunk!",
        "500-sunken": "Last Ship Sunk - You Lose!"
    }
    
    response = AttackResponse(
        position=attack.position,
        result=result,
        hit=hit,
        sunk=sunk,
        game_over=game_over,
        message=messages.get(result, result)
    )

    """Tercera correccion (3)"""
    print(f"[ATTACK] Respuesta: {response}")
    return response
    

@app.get("/api/defense/status")
#@app.get("/api/defense/status", response_model=GameStatus) ESO SE QUITO
async def get_defense_status(game_id: str = "default"):
    """Get current defense game status"""
    if game_id not in defense_games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    fsm = defense_games[game_id]
    
    ships_status = []
    for ship in fsm.ships:
        ships_status.append({
            "name": ship.name,
            "positions": list(ship.positions),
            "hits": list(ship.hits),
            "is_sunk": ship.is_sunk,
            "hit_count": len(ship.hits),
            "total_positions": len(ship.positions)
        })
    
    # Create grid representation
    grid = {}
    for row in 'ABCDE':
        for col in '12345':
            pos = f"{row}{col}"
            if pos in fsm.all_attacks:
                # Check if it was a hit
                hit_ship = any(ship.is_position_ship(pos) for ship in fsm.ships)
                if hit_ship:
                    sunk_ship = any(ship.is_position_ship(pos) and ship.is_sunk for ship in fsm.ships)
                    grid[pos] = '#' if sunk_ship else 'X'
                else:
                    grid[pos] = 'O'
            else:
                grid[pos] = '~'
    
    return GameStatus(
        state=fsm.current_state.value,
        ships_status=ships_status,
        total_attacks=len(fsm.all_attacks),
        grid=grid
    )

# Attack API endpoints
@app.post("/api/attack/init")
async def init_attack_game(request : Request):
    """Initialize attack game"""
    data = await request.json()
    game_id = data.get("game_id", "default")
    attack_games[game_id] = AttackClientFSM()
    return {"message": "Attack game initialized", "game_id": game_id}

@app.post("/api/attack/send")
async def send_attack(request: Request):
    """Send attack to enemy server"""
    data = await request.json()
    print("[DEBUG] Attack Data:", data)

    position = data.get("position")
    enemy_host = data.get("enemy_host")
    enemy_port = int(data.get("enemy_port"))
    enemy_game_id = data.get("enemy_game_id") #correccion para recibir el game id enemigo
    game_id = data.get("game_id", "default") #game id del atacante

    #se agrega este mensaje
    print(f"[ATTACK] Atacando posición {position} en {enemy_host}:{enemy_port} con enemy_game_id={enemy_game_id}")

    if game_id not in attack_games:
        raise HTTPException(status_code=404, detail="Attack game not found")
    
    print(f"[DEBUG] attack_games: {list(attack_games.keys())}")
    print(f"[DEBUG] Usando game_id atacante: {game_id}")

    fsm = attack_games[game_id]
    
    # Check if position already attacked
    if position in fsm.attack_board.attacks:
        raise HTTPException(status_code=400, detail="Position already attacked")
    

    #nuevo envio de ataque usando request directamente
    try:
        enemy_url = f"http://{enemy_host}:{enemy_port}/api/defense/attack"

        # Enviar ataque al servidor enemigo
        attack_payload = {"position": position}
        params = {"game_id": enemy_game_id}

        print(f"[DEBUG] Enviando POST a {enemy_url} con payload {attack_payload} y params {params}")

        response = requests.post(
            enemy_url,
            json=attack_payload,
            params=params,
            timeout=30
        )

        print(f"[DEBUG] Respuesta HTTP: {response.status_code}")
        print(f"[DEBUG] Contenido respuesta: {response.text}")

        if response.status_code == 200:
            result_data = response.json()
            result_code = result_data.get("result", "unknown")

            # Process result in our FSM
            fsm.process_attack_result(position, result_code)
            print(f"ATAQUE REGISTRADO: {position} → {result_code}")

            return {
                "position": position,
                "response": result_code,
                "result_data": result_data,
                "game_won": fsm.game_won
            }
        else:
            error_msg = f"HTTP {response.status_code}: {response.text}"
            print(f"[ERROR] {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
    
    except requests.exceptions.ConnectionError as e:
        error_msg = f"Connection error: Could not connect to {enemy_host}:{enemy_port}"
        print(f"[ERROR] {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
    except requests.exceptions.Timeout as e:
        error_msg = f"Timeout error: Server {enemy_host}:{enemy_port} did not respond"
        print(f"[ERROR] {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"[ERROR] {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
    

@app.get("/api/attack/status")
#@app.get("/api/attack/status", response_model=AttackStatus) esto se cambio
async def get_attack_status(game_id: str = "default"):
    """Get current attack game status"""
    if game_id not in attack_games:
        raise HTTPException(status_code=404, detail="Attack game not found")
    
    fsm = attack_games[game_id]
    
    accuracy = (fsm.hits / fsm.total_attacks * 100) if fsm.total_attacks > 0 else 0
    
    return AttackStatus(
        total_attacks=fsm.total_attacks,
        hits=fsm.hits,
        misses=fsm.misses,
        sunk_ships=fsm.sunk_ships,
        accuracy=accuracy,
        game_won=fsm.game_won,
        grid=fsm.attack_board.grid
    )
@app.get("/api/debug/defense_games")
async def debug_defense_games():
    #return list(defense_games.keys()) esto se quita y se cambia por:
    return{
        "defense_games": list(defense_games.keys()),
        "attack_games": list(attack_games.keys())
    }
    

# WebSocket for real-time updates
@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    await websocket.accept()
    try:
        while True:
            # Send periodic updates
            if game_id in defense_games:
                status = await get_defense_status(game_id)
                await websocket.send_text(json.dumps(status.model_dump())) #aqui quite status.dict por status.model_dump
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass

@app.get("/")
async def root():
    return {"message": "Naval Battle API is running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)