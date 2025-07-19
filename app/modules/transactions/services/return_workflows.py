"""
Return workflow management for different return types.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Set
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.transactions.base.models import TransactionHeader
from app.modules.transactions.schemas.returns import ReturnWorkflowState
import logging
logger = logging.getLogger(__name__)


class WorkflowTransition:
    """Represents a valid workflow transition."""
    
    def __init__(
        self, 
        from_state: str, 
        to_state: str, 
        condition: Optional[callable] = None,
        side_effects: Optional[List[callable]] = None
    ):
        self.from_state = from_state
        self.to_state = to_state
        self.condition = condition
        self.side_effects = side_effects or []
    
    def is_valid(self, context: Dict) -> bool:
        """Check if transition is valid given context."""
        if self.condition:
            return self.condition(context)
        return True
    
    async def execute_side_effects(self, context: Dict) -> None:
        """Execute side effects of the transition."""
        for effect in self.side_effects:
            if asyncio.iscoroutinefunction(effect):
                await effect(context)
            else:
                effect(context)


class ReturnWorkflow(ABC):
    """Abstract base class for return workflows."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._transitions: List[WorkflowTransition] = []
        self._initialize_transitions()
    
    @abstractmethod
    def _initialize_transitions(self) -> None:
        """Initialize workflow transitions."""
        pass
    
    def get_allowed_transitions(self, current_state: str) -> List[str]:
        """Get allowed transitions from current state."""
        allowed = []
        for transition in self._transitions:
            if transition.from_state == current_state:
                allowed.append(transition.to_state)
        return allowed
    
    def can_transition(
        self, 
        current_state: str, 
        target_state: str, 
        context: Optional[Dict] = None
    ) -> bool:
        """Check if transition is allowed."""
        context = context or {}
        
        for transition in self._transitions:
            if (transition.from_state == current_state and 
                transition.to_state == target_state):
                return transition.is_valid(context)
        
        return False
    
    async def transition(
        self,
        return_id: UUID,
        current_state: str,
        target_state: str,
        context: Optional[Dict] = None
    ) -> None:
        """Execute a state transition."""
        context = context or {}
        context['return_id'] = return_id
        
        # Find the transition
        transition = None
        for t in self._transitions:
            if t.from_state == current_state and t.to_state == target_state:
                transition = t
                break
        
        if not transition:
            raise ValueError(f"Invalid transition: {current_state} → {target_state}")
        
        if not transition.is_valid(context):
            raise ValueError(f"Transition conditions not met: {current_state} → {target_state}")
        
        # Execute side effects
        await transition.execute_side_effects(context)
        
        # Log transition
        logger.info(
            f"Return {return_id} transitioned: {current_state} → {target_state}"
        )
    
    @abstractmethod
    async def on_state_change(
        self, 
        return_id: UUID, 
        old_state: str, 
        new_state: str,
        context: Optional[Dict] = None
    ) -> None:
        """Handle state change side effects."""
        pass


