"""Verify datetime.utcnow was removed and replaced."""
import sys
sys.path.insert(0, '.')

from agente_rme.core.agents.agent_result import MultiAgentResult
r = MultiAgentResult()
print('completed_at=', r.completed_at)
assert 'utcnow' not in r.completed_at.lower(), "Still contains utcnow!"

from agente_rme.core.agents.contracts.agent_response import AgentResponse
ar = AgentResponse(agent_id='test')
print('timestamp=', ar.timestamp)
assert 'utcnow' not in ar.timestamp.lower(), "Still contains utcnow!"

from agente_rme.core.agents.contracts.agent_task import AgentTask
at = AgentTask(agent_id='test')
print('created_at=', at.created_at)
assert 'utcnow' not in at.created_at.lower(), "Still contains utcnow!"

from agente_rme.core.agents.contracts.workflow_state import WorkflowState
ws = WorkflowState()
ws.start()
print('started_at=', ws.started_at)
assert 'utcnow' not in ws.started_at.lower(), "Still contains utcnow!"
ws.complete()
print('completed_at=', ws.completed_at)
assert 'utcnow' not in ws.completed_at.lower(), "Still contains utcnow!"

# Check that we have a +00:00 suffix (timezone-aware)
assert ws.completed_at.endswith('+00:00'), f"Missing +00:00 suffix: {ws.completed_at}"

print("All timezone assertions passed!")
