from .modules import available_modules, get_module


def portal(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {}
    match = getattr(request, "resolver_match", None)
    namespace = match.namespace if match else ""
    current = None
    for module in available_modules(request):
        if module.url_name.split(":")[0] == namespace and namespace != "portal":
            current = module
    if namespace == "portal" and match and match.url_name and match.url_name.startswith("settings"):
        current = get_module("settings")
    return {"apps": available_modules(request), "current_app": current}
