from .basket import Basket
from .models import WishItem



def basket(request):
    return {'basket':Basket(request)}


def wishlist_count(request):
    if request.user.is_authenticated:
        wish = WishItem.objects.filter(user=request.user).count()
    else:
        wish = 0 
    return {'wish':wish}