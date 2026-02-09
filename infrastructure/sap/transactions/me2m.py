"""
ME2M - Pedidos por material (SAP GUI Scripting).
TODO: implementar quando SAP GUI real estiver disponível.
"""


class ME2MTransaction:
    def execute(self, session, params: dict) -> list[dict]:
        """
        Executa ME2M e retorna uma lista de pedidos.

        params esperado (exemplo):
        {
          "material": "MAT-001",
          "centro": "1000"
        }
        """
        raise NotImplementedError("ME2M ainda nao implementado.")
