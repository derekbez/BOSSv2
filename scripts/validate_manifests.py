#!/usr/bin/env python3
"""
Manifest Validator for B.O.S.S. Mini-Apps

Validates all mini-app manifests against the blueprint schema defined in
.github/instructions/mini_app_blueprint.md

Usage:
    python scripts/validate_manifests.py [--fix-auto]

Exit codes:
    0 - All manifests valid (or warnings only)
    1 - One or more critical errors found
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


# Canonical taxonomy from blueprint
CANONICAL_TAGS = {
    "admin", "content", "network", "sensor", "novelty", "system", "utility"
}

# Required fields per blueprint
REQUIRED_FIELDS = {"name", "description", "version", "author"}

# Allowed optional fields
OPTIONAL_FIELDS = {
    "entry_point", "timeout_seconds", "timeout_behavior", "tags",
    "requires_network", "requires_audio", "external_apis", "required_env", "config"
}

# Deprecated fields that should trigger warnings
DEPRECATED_FIELDS = {
    "id", "title", "assets_required", "api_keys", "instructions"
}

# Valid timeout behaviors
VALID_TIMEOUT_BEHAVIORS = {"return", "rerun", "none"}


@dataclass
class ValidationResult:
    """Result of validating a single manifest."""
    app_name: str
    path: Path
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, message: str):
        """Add a critical error."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add a non-critical warning."""
        self.warnings.append(message)
    
    @property
    def has_issues(self) -> bool:
        """Check if there are any errors or warnings."""
        return bool(self.errors or self.warnings)


