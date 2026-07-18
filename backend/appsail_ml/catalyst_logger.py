import logging
from fastapi import Request
import datetime

logger = logging.getLogger("astra.catalyst")

def log_user_action(request: Request, action: str, query_details: str = ""):
    """Log an investigator action to the Zoho Catalyst Data Store 'AuditLogs' table.
    
    Degrades gracefully to a local logger when running outside the AppSail environment.
    """
    # 1. Fallback local logging
    now = datetime.datetime.utcnow().isoformat()
    logger.info(f"[AUDIT] {now} | Action: {action} | Details: {query_details}")
    
    # 2. Try to write to Zoho Catalyst Data Store
    try:
        import zcatalyst_sdk
        # In AppSail, catalyst credentials are automatically parsed from request headers
        catalyst_app = zcatalyst_sdk.initialize(request=request)
        
        # Get datastore instance
        datastore = catalyst_app.datastore()
        table = datastore.table("AuditLogs")
        
        # Create row (Teammate Action Required: Create 'AuditLogs' table in Catalyst Console 
        # with columns 'ActionType' (VarChar) and 'QueryDetails' (VarChar))
        row_data = {
            "ActionType": action,
            "QueryDetails": query_details
        }
        
        # Insert row into Catalyst Data Store
        table.insert_row(row_data)
        logger.info("Successfully pushed audit log to Catalyst Data Store.")
    except ImportError:
        logger.debug("zcatalyst-sdk not installed or not running in AppSail environment.")
    except Exception as e:
        # Graceful degradation so local testing never crashes
        logger.warning(f"Failed to push audit log to Catalyst: {e}. (This is normal during local runs).")
