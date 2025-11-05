from pymongo import MongoClient
import firebase_admin  # type: ignore
from firebase_admin import credentials, firestore  # type: ignore
import os


class ConnectionBanks:
    def __init__(self) -> None:
        self.mongo = None
        self.firestore = None
        self._connect_mongo()
        self._connect_firestore()

    def _connect_mongo(self):
        try:
            client_mongo = MongoClient("mongodb://localhost:27017/")
            bank_mongo = client_mongo["sistema_veiculos"]
            self.mongo = bank_mongo["veiculos"]
            print("✅ Conectado ao MongoDB")
        except Exception as e:
            print("❌ Erro ao conectar no MongoDB:", e)

    def json_path(self, filename: str) -> str:

        return os.path.join(os.path.dirname(__file__), "config", filename)

    def find_json_in_config(self) -> str | None:

        config_dir = os.path.join(os.path.dirname(__file__), "config")
        try:
            for name in os.listdir(config_dir):
                if name.lower().endswith('.json'):
                    return os.path.join(config_dir, name)
        except FileNotFoundError:
            return None
        return None

    def _connect_firestore(self) -> None:
        try:

            json_file = self.find_json_in_config()
            if not json_file:
                print("⚠️ Nenhum arquivo .json de credenciais \
                      encontrado em 'config'.")

                print("Pulando inicialização do Firestore.")
                self.firestore = None
                return

            cred = credentials.Certificate(json_file)
            firebase_admin.initialize_app(cred)
            self.firestore = firestore.client()
            print("✅ Conectado ao Firestore")
        except Exception as e:
            print("❌ Erro ao conectar no Firestore:", e)


class Vehicles:

    def __init__(self, sign, model, brand, year, color, owner) -> None:
        self.sign = sign.upper()
        self.model = model
        self.brand = brand
        self.year = year
        self.color = color
        self.owner = owner

    def to_dict(self) -> dict:
        return {
            "Placa": self.sign,
            "Modelo": self.model,
            "Marca": self.brand,
            "Ano": self.year,
            "Cor": self.color,
            "Proprietario": self.owner
        }


class SystemVehicles(ConnectionBanks, Vehicles):
    def __init__(self, connection) -> None:
        self.mongo = connection.mongo
        self.firestore = connection.firestore

    def register(self):
        print("\n=== Cadastro de Veículo ===")
        sign = input("Placa: ")
        model = input("Modelo: ")
        brand = input("Marca: ")
        year = input("Ano: ")
        color = input("Cor: ")
        owner = input("Proprietario: ")

        vehicle = Vehicles(sign, model, brand, year, color, owner)

        try:
            self.mongo.insert_one(vehicle.to_dict())
            if self.firestore:
                self.firestore.collection("veiculos").document(vehicle.sign)\
                    .set(vehicle.to_dict())
            print("🚗 Veículo cadastrado com sucesso nos dois bancos!")
        except Exception as e:
            print(f"❌ Erro ao cadastrar o veículo: {e}")

    def to_list(self):

        print("\n=== Lista de Veículos (MongoDB) ===")
        for v in self.mongo.find():
            print(
                f"{v['Placa']} - {v['Modelo']} - {v['Marca']} - {v['Ano']} - \
                      {v['Cor']} - {v['Proprietario']}")

        print("\n=== Lista de Veículos (Firestore) ===")
        docs = self.firestore.collection("veiculos").stream()
        for doc in docs:
            v = doc.to_dict()
            print(
                f"{v['Placa']} - {v['Modelo']} - {v['Marca']} - {v['Ano']} - \
                      {v['Cor']} - {v['Proprietario']}")

    def to_search(self):
        sign = input("\nDigite a placa do veiculo para cadastrar: ").upper()

        v = self.mongo.find_one({"Placa": sign})
        if v:
            print("\n✅ Veículo encontrado no MongoDB:")
            print(v)
        else:
            print("❌ Veículo não encontrado no MongoDB.")

        doc = self.firestore.collection("veiculos").document(sign).get()
        if doc.exists:
            print("\n✅ Veículo encontrado no Firestore:")
            print(doc.to_dict())
        else:
            print("❌ Veículo não encontrado no Firestore.")

    def update(self):
        sign = input("\nDigite a placa do veiculo a Atualizar: ")
        new_model = input("Novo Modelo: ")
        new_color = input("Nova Cor: ")

        result = self.mongo.update_one(
            {"Placa": sign},
            {"$set": {"Modelo": new_model, "Cor": new_color}}
        )
        self.firestore.collection("veiculos").document(sign).update({
            "Modelo": new_model,
            "Cor": new_color
        })

        if result.modified_count > 0:
            print("✅ Veículo atualizado com sucesso nos dois bancos!")
        else:
            print("❌ Veículo não encontrado para atualização.")

    def remove(self):
        sign = input("\nDigite a placa do veículo a remover: ")
        result = self.mongo.delete_one({"sign": sign})
        self.firestore.collection("vehicles").document(sign).delete()

        if result.deleted_count > 0:
            print("🚗 Veículo removido com sucesso dos dois bancos!")
        else:
            print("❌ Veículo não encontrado para remoção.")


class Menu(SystemVehicles):
    def __init__(self, system):
        self.system = system

    def exibir(self) -> None:
        while True:
            print("\n=== SISTEMA DE CADASTRO DE VEÍCULOS ===")
            print("1 - Cadastrar veículo")
            print("2 - Listar veículos")
            print("3 - Buscar veículo")
            print("4 - Atualizar veículo")
            print("5 - Remover veículo")
            print("6 - Sair")
            option = input("Escolha uma opção: ")

            if option == "1":
                self.system.register()
            elif option == "2":
                self.system.to_list()
            elif option == "3":
                self.system.to_search()
            elif option == "4":
                self.system.update()
            elif option == "5":
                self.system.remove()
            elif option == "6":
                print("Encerrando o system...")
                break
            else:
                print("⚠️ Opção inválida, tente novamente.")


if __name__ == "__main__":
    connection = ConnectionBanks()
    system = SystemVehicles(connection)
    menu = Menu(system)
    menu.exibir()
