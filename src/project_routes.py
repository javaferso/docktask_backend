# src/project_routes.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import Proyecto, Mensaje, Usuario, db
from datetime import datetime, timezone
project = Blueprint("project", __name__, url_prefix="/api")

# ---------- helpers ----------
def is_admin(uid):
    u = db.session.get(Usuario, uid)
    return u and u.rol == "admin"

def owner_to_username(uid):
    u = db.session.get(Usuario, uid)
    return u.username if u else ""

def proyecto_to_dict(proyecto):
    return {
        "id": proyecto.id,
        "nombre": proyecto.nombre,
        "owner_id": proyecto.owner_id,
        "username": owner_to_username(proyecto.owner_id),
        "descripcion": proyecto.descripcion,
        "created_at": proyecto.created_at.astimezone(timezone.utc).isoformat(),
        "updated_at": proyecto.updated_at.astimezone(timezone.utc).isoformat(),
        "end_date": proyecto.end_date.astimezone(timezone.utc).isoformat() if proyecto.end_date else None,
        "estado": proyecto.estado
    }

# -----------------ENDPOINT GET PROYECTOS-----------------

@project.route("/proyectos", methods=["GET"])
@jwt_required()
def get_proyectos():
    proyectos = db.session.query(Proyecto).all()
    return jsonify([proyecto_to_dict(p) for p in proyectos]), 200

# -----------------ENDPOINT POST PROYECTOS-----------------

@project.route("/proyectos", methods=["POST"])
@jwt_required()
def create_proyecto():
    data = request.json
    
    if not data or not data.get("nombre") or not data.get("descripcion"):
        return jsonify({"error": "Faltan campos requeridos"}), 400
    end_date = None
    if data.get("end_date"):
        try:
            end_date = datetime.fromisoformat(data["end_date"])
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Usa ISO 8601."}), 400
    
    nuevo = Proyecto(
        nombre=data["nombre"],
        descripcion=data["descripcion"],
        owner_id=get_jwt_identity(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        end_date=end_date
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({"message": "Proyecto creado exitosamente"}), 201

# -----------------ENDPOINT PUT PROYECTOS-----------------
@project.route("/proyectos/<int:proyecto_id>", methods=["PUT"])
@jwt_required()
def update_proyecto(proyecto_id):
    data = request.json
    proyecto = db.session.get(Proyecto, proyecto_id)
    if not proyecto:
        return jsonify({"error": "Proyecto no encontrado"}), 404
    
    proyecto.nombre = data.get("nombre", proyecto.nombre)
    proyecto.descripcion = data.get("descripcion", proyecto.descripcion)
    proyecto.end_date = data.get("end_date", proyecto.end_date)
    proyecto.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"message": "Proyecto actualizado exitosamente"}), 200

# -----------------ENDPOINT DELETE PROYECTOS-----------------
@project.route("/proyectos/<int:proyecto_id>", methods=["DELETE"])
@jwt_required()
def delete_proyecto(proyecto_id):
    proyecto = db.session.get(Proyecto, proyecto_id)
    if not proyecto:
        return jsonify({"error": "Proyecto no encontrado"}), 404
    
    db.session.delete(proyecto)
    db.session.commit()
    return jsonify({"message": "Proyecto eliminado exitosamente"}), 200


# --- extra: mensajes de un proyecto ---
@project.route("/proyectos/<int:pid>/mensajes", methods=["GET"])
@jwt_required()
def mensajes_de_proyecto(pid):
    p = db.session.get(Proyecto, pid)
    return jsonify([
        {"id": m.id, "nombre": m.nombre, "mensaje": m.mensaje, "estado": m.estado}
        for m in p.mensajes
    ])

# --- extra: crear mensaje para un proyecto ---
@project.route("/proyectos/<int:pid>/mensajes", methods=["POST"])
@jwt_required()
def crear_mensaje(pid):
    p = db.session.get(Proyecto, pid)
    data = request.json
    if not data or not data.get("mensaje"):
        return jsonify({"error": "Faltan campos requeridos"}), 400

    nuevo = Mensaje(
        nombre=data["nombre"],
        mensaje=data["mensaje"],
        proyecto_id=pid,
        usuario_id= get_jwt_identity()
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({"message": "Mensaje creado exitosamente"}), 201



    

    
    

