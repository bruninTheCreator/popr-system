# popr/domain/exceptions/domain_exceptions.py
"""
Exceções de Domínio
Erros específicos das regras de negócio do POPR
"""


class POPRDomainException(Exception):
    """Exceção base para erros de domínio"""
    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class InvalidPOStateTransition(POPRDomainException):
    """Transição de estado inválida"""
    def __init__(self, from_status: str, to_status: str):
        message = f"Cannot transition from {from_status} to {to_status}"
        super().__init__(message, {
            "from_status": from_status,
            "to_status": to_status
        })


class POAlreadyLockedException(POPRDomainException):
    """PO já está bloqueada por outro usuário"""
    def __init__(self, po_number: str, locked_by: str, expires_at: str):
        message = f"PO {po_number} is already locked by {locked_by} until {expires_at}"
        super().__init__(message, {
            "po_number": po_number,
            "locked_by": locked_by,
            "expires_at": expires_at
        })


class PONotLockedException(POPRDomainException):
    """PO não está bloqueada"""
    def __init__(self, po_number: str):
        message = f"PO {po_number} is not locked"
        super().__init__(message, {"po_number": po_number})


class POLockOwnershipException(POPRDomainException):
    """Usuário tentando liberar lock que não é dele"""
    def __init__(self, po_number: str, owner: str, attempted_by: str):
        message = (
            f"Cannot release lock on PO {po_number}. "
            f"Locked by {owner}, attempted by {attempted_by}"
        )
        super().__init__(message, {
            "po_number": po_number,
            "owner": owner,
            "attempted_by": attempted_by
        })


class POValidationException(POPRDomainException):
    """Validação da PO falhou"""
    def __init__(self, po_number: str, errors: list):
        message = f"PO {po_number} validation failed: {', '.join(errors)}"
        super().__init__(message, {
            "po_number": po_number,
            "errors": errors
        })


class PONotFoundException(POPRDomainException):
    """PO não encontrada"""
    def __init__(self, identifier: str):
        message = f"PO not found: {identifier}"
        super().__init__(message, {"identifier": identifier})


class DuplicatePOException(POPRDomainException):
    """PO duplicada"""
    def __init__(self, po_number: str):
        message = f"PO {po_number} already exists"
        super().__init__(message, {"po_number": po_number})


class InvalidApprovalException(POPRDomainException):
    """Tentativa de aprovação inválida"""
    def __init__(self, po_number: str, current_status: str, reason: str):
        message = (
            f"Cannot approve PO {po_number} in status {current_status}. "
            f"Reason: {reason}"
        )
        super().__init__(message, {
            "po_number": po_number,
            "current_status": current_status,
            "reason": reason
        })


class InvalidRejectionException(POPRDomainException):
    """Tentativa de rejeição inválida"""
    def __init__(self, po_number: str, current_status: str, reason: str):
        message = (
            f"Cannot reject PO {po_number} in status {current_status}. "
            f"Reason: {reason}"
        )
        super().__init__(message, {
            "po_number": po_number,
            "current_status": current_status,
            "reason": reason
        })


class ReconciliationException(POPRDomainException):
    """Erro na reconciliação de dados"""
    def __init__(self, po_number: str, discrepancies: list):
        message = f"Reconciliation failed for PO {po_number}"
        super().__init__(message, {
            "po_number": po_number,
            "discrepancies": discrepancies
        })


class ConcurrencyException(POPRDomainException):
    """Conflito de concorrência (versão desatualizada)"""
    def __init__(self, po_number: str, expected_version: int, actual_version: int):
        message = (
            f"Concurrency conflict for PO {po_number}. "
            f"Expected version {expected_version}, but found {actual_version}"
        )
        super().__init__(message, {
            "po_number": po_number,
            "expected_version": expected_version,
            "actual_version": actual_version
        })