#!/usr/bin/env python3
"""
Taskmaster CLI - Herramienta ligera de orquestación para woptimizer.
Uso:
    python .taskmaster/tm.py list
    python .taskmaster/tm.py next
    python .taskmaster/tm.py start <task_id>
    python .taskmaster/tm.py done <task_id>
"""

import sys
import json
import os
import io

# Asegurar compatibilidad de encoding en terminales Windows estándar (cp1252)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB_PATH = os.path.join(os.path.dirname(__file__), "tasks.json")

def load_data():
    if not os.path.exists(DB_PATH):
        print(f"Error: No existe {DB_PATH}")
        sys.exit(1)
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def cmd_list(data):
    print("\n=== TASKMASTER: Tareas del Proyecto ===")
    for t in data["tasks"]:
        status_tag = "[PENDING]" if t["status"] == "pending" else ("[IN_PROG]" if t["status"] == "in_progress" else "[DONE   ]")
        print(f"{status_tag:10} {t['id']}: {t['title']} (Complejidad: {t['complexity']}/10, Prioridad: {t['priority']})")
    print()

def cmd_next(data):
    completed_ids = {t["id"] for t in data["tasks"] if t["status"] == "completed"}
    
    # Buscar en progreso primero
    for t in data["tasks"]:
        if t["status"] == "in_progress":
            print(f"\n[EN PROGRESO ACTUALMENTE]\nID: {t['id']}\nTitulo: {t['title']}\nModulo a leer: {t.get('module', 'N/A')}\nDescripcion: {t['description']}\n")
            return
            
    # Buscar siguiente pendiente con dependencias resueltas
    for t in data["tasks"]:
        if t["status"] == "pending":
            deps = t.get("dependencies", [])
            if all(d in completed_ids for d in deps):
                print(f"\n[SIGUIENTE TAREA DISPONIBLE]\nID: {t['id']}\nTitulo: {t['title']}\nComplejidad: {t['complexity']}/10\nModulo a leer: {t.get('module', 'N/A')}\nDescripcion: {t['description']}\n")
                return
                
    print("\nNo hay tareas pendientes disponibles. ¡Todas estan completadas o bloqueadas!\n")

def cmd_status(data, task_id, new_status):
    found = False
    for t in data["tasks"]:
        if t["id"].upper() == task_id.upper():
            t["status"] = new_status
            found = True
            break
    if found:
        save_data(data)
        print(f"\nTarea {task_id} actualizada a: {new_status.upper()}\n")
    else:
        print(f"\nNo se encontro la tarea {task_id}\n")

def main():
    if len(sys.argv) < 2:
        print("Comandos disponibles: list, next, start <ID>, done <ID>")
        sys.exit(0)
        
    cmd = sys.argv[1].lower()
    data = load_data()
    
    if cmd == "list":
        cmd_list(data)
    elif cmd == "next":
        cmd_next(data)
    elif cmd == "start" and len(sys.argv) > 2:
        cmd_status(data, sys.argv[2], "in_progress")
    elif cmd == "done" and len(sys.argv) > 2:
        cmd_status(data, sys.argv[2], "completed")
    else:
        print("Uso no reconocido. Comandos: list, next, start <ID>, done <ID>")

if __name__ == "__main__":
    main()
