import React, { useState, useEffect } from 'react';
import { Ship, Target, Waves, Zap, Shield, Crosshair } from 'lucide-react';

const NavalBattleGame = () => {
  const [gameMode, setGameMode] = useState('menu'); // 'menu', 'defense', 'attack'
  const [gameId, setGameId] = useState('player1');
  const [enemyGameId, setEnemyGameId] = useState('player1');
  const [apiUrl] = useState('http://localhost:8000');

  // Defense state
  const [fleetSetup, setFleetSetup] = useState({
    battleship: [],
    submarine: [],
    destroyer: []
  });
  const [defenseStatus, setDefenseStatus] = useState(null);
  const [setupMode, setSetupMode] = useState('battleship');

  // Attack state
  const [attackStatus, setAttackStatus] = useState(null);
  const [enemyHost, setEnemyHost] = useState('localhost');
  const [enemyPort, setEnemyPort] = useState(8000);
  const [selectedAttackPosition, setSelectedAttackPosition] = useState('');

  const GRID_ROWS = ['A', 'B', 'C', 'D', 'E'];
  const GRID_COLS = ['1', '2', '3', '4', '5'];

  const shipTypes = {
    battleship: { name: 'Battleship', size: 3, icon: Ship, color: 'bg-red-600' },
    submarine: { name: 'Submarine', size: 2, icon: Target, color: 'bg-blue-600' },
    destroyer: { name: 'Destroyer', size: 1, icon: Zap, color: 'bg-green-600' }
  };

  // API calls
  const apiCall = async (endpoint, method = 'GET', data = null) => {
    try {
      const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
      };
      if (data) options.body = JSON.stringify(data);

      const response = await fetch(`${apiUrl}${endpoint}`, options);
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Backend error text:", errorText)
        throw new Error(`HTTP ${response.status} - ${errorText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  };

  // Defense functions
  const setupDefenseFleet = async () => {
    try {
      await apiCall('/api/defense/setup', 'POST', { ...fleetSetup, game_id: gameId });
      fetchDefenseStatus();
    } catch (error) {
      alert('Error setting up fleet: ' + error.message);
    }
  };

  const fetchDefenseStatus = async () => {
    try {
      const status = await apiCall(`/api/defense/status?game_id=${gameId}`);
      setDefenseStatus(status);
    } catch (error) {
      console.error('Error fetching defense status:', error);
    }
  };

  // Attack functions
  const initAttackGame = async () => {
    try {
      await apiCall('/api/attack/init', 'POST', { game_id: gameId });
      fetchAttackStatus();
    } catch (error) {
      alert('Error initializing attack: ' + error.message);
    }
  };

  const sendAttack = async (position) => {
    try {
      /**PRIMERA CORRECCION*/
      const result = await apiCall('/api/attack/send', 'POST', {
        position,
        enemy_host: enemyHost,
        enemy_port: parseInt(enemyPort),
        enemy_game_id: enemyGameId, //correccion: enemy_game_id
        game_id: gameId //nuestro game id como atacantes
      });

      console.log('Attack result:', result);
      fetchAttackStatus();
    } catch (error) {
      alert('Attack failed: ' + error.message);
    }
  };

  const fetchAttackStatus = async () => {
    try {
      const status = await apiCall(`/api/attack/status?game_id=${gameId}`);
      setAttackStatus(status);
    } catch (error) {
      console.error('Error fetching attack status:', error);
    }
  };

  //AGREGAMOS UN FUNCION NUEVA test connection function
  const testConnection = async () => {
    try {
      const response = await fetch(`http://${enemyHost}:${enemyPort}/api/health`);
      if (response.ok) {
        alert('✅ Connection successful!');
      } else {
        alert('❌ Server responded but with error status');
      }
    } catch (error) {
      alert(`❌ Connection failed: ${error.message}`);
    }
  };

  useEffect(() => {
    if (gameMode === 'defense') {
      const ws = new WebSocket(`ws://localhost:8000/ws/${gameId}`);

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setDefenseStatus(data);
      };

      ws.onerror = (err) => {
        console.error("WebSocket error:", err);
      };

      return () => ws.close(); // limpieza al desmontar
    }
  }, [gameMode, gameId]);


  // Fleet setup handlers
  const handleCellClick = (position) => {
    if (gameMode === 'defense' && !defenseStatus) {
      // Fleet setup mode
      const currentShip = fleetSetup[setupMode];
      const maxSize = shipTypes[setupMode].size;

      if (currentShip.includes(position)) {
        // Remove position
        setFleetSetup(prev => ({
          ...prev,
          [setupMode]: prev[setupMode].filter(pos => pos !== position)
        }));
      } else if (currentShip.length < maxSize) {
        // Add position
        setFleetSetup(prev => ({
          ...prev,
          [setupMode]: [...prev[setupMode], position]
        }));
      }
    } else if (gameMode === 'attack') {
      // Attack mode
      setSelectedAttackPosition(position);
    }
  };

  const isShipComplete = (shipType) => {
    return fleetSetup[shipType].length === shipTypes[shipType].size;
  };

  const allShipsPlaced = () => {
    return Object.keys(shipTypes).every(isShipComplete);
  };

  const getCellClass = (position) => {

    let baseClass = 'w-12 h-12 border-2 border-gray-400 cursor-pointer transition-all duration-200 flex items-center justify-center text-lg font-bold';

    if (gameMode === 'defense') {
      if (!defenseStatus) {
        // Setup mode
        const isSelected = fleetSetup[setupMode].includes(position);
        const isOccupied = Object.values(fleetSetup).flat().includes(position);

        if (isSelected) {
          baseClass += ` ${shipTypes[setupMode].color} text-white`;
        } else if (isOccupied) {
          baseClass += ' bg-gray-400 text-white';
        } else {
          baseClass += ' bg-blue-100 hover:bg-blue-200';
        }
      } else {
        // Game mode - show hits
        const cell = defenseStatus.grid[position];
        if (cell === 'X') baseClass += ' bg-red-500 text-white';
        else if (cell === '#') baseClass += ' bg-red-800 text-white';
        else if (cell === 'O') baseClass += ' bg-blue-300 text-white';
        else baseClass += ' bg-blue-100';
      }
    } else if (gameMode === 'attack' && attackStatus) {
      const cell = attackStatus.grid[position];
      if (cell === 'X') baseClass += ' bg-red-500 text-white';
      else if (cell === '#') baseClass += ' bg-red-800 text-white';
      else if (cell === 'O') baseClass += ' bg-blue-300 text-white';
      else baseClass += ' bg-blue-100 hover:bg-blue-200';

      if (selectedAttackPosition === position) {
        baseClass += ' ring-4 ring-yellow-400';
      }
    }

    return baseClass;
  };

  const getCellContent = (position) => {
    if (gameMode === 'defense' && defenseStatus) {
      const cell = defenseStatus.grid[position];
      if (cell === 'X') return '💥';
      if (cell === '#') return '💀';
      if (cell === 'O') return '💧';
    } else if (gameMode === 'attack' && attackStatus) {
      const cell = attackStatus.grid[position];
      if (cell === 'X') return '💥';
      if (cell === '#') return '💀';
      if (cell === 'O') return '💧';
    }
    return '';
  };

  useEffect(() => {
    if (gameMode === 'defense' && defenseStatus) {
      const interval = setInterval(fetchDefenseStatus, 2000);
      return () => clearInterval(interval);
    }
  }, [gameMode, defenseStatus]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-700 to-teal-600 p-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-white text-center mb-8 flex items-center justify-center gap-3">
          <Ship className="w-10 h-10" />
          Naval Battle FSM
          <Shield className="w-10 h-10" />
        </h1>
        <div className="max-w-md mx-auto mb-6 bg-white p-4 rounded-xl shadow-md">
          <label className="block text-gray-700 font-semibold mb-2">Player ID (gameId):</label>
          <input
            type="text"
            value={gameId}
            onChange={(e) => setGameId(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-lg"
            placeholder="e.g., player1 or player2"
          />
        </div>

        {gameMode === 'menu' && (
          <div className="bg-white rounded-xl shadow-2xl p-8 max-w-md mx-auto">
            <h2 className="text-2xl font-bold text-center mb-6">Choose Game Mode</h2>
            <div className="space-y-4">
              <button
                onClick={() => setGameMode('defense')}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-lg flex items-center justify-center gap-3 transition-colors"
              >
                <Shield className="w-6 h-6" />
                Defense Mode
              </button>
              <button
                onClick={() => {
                  setGameMode('attack');
                  initAttackGame();
                }}
                className="w-full bg-red-600 hover:bg-red-700 text-white p-4 rounded-lg flex items-center justify-center gap-3 transition-colors"
              >
                <Crosshair className="w-6 h-6" />
                Attack Mode
              </button>
            </div>
          </div>
        )}

        {gameMode === 'defense' && (
          <div className="bg-white rounded-xl shadow-2xl p-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold flex items-center gap-2">
                <Shield className="w-8 h-8 text-blue-600" />
                Defense Mode
              </h2>
              <button
                onClick={() => setGameMode('menu')}
                className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg"
              >
                Back to Menu
              </button>
            </div>

            {!defenseStatus ? (
              <div className="grid lg:grid-cols-2 gap-8">
                <div>
                  <h3 className="text-xl font-bold mb-4">Place Your Fleet</h3>

                  <div className="mb-6">
                    <div className="flex gap-2 mb-4">
                      {Object.entries(shipTypes).map(([key, ship]) => (
                        <button
                          key={key}
                          onClick={() => setSetupMode(key)}
                          className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${setupMode === key
                            ? `${ship.color} text-white`
                            : isShipComplete(key)
                              ? 'bg-green-200 text-green-800'
                              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                        >
                          <ship.icon className="w-4 h-4" />
                          {ship.name} ({ship.size})
                          {isShipComplete(key) && <span className="text-green-600">✓</span>}
                        </button>
                      ))}
                    </div>

                    <p className="text-sm text-gray-600 mb-4">
                      Currently placing: <strong>{shipTypes[setupMode].name}</strong>
                      ({fleetSetup[setupMode].length}/{shipTypes[setupMode].size} positions)
                    </p>

                    {allShipsPlaced() && (
                      <button
                        onClick={setupDefenseFleet}
                        className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-bold"
                      >
                        Start Defense!
                      </button>
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="text-xl font-bold mb-4">Grid (5x5)</h3>
                  <div className="grid grid-cols-6 gap-1 w-fit mx-auto">
                    <div></div>
                    {GRID_COLS.map(col => (
                      <div key={col} className="w-12 h-12 flex items-center justify-center font-bold">
                        {col}
                      </div>
                    ))}
                    {GRID_ROWS.map(row => (
                      <React.Fragment key={row}>
                        <div className="w-12 h-12 flex items-center justify-center font-bold">
                          {row}
                        </div>
                        {GRID_COLS.map(col => {
                          const position = `${row}${col}`;
                          return (
                            <div
                              key={position}
                              className={getCellClass(position)}
                              onClick={() => handleCellClick(position)}
                            >
                              {getCellContent(position)}
                            </div>
                          );
                        })}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="grid lg:grid-cols-2 gap-8">
                <div>
                  <h3 className="text-xl font-bold mb-4">Defense Status</h3>
                  <div className="bg-gray-100 p-4 rounded-lg mb-4">
                    <p><strong>Game State:</strong> {defenseStatus.state}</p>
                    <p><strong>Total Attacks:</strong> {defenseStatus.total_attacks}</p>
                  </div>

                  <h4 className="font-bold mb-2">Fleet Status:</h4>
                  <div className="space-y-2">
                    {defenseStatus.ships_status.map((ship, idx) => (
                      <div key={idx} className="bg-gray-100 p-3 rounded-lg">
                        <div className="flex justify-between items-center">
                          <span className="font-semibold">{ship.name}</span>
                          <span className={`px-2 py-1 rounded text-sm ${ship.is_sunk ? 'bg-red-200 text-red-800' : 'bg-green-200 text-green-800'
                            }`}>
                            {ship.is_sunk ? 'SUNK' : 'ACTIVE'}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">
                          Hits: {ship.hit_count}/{ship.total_positions}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="text-xl font-bold mb-4">Defense Grid</h3>
                  <div className="grid grid-cols-6 gap-1 w-fit mx-auto">
                    <div></div>
                    {GRID_COLS.map(col => (
                      <div key={col} className="w-12 h-12 flex items-center justify-center font-bold">
                        {col}
                      </div>
                    ))}
                    {GRID_ROWS.map(row => (
                      <React.Fragment key={row}>
                        <div className="w-12 h-12 flex items-center justify-center font-bold">
                          {row}
                        </div>
                        {GRID_COLS.map(col => {
                          const position = `${row}${col}`;
                          return (
                            <div
                              key={position}
                              className={getCellClass(position)}
                            >
                              {getCellContent(position)}
                            </div>
                          );
                        })}
                      </React.Fragment>
                    ))}
                  </div>
                  <div className="mt-4 text-sm">
                    <p><strong>Legend:</strong></p>
                    <p>💧 = Miss, 💥 = Hit, 💀 = Sunk</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {gameMode === 'attack' && (
          <div className="bg-white rounded-xl shadow-2xl p-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold flex items-center gap-2">
                <Crosshair className="w-8 h-8 text-red-600" />
                Attack Mode
              </h2>
              <button
                onClick={() => setGameMode('menu')}
                className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg"
              >
                Back to Menu
              </button>
            </div>

            <div className="grid lg:grid-cols-2 gap-8">
              <div>
                <h3 className="text-xl font-bold mb-4">Enemy Target</h3>

                <div className="mb-6 space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Enemy Host:</label>
                    <input
                      type="text"
                      value={enemyHost}
                      onChange={(e) => setEnemyHost(e.target.value)}
                      className="w-full p-2 border rounded-lg"
                      placeholder="localhost"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Enemy Port:</label>
                    <input
                      type="number"
                      value={enemyPort}
                      onChange={(e) => setEnemyPort(e.target.value)}
                      className="w-full p-2 border rounded-lg"
                      placeholder="8000"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Enemy Game ID:</label>
                    <input
                      type="text"
                      value={enemyGameId}
                      onChange={(e) => setEnemyGameId(e.target.value)}
                      className="w-full p-2 border rounded-lg"
                      placeholder="player1"
                    />
                  </div>
                  {/*AGREGAMOS EL BOTON DE TEST DE CONEXION*/}
                  <button
                    onClick={testConnection}
                    className="w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center justify-center gap-2"
                  >
                    {/*<wifi className="w-4 h-4" />*/}
                    Test Connection
                  </button>

                  {selectedAttackPosition && (
                    <button
                      onClick={() => sendAttack(selectedAttackPosition)}
                      className="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-bold w-full"
                    >
                      🚀 Attack {selectedAttackPosition}!
                    </button>
                  )}
                </div>

                {attackStatus && (
                  <div className="bg-gray-100 p-4 rounded-lg">
                    <h4 className="font-bold mb-2">Attack Statistics:</h4>
                    <p><strong>Total Attacks:</strong> {attackStatus.total_attacks}</p>
                    <p><strong>Hits:</strong> {attackStatus.hits}</p>
                    <p><strong>Misses:</strong> {attackStatus.misses}</p>
                    <p><strong>Ships Sunk:</strong> {attackStatus.sunk_ships}</p>
                    <p><strong>Accuracy:</strong> {attackStatus.accuracy.toFixed(1)}%</p>
                    {attackStatus.game_won && (
                      <p className="text-green-600 font-bold mt-2">🎉 VICTORY! 🎉</p>
                    )}
                  </div>
                )}
              </div>

              <div>
                <h3 className="text-xl font-bold mb-4">Attack Grid</h3>
                <div className="grid grid-cols-6 gap-1 w-fit mx-auto">
                  <div></div>
                  {GRID_COLS.map(col => (
                    <div key={col} className="w-12 h-12 flex items-center justify-center font-bold">
                      {col}
                    </div>
                  ))}
                  {GRID_ROWS.map(row => (
                    <React.Fragment key={row}>
                      <div className="w-12 h-12 flex items-center justify-center font-bold">
                        {row}
                      </div>
                      {GRID_COLS.map(col => {
                        const position = `${row}${col}`;
                        return (
                          <div
                            key={position}
                            className={getCellClass(position)}
                            onClick={() => handleCellClick(position)}
                          >
                            {getCellContent(position)}
                          </div>
                        );
                      })}
                    </React.Fragment>
                  ))}
                </div>
                <div className="mt-4 text-sm">
                  <p><strong>Legend:</strong></p>
                  <p>💧 = Miss, 💥 = Hit, 💀 = Sunk</p>
                  <p>Click a cell to select attack position</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NavalBattleGame;