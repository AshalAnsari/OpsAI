from fastapi import APIRouter

from app.controllers import (
    admin_controller,
    ai_controller,
    auth_controller,
    demo_webhook_controller,
    notification_controller,
    order_controller,
    product_controller,
    support_controller,
    user_controller,
    webhook_controller,
)

api_router = APIRouter()
api_router.include_router(auth_controller.router)
api_router.include_router(user_controller.router)
api_router.include_router(product_controller.router)
api_router.include_router(order_controller.router)
api_router.include_router(admin_controller.router)
api_router.include_router(support_controller.router)
api_router.include_router(ai_controller.router)
api_router.include_router(notification_controller.router)
api_router.include_router(webhook_controller.router)
api_router.include_router(demo_webhook_controller.router)
