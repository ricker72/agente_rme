"""
MAP-01G: NECRO Undo / Redo
Undo/redo functionality for OpenTibia mapping operations
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

class OperationType(Enum):
    """Types of operations that can be undone/redone"""
    TERRAIN_PAINT = "terrain_paint"
    ITEM_PLACEMENT = "item_placement"
    ITEM_REMOVAL = "item_removal"
    METADATA_UPDATE = "metadata_update"

@dataclass
class Operation:
    """Represents a single undoable operation"""
    op_type: OperationType
    data: Dict[str, Any]
    inverse_data: Dict[str, Any]

    def apply(self, workspace=None) -> bool:
        """Apply this operation"""
        if workspace is None:
            return True

        if self.op_type == OperationType.TERRAIN_PAINT:
            x = self.data['x']
            y = self.data['y']
            z = self.data['z']
            ground_id = self.data['ground_id']
            workspace.set_ground_id(x, y, z, ground_id)
            return True

        elif self.op_type == OperationType.ITEM_PLACEMENT:
            x = self.data['x']
            y = self.data['y']
            z = self.data['z']
            item_id = self.data['item_id']
            workspace.add_item(x, y, z, item_id)
            return True

        elif self.op_type == OperationType.ITEM_REMOVAL:
            x = self.data['x']
            y = self.data['y']
            z = self.data['z']
            item_id = self.data['item_id']
            workspace.remove_item(x, y, z, item_id)
            return True

        elif self.op_type == OperationType.METADATA_UPDATE:
            # Metadata updates would need tile reference
            # Simplified for MAP-01
            return True

        return False

class UndoManager:
    """Undo/redo manager for NECRO mapping operations"""

    def __init__(self, max_history: int = 100, workspace=None):
        self.undo_stack: List[Operation] = []
        self.redo_stack: List[Operation] = []
        self.max_history = max_history
        self.recording = True
        self.workspace = workspace

    def start_transaction(self):
        """Start recording operations"""
        self.recording = True

    def end_transaction(self):
        """End recording operations"""
        self.recording = False

    def record_operation(self, operation: Operation):
        """Record an operation for undo"""
        if not self.recording:
            return

        # Clear redo stack when new operation is recorded
        self.redo_stack.clear()

        # Add to undo stack
        self.undo_stack.append(operation)

        # Limit history size
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

    def undo(self, workspace=None) -> bool:
        """Undo the last operation"""
        if not self.undo_stack:
            return False

        operation = self.undo_stack.pop()
        target = workspace or self.workspace

        # Create inverse operation for redo
        inverse_op = Operation(
            op_type=operation.op_type,
            data=operation.inverse_data,
            inverse_data=operation.data
        )

        # Apply inverse operation
        success = inverse_op.apply(target)

        if success:
            self.redo_stack.append(operation)

        return success

    def redo(self, workspace=None) -> bool:
        """Redo the last undone operation"""
        if not self.redo_stack:
            return False

        operation = self.redo_stack.pop()
        target = workspace or self.workspace

        # Apply operation
        success = operation.apply(target)

        if success:
            self.undo_stack.append(operation)

        return success

    def clear(self):
        """Clear undo/redo history"""
        self.undo_stack.clear()
        self.redo_stack.clear()

    def get_status(self) -> Dict:
        """Get current undo/redo status"""
        return {
            'can_undo': len(self.undo_stack) > 0,
            'can_redo': len(self.redo_stack) > 0,
            'undo_count': len(self.undo_stack),
            'redo_count': len(self.redo_stack)
        }

    def create_terrain_paint_operation(self, x: int, y: int, z: int,
                                     old_ground_id: int, new_ground_id: int) -> Operation:
        """Create operation for terrain painting"""
        return Operation(
            op_type=OperationType.TERRAIN_PAINT,
            data={
                'x': x,
                'y': y,
                'z': z,
                'ground_id': new_ground_id
            },
            inverse_data={
                'x': x,
                'y': y,
                'z': z,
                'ground_id': old_ground_id
            }
        )

    def create_item_placement_operation(self, x: int, y: int, z: int, item_id: int) -> Operation:
        """Create operation for item placement"""
        return Operation(
            op_type=OperationType.ITEM_PLACEMENT,
            data={
                'x': x,
                'y': y,
                'z': z,
                'item_id': item_id
            },
            inverse_data={
                'x': x,
                'y': y,
                'z': z,
                'item_id': item_id
            }
        )

    def create_item_removal_operation(self, x: int, y: int, z: int, item_id: int) -> Operation:
        """Create operation for item removal"""
        return Operation(
            op_type=OperationType.ITEM_REMOVAL,
            data={
                'x': x,
                'y': y,
                'z': z,
                'item_id': item_id
            },
            inverse_data={
                'x': x,
                'y': y,
                'z': z,
                'item_id': item_id
            }
        )

    def get_operation_log(self) -> List[Dict]:
        """Get log of recent operations"""
        return [{
            'type': op.op_type.value,
            'data': op.data
        } for op in self.undo_stack[-10:]]  # Last 10 operations
