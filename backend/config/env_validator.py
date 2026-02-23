"""
Battwheels OS - Environment Configuration Validator
====================================================

Validates required environment variables on application startup.
Prevents running with misconfigured or missing credentials.
"""

import os
import sys
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EnvVarLevel(str, Enum):
    """Criticality level for environment variables"""
    CRITICAL = "critical"  # App won't start without this
    REQUIRED = "required"  # App may not function correctly
    OPTIONAL = "optional"  # Nice to have


@dataclass
class EnvVarConfig:
    """Configuration for an environment variable"""
    name: str
    level: EnvVarLevel
    description: str
    default: Optional[str] = None
    min_length: int = 0
    pattern: Optional[str] = None


# Environment variable definitions
ENV_VARS: List[EnvVarConfig] = [
    # Critical - App won't start
    EnvVarConfig(
        name="MONGO_URL",
        level=EnvVarLevel.CRITICAL,
        description="MongoDB connection string",
        min_length=10
    ),
    EnvVarConfig(
        name="DB_NAME",
        level=EnvVarLevel.CRITICAL,
        description="Database name",
        min_length=1
    ),
    EnvVarConfig(
        name="JWT_SECRET",
        level=EnvVarLevel.CRITICAL,
        description="JWT signing secret (minimum 32 characters recommended)",
        min_length=16
    ),
    
    # Required - App may not function correctly
    EnvVarConfig(
        name="CORS_ORIGINS",
        level=EnvVarLevel.REQUIRED,
        description="CORS allowed origins",
        default="*"
    ),
    
    # Optional - Features won't work without these
    EnvVarConfig(
        name="EMERGENT_LLM_KEY",
        level=EnvVarLevel.OPTIONAL,
        description="Emergent LLM API key for AI features"
    ),
    EnvVarConfig(
        name="RAZORPAY_KEY_ID",
        level=EnvVarLevel.OPTIONAL,
        description="Razorpay API key ID for payments"
    ),
    EnvVarConfig(
        name="RAZORPAY_KEY_SECRET",
        level=EnvVarLevel.OPTIONAL,
        description="Razorpay API secret for payments"
    ),
    EnvVarConfig(
        name="STRIPE_API_KEY",
        level=EnvVarLevel.OPTIONAL,
        description="Stripe API key for payments"
    ),
    EnvVarConfig(
        name="ZOHO_CLIENT_ID",
        level=EnvVarLevel.OPTIONAL,
        description="Zoho API client ID for accounting sync"
    ),
    EnvVarConfig(
        name="RESEND_API_KEY",
        level=EnvVarLevel.OPTIONAL,
        description="Resend API key for email notifications"
    ),
]


def validate_env_var(config: EnvVarConfig) -> tuple:
    """
    Validate a single environment variable.
    
    Returns:
        (is_valid, value, error_message)
    """
    value = os.environ.get(config.name)
    
    if not value:
        if config.default is not None:
            return True, config.default, None
        if config.level == EnvVarLevel.OPTIONAL:
            return True, None, None
        return False, None, f"{config.name} is not set"
    
    if config.min_length > 0 and len(value) < config.min_length:
        return False, value, f"{config.name} must be at least {config.min_length} characters"
    
    return True, value, None


def validate_environment() -> Dict[str, any]:
    """
    Validate all environment variables.
    
    Returns:
        Dict with 'valid', 'critical_errors', 'warnings' keys
    """
    result = {
        'valid': True,
        'critical_errors': [],
        'required_warnings': [],
        'optional_missing': [],
        'validated_vars': {}
    }
    
    for config in ENV_VARS:
        is_valid, value, error = validate_env_var(config)
        
        if not is_valid:
            if config.level == EnvVarLevel.CRITICAL:
                result['critical_errors'].append(error)
                result['valid'] = False
            elif config.level == EnvVarLevel.REQUIRED:
                result['required_warnings'].append(error)
        elif value is None and config.level == EnvVarLevel.OPTIONAL:
            result['optional_missing'].append(config.name)
        
        if value:
            result['validated_vars'][config.name] = True
    
    return result


def check_and_report() -> bool:
    """
    Check environment variables and report findings.
    
    Returns:
        True if app should start, False if critical errors exist
    """
    result = validate_environment()
    
    logger.info("=" * 60)
    logger.info("ENVIRONMENT VALIDATION")
    logger.info("=" * 60)
    
    if result['critical_errors']:
        logger.error("CRITICAL ERRORS - Application cannot start:")
        for error in result['critical_errors']:
            logger.error(f"  ✗ {error}")
    
    if result['required_warnings']:
        logger.warning("WARNINGS - Some features may not work:")
        for warning in result['required_warnings']:
            logger.warning(f"  ⚠ {warning}")
    
    if result['optional_missing']:
        logger.info("OPTIONAL - Not configured (features disabled):")
        for var in result['optional_missing']:
            logger.info(f"  - {var}")
    
    validated_count = len(result['validated_vars'])
    total_count = len(ENV_VARS)
    logger.info(f"Validated: {validated_count}/{total_count} environment variables")
    logger.info("=" * 60)
    
    return result['valid']


def require_startup_validation():
    """
    Run validation and exit if critical errors found.
    Call this during application startup.
    """
    if not check_and_report():
        logger.critical("Application startup aborted due to missing critical environment variables")
        logger.critical("Please check your .env file and ensure all required variables are set")
        logger.critical("See .env.example for a template")
        sys.exit(1)
