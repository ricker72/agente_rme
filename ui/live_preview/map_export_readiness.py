"""
MAP-01H: NECRO OpenTibia Export Preparation
Export readiness checking for OpenTibia compatibility
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass

from .map_brushes import VALID_ITEM_IDS

@dataclass
class ExportIssue:
    """Represents an export compatibility issue"""
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    location: Tuple[int, int, int] = None
    details: Dict = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'type': self.issue_type,
            'severity': self.severity,
            'message': self.message,
            'location': self.location,
            'details': self.details or {}
        }

class ExportReadinessChecker:
    """Export readiness checker for NECRO project"""

    def __init__(self):
        self.issues: List[ExportIssue] = []

    def check_export_readiness(self, workspace) -> Dict:
        """Check if project is ready for OpenTibia export"""
        if not workspace or not workspace.project:
            issue = ExportIssue(
                issue_type='project_error',
                severity='error',
                message='No valid NECRO project loaded'
            )
            return {
                'ready': False,
                'has_warnings': False,
                'has_errors': True,
                'issues': [issue.to_dict()],
                'issue_count': 1,
                'error_count': 1,
                'warning_count': 0
            }

        self.issues = []

        # Check project metadata
        self._check_project_metadata(workspace.project)

        # Check tiles
        self._check_tiles(workspace.project)

        # Check items
        self._check_items(workspace.project)

        # Check regions
        self._check_regions(workspace.project)

        # Check spawns
        self._check_spawns(workspace.project)

        # Check waypoints
        self._check_waypoints(workspace.project)

        # Determine overall readiness
        has_errors = any(issue.severity == 'error' for issue in self.issues)
        has_warnings = any(issue.severity == 'warning' for issue in self.issues)

        return {
            'ready': not has_errors,
            'has_warnings': has_warnings,
            'has_errors': has_errors,
            'issues': [issue.to_dict() for issue in self.issues],
            'issue_count': len(self.issues),
            'error_count': sum(1 for issue in self.issues if issue.severity == 'error'),
            'warning_count': sum(1 for issue in self.issues if issue.severity == 'warning')
        }

    def _check_project_metadata(self, project):
        """Check project metadata for export compatibility"""
        if not project.metadata.get('opentibia_compatible', False):
            self.issues.append(ExportIssue(
                issue_type='metadata',
                severity='error',
                message='Project not marked as OpenTibia compatible'
            ))

        if 'version' not in project.metadata:
            self.issues.append(ExportIssue(
                issue_type='metadata',
                severity='warning',
                message='Project version not specified'
            ))

    def _check_tiles(self, project):
        """Check tiles for export compatibility"""
        if not project.tiles:
            self.issues.append(ExportIssue(
                issue_type='tiles',
                severity='error',
                message='No tiles in project'
            ))
            return

        # Check for invalid ground IDs
        valid_ground_ids = {0, 1, 2, 3, 4, 5}  # Basic OpenTibia terrain

        for (x, y, z), tile in project.tiles.items():
            if tile.ground_id not in valid_ground_ids:
                self.issues.append(ExportIssue(
                    issue_type='tile',
                    severity='error',
                    message=f'Invalid ground ID: {tile.ground_id}',
                    location=(x, y, z),
                    details={'ground_id': tile.ground_id, 'valid_ids': list(valid_ground_ids)}
                ))

    def _check_items(self, project):
        """Check items for export compatibility"""
        valid_item_ids = VALID_ITEM_IDS

        for (x, y, z), tile in project.tiles.items():
            for item_id in tile.items:
                if item_id not in valid_item_ids:
                    self.issues.append(ExportIssue(
                        issue_type='item',
                        severity='error',
                        message=f'Invalid item ID: {item_id}',
                        location=(x, y, z),
                        details={'item_id': item_id, 'valid_ids': list(valid_item_ids)}
                    ))

    def _check_regions(self, project):
        """Check regions for export compatibility"""
        for region in project.regions:
            if not region.name:
                self.issues.append(ExportIssue(
                    issue_type='region',
                    severity='warning',
                    message='Region has no name',
                    details={'region': region}
                ))

            if region.min_x > region.max_x or region.min_y > region.max_y:
                self.issues.append(ExportIssue(
                    issue_type='region',
                    severity='error',
                    message='Invalid region bounds',
                    details={'region': region}
                ))

    def _check_spawns(self, project):
        """Check spawns for export compatibility"""
        for spawn in project.spawns:
            if spawn.monster_id <= 0:
                self.issues.append(ExportIssue(
                    issue_type='spawn',
                    severity='error',
                    message=f'Invalid monster ID: {spawn.monster_id}',
                    location=(spawn.x, spawn.y, spawn.z),
                    details={'monster_id': spawn.monster_id}
                ))

    def _check_waypoints(self, project):
        """Check waypoints for export compatibility"""
        for waypoint in project.waypoints:
            if not waypoint.name:
                self.issues.append(ExportIssue(
                    issue_type='waypoint',
                    severity='warning',
                    message='Waypoint has no name',
                    location=(waypoint.x, waypoint.y, waypoint.z),
                    details={'waypoint': waypoint}
                ))

    def generate_export_report(self, workspace) -> str:
        """Generate human-readable export readiness report"""
        readiness = self.check_export_readiness(workspace)
        report = []

        report.append("NECRO PROJECT EXPORT READINESS REPORT")
        report.append("=" * 40)
        report.append(f"Project: {workspace.project.name if workspace.project else 'None'}")
        report.append(f"Status: {'READY' if readiness['ready'] else 'NOT READY'}")
        report.append(f"Issues: {readiness['issue_count']} total")
        report.append(f"  Errors: {readiness['error_count']}")
        report.append(f"  Warnings: {readiness['warning_count']}")
        report.append("")

        if readiness['issues']:
            report.append("ISSUES:")
            for issue in readiness['issues']:
                severity = issue['severity'].upper()
                location = f" at {issue['location']}" if issue['location'] else ""
                report.append(f"[{severity}] {issue['message']}{location}")
        else:
            report.append("No issues found!")

        report.append("")
        report.append("RECOMMENDATIONS:")
        if readiness['ready']:
            report.append("- Project is ready for export")
            if readiness['has_warnings']:
                report.append("- Consider addressing warnings for better compatibility")
        else:
            report.append("- Fix all errors before attempting export")
            report.append("- Review warnings for potential issues")

        return "\n".join(report)

    def get_otbm_compatibility_status(self, workspace) -> Dict:
        """Get OTBM compatibility status"""
        readiness = self.check_export_readiness(workspace)

        return {
            'otbm_ready': readiness['ready'] and not readiness['has_warnings'],
            'otbm_possible': readiness['ready'],
            'blocking_issues': [issue for issue in readiness['issues'] if issue['severity'] == 'error'],
            'compatibility_score': self._calculate_compatibility_score(readiness)
        }

    def _calculate_compatibility_score(self, readiness: Dict) -> float:
        """Calculate compatibility score (0-100)"""
        if readiness['error_count'] > 0:
            return 0.0

        if readiness['warning_count'] == 0:
            return 100.0

        # Simple scoring: 100 - (warning_count * 5)
        return max(0, 100 - (readiness['warning_count'] * 5))
