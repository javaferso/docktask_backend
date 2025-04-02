def saludar(nombre: str) -> str:
    return f"Hola, {nombre} 👋"


if __name__ == "__main__":
    nombre = input("¿Cómo te llamas? ")
    print(saludar(nombre))
