from src.app import app

def test_saludo():
    cliente = app.test_client()
    respuesta = cliente.get("/saludo?nombre=Tester")
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"mensaje": "Hola, Tester 👋"}
