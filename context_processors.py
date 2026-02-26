# mainapp/context_processors.py
from django.apps import apps

def cart_count(request):
    # Try DB-backed Cart first (if exists)
    try:
        Cart = apps.get_model('mainapp', 'Cart')
    except LookupError:
        Cart = None

    if request.user.is_authenticated and Cart is not None:
        try:
            cnt = Cart.objects.filter(user=request.user).count()
        except Exception:
            cnt = 0
        return {'cart_count': cnt}

    # fallback: session-based cart (guest or model not present)
    session_cart = request.session.get('cart', [])
    try:
        return {'cart_count': len(session_cart)}
    except Exception:
        return {'cart_count': 0}
