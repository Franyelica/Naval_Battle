import socket
import threading
from enum import Enum
from typing import Dict, List, Tuple, Set

class GameState(Enum):
    """FSM STATES FOR THE NAVAL BATTLE"""

    INITIAL = "q0"
    FLEET_INTACT = "q1"
    HIT = "q2"
    SUNK = "q3"
    DEFEAT = "q4"

class Ship:
    """Represents a ship with its positions and hit status"""

    def __init__(self, name: str, positions: List[str]):
        self.name = name
        self.positions = set(positions)
        self.hits = set()
        self.is_sunk = False

    def hit(self, position: str) -> bool:
        """Hit the ship at position. Return true if hit is valid"""

        if position in self.positions and position not in self.hits:
            self.hits.add(position)
            if len(self.hits) == len(self.positions):
                self.is_sunk = True
            return True
        return False
    
    def is_position_ship(self, position: str) -> bool:
        """Check if position belongs to this ship"""

        return position in self.positions
    
    def is_position_already_hit(self, position: str) -> bool:
        """check if positions was already hit"""

        return position in self.hits
    

class NavalBattleFSM:
    """Finite State Machine for Naval Battle Defense"""

    def __init__(self, game_id: str = "default"):
        self.game_id = game_id
        self.current_state = GameState.INITIAL
        self.ships: List[Ship] = []
        self.all_attacks: Set[str] = set()

    def setup_fleet(self):
        """Setup the fleet with ships"""
        print("🛠 Configuración inicial para Game ID: {self.game_id}")
        
        
        print("Coloque su flota: ")

        #Battleship (3 positions)
        while True:
            try:
                battleship_pos = input("-> Battleship (3 casillas, ej: E3 E4 E5): ").strip().upper().split()
                if len(battleship_pos) == 3 and all(self._is_valid_position(pos) for pos in battleship_pos):
                    self.ships.append(Ship("Battleship", battleship_pos))
                    break
                else:
                    print("Error: Ingrese exactamente 3 posiciones validas")
            except:
                print("Error en el formato. Intente nuevamente.")

        
        #Submarine (2 positions)
        while True:
            try:
                submarine_pos = input(" -> Submarine (2 casillas, ej: B2 C2): ").strip().upper().split()
                if len(submarine_pos) == 2 and all(self._is_valid_position(pos) for pos in submarine_pos):
                    if not any(pos in self.ships[0].positions for pos in submarine_pos):
                        self.ships.append(Ship("Submarine", submarine_pos))
                        break
                    else:
                        print("Error: Posicion ya ocupada por otro barco")
                else:
                    print("Error: Ingrese exactamente 2 posiciones validas")
            except:
                print("Error en el formato. Intente nuevamente")
        

        #Destroyer 1 position
        while True:
            try:
                destroyer_pos = input(" -> Destroyer (1 casilla, ej: E5): ").strip().upper().split()
                if len(destroyer_pos) == 1 and self._is_valid_position(destroyer_pos[0]):
                    if not any(destroyer_pos[0] in ship.positions for ship in self.ships):
                        self.ships.append(Ship("Destroyer", destroyer_pos))
                        break
                    else:
                        print("Error: Posición ya ocupada por otro barco")
                else:
                    print("Error: INgrese exactamente 1 posicion valida")
            except:
                print("Error en el formato. Intente nuevamente.")

        self.current_state = GameState.FLEET_INTACT
        print("Flota colocada correctamente para Game ID: {self.game_id}")
        self._display_fleet()

    def _is_valid_position(self, position: str) -> bool:
        """Validate if position is within grid bounds"""
        if len(position) != 2:
            return False
        row = position[0]
        col = position[1]
        return row in 'ABCDE' and col in '12345'
    
    def _display_fleet(self):
        """Display current fleet status"""
        print("\n🚢 Estado de la flota (Game ID: {self.game_id})")
        for ship in self.ships:
            status = "HUNDIDO" if ship.is_sunk else f"INTACTO ({len(ship.hits)}/{len(ship.positions)} impactos)"
            print(f" {ship.name}: {' '.join(ship.positions)}-{status}")
        print()

    def process_attack(self, position: str) -> str:
        """process an attack and return response code"""
        position = position.strip().upper()

        #Validate position format
        if not self._is_valid_position(position):
            return "404-failed"

        #check if position was already attacked
        if position in self.all_attacks:
            return "404-failed"

        #add to attack history
        self.all_attacks.add(position)

        #check if position hits any ship
        hit_ship = None
        for ship in self.ships:
            if ship.is_position_ship(position):
                hit_ship = ship
                break

        if hit_ship is None:
            #Miss-water
            return "404-failed"  
        
        #Hit the ship
        if hit_ship.hit(position):
            #update fsm state
            self._update_state()

            if hit_ship.is_sunk:
                if self.current_state == GameState.DEFEAT:
                    return "500-sunken" #Last ship sunk
                else:
                    return "200-sunken" #ship sunk but game continues
            else:
                return "202-shocked" #ship hit but not sunk
        
        return "404-failed" #position already hit
    
    def _update_state(self):
        """Update FSM state based on fleet condition"""
        sunk_ships = sum(1 for ship in self.ships if ship.is_sunk)
        hit_ships = sum(1 for ship in self.ships if len(ship.hits) > 0 and not ship.is_sunk)

        if sunk_ships == len(self.ships):
            self.current_state = GameState.DEFEAT
        elif sunk_ships > 0:
            self.current_state = GameState.SUNK
        elif hit_ships > 0:
            self.current_state = GameState.HIT
        else:
            self.current_state = GameState.FLEET_INTACT

    def is_game_over(self) -> bool:
        """check if game is over"""
        return self.current_state == GameState.DEFEAT
    