class SaleReturnWorkflow(ReturnWorkflow):
    """Workflow for sale returns."""
    
    def _initialize_transitions(self) -> None:
        """Initialize sale return transitions."""
        # INITIATED → VALIDATED
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.INITIATED,
                ReturnWorkflowState.VALIDATED,
                side_effects=[self._create_return_tasks]
            )
        )
        
        # VALIDATED → ITEMS_RECEIVED
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.VALIDATED,
                ReturnWorkflowState.ITEMS_RECEIVED,
                side_effects=[self._mark_items_received]
            )
        )
        
        # ITEMS_RECEIVED → INSPECTION_PENDING (if quality check required)
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.ITEMS_RECEIVED,
                ReturnWorkflowState.INSPECTION_PENDING,
                condition=lambda ctx: ctx.get('quality_check_required', False),
                side_effects=[self._create_inspection_tasks]
            )
        )
        
        # ITEMS_RECEIVED → REFUND_APPROVED (if no inspection needed)
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.ITEMS_RECEIVED,
                ReturnWorkflowState.REFUND_APPROVED,
                condition=lambda ctx: not ctx.get('quality_check_required', False),
                side_effects=[self._calculate_final_refund]
            )
        )
        
        # INSPECTION_PENDING → INSPECTION_COMPLETE
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.INSPECTION_PENDING,
                ReturnWorkflowState.INSPECTION_COMPLETE,
                side_effects=[self._process_inspection_results]
            )
        )
        
        # INSPECTION_COMPLETE → REFUND_APPROVED
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.INSPECTION_COMPLETE,
                ReturnWorkflowState.REFUND_APPROVED,
                side_effects=[self._calculate_final_refund]
            )
        )
        
        # REFUND_APPROVED → REFUND_PROCESSED
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.REFUND_APPROVED,
                ReturnWorkflowState.REFUND_PROCESSED,
                side_effects=[self._process_refund, self._update_inventory]
            )
        )
        
        # REFUND_PROCESSED → COMPLETED
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.REFUND_PROCESSED,
                ReturnWorkflowState.COMPLETED,
                side_effects=[self._finalize_return]
            )
        )
        
        # Allow cancellation from most states
        for state in [
            ReturnWorkflowState.INITIATED,
            ReturnWorkflowState.VALIDATED,
            ReturnWorkflowState.ITEMS_RECEIVED,
            ReturnWorkflowState.INSPECTION_PENDING
        ]:
            self._transitions.append(
                WorkflowTransition(
                    state,
                    ReturnWorkflowState.CANCELLED,
                    side_effects=[self._cancel_return]
                )
            )
    
    async def on_state_change(
        self, 
        return_id: UUID, 
        old_state: str, 
        new_state: str,
        context: Optional[Dict] = None
    ) -> None:
        """Handle sale return state changes."""
        logger.info(f"Sale return {return_id}: {old_state} → {new_state}")
        
        # Notify relevant parties
        if new_state == ReturnWorkflowState.REFUND_PROCESSED:
            await self._notify_customer_refund_processed(return_id)
        elif new_state == ReturnWorkflowState.CANCELLED:
            await self._notify_return_cancelled(return_id)
    
    # Side effect methods
    async def _create_return_tasks(self, context: Dict) -> None:
        """Create tasks for processing the return."""
        # This would create actual tasks in a task management system
        logger.info(f"Creating return tasks for {context['return_id']}")
    
    async def _mark_items_received(self, context: Dict) -> None:
        """Mark items as received."""
        logger.info(f"Marking items received for {context['return_id']}")
    
    async def _create_inspection_tasks(self, context: Dict) -> None:
        """Create quality inspection tasks."""
        logger.info(f"Creating inspection tasks for {context['return_id']}")
    
    async def _process_inspection_results(self, context: Dict) -> None:
        """Process inspection results."""
        logger.info(f"Processing inspection results for {context['return_id']}")
    
    async def _calculate_final_refund(self, context: Dict) -> None:
        """Calculate final refund amount."""
        logger.info(f"Calculating final refund for {context['return_id']}")
    
    async def _process_refund(self, context: Dict) -> None:
        """Process the actual refund."""
        logger.info(f"Processing refund for {context['return_id']}")
    
    async def _update_inventory(self, context: Dict) -> None:
        """Update inventory for returned items."""
        logger.info(f"Updating inventory for {context['return_id']}")
    
    async def _finalize_return(self, context: Dict) -> None:
        """Finalize the return."""
        logger.info(f"Finalizing return {context['return_id']}")
    
    async def _cancel_return(self, context: Dict) -> None:
        """Cancel the return."""
        logger.info(f"Cancelling return {context['return_id']}")
    
    async def _notify_customer_refund_processed(self, return_id: UUID) -> None:
        """Notify customer that refund is processed."""
        logger.info(f"Notifying customer about refund for {return_id}")
    
    async def _notify_return_cancelled(self, return_id: UUID) -> None:
        """Notify about return cancellation."""
        logger.info(f"Notifying about cancellation of {return_id}")


