# src/main_routes.py
from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from .models import Usuario, Mensaje
from . import db, r
from datetime import datetime

main = Blueprint("main", __name__)

@main.route("/")
def index():
    nombre = request.args.get("nombre", "Desarrollador")
    return render_template("index.html", nombre=nombre)

@main.route("/saludo", methods=["GET"])
def saludo():
    nombre = request.args.get("nombre", "Desarrollador")
    return jsonify({"mensaje": f"Hola, {nombre} 👋"})

@main.route("/contacto", methods=["GET", "POST"])
def contacto():
    respuesta = None
    if request.method == "POST":
        nombre = request.form.get("nombre")
        mensaje = request.form.get("mensaje")

        nuevo_mensaje = Mensaje(nombre=nombre, mensaje=mensaje)
        db.session.add(nuevo_mensaje)
        db.session.commit()

        r.set("ultimo_mensaje", mensaje)
        respuesta = f"Gracias por tu mensaje, {nombre}! 📬"
    return render_template("contacto.html", respuesta=respuesta)

@main.route("/mensajes", methods=["GET"])
def ver_mensajes():
    mensajes = Mensaje.query.order_by(Mensaje.id.desc()).all()
    return render_template("mensajes.html", mensajes=mensajes)

@main.route("/api/mensajes", methods=["GET"])
def api_mensajes():
    mensajes = Mensaje.query.order_by(Mensaje.id.desc()).all()
    data = [
        {"id": m.id, "nombre": m.nombre, "mensaje": m.mensaje}
        for m in mensajes
    ]
    return jsonify(data)

@main.route("/api/mensajes", methods=["POST"])
@jwt_required()
def api_crear_mensaje():
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get("nombre") or not data.get("mensaje"):
        return jsonify({"error": "Faltan campos requeridos"}), 400

    expiration_date = None
    if data.get("expiration_date"):
        try:
            expiration_date = datetime.fromisoformat(data["expiration_date"])
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Usa ISO 8601."}), 400

    nuevo = Mensaje(
        nombre=data["nombre"],
        mensaje=data["mensaje"],
        usuario_id=int(user_id),
        estado=data.get("estado", "pendiente"),
        proyecto_id=data.get("proyecto_id"),
        expiration_date=expiration_date
    )
    if not nuevo.proyecto_id:
        return jsonify({"error": "Proyecto no especificado"}), 400
    
    db.session.add(nuevo)
    db.session.commit()

    return jsonify({
        "mensaje": "Mensaje guardado exitosamente",
        "data": {
            "id": nuevo.id,
            "nombre": nuevo.nombre,
            "mensaje": nuevo.mensaje,
            "estado": nuevo.estado,
            "expiration_date": nuevo.expiration_date.isoformat() if nuevo.expiration_date else None
        },
        "autor": user_id
    }), 201

@main.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Faltan credenciales"}), 400

    user = Usuario.query.filter_by(username=username, password=password).first()

    if not user:
        return jsonify({"error": "Credenciales inválidas"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({
        "access_token": token,
        "usuario": {
            "id": user.id,
            "username": user.username,
            "rol": user.rol,
            "nombre": user.nombre,
            "apellido": user.apellido
        }
    }), 200

@main.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Faltan campos"}), 400

    if Usuario.query.filter_by(username=username).first():
        return jsonify({"error": "Usuario ya existe"}), 409

    nuevo_usuario = Usuario(username=username, password=password, rol="usuario")
    db.session.add(nuevo_usuario)
    db.session.commit()

    return jsonify({"mensaje": "Usuario registrado exitosamente"}), 201

@main.route("/api/mis-mensajes", methods=["GET"])
@jwt_required()
def mis_mensajes():
    user_id = get_jwt_identity()
    mensajes = Mensaje.query.filter_by(usuario_id=user_id).order_by(Mensaje.id.desc()).all()
    return jsonify([
        {"id": m.id, "nombre": m.nombre, 
         "mensaje": m.mensaje, 
         "created_at": m.created_at, 
         "updated_at": m.updated_at,
         "estado": m.estado,
         "expiration_date": m.expiration_date.isoformat() if m.expiration_date else None
         }
        for m in mensajes
    ])

@main.route("/api/mensajes/<int:id>", methods=["PUT"])
@jwt_required()
def actualizar_mensaje(id):
    user_id = int(get_jwt_identity())
    mensaje = Mensaje.query.get(id)
    if not mensaje or mensaje.usuario_id != user_id:
        return jsonify({"error": "Mensaje no encontrado o sin permisos",
                        "user_id": user_id,
                        "mensaje_id": mensaje.usuario_id if mensaje else None}), 403

    data = request.get_json()

    if "estado" in data:
        mensaje.estado = data["estado"]
    if "expiration_date" in data:
        try:
            mensaje.expiration_date = datetime.fromisoformat(data["expiration_date"])
        except Exception as e:
            return jsonify({"error": f"Formato de fecha inválido: {str(e)}"}), 400
    mensaje.updated_at = datetime.utcnow()
    mensaje.mensaje = data.get("mensaje", mensaje.mensaje)
    db.session.commit()
    return jsonify({"mensaje": "Mensaje actualizado"})

@main.route("/api/mensajes/<int:id>", methods=["DELETE"])
@jwt_required()
def eliminar_mensaje(id):
    user_id = int(get_jwt_identity())
    mensaje = Mensaje.query.get(id)
    if not mensaje or mensaje.usuario_id != user_id:
        return jsonify({"error": "Mensaje no encontrado o sin permisos",
                        "user_id": user_id,
                        "mensaje_id": mensaje.usuario_id if mensaje else None}), 403

    db.session.delete(mensaje)
    db.session.commit()
    return jsonify({"mensaje": "Mensaje eliminado"})

@main.route("/api/mis-mensajes/<int:id>/duplicate", methods=["POST"])
@jwt_required()
def duplicar_mensaje(id):
    user_id = int(get_jwt_identity())
    mensaje = Mensaje.query.get_or_404(id)

    # Verifica que el usuario sea dueño del mensaje
    if mensaje.usuario_id != user_id:
        return jsonify({"error": "No autorizado",
                        "mensaje.usuario_id": mensaje.usuario_id,
                        "user_id": user_id}), 403

    nuevo = Mensaje(
        nombre=mensaje.nombre + " (copia)",
        mensaje=mensaje.mensaje,
        usuario_id=mensaje.usuario_id,
        proyecto_id=mensaje.proyecto_id,
        estado=mensaje.estado,
        expiration_date=mensaje.expiration_date
    )
    db.session.add(nuevo)
    db.session.commit()

    return jsonify(nuevo.to_dict()), 201