class DefenseServer:
    """TCP Server for handling attacks"""

    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.games: Dict[str, NavalBattleFSM] = {}
        self.socket = None
        self.default_game_id = "default"
    
    def start(self):
        """Start the defense server"""
        print("╔══════════════════════════════════════════╗")
        print("║         [ SERVIDOR DE DEFENSA - FSM ]     ║")
        print("╚══════════════════════════════════════════╝")

        # Get game ID for this server instance
        game_id = input(f"Ingrese Game ID (Enter para '{self.default_game_id}'): ").strip()
        if not game_id:
            game_id = self.default_game_id

        #setup fleet
        fsm = NavalBattleFSM(game_id)
        fsm.setup_fleet()
        self.games[game_id] = fsm

        print(f"\n🎮 Juego registrado con Game ID: '{game_id}'")
        print(f"🎯 Los ataques deben incluir este Game ID para ser procesados")

        #start server
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)

            #Display server information
            print(f"🌐 Servidor iniciado:")
            print(f"   Host: {self.host}")
            print(f"   Puerto: {self.port}")
            print(f"   Game ID activo: {game_id}")

            if self.host == 'localhost':
                print(f"   IP Local: 127.0.0.1")
                try:
                    import socket as sock
                    hostname = sock.gethostname()
                    local_ip = sock.gethostbyname(hostname)
                    print(f"   IP Red: {local_ip}")
                except:
                    pass

            print(f"Esperando ataques en {self.host}:{self.port}...")
            print("───────────────────────────────────────────")

            # Keep server running until all games are over
            while any(not game.is_game_over() for game in self.games.values()):
                try:
                    client_socket, addr = self.socket.accept()
                    thread = threading.Thread(target=self._handle_attack, args=(client_socket, addr))
                    thread.start()
                except socket.error:
                    break
            
            print("🏁 Todos los juegos han terminado.")
            
        except Exception as e:
            print(f"Error del servidor: {e}")
        finally:
            if self.socket:
                self.socket.close()

    def _handle_attack(self, client_socket, addr):
        """Handle individual attack from client"""
        try:
                #receive attack
                data = client_socket.recv(1024).decode('utf-8').strip()
                if not data:
                    return
            
                print(f"ataque recibido de {addr}: {data}")

                # Parse attack data (expecting format: "GAME_ID:POSITION" or just "POSITION")
                if ':' in data:
                    game_id, position = data.split(':', 1)
                else:
                    # Use default game if no game_id specified
                    position = data
                    game_id = self.default_game_id

                # Check if game exists
                if game_id not in self.games:
                    response = f"ERROR: Game ID '{game_id}' not found"
                    client_socket.send(response.encode('utf-8'))
                    print(f"❌ {response}")
                    return

                # Get the appropriate game FSM
                fsm = self.games[game_id]

                # Check if game is already over
                if fsm.is_game_over():
                    response = "ERROR: Game already over"
                    client_socket.send(response.encode('utf-8'))
                    print(f"❌ {response}")
                    return
                
                # Process attack with FSM
                response = fsm.process_attack(position)

                # Send response
                client_socket.send(response.encode('utf-8'))

                # Display response
                result_msg = {
                    "404-failed": "404-failed (Agua)",
                    "202-shocked": "202-shocked (¡Impacto!)",
                    "200-sunken": "200-sunken (¡Barco hundido!)",
                    "500-sunken": "500-sunken (¡Último barco hundido!)"
                }

                print(f"📤 Resultado para Game ID '{game_id}': {result_msg.get(response, response)}")

                if response == "500-sunken":
                    print(f"🏴 Juego '{game_id}': Toda la flota ha sido destruida. Fin del juego.") 
                    self._display_final_state(game_id)

                fsm._display_fleet()
        
        except Exception as e:
            print(f"Error manejando ataque: {e}")
            try:
                error_response = f"ERROR: {str(e)}"
                client_socket.send(error_response.encode('utf-8'))
            except:
                pass
        finally:
            client_socket.close()
    
    def _display_final_state(self, game_id: str):
        """Display final game state"""
        if game_id in self.games:
            fsm = self.games[game_id]
            print(f"\n🎯 Resumen final de ataques para Game ID '{game_id}':")
            for attack in sorted(fsm.all_attacks):
                print(f"    {attack}")
            print()

    def add_game(self, game_id: str, ships_data: Dict = None):
        """Add a new game programmatically (for API integration)"""
        if game_id in self.games:
            return False
        
        fsm = NavalBattleFSM(game_id)
        
        if ships_data:
            # Setup fleet programmatically
            fsm.ships = [
                Ship("Battleship", ships_data.get("battleship", [])),
                Ship("Submarine", ships_data.get("submarine", [])),
                Ship("Destroyer", ships_data.get("destroyer", []))
            ]
            fsm.current_state = GameState.FLEET_INTACT
        
        self.games[game_id] = fsm
        print(f"🎮 Nuevo juego añadido: Game ID '{game_id}'")
        return True
    
    def get_game_status(self, game_id: str):
        """Get status of a specific game"""
        if game_id not in self.games:
            return None
        
        fsm = self.games[game_id]
        return {
            "game_id": game_id,
            "state": fsm.current_state.value,
            "ships": [
                {
                    "name": ship.name,
                    "positions": list(ship.positions),
                    "hits": list(ship.hits),
                    "is_sunk": ship.is_sunk
                }
                for ship in fsm.ships
            ],
            "total_attacks": len(fsm.all_attacks),
            "is_game_over": fsm.is_game_over()
        }

def main():
    try:
        #get server configuration
        host = input("Ingrese la IP del servidor (Enter para el localhost): ").strip()
        if not host:
            host = 'localhost'

        port_input = input("Ingrese el puerto (Enter para 5000): ").strip()
        port = int(port_input) if port_input else 5000

        #start server
        server = DefenseServer(host, port)
        server.start()

    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()