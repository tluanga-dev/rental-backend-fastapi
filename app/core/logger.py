"""
Enhanced logging system for purchase transaction debugging.
Provides structured logging with timestamps and markdown formatting.
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import traceback


class PurchaseTransactionLogger:
    """Specialized logger for purchase transaction debugging."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"purchase_transactions_{timestamp}.md"
        
        # Initialize markdown log file
        self._init_markdown_log()
        
        # Setup Python logger
        self.logger = logging.getLogger("purchase_transaction")
        self.logger.setLevel(logging.DEBUG)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create file handler
        file_handler = logging.FileHandler(
            self.log_dir / f"purchase_transactions_{timestamp}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # Add handlers
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)
    
    def _init_markdown_log(self):
        """Initialize markdown log file with header."""
        with open(self.log_file, "w") as f:
            f.write(f"""# Purchase Transaction Debug Log

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Purchase Transaction Processing Log

This log tracks the complete flow of purchase transactions and stock level integration.

""")
    
    def _write_markdown(self, content: str):
        """Write content to markdown log file."""
        with open(self.log_file, "a") as f:
            f.write(content + "\n")
    
    def log_purchase_start(self, purchase_data: Dict[str, Any], transaction_id: str = None):
        """Log the start of a purchase transaction."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Console/file log
        self.logger.info(f"🛒 PURCHASE TRANSACTION STARTED - ID: {transaction_id}")
        
        # Markdown log
        content = f"""
### 🛒 Purchase Transaction Started
**Timestamp:** {timestamp}  
**Transaction ID:** {transaction_id or "Not yet assigned"}

**Purchase Data:**
```json
{json.dumps(purchase_data, indent=2, default=str)}
```

**Items Count:** {len(purchase_data.get('items', []))}  
**Supplier ID:** {purchase_data.get('supplier_id')}  
**Location ID:** {purchase_data.get('location_id')}

---
"""
        self._write_markdown(content)
    
    def log_validation_step(self, step: str, result: bool, details: str = None):
        """Log validation steps."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        status = "✅ PASSED" if result else "❌ FAILED"
        
        # Console/file log
        self.logger.info(f"🔍 VALIDATION - {step}: {status}")
        if details:
            self.logger.debug(f"Details: {details}")
        
        # Markdown log
        content = f"""
#### 🔍 Validation: {step}
**Timestamp:** {timestamp}  
**Status:** {status}

{f"**Details:** {details}" if details else ""}

"""
        self._write_markdown(content)
    
    def log_transaction_creation(self, transaction_data: Dict[str, Any]):
        """Log transaction header creation."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Console/file log
        self.logger.info(f"📝 TRANSACTION CREATED - Number: {transaction_data.get('transaction_number')}")
        
        # Markdown log
        content = f"""
#### 📝 Transaction Header Created
**Timestamp:** {timestamp}

**Transaction Details:**
- **ID:** {transaction_data.get('id')}
- **Number:** {transaction_data.get('transaction_number')}
- **Type:** {transaction_data.get('transaction_type')}
- **Status:** {transaction_data.get('status')}
- **Total Amount:** ${transaction_data.get('total_amount', 0)}

"""
        self._write_markdown(content)
    
    def log_stock_level_processing_start(self, items_count: int):
        """Log start of stock level processing."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Console/file log
        self.logger.info(f"📦 STOCK LEVEL PROCESSING STARTED - {items_count} items")
        
        # Markdown log
        content = f"""
#### 📦 Stock Level Processing Started
**Timestamp:** {timestamp}  
**Items to Process:** {items_count}

"""
        self._write_markdown(content)
    
    def log_item_stock_processing(self, item_id: str, quantity: int, existing_stock: Optional[Dict] = None):
        """Log individual item stock processing."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        if existing_stock:
            action = "UPDATE EXISTING"
            old_qty = existing_stock.get('quantity_on_hand', 0)
            # Handle string, float, Decimal, or int quantities
            if isinstance(old_qty, str):
                old_qty = float(old_qty) if '.' in str(old_qty) else int(old_qty)
            new_qty = old_qty + quantity if old_qty else quantity
            
            # Console/file log
            self.logger.info(f"📈 STOCK UPDATE - Item: {item_id}, {old_qty} → {new_qty}")
            
            # Markdown log
            content = f"""
##### 📈 Stock Update (Existing Stock)
**Timestamp:** {timestamp}  
**Item ID:** {item_id}  
**Action:** {action}

