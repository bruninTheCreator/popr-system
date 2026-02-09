"""
MB52 - Estoque por material (SAP GUI Scripting).
TODO: implementar quando SAP GUI real estiver disponível.
"""


class MB52Transaction:
    def execute(self, session, params: dict) -> list[dict]:
        """
        Executa MB52 e retorna uma lista de linhas do estoque.

        params esperado (exemplo):
        {
          "material": "MAT-001",
          "centro": "1000",
          "deposito": "0001"
        }
        """
        raise NotImplementedError("MB52 ainda nao implementado.")