class PurchaseReturnWorkflow(ReturnWorkflow):
    """Workflow for purchase returns."""
    
    def _initialize_transitions(self) -> None:
        """Initialize purchase return transitions."""
        # INITIATED → VALIDATED
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.INITIATED,
                ReturnWorkflowState.VALIDATED,
                side_effects=[self._generate_rma_documents]
            )
        )
        
        # VALIDATED → ITEMS_RECEIVED (actually ITEMS_SHIPPED to supplier)
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.VALIDATED,
                ReturnWorkflowState.ITEMS_RECEIVED,
                side_effects=[self._ship_to_supplier, self._remove_from_inventory]
            )
        )
        
        # ITEMS_RECEIVED → REFUND_APPROVED (actually CREDIT_PENDING)
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.ITEMS_RECEIVED,
                ReturnWorkflowState.REFUND_APPROVED,
                side_effects=[self._create_credit_expectation]
            )
        )
        
        # REFUND_APPROVED → REFUND_PROCESSED (actually CREDIT_RECEIVED)
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.REFUND_APPROVED,
                ReturnWorkflowState.REFUND_PROCESSED,
                condition=lambda ctx: ctx.get('credit_received', False),
                side_effects=[self._process_supplier_credit]
            )
        )
        
        # REFUND_PROCESSED → COMPLETED
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.REFUND_PROCESSED,
                ReturnWorkflowState.COMPLETED,
                side_effects=[self._finalize_purchase_return]
            )
        )
        
        # Allow cancellation from early states
        for state in [
            ReturnWorkflowState.INITIATED,
            ReturnWorkflowState.VALIDATED
        ]:
            self._transitions.append(
                WorkflowTransition(
                    state,
                    ReturnWorkflowState.CANCELLED,
                    side_effects=[self._cancel_purchase_return]
                )
            )
    
    async def on_state_change(
        self, 
        return_id: UUID, 
        old_state: str, 
        new_state: str,
        context: Optional[Dict] = None
    ) -> None:
        """Handle purchase return state changes."""
        logger.info(f"Purchase return {return_id}: {old_state} → {new_state}")
        
        if new_state == ReturnWorkflowState.ITEMS_RECEIVED:
            await self._notify_accounting_items_shipped(return_id)
        elif new_state == ReturnWorkflowState.REFUND_PROCESSED:
            await self._notify_accounting_credit_received(return_id)
    
    # Side effect methods
    async def _generate_rma_documents(self, context: Dict) -> None:
        """Generate RMA documents."""
        logger.info(f"Generating RMA documents for {context['return_id']}")
    
    async def _ship_to_supplier(self, context: Dict) -> None:
        """Process shipping to supplier."""
        logger.info(f"Processing supplier shipment for {context['return_id']}")
    
    async def _remove_from_inventory(self, context: Dict) -> None:
        """Remove items from inventory."""
        logger.info(f"Removing items from inventory for {context['return_id']}")
    
    async def _create_credit_expectation(self, context: Dict) -> None:
        """Create expected credit entry."""
        logger.info(f"Creating credit expectation for {context['return_id']}")
    
    async def _process_supplier_credit(self, context: Dict) -> None:
        """Process received supplier credit."""
        logger.info(f"Processing supplier credit for {context['return_id']}")
    
    async def _finalize_purchase_return(self, context: Dict) -> None:
        """Finalize purchase return."""
        logger.info(f"Finalizing purchase return {context['return_id']}")
    
    async def _cancel_purchase_return(self, context: Dict) -> None:
        """Cancel purchase return."""
        logger.info(f"Cancelling purchase return {context['return_id']}")
    
    async def _notify_accounting_items_shipped(self, return_id: UUID) -> None:
        """Notify accounting about shipment."""
        logger.info(f"Notifying accounting about shipment for {return_id}")
    
    async def _notify_accounting_credit_received(self, return_id: UUID) -> None:
        """Notify accounting about credit."""
        logger.info(f"Notifying accounting about credit for {return_id}")


