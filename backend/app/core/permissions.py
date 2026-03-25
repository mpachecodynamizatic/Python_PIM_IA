"""
Permission system constants and utilities.

Permissions are structured as: {resource}:{level}
- resource: the part of the app (products, categories, etc.)
- level: none, read, write

Examples:
- products:read - can view products
- products:write - can create/edit products
- categories:write - can create/edit categories
"""

# Available resources in the system
RESOURCES = [
    "products",
    "categories",
    "media",
    "brands",
    "channels",
    "suppliers",
    "sync",
    "quality",
    "i18n",
    "users",
    "settings",
]

# Permission levels
PERMISSION_LEVELS = ["none", "read", "write"]

# Human-readable labels for resources
RESOURCE_LABELS = {
    "products": "Productos",
    "categories": "Categorías",
    "media": "Multimedia",
    "brands": "Marcas",
    "channels": "Canales",
    "suppliers": "Proveedores",
    "sync": "Sincronización",
    "quality": "Calidad",
    "i18n": "Traducción",
    "users": "Usuarios",
    "settings": "Configuración",
}

# Default permissions by role
ROLE_PERMISSIONS = {
    "admin": {
        # Admins have full access to everything
        resource: "write" for resource in RESOURCES
    },
    "editor": {
        # Editors can read/write most things except users and settings
        "products": "write",
        "categories": "write",
        "media": "write",
        "brands": "write",
        "channels": "write",
        "suppliers": "write",
        "sync": "write",
        "quality": "write",
        "i18n": "write",
        "users": "read",
        "settings": "read",
    },
    "viewer": {
        # Viewers can only read
        resource: "read" for resource in RESOURCES
    },
}


def get_default_permissions(role: str) -> dict[str, str]:
    """Get default permissions for a role."""
    return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["viewer"])


def has_permission(user_role: str, user_scopes: list[str], resource: str, required_level: str) -> bool:
    """
    Check if a user has permission for a resource.

    Args:
        user_role: User's role (admin, editor, viewer)
        user_scopes: Custom scopes for the user (overrides role defaults)
        resource: Resource to check (products, categories, etc.)
        required_level: Required permission level (read or write)

    Returns:
        True if user has permission, False otherwise
    """
    # Admins always have full access
    if user_role == "admin":
        return True

    # Check custom scopes first
    for scope in user_scopes:
        if ":" not in scope:
            continue
        scope_resource, scope_level = scope.split(":", 1)
        if scope_resource == resource:
            if required_level == "read":
                return scope_level in ["read", "write"]
            elif required_level == "write":
                return scope_level == "write"

    # Fall back to role default permissions
    default_perms = get_default_permissions(user_role)
    resource_level = default_perms.get(resource, "none")

    if required_level == "read":
        return resource_level in ["read", "write"]
    elif required_level == "write":
        return resource_level == "write"

    return False