**Stock Changes:**
- **Previous Quantity:** {old_qty}
- **Added Quantity:** +{quantity}
- **New Quantity:** {new_qty}

**Existing Stock Details:**
```json
{json.dumps(existing_stock, indent=2, default=str)}
```

"""
        else:
            action = "CREATE NEW"
            
            # Console/file log
            self.logger.info(f"➕ STOCK CREATE - Item: {item_id}, Quantity: {quantity}")
            
            # Markdown log
            content = f"""
##### ➕ Stock Creation (New Stock)
**Timestamp:** {timestamp}  
**Item ID:** {item_id}  
**Action:** {action}

**New Stock Details:**
- **Initial Quantity:** {quantity}
- **Available Quantity:** {quantity}
- **Reserved Quantity:** 0

"""
        
        self._write_markdown(content)
    
    def log_stock_level_creation(self, stock_data: Dict[str, Any]):
        """Log stock level object creation."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Console/file log
        self.logger.info(f"🏗️ STOCK OBJECT CREATED - Item: {stock_data.get('item_id')}")
        
        # Markdown log
        content = f"""
##### 🏗️ Stock Level Object Created
**Timestamp:** {timestamp}

**Stock Level Data:**
```json
{json.dumps(stock_data, indent=2, default=str)}
```

"""
        self._write_markdown(content)
    
    def log_session_operation(self, operation: str, details: str = None):
        """Log database session operations."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Console/file log
        self.logger.info(f"🗄️ DATABASE - {operation}")
        if details:
            self.logger.debug(f"Details: {details}")
        
        # Markdown log
        content = f"""
##### 🗄️ Database Operation: {operation}
**Timestamp:** {timestamp}

{f"**Details:** {details}" if details else ""}

"""
        self._write_markdown(content)
    
    def log_transaction_commit(self, success: bool, error: str = None):
        """Log transaction commit result."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        status = "✅ SUCCESS" if success else "❌ FAILED"
        
        # Console/file log
        if success:
            self.logger.info("💾 TRANSACTION COMMITTED SUCCESSFULLY")
        else:
            self.logger.error(f"💥 TRANSACTION COMMIT FAILED: {error}")
        
        # Markdown log
        content = f"""
#### 💾 Transaction Commit
**Timestamp:** {timestamp}  
**Status:** {status}

{f"**Error:** {error}" if error else "**Result:** All changes committed to database"}

"""
        self._write_markdown(content)
    
    def log_purchase_completion(self, success: bool, transaction_id: str, response_data: Dict = None):
        """Log purchase transaction completion."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        status = "✅ COMPLETED" if success else "❌ FAILED"
        
        # Console/file log
        self.logger.info(f"🎯 PURCHASE TRANSACTION {status} - ID: {transaction_id}")
        
        # Markdown log
        json_block = ""
        if response_data:
            json_str = json.dumps(response_data, indent=2, default=str)
            json_block = f"```json\n{json_str}\n```"
        
        content = f"""
### 🎯 Purchase Transaction Completed
**Timestamp:** {timestamp}  
**Status:** {status}  
**Transaction ID:** {transaction_id}

{"**Response Data:**" if response_data else ""}
{json_block}

---

"""
        self._write_markdown(content)
    
    def log_error(self, error: Exception, context: str = None):
        """Log errors with full context."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Console/file log
        self.logger.error(f"💥 ERROR in {context}: {str(error)}")
        self.logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Markdown log
        content = f"""
### 💥 ERROR OCCURRED
**Timestamp:** {timestamp}  
**Context:** {context or "Unknown"}

**Error Message:**
```
{str(error)}
```

**Traceback:**
```
{traceback.format_exc()}
```

---

"""
        self._write_markdown(content)
    
    def log_debug_info(self, title: str, data: Any):
        """Log debug information."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # Console/file log
        self.logger.debug(f"🔧 DEBUG - {title}")
        
        # Markdown log
        content = f"""
##### 🔧 Debug Info: {title}
**Timestamp:** {timestamp}

```json
{json.dumps(data, indent=2, default=str) if isinstance(data, (dict, list)) else str(data)}
```

"""
        self._write_markdown(content)


# Global logger instance
purchase_logger = PurchaseTransactionLogger()


def get_purchase_logger() -> PurchaseTransactionLogger:
    """Get the purchase transaction logger instance."""
    return purchase_logger
