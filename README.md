# 🛳️ Juego de Batalla Naval con FSM

Este es un proyecto web de un juego de **Batalla Naval**, desarrollado con un enfoque de **Máquina de Estados Finitos (FSM)** para gestionar la lógica del juego. El proyecto está dividido en dos partes:  
- **Backend:** Python + FastAPI  
- **Frontend:** React JS + Tailwind CSS

## ⚙️ Características

- Juego clásico de batalla naval para dos jugadores
- Gestión del estado del juego mediante FSM
- API RESTful con FastAPI
- Interfaz moderna con React y estilos en Tailwind
- Arquitectura modular y escalable

## 🚀 Instalación y ejecución
### 🔙 Backend (FastAPI)
--Install dependencies
    cd backend
    pip install -r requirements.txt (si este funciona utilizar pip install --user fastapi uvicorn pydantic websockets python-multipart)
## 🎨 Frontend (React + Tailwind)
pm install
npm install lucide-react

--Install Tailwind CSS
  npm install -D tailwindcss postcss autoprefixer
--Generate config files
  npx tailwindcss init -p

### Ejecutar
## 🔙 Backend (FastAPI)
  cd backend
   uvicorn api_server:app --host 0.0.0.0 --port 8001
## 🎨 Frontend
  cd frontend
  npm start

