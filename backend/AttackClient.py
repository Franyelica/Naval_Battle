import socket
import sys
import requests
from typing import Dict, Set

class AttackBoard:
    """Visual representation of attack results"""
    
    def __init__(self):
        self.grid = {}
        self.attacks = set()


        # Initialize empty grid
        for row in 'ABCDE':
            for col in '12345':
                self.grid[f"{row}{col}"]= '~' #water/unknown

    def update_attack(self, position: str, result: str):
        """Update board with attack result"""
        self.attacks.add(position)

        if "404-failed" in result:
            self.grid[position] = 'O' #miss
        elif "202-shocked" in result:
            self.grid[position] = 'X' #hit
        elif "200-sunken" in result or "500-sunken" in result:
            self.grid[position] = '#' #sunk

    def display(self):
        """Display the attack board"""
        print("\nTablero de ataque 5x5:")
        print("     1 2 3 4 5")
        print("   ┌─────────┐")

        for row in 'ABCDE':
            line = f"{row} | "
            for col in '12345':
                pos = f"{row}{col}"
                line += self.grid[pos] + " "
            line += "|"
            print(line)
            

        print("  └─────────┘")
        print("Legend: ~ = Not attacked, O= Miss, X= Hit, #=Sunk")

class AttackClientFSM:
    """FSM for managinf attack states and strategy"""

    def __init__(self):
        self.attack_board = AttackBoard()
        self.total_attacks = 0
        self.hits = 0
        self.misses = 0
        self.sunk_ships = 0
        self.game_won = False

    def connect_to_server(self, host: str, port: int) -> bool:
        """Test connection to enemy server"""

        try:
            # Test HTTP connection to the API
            test_url = f"http://{host}:{port}/api/health"
            response = requests.get(test_url, timeout=5)

            if response.status_code == 200:
                print(f"✅ Conexión HTTP establecida. Respuesta: {response.json()}")
                return True
            else:
                print(f"⚠️ Servidor responde pero con código: {response.status_code}")
                return False
            
            """test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5)
            test_socket.connect((host, port))


            #send test attack A0 (should return 404 or similar)
            test_socket.send("A0".encode('utf-8'))
            response = test_socket.recv(1024).decode('utf-8')
            test_socket.close()
            
             print(f"✅ Conexión establecida. Respuesta de prueba: {response}")
            return True"""

           
        except requests.exceptions.ConnectionError:
            print(f"❌ No se pudo conectar a http://{host}:{port}")
            return False
        except requests.exceptions.Timeout:
            print(f"❌ Timeout al conectar a http://{host}:{port}")
            return False
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False
        
    
    def send_attack(self, host: str, port: int, position: str, enemy_game_id: str) -> str:
        """Send attack to enemy server"""

        try:
            url=f"http://{host}:{port}/api/defense/attack"
            payload = {"position": position}
            params = {"game_id": enemy_game_id}

            print(f"[DEBUG] Enviando ataque a {url}")
            print(f"[DEBUG] Payload: {payload}")
            print(f"[DEBUG] Params: {params}")

            response = requests.post(url, json=payload, params=params, timeout=10)

            print(f"[DEBUG] Código de respuesta: {response.status_code}")
            print(f"[DEBUG] Respuesta: {response.text}")

            if response.status_code == 200:
                result_data = response.json()
                return result_data.get("result", "unknown")
            else:
                return f"ERROR: HTTP {response.status_code} - {response.text}"
            
        except requests.exceptions.ConnectionError:
            return f"ERROR: No se pudo conectar a {host}:{port}"
        except requests.exceptions.Timeout:
            return f"ERROR: Timeout al conectar a {host}:{port}"
        except Exception as e:
            return f"ERROR: {e}"
        
            #if response.status_code != 200:
               # return f"ERROR: HTTP {response.status_code} - {response.text}"
            
            #result = response.json()
            #return result["result"]
        #except Exception as e:
            #return f"ERROR: {e}"
        
        """try:
            attack_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            attack_socket.settimeout(10)
            attack_socket.connect((host, port))

            #send attack
            attack_socket.send(position.encode('utf-8'))

            #receive response
            response = attack_socket.recv(1024).decode('utf-8')
            attack_socket.close()

            return response.strip()
        
        except Exception as e:
            return f"ERROR: {e}"""
        
    def process_attack_result(self, position: str, response: str):
        """process and update attact result"""

        self.total_attacks += 1

        #update board
        self.attack_board.update_attack(position, response)

        #update statistics

        if "404-failed" in response:
            self.misses += 1
        elif "202-shocked" in response:
            self.hits += 1
        elif "200-sunken" in response:
            self.hits += 1
            self.sunk_ships += 1
        elif "500-sunken" in response:
            self.hits += 1
            self.sunk_ships += 1
            self.game_won = True

    def display_stats(self):
        """Display attack statistics"""
        print(f"\n📊 Estadísticas:")
        print(f"  Total ataques: {self.total_attacks}")
        print(f"  Impactos: {self.hits}")
        print(f"  Fallos: {self.misses}")
        print(f"  Barcos hundidos: {self.sunk_ships}")
        if self.total_attacks > 0:
            accuracy = (self.hits / self.total_attacks) * 100
            print(f"  Precisión: {accuracy:.1f}%")

