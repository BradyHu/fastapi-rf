import user.views
import keto.views
import organization.views


def register_urls(app):
    app.include_router(user.views.router)
    app.include_router(keto.views.router)
    app.include_router(organization.views.router)
