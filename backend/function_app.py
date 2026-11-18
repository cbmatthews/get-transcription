"""Prism by Kaleidoscope — Azure Functions entry point.

All HTTP routes are served under /api by the linked Static Web App, which handles
sign-in and forwards the caller's identity in the x-ms-client-principal header.
Long-running work (transcription, generation) runs as Durable Functions
orchestrations, registered from blueprints in prism/.
"""

import azure.durable_functions as df
import azure.functions as func

from prism.api.health import bp as health_bp
from prism.api.me import bp as me_bp

# Auth level is ANONYMOUS because authentication happens at the Static Web App:
# linking restricts the Function App to traffic from the SWA, and each handler
# additionally checks the forwarded principal for the 'owner' role.
app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)

app.register_functions(me_bp)
app.register_functions(health_bp)