class ManifestValidator:
    """Validates mini-app manifests against blueprint schema."""
    
    def __init__(self, apps_dir: Path):
        self.apps_dir = apps_dir
        self.results: List[ValidationResult] = []
    
    def validate_all(self) -> Tuple[int, int, int]:
        """
        Validate all manifests in apps directory.
        
        Returns:
            Tuple of (total_count, error_count, warning_count)
        """
        manifest_paths = list(self.apps_dir.glob("*/manifest.json"))
        
        if not manifest_paths:
            print(f"⚠️  No manifests found in {self.apps_dir}")
            return 0, 0, 0
        
        print(f"🔍 Validating {len(manifest_paths)} manifests...\n")
        
        for manifest_path in sorted(manifest_paths):
            result = self.validate_manifest(manifest_path)
            self.results.append(result)
        
        return self._summarize_results()
    
    def validate_manifest(self, manifest_path: Path) -> ValidationResult:
        """Validate a single manifest file."""
        app_dir = manifest_path.parent
        app_name = app_dir.name
        result = ValidationResult(app_name=app_name, path=manifest_path)
        
        # Check JSON parseability
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON: {e}")
            return result
        except Exception as e:
            result.add_error(f"Could not read file: {e}")
            return result
        
        # Validate required fields
        self._check_required_fields(data, result)
        
        # Validate name matches directory
        self._check_name_match(data, app_name, result)
        
        # Validate tags
        self._check_tags(data, result)
        
        # Validate timeout_behavior
        self._check_timeout_behavior(data, result)
        
        # Check for deprecated fields
        self._check_deprecated_fields(data, result)
        
        # Check for unknown fields
        self._check_unknown_fields(data, result)
        
        # Check entry point exists
        self._check_entry_point(data, app_dir, result)
        
        return result
    
    def _check_required_fields(self, data: Dict, result: ValidationResult):
        """Check all required fields are present."""
        missing = REQUIRED_FIELDS - set(data.keys())
        if missing:
            result.add_error(f"Missing required fields: {', '.join(sorted(missing))}")
    
    def _check_name_match(self, data: Dict, app_name: str, result: ValidationResult):
        """Check manifest name matches directory name."""
        manifest_name = data.get("name")
        if manifest_name and manifest_name != app_name:
            result.add_error(
                f"Name mismatch: manifest name '{manifest_name}' != directory '{app_name}'"
            )
    
    def _check_tags(self, data: Dict, result: ValidationResult):
        """Validate tags field."""
        tags = data.get("tags")
        
        if tags is None:
            result.add_error("Missing mandatory 'tags' field")
            return
        
        if not isinstance(tags, list):
            result.add_error("Field 'tags' must be a list")
            return
        
        if not tags:
            result.add_error("Field 'tags' cannot be empty (must include at least one canonical tag)")
            return
        
        # Check for non-canonical tags
        non_canonical = set(tags) - CANONICAL_TAGS
        if non_canonical:
            suggestions = self._suggest_tags(non_canonical)
            result.add_error(
                f"Non-canonical tags found: {', '.join(sorted(non_canonical))}. "
                f"Use only: {', '.join(sorted(CANONICAL_TAGS))}. {suggestions}"
            )
    
    def _suggest_tags(self, invalid_tags: set) -> str:
        """Suggest canonical alternatives for invalid tags."""
        mapping = {
            "fun": "novelty",
            "joke": "novelty",
            "weather": "content + network",
            "demo": "utility",
            "template": "utility",
            "birds": "content",
            "astronomy": "content",
            "news": "content",
        }
        suggestions = []
        for tag in invalid_tags:
            if tag.lower() in mapping:
                suggestions.append(f"{tag}→{mapping[tag.lower()]}")
        return f"Suggestions: {', '.join(suggestions)}" if suggestions else ""
    
    def _check_timeout_behavior(self, data: Dict, result: ValidationResult):
        """Validate timeout_behavior field."""
        timeout_behavior = data.get("timeout_behavior")
        
        if timeout_behavior is None:
            result.add_warning("Missing recommended field 'timeout_behavior' (should be return/rerun/none)")
            return
        
        if timeout_behavior not in VALID_TIMEOUT_BEHAVIORS:
            result.add_error(
                f"Invalid timeout_behavior '{timeout_behavior}'. "
                f"Must be one of: {', '.join(sorted(VALID_TIMEOUT_BEHAVIORS))}"
            )
    
    def _check_deprecated_fields(self, data: Dict, result: ValidationResult):
        """Check for deprecated fields."""
        deprecated = DEPRECATED_FIELDS & set(data.keys())
        if deprecated:
            result.add_warning(
                f"Deprecated fields found: {', '.join(sorted(deprecated))}. "
                f"Migrate: id→name, title→description, remove assets_required/api_keys/instructions"
            )
    
    def _check_unknown_fields(self, data: Dict, result: ValidationResult):
        """Check for unknown/unexpected fields."""
        known = REQUIRED_FIELDS | OPTIONAL_FIELDS | DEPRECATED_FIELDS
        unknown = set(data.keys()) - known
        if unknown:
            result.add_warning(f"Unknown fields (not in schema): {', '.join(sorted(unknown))}")
    
    def _check_entry_point(self, data: Dict, app_dir: Path, result: ValidationResult):
        """Check entry point file exists."""
        entry_point = data.get("entry_point", "main.py")
        entry_path = app_dir / entry_point
        if not entry_path.exists():
            result.add_error(f"Entry point file not found: {entry_point}")
    
    def _summarize_results(self) -> Tuple[int, int, int]:
        """Print summary and return counts."""
        total = len(self.results)
        error_count = sum(1 for r in self.results if r.errors)
        warning_count = sum(1 for r in self.results if r.warnings and not r.errors)
        clean_count = total - error_count - warning_count
        
        # Print individual results
        for result in self.results:
            if result.errors:
                print(f"❌ {result.app_name}")
                for error in result.errors:
                    print(f"   ERROR: {error}")
                if result.warnings:
                    for warning in result.warnings:
                        print(f"   WARNING: {warning}")
                print()
            elif result.warnings:
                print(f"⚠️  {result.app_name}")
                for warning in result.warnings:
                    print(f"   WARNING: {warning}")
                print()
        
        # Print clean apps (optional, can be verbose)
        if clean_count > 0 and clean_count <= 5:
            for result in self.results:
                if not result.has_issues:
                    print(f"✅ {result.app_name}")
        
        # Print summary
        print("\n" + "="*60)
        print(f"📊 VALIDATION SUMMARY")
        print("="*60)
        print(f"Total manifests:  {total}")
        print(f"✅ Clean:         {clean_count}")
        print(f"⚠️  Warnings:      {warning_count}")
        print(f"❌ Errors:        {error_count}")
        print("="*60)
        
        if error_count == 0 and warning_count == 0:
            print("🎉 All manifests valid!")
        elif error_count == 0:
            print("✅ No critical errors (warnings only)")
        else:
            print("❌ Critical errors found - manifests must be fixed")
        
        return total, error_count, warning_count


def main():
    """Main entry point."""
    # Determine repository root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent
    apps_dir = repo_root / "boss" / "apps"
    
    if not apps_dir.exists():
        print(f"❌ Apps directory not found: {apps_dir}")
        sys.exit(1)
    
    validator = ManifestValidator(apps_dir)
    total, errors, warnings = validator.validate_all()
    
    # Exit with error code if critical errors found
    if errors > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