class RentalReturnWorkflow(ReturnWorkflow):
    """Workflow for rental returns."""
    
    def _initialize_transitions(self) -> None:
        """Initialize rental return transitions."""
        # INITIATED → ITEMS_RECEIVED
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.INITIATED,
                ReturnWorkflowState.ITEMS_RECEIVED,
                side_effects=[self._record_actual_return]
            )
        )
        
        # ITEMS_RECEIVED → INSPECTION_PENDING (always for rentals)
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.ITEMS_RECEIVED,
                ReturnWorkflowState.INSPECTION_PENDING,
                side_effects=[self._create_rental_inspection_checklist]
            )
        )
        
        # INSPECTION_PENDING → INSPECTION_COMPLETE
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.INSPECTION_PENDING,
                ReturnWorkflowState.INSPECTION_COMPLETE,
                condition=lambda ctx: ctx.get('inspection_complete', False),
                side_effects=[self._process_rental_inspection]
            )
        )
        
        # INSPECTION_COMPLETE → REFUND_APPROVED
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.INSPECTION_COMPLETE,
                ReturnWorkflowState.REFUND_APPROVED,
                side_effects=[self._calculate_deposit_refund]
            )
        )
        
        # REFUND_APPROVED → REFUND_PROCESSED
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.REFUND_APPROVED,
                ReturnWorkflowState.REFUND_PROCESSED,
                side_effects=[self._process_deposit_refund]
            )
        )
        
        # REFUND_PROCESSED → COMPLETED
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.REFUND_PROCESSED,
                ReturnWorkflowState.COMPLETED,
                side_effects=[self._finalize_rental_return, self._update_rental_unit_status]
            )
        )
        
        # Limited cancellation for rentals
        self._transitions.append(
            WorkflowTransition(
                ReturnWorkflowState.INITIATED,
                ReturnWorkflowState.CANCELLED,
                side_effects=[self._cancel_rental_return]
            )
        )
    
    async def on_state_change(
        self, 
        return_id: UUID, 
        old_state: str, 
        new_state: str,
        context: Optional[Dict] = None
    ) -> None:
        """Handle rental return state changes."""
        logger.info(f"Rental return {return_id}: {old_state} → {new_state}")
        
        if new_state == ReturnWorkflowState.INSPECTION_COMPLETE:
            await self._notify_customer_inspection_complete(return_id)
        elif new_state == ReturnWorkflowState.REFUND_PROCESSED:
            await self._notify_customer_deposit_processed(return_id)
    
    # Side effect methods
    async def _record_actual_return(self, context: Dict) -> None:
        """Record actual return date and calculate late fees."""
        logger.info(f"Recording actual return for {context['return_id']}")
    
    async def _create_rental_inspection_checklist(self, context: Dict) -> None:
        """Create comprehensive inspection checklist."""
        logger.info(f"Creating inspection checklist for {context['return_id']}")
    
    async def _process_rental_inspection(self, context: Dict) -> None:
        """Process inspection results and calculate damages."""
        logger.info(f"Processing inspection for {context['return_id']}")
    
    async def _calculate_deposit_refund(self, context: Dict) -> None:
        """Calculate deposit refund after all deductions."""
        logger.info(f"Calculating deposit refund for {context['return_id']}")
    
    async def _process_deposit_refund(self, context: Dict) -> None:
        """Process deposit refund."""
        logger.info(f"Processing deposit refund for {context['return_id']}")
    
    async def _finalize_rental_return(self, context: Dict) -> None:
        """Finalize rental return."""
        logger.info(f"Finalizing rental return {context['return_id']}")
    
    async def _update_rental_unit_status(self, context: Dict) -> None:
        """Update rental unit availability."""
        logger.info(f"Updating rental unit status for {context['return_id']}")
    
    async def _cancel_rental_return(self, context: Dict) -> None:
        """Cancel rental return."""
        logger.info(f"Cancelling rental return {context['return_id']}")
    
    async def _notify_customer_inspection_complete(self, return_id: UUID) -> None:
        """Notify customer about inspection completion."""
        logger.info(f"Notifying customer about inspection for {return_id}")
    
    async def _notify_customer_deposit_processed(self, return_id: UUID) -> None:
        """Notify customer about deposit refund."""
        logger.info(f"Notifying customer about deposit for {return_id}")


class WorkflowManager:
    """Manages workflows for all return types."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.workflows = {
            "SALE_RETURN": SaleReturnWorkflow(session),
            "PURCHASE_RETURN": PurchaseReturnWorkflow(session),
            "RENTAL_RETURN": RentalReturnWorkflow(session)
        }
    
    def get_workflow(self, return_type: str) -> Optional[ReturnWorkflow]:
        """Get workflow for return type."""
        return self.workflows.get(return_type)
    
    async def transition_return(
        self,
        return_id: UUID,
        return_type: str,
        current_state: str,
        target_state: str,
        context: Optional[Dict] = None
    ) -> None:
        """Transition a return through workflow."""
        workflow = self.get_workflow(return_type)
        if not workflow:
            raise ValueError(f"Unknown return type: {return_type}")
        
        await workflow.transition(return_id, current_state, target_state, context)
        await workflow.on_state_change(return_id, current_state, target_state, context)
    
    def get_allowed_transitions(
        self, 
        return_type: str, 
        current_state: str
    ) -> List[str]:
        """Get allowed transitions for current state."""
        workflow = self.get_workflow(return_type)
        if not workflow:
            return []
        
        return workflow.get_allowed_transitions(current_state)


# Import for async support
import asyncio