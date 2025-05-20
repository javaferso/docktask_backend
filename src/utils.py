from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps
from flask import jsonify
from .models import Usuario

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = Usuario.query.get(user_id)
        if not user or user.rol != 'admin':
            return jsonify({"error": "Acceso restringido a administradores"}), 403
        return fn(*args, **kwargs)
    return wrapper
