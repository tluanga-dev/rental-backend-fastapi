"""
Transaction schemas package.
"""

# Import all schemas from main and returns modules for backward compatibility
from .main import *
from .returns import *

# Explicitly define what should be available when importing from this package
__all__ = [
    # From main schemas
    "TransactionHeaderCreate",
    "TransactionHeaderUpdate", 
    "TransactionHeaderResponse",
    "TransactionLineCreate",
    "TransactionLineUpdate", 
    "TransactionLineResponse",
    "TransactionWithLinesResponse",
    "TransactionSummaryResponse",
    
    # Purchase and rental schemas
    "NewPurchaseRequest",
    "NewPurchaseResponse",
    "NewRentalRequest", 
    "NewRentalResponse",
    "NewSaleRequest",
    "NewSaleResponse",
    "SaleItemCreate",
    
    # Rentable items schemas
    "RentableItemResponse",
    "LocationAvailability",
    
    # From returns schemas  
    "SaleReturnCreate",
    "PurchaseReturnCreate",
    "RentalReturnCreate",
    "ReturnTransactionCreate",
    "ReturnValidationResponse", 
    "ReturnDetailsResponse",
    "ReturnStatusUpdate",
    "ReturnWorkflowState", 
    "PurchaseCreditMemoCreate", 
    "PurchaseCreditMemoResponse"
]