class AttackClient:
    """Main attack client application"""

    def __init__(self):
        self.fsm = AttackClientFSM()
        self.enemy_host = None
        self.enemy_port = None
    
    def start(self):
        """Start the attack client"""
        print("╔══════════════════════════════════════════╗")
        print("║         [ CLIENTE DE ATAQUE - FSM ]       ║")
        print("╚══════════════════════════════════════════╝") 

        #get enemy server info
        if not self._setup_connection():
            return
        
        print("FSM de ataque iniciado")

        #Main attack loop
        self._attack_loop()


    def _setup_connection(self) -> bool:
        """Setup conecction to enemy server"""
        while True:
            try:
                self.enemy_host = input("Ingrese la IP del enemigo").strip()
                if not self.enemy_host:
                    print("❌ IP requerida")
                    continue

                port_input = input("Ingrese el puerto: (por defecto 8000) ").strip()
                self.enemy_port = int(port_input) if port_input else 8000

                self.enemy_game_id = input("Ingrese el game_id del enemigo (por defecto 'default'): ").strip()
                if not self.enemy_game_id:
                    self.enemy_game_id = "default"

                #test connectionn
                if self.fsm.connect_to_server(self.enemy_host,self.enemy_port):
                    print(f"✅ Conectado a {self.enemy_host}:{self.enemy_port}")
                    print(f"🎯 Game ID enemigo: {self.enemy_game_id}")
                    return True
                else:
                    retry = input("¿Intentar con otra dirección? (s/n): ").strip().lower()
                    if retry != 's':
                        return False
                    
            except ValueError:
                print("❌ Puerto inválido")
            except KeyboardInterrupt:
                print("\n🛑 Cancelado por el usuario")
                return False
            

    def _attack_loop(self):
        """Main attack interaction loop"""
        while not self.fsm.game_won:
            try:
                #Display current board and stats
                self.fsm.attack_board.display()
                self.fsm.display_stats()

                #Get attack position
                position = input("\nIngrese coordenada de ataque (ej: B2) o 'q' para salir: ").strip().upper()

                if position.lower() == 'q':
                    print("🛑 Saliendo del juego...")
                    break

                #Validate position
                if not self._is_valid_position(position):
                    print("❌ Posición inválida. Use formato como A1, B2, etc.")
                    continue

                #check if already attacked
                if position in self.fsm.attack_board.attacks:
                    print("❌ Ya atacaste esa posición. Intenta otra.")
                    continue

                #send attack
                print("🚀 Enviando ataque...")
                response = self.fsm.send_attack(self.enemy_host, self.enemy_port, position, self.enemy_game_id)

                if response.startswith("ERROR"):
                    print(f"❌ {response}")
                    continue

                #process result
                self.fsm.process_attack_result(position, response)

                #display result
                self._display_attack_result(position, response)

                #check for victory
                if self.fsm.game_won:
                    self._display_victory()
                    break
            
            except KeyboardInterrupt:
                print("\n🛑 Juego interrumpido por el usuario")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    
    def _is_valid_position(self, position: str) -> bool:
        """Validate attack position format"""

        if len(position) != 2:
            return False
        row = position[0]
        col = position[1]
        return row in 'ABCDE' and col in '12345'
    
    def _display_attack_result(self, position: str, response: str):
        """Display formatted attack result"""
        result_messages = {
            "404-fallido": f"💧 {response} (Agua)",
            "202-impactado": f"💥 {response} (¡Impacto!)",
            "200-hundido": f"🔥 {response} (¡Barco hundido!)",
            "500-hundido": f"🎆 {response} (¡Último barco hundido!)"
        }

        #find matching response type
        message = response
        for key, formatted_msg in result_messages.items():
            if key in response:
                message = formatted_msg
                break

        print(f"📡 Respuesta: {message}")

    def _display_victory(self):
        """Display victory message and final stats"""
        print("\n" + "="*50)
        print("🎉 ¡VICTORIA! ¡Has ganado!")
        print("🏆 Toda la flota enemiga ha sido destruida.")
        print("="*50)

        self.fsm.attack_board.display()
        self.fsm.display_stats()

        print(f"\n🎯 Juego completado en {self.fsm.total_attacks} ataques")

def main():
    """Main function"""
    try:
        client = AttackClient()
        client.start()

    except KeyboardInterrupt:
        print("\n🛑 Programa interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error fatal: {e}")
    
if __name__ == "__main__":
 main()